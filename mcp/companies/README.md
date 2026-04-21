# SignedData CDS MCP Server: Brazil Companies

Signed MCP server for factual Brazilian company registration data sourced from BrasilAPI / Receita Federal.

## Install

```bash
pip install signeddata-mcp-companies
```

## Run

Stdio transport:

```bash
signeddata-mcp-companies
```

SSE transport:

```bash
signeddata-mcp-companies --transport sse --port 8012
```

For remote HTTP deployment, expose the FastMCP app through a wrapper that runs `streamable-http` on `/mcp`, as `cds-services` does for production.

## Tools

- `get_company_profile`
- `get_company_partners`
- `check_company_status`
- `validate_cnpj_tool`
- `get_cnae_info`
- `batch_company_lookup`

All factual outputs are signed by `signed-data.org` when a signing key is configured.
