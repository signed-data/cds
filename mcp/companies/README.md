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

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
