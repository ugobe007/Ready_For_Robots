# Spot — Open-World Extension 15

**Purpose:** Extension pressure — not a persistence unlock.  
**Envelope:** [spot.md](../envelopes/spot.md) · [spot_work_translation.md](../envelopes/spot_work_translation.md)  
**Results:** [spot_open_world_15_results.md](./spot_open_world_15_results.md)

## Question

> Does Work Claim → Automation Interpretation → Robot Job still hold when the physics are *observe a target* (not move an object, not scrub a surface)?

## Architecture (unchanged)

```
Queries → Docs → LWOs → Work Claims → Automation Interpretation → Robot Jobs → Fit
```

Physics live only in `requirements` under `capability_family=inspection_mobile`.

## Budget

- **15 queries**
- No known Spot customers as seeds
- Dual-arm: ~8 EXPLOIT (PdM / thermography / walkdown / operator rounds) + ~7 EXPLORE (facilities tech / substation visual / data-center inspection)

## Promotion gate

1. DIRECT or DERIVED ≥ E2  
2. Named `inspection_target` **or** named inspection `route`  
3. `commercial_availability` set (may be unknown)  
4. `investigate`: yes / weak / no  

Else → Work Claim (retain uncertainty).

## Explicit rejects

- Tote transport · floor scrub  
- Armed security response  
- Certified NDT / Level II *judgment as the robot job*  
- Multi-state travel thermographer as the job unit (claim OK)

## Pass criteria

| | |
|--|--|
| Funnel intact | Work Claim still first-class |
| New extension shape | Without Origin/Neo universal columns |
| ≥3 operating contexts | e.g. plant · substation · data center |
| Precision among Robot Jobs | ≥75% |
| Density | ≥4 investigate=yes / 10 queries |
