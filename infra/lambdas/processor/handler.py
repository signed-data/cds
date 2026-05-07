"""
SignedData CDS — Processor Lambda
SQS → optional LLM enrichment via ai-gateway-rs → S3 → EventBridge
"""
import json, os
import urllib.request
import boto3
from datetime import datetime, timezone

s3          = boto3.client("s3")
eventbridge = boto3.client("events")

BUCKET       = os.environ["EVENTS_BUCKET"]
EVENT_BUS    = os.environ["EVENT_BUS_NAME"]
MODEL_ID     = os.environ.get("AI_MODEL", "nova-micro")
ENRICH       = os.environ.get("ENRICH_WITH_LLM", "false").lower() == "true"
_GATEWAY_URL = os.environ.get("AI_GATEWAY_URL", "").rstrip("/")
_GATEWAY_KEY = os.environ.get("GATEWAY_API_KEY", "")


def _enrich(event_dict: dict) -> str:
    prompt = (
        f"Domain: {event_dict.get('domain', '')}\n"
        f"Data: {json.dumps(event_dict.get('payload', {}), ensure_ascii=False)}\n"
        f"Base summary: {event_dict.get('context', {}).get('summary', '')}\n\n"
        "Generate a single concise insight (max 2 sentences) about this data. "
        "Be factual and specific."
    )
    req = urllib.request.Request(
        f"{_GATEWAY_URL}/v1/chat/completions",
        data=json.dumps({
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
        }).encode(),
        headers={
            "Authorization": f"Bearer {_GATEWAY_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"].strip()


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
