# Spot — Capability → Work translation

**Gate:** Observed human work ≠ robot action. Spot **observes**; humans **judge**.

```
Observed Workflow
  → Friction / inspection-route requirement
  → Robot-compatible task (Spot capture along route)
  → Robot Job
  → Fit
```

Core objects unchanged: Work Claim · Evidence · Automation Interpretation · Robot Job.

---

## Vocabulary

### A. Direct Spot work

| ID | Description |
|----|-------------|
| `inspect_route_waypoints` | Visit waypoints; capture observations |
| `thermal_capture_at_targets` | Thermal images of panels/equipment |
| `visual_gauge_capture` | Photograph gauges / indicators for later read |
| `recurring_plant_walkdown` | Repeatable facility inspection path |
| `hazard_area_observation` | Observe where human presence is costly |

### B. Search terms (not robot actions)

operator rounds · PdM route · thermography route · walkdown · gauge reading · facility inspection rounds · CBM route

### C. Reject

tote transport · floor scrub · armed security response · certified NDT judgment-as-robot · multi-state travel thermographer as the job unit

---

## Promotion gate

Robot Job if:

1. DIRECT | DERIVED≥E2  
2. Named `inspection_target` **or** `route`/`spatial` inspection path  
3. `commercial_availability` set  

### Spot requirements (extension — not universal columns)

| Field | Examples |
|-------|----------|
| `inspection_target` | electrical_panel · gauge · rotating_equipment · transformer · leak_point · unknown |
| `sensor_modality` | rgb · thermal · acoustic · mixed · unknown |
| `route` | operator_round · pdm_route · walkdown · patrol · unknown |
| `observation_frequency` | every_shift · daily · weekly · unknown |
| `hazard_environment` | plant_floor · substation · data_center · yard · unknown |

---

## Correct vs incorrect job

**Correct:** Capture thermal images of electrical panels along the plant PdM route each week.  
**Incorrect:** Be the Level II thermographer. · Secure the warehouse.
