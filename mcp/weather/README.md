# SignedData MCP Server — Weather

Real-time weather and 7-day forecasts from Open-Meteo as MCP tools for Claude.
All data cryptographically signed and timestamped by signed-data.org.

## Quick Start — Remote

```json
{
  "mcpServers": {
    "signeddata-weather": {
      "url": "https://weather.mcp.signed-data.org/mcp",
      "headers": { "x-wdotnet-key": "<your-api-key>" }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `get_current_weather` | Current conditions for a city or coordinates |
| `get_forecast` | 7-day daily forecast |
| `get_hourly_forecast` | Hourly forecast for next 48h |
| `get_weather_by_coordinates` | Weather at arbitrary lat/lon |

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | No |
| `CDS_ISSUER` | Issuer URI | No (default: `signed-data.org`) |

Data source: [Open-Meteo](https://open-meteo.com) — free, no authentication required.

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.
