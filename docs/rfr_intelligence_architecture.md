# ReadyForRobots Intelligence Architecture

**Graph** = intelligence structure (what connects a robot to a job opportunity)  
**Loop** = learning behavior (what we learned after we acted)

> Find the Work. Match the Robot. Test the Truth. Learn from Every Deployment.

This is the canonical product architecture. Implementation lands incrementally on top of existing catalog, primitives (`ontology/primitives.v1.json`), robotability (`docs/robotability_schema_v1.json`), and the worker market-graph loop (`docs/market_graph_loop.md`).

---

## 1. Graph at the center: WORK

Not company-first. Not robot-first. **Work-first.**

```
                         COMPANY
                            │
                            ▼
                         FACILITY
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
            LABOR SIGNAL          OPERATING SIGNAL
                 │                     │
         job / wage / shift       expansion / uptime
                 │                     │
                 └──────────┬──────────┘
                            ▼
                           WORK
                            │
                  ┌─────────┼─────────┐
                  ▼         ▼         ▼
                TASK     OBJECT   ENVIRONMENT
                  │         │         │
                  └─────────┼─────────┘
                            ▼
                     WORK PRIMITIVES
                            │
                            ▼
                        ROBOTABILITY
                            │
                            ▼
                     ROBOT CAPABILITY
                            │
                            ▼
                          ROBOT
                            │
                            ▼
                         VENDOR
```

### Commercial extension (derived opportunity stack)

```
WORK
 │
 ├── LABOR PRESSURE
 ├── OPERATIONAL EXPOSURE
 ├── AUTOMATION DRIVER
 ├── ROBOT MATCH
 ├── BUYABILITY
 └── DEPLOYABILITY
          │
          ▼
     OPPORTUNITY
          │
          ▼
        BUYER
```

### Bidirectional traversal (one graph, two products)

| Direction | Path | Product |
|-----------|------|---------|
| **Robot → Job** | ROBOT → CAPABILITIES → PRIMITIVES → MATCHING WORK → FACILITIES → LABOR PRESSURE → JOBS | *Find Jobs for Robots.* |
| **Job → Robot** | JOB → TASKS → WORK → PRIMITIVES → ROBOTABILITY → ROBOT CATEGORIES → MODELS → VENDORS | *Which robot should automate this work?* |

One graph supports both sides of the marketplace without requiring a marketplace today.

---

## 2. Eight major node families

| # | Family | Contents |
|---|--------|----------|
| 1 | **ROBOT** | Manufacturer, model, configuration, capability, payload, mobility, manipulation, environment, commercial maturity |
| 2 | **WORK** | Task, action, object, origin, destination, frequency, volume, performance requirement |
| 3 | **LABOR** | Job, wage, shift, overtime, openings, persistence, temp labor, turnover |
| 4 | **FACILITY** | Plant, warehouse, hospital, hotel, restaurant, DC + topology (receiving → storage → production → staging → shipping) |
| 5 | **COMPANY** | Industry, scale, growth, automation maturity, facilities |
| 6 | **PEOPLE** | Plant manager, ops leader, warehouse manager, automation engineer, economic buyer |
| 7 | **OPPORTUNITY** | Derived: Robot + Work + Facility + Timing |
| 8 | **DEPLOYMENT** | What happened: robot, qty, task, performance, failures, economics, expansion |

**DEPLOYMENT is crucial** — it closes the loop from prediction to truth.

Canonical schema: `ontology/rfr_graph.v1.json`  
Work primitives: `ontology/primitives.v1.json`  
Robotability records: `docs/robotability_schema_v1.json`

---

## 3. Edges (where the value is)

Examples (not exhaustive — see schema):

| Subject | Predicate | Object |
|---------|-----------|--------|
| COMPANY | OWNS | FACILITY |
| FACILITY | EMPLOYS | JOB |
| JOB | PERFORMS | WORK |
| WORK | REQUIRES | PRIMITIVE |
| ROBOT | SUPPORTS | PRIMITIVE |
| ROBOT | MATCHES | WORK |
| WORK | CAUSES | LABOR_PRESSURE |
| WORK | IMPACTS | PRODUCTION |
| PERSON | OWNS | WORKFLOW |
| OPPORTUNITY | INVOLVES | ROBOT |
| OPPORTUNITY | TARGETS | FACILITY |
| OPPORTUNITY | RESOLVED_AS | DEPLOYMENT |

Every edge carries:

- `confidence` (0–1)
- `truth_state` (e.g. `OEM_VERIFIED`, `INFERRED`, `CUSTOMER_CONFIRMED`, `DEPLOYMENT_VERIFIED`, `DISPROVED`)
- `valid_from` / `valid_to`
- `source`

**Spec claim ≠ real-world success.**  
`ROBOT CAN_PERFORM WORK` (OEM_VERIFIED) is not the same as  
`ROBOT SUCCESSFULLY_PERFORMED WORK` (DEPLOYMENT_VERIFIED, facility_type, payload, uptime).

---

## 4. Knowledge Graph vs Deployment Evidence

