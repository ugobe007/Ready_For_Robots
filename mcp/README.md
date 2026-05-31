# Ready For Robots MCP Server

Publish Ready For Robots intelligence to third-party AI sites, marketplaces, and agent platforms via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

## Strategy

### Why MCP

Third parties (robot OEM marketplaces, integrator sites, research portals) need structured access to:

- **Humanoid benchmark data** (HEIF scores, specs, vendor catalog)
- **Buyer-intent leads** (HOT/WARM signals, industry filters)
- **Matching** (robot URL → ideal customers via Robot Ready)
- **Analysis** (ontological NLP on text/URLs)

MCP is the emerging standard for AI tool integration. Your marketplace already stores `mcp_server_url` on connections — this server is the canonical URL partners register.

### Architecture

```
Third-party AI client  →  MCP (Streamable HTTP)  →  Ready For Robots REST API
                              /mcp                      ready-2-robot.fly.dev/api/*
```

The MCP layer is a **read-mostly proxy** with curated tools. It does not expose admin, scraper, purge, or CRM routes.

### Tool tiers

| Tier | Tools | Auth | Notes |
|------|-------|------|-------|
| **Public read** | `humanoid_*`, `search_*`, `leads_*`, `trending_*`, `get_company`, `list_robot_vendors` | Optional bearer | Cached REST endpoints; safe for embeds |
| **Compute** | `analyze_text`, `analyze_url`, `robot_ready_match` | Bearer recommended | Scraping / matching; rate-limit per partner |
| **Premium** | `scout_chat` | Bearer + `R4R_MCP_PREMIUM=1` | Server-side LLM cost |

### Authentication model

Two layers (both optional in dev):

1. **MCP bearer** — partners send `Authorization: Bearer <R4R_MCP_BEARER_TOKEN>` to `/mcp`
2. **Partner API key** — MCP forwards `X-R4R-API-Key` to the REST API (future rate-limit tiers)

Generate per-partner tokens; store mapping in admin/marketplace connections.

### Deployment options

**A. Mounted on Fly (recommended)** — same app, no extra infra:

```bash
fly secrets set R4R_MCP_ENABLED=1 R4R_MCP_BEARER_TOKEN=<long-random-token>
```

Endpoint: `https://ready-2-robot.fly.dev/mcp`

**B. Standalone process** — separate port or machine:

```bash
R4R_MCP_TRANSPORT=streamable-http R4R_MCP_PORT=8090 python -m app.mcp
```

**C. Local stdio** — Cursor / Claude Desktop:

```json
{
  "mcpServers": {
    "ready-for-robots": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "/path/to/Ready_For_Robots",
      "env": {
        "R4R_API_BASE": "https://ready-2-robot.fly.dev"
      }
    }
  }
}
```

### Partner onboarding checklist

1. Issue `R4R_MCP_BEARER_TOKEN` (and optional `R4R_PARTNER_API_KEY`)
2. Share MCP URL: `https://ready-2-robot.fly.dev/mcp`
3. Partner registers URL in marketplace connection (`connectionType: mcp_server`)
4. Document allowed tools for their use case (humanoid-only vs full intelligence)
5. Monitor usage via Fly logs / future partner analytics

### Roadmap

- [ ] Per-partner API keys in DB (marketplace connections → key rotation)
- [ ] Rate limits by `X-R4R-API-Key` on REST layer
- [ ] OpenAPI → auto-generated MCP tool sync
- [ ] Webhook push when humanoid catalog updates
- [ ] OAuth for enterprise partners (FastMCP OAuth provider)

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `R4R_MCP_ENABLED` | off | Mount MCP at `/mcp` on FastAPI |
| `R4R_MCP_BEARER_TOKEN` | — | Require bearer auth on MCP HTTP |
| `R4R_MCP_PREMIUM` | off | Enable `scout_chat` tool |
| `R4R_API_BASE` | `https://ready-2-robot.fly.dev` | REST API base URL |
| `R4R_PARTNER_API_KEY` | — | Forwarded as `X-R4R-API-Key` |
| `R4R_MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` for standalone |
| `R4R_MCP_HOST` | `0.0.0.0` | Standalone HTTP bind |
| `R4R_MCP_PORT` | `8090` | Standalone HTTP port |

## Tool reference

See `app/mcp/server.py` for implementations. OpenAPI docs: `/api/docs`.

## Tests

```bash
pytest tests/test_mcp_server.py -q
```
