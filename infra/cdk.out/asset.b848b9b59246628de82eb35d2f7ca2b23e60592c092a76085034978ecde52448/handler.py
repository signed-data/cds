"""
SignedData CDS — API Lambda
GET /events?domain=sports.football&limit=10
GET /events/{domain}/{event_type}
GET /events/{id}/verify
"""
import json, os
import boto3
from datetime import datetime, timezone

s3     = boto3.client("s3")
BUCKET = os.environ["EVENTS_BUCKET"]


def _respond(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":  "application/json",
            "X-CDS-Version": "0.1.0",
            "X-Issuer":      "signed-data.org",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def _list(domain: str | None = None, limit: int = 10) -> list:
    prefix = "events/"
    if domain:
        prefix += domain.replace(".", "/") + "/"
    prefix += datetime.now(timezone.utc).strftime("%Y/%m/%d") + "/"
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix, MaxKeys=limit)
    out  = []
    for obj in resp.get("Contents", []):
        b = s3.get_object(Bucket=BUCKET, Key=obj["Key"])
        out.append(json.loads(b["Body"].read()))
    return out


def handler(event, context):
    path       = event.get("path", "/")
    method     = event.get("httpMethod", "GET")
    params     = event.get("queryStringParameters") or {}
    path_params= event.get("pathParameters") or {}

    try:
        if path.startswith("/v1/events") and method == "GET" and not path_params.get("domain"):
            domain = params.get("domain")
            limit  = min(int(params.get("limit", 10)), 100)
            evts   = _list(domain=domain, limit=limit)
            return _respond(200, {"count": len(evts), "domain": domain, "events": evts})

        if path_params.get("domain") and path_params.get("event_type"):
            domain     = path_params["domain"]
            event_type = path_params["event_type"]
            evts       = [e for e in _list(domain=domain, limit=50) if e.get("event_type") == event_type]
            return _respond(200, {"count": len(evts), "domain": domain, "event_type": event_type, "events": evts})

        if path_params.get("id") and path.endswith("/verify"):
            return _respond(200, {
                "id": path_params["id"],
                "status": "use_sdk_verifier",
                "message": "Verify locally with the CDS SDK and the issuer public key.",
                "public_key_url": "https://signed-data.org/.well-known/cds-public-key.pem",
            })

        return _respond(404, {"error": "Not found"})

    except Exception as e:
        print(f"[API] ERROR: {e}")
        return _respond(500, {"error": str(e)})
