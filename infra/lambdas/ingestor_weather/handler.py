"""
SignedData CDS — Weather Ingestor Lambda
Triggered by EventBridge schedule every 30 minutes.
"""
import asyncio, json, os, tempfile
import boto3

secrets = boto3.client("secretsmanager")
sqs     = boto3.client("sqs")


def handler(event, context):
    from cds.signer import CDSSigner
    from cds.sources.weather import WeatherIngestor

    pem = secrets.get_secret_value(SecretId=os.environ["SIGNING_SECRET_ARN"])["SecretString"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(pem)
        key_path = f.name

    try:
        signer   = CDSSigner(key_path, issuer=os.environ.get("CDS_ISSUER", "signed-data.org"))
        locations = json.loads(os.environ.get("LOCATIONS", "[]"))
        ingestor  = WeatherIngestor(signer=signer, locations=locations)
        events    = asyncio.run(ingestor.ingest())

        queue_url = os.environ["QUEUE_URL"]
        for ev in events:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=ev.model_dump_json(),
                MessageAttributes={
                    "domain":      {"StringValue": ev.domain,      "DataType": "String"},
                    "event_type":  {"StringValue": ev.event_type,  "DataType": "String"},
                },
            )
        print(f"[WeatherIngestor] Sent {len(events)} signed events")
        return {"statusCode": 200, "sent": len(events)}
    finally:
        os.unlink(key_path)
