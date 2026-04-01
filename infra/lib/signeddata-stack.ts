import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as logs from "aws-cdk-lib/aws-logs";
import * as route53 from "aws-cdk-lib/aws-route53";
import * as route53targets from "aws-cdk-lib/aws-route53-targets";
import * as acm from "aws-cdk-lib/aws-certificatemanager";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import { Construct } from "constructs";
import * as path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Domain configuration ───────────────────────────────────
// Both hosted zones already exist in Route53 (registered via GoDaddy,
// nameservers pointing to AWS). We just look them up by domain name.
const PRIMARY_DOMAIN = "signed-data.org";
const ALT_DOMAIN     = "signeddata.org";

export class SignedDataStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── Hosted zones (already exist — lookup only) ─────────
    const primaryZone = route53.HostedZone.fromLookup(this, "PrimaryZone", {
      domainName: PRIMARY_DOMAIN,
    });

    const altZone = route53.HostedZone.fromLookup(this, "AltZone", {
      domainName: ALT_DOMAIN,
    });

    // ── ACM certificate (covers both domains + www) ────────
    // Must be in us-east-1 for CloudFront.
    // If deploying to a different region, use DnsValidatedCertificate
    // or a cross-region reference.
    const certificate = new acm.Certificate(this, "SiteCert", {
      domainName: PRIMARY_DOMAIN,
      subjectAlternativeNames: [
        `www.${PRIMARY_DOMAIN}`,
        ALT_DOMAIN,
        `www.${ALT_DOMAIN}`,
      ],
      validation: acm.CertificateValidation.fromDnsMultiZone({
        [PRIMARY_DOMAIN]:        primaryZone,
        [`www.${PRIMARY_DOMAIN}`]: primaryZone,
        [ALT_DOMAIN]:            altZone,
        [`www.${ALT_DOMAIN}`]:   altZone,
      }),
    });

    // ── S3 — static site bucket ────────────────────────────
    const siteBucket = new s3.Bucket(this, "SiteBucket", {
      bucketName:        `signeddata-site-${this.account}-${this.region}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption:        s3.BucketEncryption.S3_MANAGED,
      removalPolicy:     cdk.RemovalPolicy.RETAIN,
    });

    // ── CloudFront distribution ────────────────────────────
    const oac = new cloudfront.S3OriginAccessControl(this, "SiteOAC", {
      description: "OAC for signed-data.org site bucket",
    });

    const distribution = new cloudfront.Distribution(this, "SiteDist", {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket, {
          originAccessControl: oac,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        compress: true,
      },
      domainNames: [
        PRIMARY_DOMAIN, `www.${PRIMARY_DOMAIN}`,
        ALT_DOMAIN,     `www.${ALT_DOMAIN}`,
      ],
      certificate,
      defaultRootObject: "index.html",
      errorResponses: [
        { httpStatus: 403, responseHttpStatus: 200, responsePagePath: "/index.html" },
        { httpStatus: 404, responseHttpStatus: 200, responsePagePath: "/index.html" },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
    });

    // ── Route53 A records (both domains + www) ─────────────
    const cfTarget = new route53targets.CloudFrontTarget(distribution);

    new route53.ARecord(this, "PrimaryARecord", {
      zone: primaryZone, recordName: PRIMARY_DOMAIN,
      target: route53.RecordTarget.fromAlias(cfTarget),
    });
    new route53.ARecord(this, "PrimaryWwwARecord", {
      zone: primaryZone, recordName: `www.${PRIMARY_DOMAIN}`,
      target: route53.RecordTarget.fromAlias(cfTarget),
    });
    new route53.ARecord(this, "AltARecord", {
      zone: altZone, recordName: ALT_DOMAIN,
      target: route53.RecordTarget.fromAlias(cfTarget),
    });
    new route53.ARecord(this, "AltWwwARecord", {
      zone: altZone, recordName: `www.${ALT_DOMAIN}`,
      target: route53.RecordTarget.fromAlias(cfTarget),
    });

    // ── Secrets Manager — RSA signing key ──────────────────
    const signingSecret = new secretsmanager.Secret(this, "SigningKey", {
      secretName:  "cds/signing-private-key",
      description: "RSA-4096 private key for CDS event signing",
    });

    // ── S3 — immutable event store ─────────────────────────
    const eventsBucket = new s3.Bucket(this, "EventsBucket", {
      bucketName:  `signeddata-events-${this.account}-${this.region}`,
      versioned:   true,
      encryption:  s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [{
        transitions: [{
          storageClass:     s3.StorageClass.INTELLIGENT_TIERING,
          transitionAfter:  cdk.Duration.days(30),
        }],
      }],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // ── SQS — ingestion queue ──────────────────────────────
    const dlq = new sqs.Queue(this, "IngestDlq", {
      queueName:       "signeddata-ingest-dlq",
      retentionPeriod: cdk.Duration.days(14),
    });

    const ingestQueue = new sqs.Queue(this, "IngestQueue", {
      queueName:         "signeddata-ingest-queue",
      visibilityTimeout: cdk.Duration.seconds(90),
      deadLetterQueue:   { queue: dlq, maxReceiveCount: 3 },
    });

    // ── EventBridge — custom bus ───────────────────────────
    const eventBus = new events.EventBus(this, "EventBus", {
      eventBusName: "signeddata-event-bus",
    });

    // ── Lambda Layer — shared CDS Python library ───────────
    const cdsLayer = new lambda.LayerVersion(this, "CdsLayer", {
      layerVersionName: "signeddata-cds-core",
      description:      "CDS schema, signer, and ingestor base classes",
      code:             lambda.Code.fromAsset(
        path.join(__dirname, "../../sdk/python/cds"),
      ),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
    });

    // ── IAM roles ──────────────────────────────────────────
    const ingestorRole = new iam.Role(this, "IngestorRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )],
    });
    signingSecret.grantRead(ingestorRole);
    ingestQueue.grantSendMessages(ingestorRole);

    const processorRole = new iam.Role(this, "ProcessorRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )],
    });
    eventsBucket.grantWrite(processorRole);
    ingestQueue.grantConsumeMessages(processorRole);
    eventBus.grantPutEventsTo(processorRole);
    processorRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        "bedrock:InvokeModel",
      ],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-micro-v1:0`,
        `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-lite-v1:0`,
      ],
    }));

    const apiRole = new iam.Role(this, "ApiRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )],
    });
    eventsBucket.grantRead(apiRole);

    // ── Lambda — Weather Ingestor (cron every 30 min) ──────
    const weatherIngestor = new lambda.Function(this, "WeatherIngestor", {
      functionName: "signeddata-ingestor-weather",
      runtime:      lambda.Runtime.PYTHON_3_12,
      handler:      "handler.handler",
      code:         lambda.Code.fromAsset(
        path.join(__dirname, "../lambdas/ingestor_weather")
      ),
      layers:       [cdsLayer],
      role:         ingestorRole,
      timeout:      cdk.Duration.seconds(60),
      memorySize:   256,
      environment: {
        QUEUE_URL:          ingestQueue.queueUrl,
        SIGNING_SECRET_ARN: signingSecret.secretArn,
        CDS_ISSUER:         "signed-data.org",
        LOCATIONS: JSON.stringify([
          { city: "São Paulo",     lat: -23.55, lon: -46.63 },
          { city: "Jundiaí",       lat: -23.19, lon: -46.88 },
          { city: "Rio de Janeiro",lat: -22.91, lon: -43.17 },
          { city: "Brasília",      lat: -15.78, lon: -47.93 },
          { city: "London",        lat:  51.51, lon:  -0.13 },
          { city: "New York",      lat:  40.71, lon: -74.01 },
        ]),
      },
      logGroup: new logs.LogGroup(this, "WeatherIngestorLogGroup", {
        logGroupName: "/aws/lambda/signeddata-ingestor-weather",
        retention:    logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    new events.Rule(this, "WeatherSchedule", {
      schedule: events.Schedule.rate(cdk.Duration.minutes(30)),
      targets:  [new targets.LambdaFunction(weatherIngestor)],
    });

    // ── Lambda — Processor (SQS → S3 + EventBridge) ────────
    const processor = new lambda.Function(this, "Processor", {
      functionName: "signeddata-processor",
      runtime:      lambda.Runtime.PYTHON_3_12,
      handler:      "handler.handler",
      code:         lambda.Code.fromAsset(
        path.join(__dirname, "../lambdas/processor")
      ),
      layers:       [cdsLayer],
      role:         processorRole,
      timeout:      cdk.Duration.seconds(90),
      memorySize:   512,
      environment: {
        EVENTS_BUCKET:    eventsBucket.bucketName,
        EVENT_BUS_NAME:   eventBus.eventBusName,
        BEDROCK_MODEL_ID: "amazon.nova-micro-v1:0",
        ENRICH_WITH_LLM:  "true",
      },
      logGroup: new logs.LogGroup(this, "ProcessorLogGroup", {
        logGroupName: "/aws/lambda/signeddata-processor",
        retention:    logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    processor.addEventSource(new SqsEventSource(ingestQueue, {
      batchSize:          10,
      maxBatchingWindow:  cdk.Duration.seconds(10),
    }));

    // ── Lambda — API Consumer ──────────────────────────────
    const apiHandler = new lambda.Function(this, "ApiHandler", {
      functionName: "signeddata-api",
      runtime:      lambda.Runtime.PYTHON_3_12,
      handler:      "handler.handler",
      code:         lambda.Code.fromAsset(
        path.join(__dirname, "../lambdas/api")
      ),
      layers:       [cdsLayer],
      role:         apiRole,
      timeout:      cdk.Duration.seconds(30),
      memorySize:   256,
      environment: {
        EVENTS_BUCKET: eventsBucket.bucketName,
      },
      logGroup: new logs.LogGroup(this, "ApiHandlerLogGroup", {
        logGroupName: "/aws/lambda/signeddata-api",
        retention:    logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // ── API Gateway ────────────────────────────────────────
    const api = new apigateway.RestApi(this, "Api", {
      restApiName: "SignedData CDS API",
      description: "Curated Data Standard — consumer API",
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
      deployOptions: {
        stageName:           "v1",
        throttlingRateLimit:  100,
        throttlingBurstLimit: 200,
      },
    });

    const integration  = new apigateway.LambdaIntegration(apiHandler);
    const eventsRes    = api.root.addResource("events");
    eventsRes.addMethod("GET", integration);
    const domainRes    = eventsRes.addResource("{domain}");
    domainRes.addResource("{event_type}").addMethod("GET", integration);
    eventsRes.addResource("{id}").addResource("verify").addMethod("GET", integration);

    // ── Outputs ────────────────────────────────────────────
    new cdk.CfnOutput(this, "SiteUrl",         { value: `https://${PRIMARY_DOMAIN}` });
    new cdk.CfnOutput(this, "CfDistributionId",{ value: distribution.distributionId, exportName: "SignedDataCfDistId" });
    new cdk.CfnOutput(this, "SiteBucketName",  { value: siteBucket.bucketName,       exportName: "SignedDataSiteBucket" });
    new cdk.CfnOutput(this, "ApiEndpoint",     { value: api.url,                     exportName: "SignedDataApiEndpoint" });
    new cdk.CfnOutput(this, "EventsBucketOutput", { value: eventsBucket.bucketName,     exportName: "SignedDataEventsBucket" });
    new cdk.CfnOutput(this, "IngestQueueUrl",  { value: ingestQueue.queueUrl,        exportName: "SignedDataIngestQueue" });
    new cdk.CfnOutput(this, "EventBusName",    { value: eventBus.eventBusName,       exportName: "SignedDataEventBus" });
    new cdk.CfnOutput(this, "SigningSecretArn",{ value: signingSecret.secretArn,     exportName: "SignedDataSigningKey" });
  }
}
