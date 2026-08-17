# Manipulation Open-World 25

**Purpose:** Feed Cross Company (Doosan / UR / FANUC) — commercial, not ontology.  
**Envelope:** [cross_company.md](../envelopes/cross_company.md)  
**Results:** [manipulation_open_world_25_results.md](./manipulation_open_world_25_results.md)

## Question

> Can robot-directed discovery find **palletizing** and **machine-tending** work at real named facilities?

## Split

| Arm | Queries | Workflow |
|-----|---------|----------|
| Palletizing | 12 | case/carton off line → lift → place on pallet → pattern → complete |
| Machine tending | 13 | retrieve part → load machine → cycle → unload → place output |

## Architecture (unchanged)

```
Queries → Docs → LWOs → Work Claims → Automation Interpretation → Robot Jobs → Match
```

Requirements extensions only (not universal columns):

```json
{
  "object": "case|part|unknown",
  "weight": "unknown|range",
  "geometry": "unknown",
  "grasp": "unknown|vacuum|clamp",
  "reach": "unknown",
  "cycle_time": "unknown",
  "placement_target": "pallet|fixture|bin|unknown"
}
```

## Promotion gate

1. DIRECT or DERIVED ≥ E2  
2. Named object/placement or named machine-cycle load/unload  
3. `commercial_availability` set  
4. `investigate`: yes / weak / no  

Else → Work Claim.

## Explicit rejects

- Pure forklift putaway (Origin-class)  
- Floor scrub / inspection Spot-class  
- Already-robotic-only cells with no residual manual stack/tend (unless residual named)  
- Skilled setup/programming as the robot job  

## Pass criteria

| | |
|--|--|
| Funnel intact | Work Claim first-class |
| ≥5 palletizing Robot Jobs | named facilities |
| ≥5 machine-tending Robot Jobs | named facilities |
| Precision among Robot Jobs | ≥75% |
| Cross intersect | ≥1 job in SE footprint with cobot/industrial match |
