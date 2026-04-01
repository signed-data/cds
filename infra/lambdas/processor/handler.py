"""
SignedData CDS — Processor Lambda
SQS → optional Bedrock enrichment → S3 → EventBridge
"""
import json, os
import boto3
from datetime import datetime, timezone

s3          = boto3.client("s3")
eventbridge = boto3.client("events")
bedrock     = boto3.client("bedrock-runtime")

BUCKET       = os.environ["EVENTS_BUCKET"]
EVENT_BUS    = os.environ["EVENT_BUS_NAME"]
MODEL_ID     = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
ENRICH       = os.environ.get("ENRICH_WITH_LLM", "false").lower() == "true"


def _enrich(event_dict: dict) -> str:
    prompt = (
        f"Domain: {event_dict.get('domain', '')}\n"
        f"Data: {json.dumps(event_dict.get('payload', {}), ensure_ascii=False)}\n"
        f"Base summary: {event_dict.get('context', {}).get('summary', '')}\n\n"
        "Generate a single concise insight (max 2 sentences) about this data. "
        "Be factual and specific."
    )
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": 150}),
        contentType="application/json", accept="application/json",
    )
    body = json.loads(resp["body"].read())
    return body["output"]["message"]["content"][0]["text"].strip()


def handler(event, context):
    from cds.schema import CDSEvent
    processed = failed = 0

    for record in event.get("Records", []):
        try:
            body    = json.loads(record["body"])
            ev      = CDSEvent(**body)

            if ENRICH and ev.context:
                try:
                    body["context"]["summary"] = _enrich(body)
                    body["context"]["model"]   = MODEL_ID
                except Exception as e:
                    print(f"[Processor] Bedrock failed: {e}")

            # Persist to S3
            domain = ev.domain.replace(".", "/")
            date   = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            key    = f"events/{domain}/{date}/{ev.id}.json"
            s3.put_object(
                Bucket=BUCKET, Key=key,
                Body=json.dumps(body, ensure_ascii=False, default=str),
                ContentType="application/json",
            )

            # Publish to EventBridge
            eventbridge.put_events(Entries=[{
                "EventBusName": EVENT_BUS,
                "Source":       f"cds.{ev.domain}",
                "DetailType":   ev.event_type,
                "Detail":       json.dumps(body, default=str),
            }])

            print(f"[Processor] Stored s3://{BUCKET}/{key}")
            processed += 1

        except Exception as e:
            print(f"[Processor] ERROR: {e}")
            failed += 1
            raise

    return {"processed": processed, "failed": failed}
