# Market Graph Loop

Self-running demand ↔ supply loop for ReadyForRobots.

## Cycle

1. **Research demand** — sample HOT/WARM buyers + signal types  
2. **Index vendors** — manufacturer catalog coverage by industry bucket  
3. **Detect tension** — demand pressure vs thin supply → actionable scores  
4. **Propose matches** — vendor↔customer edges for review/surfacing  
5. **Queue customer refresh** — HOT buyers whose opportunity values may have shifted  

Optional research (when `LEAD_RESEARCH_AGENT_ENABLED=1` and `MARKET_GRAPH_RUN_RESEARCH=1`) runs lead research on the top refresh queue.

## Runtime

- Worker daemon: `app/main.py` → `_start_scheduled_market_graph_loop`  
- Service: `app/services/market_graph_loop.py`  
- Env (see `fly.toml`): `ENABLE_SCHEDULED_MARKET_GRAPH_LOOP`, `MARKET_GRAPH_EVERY_HOURS`, …  

## API

- `GET /api/v1/market-graph/status`  
- `GET /api/v1/market-graph/tensions`  
- `GET /api/v1/market-graph/matches`  
- `POST /api/v1/market-graph/run` (manual ops trigger)

Snapshot cache key: `public:market_graph:loop:v1`.

## Product use

Tension + match edges are the input for improving Results/Pipeline “why now” and vendor fit. Next steps: render tensions on Pipeline/Results and feed match edges into SCOUT activation.
