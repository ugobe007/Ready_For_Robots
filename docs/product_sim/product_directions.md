# Product directions — scored

**Problem:** Search space for “where should I sell this robot?” is too large for a salesperson.

## Six products

| Product | User gives | R4R returns | Core value |
|---------|------------|-------------|------------|
| Lead intelligence | ICP | Companies | Who to sell |
| Signal intelligence | ICP | Companies with intent | When to sell |
| Robot job board | Robot | Explicit jobs/RFPs | Known demand |
| **Robot job discovery** | Robot capabilities | Inferred physical work | **Hidden demand** |
| Robot matching | Job requirements | Compatible robots | What to buy |
| Automation discovery | Operations/workflows | Automatable jobs | What to automate |

## Score (1–5, judgment)

| | Big problem | Differentiated | Data obtainable | Immediate utility | Defensible | Σ |
|--|-------------|----------------|-----------------|-------------------|------------|---|
| Lead intelligence | 3 | 1 | 5 | 3 | 1 | 13 |
| Signal intelligence | 3 | 2 | 5 | 3 | 2 | 15 |
| Job board | 3 | 3 | 2 | 5 | 2 | 15 |
| **Job discovery** | **5** | **5** | **3** | **5** | **5** | **23** |
| Robot matching | 4 | 3 | 4 | 4 | 4 | 19 |
| Automation discovery | 5 | 4 | 2 | 4 | 5 | 20 |

**Wedge:** Job discovery. Matching and automation-discovery are natural expansions (WHO reverse / Face B).

## Job attractiveness dimensions (surround the result)

Not “are they buying?” — **adoption friction / attractiveness**:

| Dimension | Meaning |
|-----------|---------|
| Work exists | Confidence physical work is present |
| Robot fit | Capability match + blockers |
| Operational pain | Labor / throughput / safety / capacity |
| Economic potential | Scale / burden worth changing |
| Integration complexity | Facility / WMS / process disruption |
| Comparable deployments | Peer proof |
| Buying evidence | Weaker early; fine if low |

Example readout:

```
Work exists        ██████████ 96%
Robot fit          █████████░ 91%
Operational pain   ████████░░ 78%
Economic potential ████████░░ 76%
Integration        ████░░░░░░ HIGH
Comparable deployments  3 found
Buying evidence    █████░░░░░ 48%
```

Salesperson sees opportunity **and** uncertainty.