| Layer | Meaning |
|-------|---------|
| **Knowledge Graph** | Everything we currently believe (robots, companies, jobs, tasks, facilities, people, capabilities, workflows) |
| **Deployment Evidence** | Public-record observations of robots performing work (OEM/customer announcements, case studies, earnings, conferences) — **not** live customer telemetry |

Knowledge generates predictions. **Deployment Evidence** strengthens or weakens them from the public market. Optional later: customer-confirmed site facts and telemetry as a stronger evidence tier.

See [`docs/deployment_evidence_engine.md`](deployment_evidence_engine.md).

---

## 5. The Loop (learning behavior)

```
OBSERVE LABOR → FIND WORK → MATCH ROBOT → OBSERVE DEPLOYMENTS
→ STRENGTHEN/WEAKEN MATCH → RANK → KEEP WATCHING
```

Sales stages (ACT / QUALIFY) remain product workflow; **deployment feedback does not wait on our customers.**

| Stage | What happens |
|-------|----------------|
| **OBSERVE LABOR** | Labor + market signals |
| **UNDERSTAND** | Reconstruct physical WORK (tasks, objects, primitives) |
| **MATCH** | Robot ↔ work ↔ facility (capability) |
| **OBSERVE DEPLOYMENTS** | Public Deployment Evidence for similar work |
| **STRENGTHEN / WEAKEN** | Evidence-based Work Match |
| **PRIORITIZE / ACT** | Where sales should act |
| **KEEP WATCHING** | New pilots, commercial deploys, expansions → update robot model |

Example: third-shift forklift hiring → reconstruct pallet flow → high Work Match → CALL NOW → customer confirms 1,600 pallets/day → site survey finds 1,900 kg payload vs 1,500 kg robot → loss `PAYLOAD_BLOCKER` → ontology learns “5,000-lb forklift” signal → payload risk on next similar opp.

---

## 6. Four simultaneous loops

All feed the same graph:

| Loop | Path | Learns |
|------|------|--------|
| **Labor** | Job postings → tasks → work → robotability → opportunity → customer validation → better task extraction | Understanding human work |
| **Robot** | Specs → capabilities → work match → deployment → actual performance → better capability model | Spec vs real-world capability |
| **Sales** | Opportunity → call priority → action → response → qualify → win/loss → better buyability | What leads to meetings → surveys → deployments |
| **Deployment** | Work → robot → pilot → performance → failures → interventions → economics → expansion | What actually works |

```
                 READYFORROBOTS GRAPH
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
    LABOR              ROBOTS          FACILITIES
       │                 │                 │
       └──────────────┐  │  ┌──────────────┘
                      ▼  ▼  ▼
                        WORK
                         │
                         ▼
                    OPPORTUNITY
                         │
                ┌────────┴────────┐
                ▼                 ▼
              SALES           DEPLOYMENT
                │                 │
                └────────┬────────┘
                         ▼
                       TRUTH
                         │
                         ▼
                       LEARN ──► GRAPH
```

---

## 7. Similarity (future power)

With enough deployments, a new facility connects to similar successful Work Graphs:

> Food factory · 3 shifts · pallets · production→warehouse · ~1,000 kg  
> → 42 similar · 11 qualified · 7 pilots · 6 successes  
> → Robot A: 5 successes · Robot B: 1 failure  

Recommendation becomes evidence-based, not just “specs look compatible.”

---

## 8. Four fundamental questions the graph must answer

1. **Robot sellers:** Where should my robot work?  
2. **Companies:** Which of my jobs should become robot jobs?  
3. **Manufacturers:** What should we build next? (unmet Work Units)  
4. **Investors:** Which robots address the largest pools of unmet work?

---

## 9. Implementation map (current → next)

| Layer | Today | Next |
|-------|--------|------|
| Nodes ROBOT / VENDOR | `manufacturers`, robot catalog, humanoid catalog | Config/capability edges with confidence |
| Nodes COMPANY / LABOR signals | `companies`, `signals`, HOT/WARM classify | Explicit JOB / FACILITY nodes |
| WORK / PRIMITIVES | `work_unit_reconstruct.py` → primitives.v1 from signal/job text | Persist WORK units (beyond snapshot); full JD capture |
| ROBOT capabilities | `robot_primitives.py` category → primitives.v1 | Product-page claim → primitive cards |
| MATCH | `primitive_match.py` + market graph edges | Surface Work Match on Pipeline / Results |
| OPPORTUNITY | Pipeline leads, SCOUT matches | Derived opportunity nodes from Work Match |
| WORK persistence | `work_units` + `work_matches` tables | Full JD capture + facility link |
| DEPLOYMENT EVIDENCE | `deployment_*` tables + public seed claims | Recurring crawler across ~500 vendors |
| Loop runner | `market_graph_loop.py` + persist WORK | Deployment evidence crawl worker |
| Product | Pipeline Work Match badge | Comparable deployment evidence on cards |

See also: [`docs/work_unit_reconstruction.md`](work_unit_reconstruction.md), [`docs/deployment_evidence_engine.md`](deployment_evidence_engine.md).

**Codified system name:** Graph (map) + Loop (continuous conversion of prediction → truth).
