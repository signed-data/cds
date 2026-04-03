"""
SignedData CDS — Weather Ingestor
Source: Open-Meteo API (free, no auth)
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.vocab import CDSSources, CDSVocab

API_BASE = "https://api.open-meteo.com/v1"


class WeatherIngestor(BaseIngestor):
    content_type = CDSVocab.WEATHER_CURRENT

    def __init__(
        self,
        signer: Any,
        latitude: float = -23.5505,
        longitude: float = -46.6333,
        location_name: str = "São Paulo, BR",
    ) -> None:
        super().__init__(signer)
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name

    async def fetch(self) -> list[CDSEvent]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{API_BASE}/forecast",
                params={
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "current_weather": True,
                },
            )
            resp.raise_for_status()

        fp = "sha256:" + hashlib.sha256(resp.content).hexdigest()
        data = resp.json()
        current = data.get("current_weather", {})

        payload = {
            "location": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": current.get("weathercode"),
            "time": current.get("time"),
        }

        summary = (
            f"Weather in {self.location_name}: "
            f"{current.get('temperature', '?')}°C, "
            f"wind {current.get('windspeed', '?')} km/h"
        )

        return [CDSEvent(
            content_type=CDSVocab.WEATHER_CURRENT,
            source=SourceMeta(id=CDSSources.OPEN_METEO, fingerprint=fp),
            occurred_at=datetime.now(timezone.utc),
            lang="en",
            payload=payload,
            event_context=ContextMeta(summary=summary, model="rule-based-v1"),
        )]
