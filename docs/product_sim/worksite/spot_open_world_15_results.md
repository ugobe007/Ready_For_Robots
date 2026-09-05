# Spot — Open-World Extension 15 — Results

**Purpose:** Extension pressure — observe-a-target ≠ move-object ≠ scrub-surface.  
**Not** a persistence gate (already earned).  
**Queries:** 15 · no known Spot customers  

---

## Verdict: **PASS (core holds; new extension shape confirmed)**

| Criterion | Result |
|-----------|--------|
| Funnel still Work Claim → Interpretation → Robot Job | **Yes** |
| Promotion without inventing Origin/Neo columns | **Yes** — `inspection_target` / `sensor_modality` / `route` |
| ≥3 contexts | manufacturing · food plant · data center · substation · oil/gas walkdown |
| Precision among Robot Jobs | **~85%** (11/13) |
| Density | **~7.3** yes / 10 q |

Starting only with Spot’s capabilities, ReadyForRobots found **~13** defensible inspection Robot Jobs across **~12** companies/sites; **~11** worth investigating.

---

## Promoted (investigate=yes)

| Company · site | Task | Requirements sketch | Class |
|----------------|------|---------------------|-------|
| Owens Corning · Minneapolis, MN | PdM routes · IR + vibration + ultrasound | target=rotating_equipment+electrical · modality=thermal+vibration · route=pdm_route · freq=scheduled | DIRECT E1 |
| Cambria · Le Sueur, MN | Condition monitoring routes · IR/vibration/ultrasound | same family | DIRECT E1 |
| Kraft Heinz · Garland, TX | CBM routes · IR + vibration collection | target=plant_equipment · modality=thermal+vibration · route=pdm_route | DIRECT E1 |
| Baxters NA | CBM visual/thermal/vibration/acoustic routes | modality=mixed · route=pdm_route | DIRECT E1 |
| ATS (customer factories) | On-site PdM · thermal/ultrasound/vibration | route=pdm_route · hazard=plant_floor | DIRECT E1 |
| LTTS @ ExxonMobil facilities | Field walkdown · photo capture · equipment verify | target=equipment_tag · modality=rgb · route=walkdown | DERIVED E2 |
| Enbridge LNG · Magna, UT | Equipment inspections / walkdowns / operational checks | target=plant_equipment · route=walkdown · hazard=lng_plant | DERIVED E2 |
| HB NEXT · Georgia substations | Operational & visual substation inspections · photos | target=transformer/breaker · modality=rgb · route=substation_round · hazard=substation | DIRECT E1 |
| CBRE data center · Barker, NY | Building walkthroughs · meter readings UPS/PDU | target=meters_panels · modality=rgb · route=facility_round · hazard=data_center | DERIVED E2 |
| xAI facilities ops | Daily inspections of critical MEP systems | target=mep_equipment · route=facility_round · hazard=data_center | DERIVED E2 |
| Google DC facilities tech | Inspect/tour systems · assess working order | target=facility_systems · route=facility_round | DERIVED E2 |

### Weak

| | |
|--|--|
| Guidant / multi-site travel thermographer | Capture physics fit; **job unit is travel** — claim/weak |
| ABM electrical thermography specialist | Strong thermal language; site locality soft |

### Claims (not jobs)

Operator-rounds *essays* without site · security CCTV desk roles · API-certified vessel inspectors (judgment-primary)

### Rejects

Armed security response · Origin tote jobs · Neo scrub jobs · “robot is the certified Level II”

---

## Extension pressure lesson

| Robot | Physics | Extension keys |
|-------|---------|----------------|
| Origin | move object | load_interface · path · payload |
| Neo | act on surface | floor_surface · spatial_unit · condition |
| Spot | observe target | inspection_target · sensor_modality · route · observation_frequency · hazard_environment |

Universal core **did not** need new tables — only a new `requirements` shape under `capability_family=inspection_mobile`.

Grammar hypothesis emerging:

```
ACTION × TARGET × ROUTE × OPERATING CONTEXT × FREQUENCY
inspect|capture × gauge|panel|equipment × pdm_route|walkdown × plant|substation|dc × every_shift|weekly
```

Still do not freeze this as ontology — three robots informed it; product uses `requirements` JSONB.

---

## Persistence implication

Confirmed: persist thin core + family extensions. Spot did not break the model.
