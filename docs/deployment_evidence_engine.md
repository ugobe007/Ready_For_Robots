# Deployment Evidence Engine

**V1 name:** Deployment Intelligence Engine  
**Not:** live deployment telemetry / customer OS data.

We scrape and structure the **public record** of robot deployments, connect it to the Work Graph, and use those observations as evidence — without waiting for customers to share operating data.

Rename: **DEPLOYMENT TRUTH → DEPLOYMENT EVIDENCE**

## Why

OEM announcements, case studies, earnings calls, and customer press already report:

- Digit / GXO: 100,000+ totes; 65,000+ operating hours; nine facilities  
- Figure / BMW: 11-month deployment; 90,000+ parts; 10-hour weekday shifts  

Those are evidence. Some are excellent; some are marketing. The system must know the difference.

## Loop

```
OBSERVE LABOR → identify human work
→ MATCH ROBOT → identify opportunity
→ OBSERVE DEPLOYMENTS → public evidence of similar work
→ STRENGTHEN / WEAKEN MATCH → rank opportunity
→ KEEP WATCHING
```

Public robotics news is the feedback mechanism. Our own customer telemetry can enhance later; it is **not** required.

## Graph branch

```
ROBOT
  ├─ CAPABILITY
  └─ DEPLOYMENT EVIDENCE
         → CUSTOMER → FACILITY → WORK
              → TASK / SCALE / OUTCOME → METRICS
```

Deployment news maps onto **primitives.v1** (`PERFORMED` / performed_primitives), so evidence strengthens Work Match — not just "deployed at BMW."

## Stages (hype filter)

`ontology/deployment_stages.v1.json`

ANNOUNCED → AGREEMENT → EVALUATION → PROOF_OF_CONCEPT → PILOT → LIVE_DEPLOYMENT → COMMERCIAL_DEPLOYMENT → MULTI_SITE → EXPANSION → COMPLETED / CANCELLED / UNKNOWN

A "partners with" headline must not become "successfully deployed."

## Evidence levels A–F

| Level | Meaning |
|-------|---------|
| A | Customer / joint + operating metrics |
| B | OEM + named customer + metrics |
| C | Named commercial, no metrics |
| D | Pilot / PoC |
| E | Agreement / intent |
| F | Vague / unverified |

## Quantity hygiene

Never equate plans with reality:

- `robots_announced` / `robots_committed` / `robots_pilot` / `robots_live` / `robots_verified`
- `sites_announced` / `sites_live` / `sites_verified`

## Database (V1)

| Table | Role |
|-------|------|
| `deployment_sources` | URL, type, tier A–F |
| `deployment_events` | Structured claim + stage + workflow + quantity fields |
| `deployment_evidence` | Claim excerpts linked to sources |
| `deployment_metrics` | Extracted numbers |

Code: `app/services/deployment_evidence_engine.py`  
Models: `app/models/deployment_evidence.py`

## Work Match formula (conceptual)

```
Work Match ≈ Capability Match + Deployment Evidence + Commercial Maturity
```

Pipeline cards surface Work Match % and optional comparable deployment evidence.

## Commercial Evidence Score

Per robot: commercial sites, named customers, pilots vs production, expansions, reported hours, metrics coverage.

## Hermes bridge (nightly crawler)

External crawler path: Hermes skill `rfr-deployment-evidence` →  
`POST /api/v1/market-graph/deployment-evidence/ingest`  
See [`docs/hermes_deployment_bridge.md`](hermes_deployment_bridge.md).

Seed examples (Digit/GXO, Figure/BMW, Figure/Catalyst agreement) still load from the market-graph loop. Full ~500-vendor fan-out is incremental via the Hermes watchlist.
