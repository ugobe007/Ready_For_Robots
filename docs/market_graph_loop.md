# Market Graph Loop

Self-running **OBSERVE → LEARN** cycle for ReadyForRobots.

Canonical product architecture: [`docs/rfr_intelligence_architecture.md`](rfr_intelligence_architecture.md)  
Graph ontology: [`ontology/rfr_graph.v1.json`](../ontology/rfr_graph.v1.json)

**Graph** = what connects a robot to a job. **Loop** = what we learn after we act.

## Cycle (canonical stages)

| Stage | v1 status | What this worker does |
|-------|-----------|------------------------|
| **OBSERVE** | done | Sample HOT/WARM buyers + signal types; index manufacturer catalog |
| **UNDERSTAND** | done | WORK units from signal/job text → `primitives.v1` (`work_unit_reconstruct`) |
| **MATCH** | done | Primitive-spine Work Match + hard blockers (`WRONG_MACHINE_*`) |
| **PRIORITIZE** | done | Tension scores + customer refresh queue |
| **ACT** | deferred | Seller outreach in Pipeline / CRM |
| **QUALIFY** | deferred | Customer-confirmed facts → Truth Graph |
| **VERIFY** | deferred | Pilot / deployment / loss → DEPLOYMENT nodes |
| **LEARN** | partial | Persist Knowledge snapshot; optional research refresh |

Optional research (when `LEAD_RESEARCH_AGENT_ENABLED=1` and `MARKET_GRAPH_RUN_RESEARCH=1`) runs lead research on the top refresh queue.

## Knowledge vs Truth

Snapshot payload includes:

- `knowledge` — beliefs from signals + catalog (current loop output)
- `truth` — empty until QUALIFY/VERIFY write `CUSTOMER_CONFIRMED` / `DEPLOYMENT_VERIFIED` / `DISPROVED` edges

Match edges are Knowledge-layer `ROBOT MATCHES WORK` using shared `primitives.v1` codes (see [`work_unit_reconstruction.md`](work_unit_reconstruction.md)).

Additional APIs:

- `GET /api/v1/market-graph/work-units`
- `POST /api/v1/market-graph/reconstruct` (Job→Robot dry-run)

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

Tension + match edges improve Results/Pipeline “why now” and vendor fit. Next: reconstruct WORK from job text, surface Work Match, and feed Truth writeback from CRM / deployments.
