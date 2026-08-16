# Robot Channel Graph v0

## Status

**Channel research stopped (2026-08-15).** Question answered: Channel × Job Graph is commercially real. Fixtures kept. No OEM 11–50, no more distributors, no Channel Match scoring, no distributor UI.

**Next:** mixed-audience traffic on `/experiment` — [`../TRAFFIC_SPRINT.md`](../TRAFFIC_SPRINT.md) · [`../CAPABILITY_MODEL.md`](../CAPABILITY_MODEL.md)

---

## Locked distinction

A channel partner is a **route**:

```
ROBOT JOB → ROBOT MATCH → OEM → CHANNEL PARTNER → TERRITORY / CAPABILITY → PURSUIT
```

A list of 5,000 distributors is commodity data.  
Knowing **which partner should receive which job** is the product.

Resist: giant directory. Measure: **U.S. channel coverage** and **multi-OEM partners**.

---

## Objects

### `robot_channel_partner` (company)

Partner identity, locations, brands observed, partner_types[].

### `oem_channel_relationship` (edge)

OEM ↔ partner: relationship_types, territory, product_lines, authorized_status, confidence C1–C5, evidence.

### `channel_capability` (on the relationship or partner×OEM)

What the partner can **do** for this OEM — not only that they “sell”:

| Capability | Meaning |
|------------|---------|
| `sales` | Commercial sell |
| `demo` | Demo units / showroom |
| `integration` | Application / system integration |
| `deployment` | On-site install / go-live |
| `training` | Operator / maintainer training |
| `field_service` | Field repair / support |
| `warranty_service` | Warranty handling |
| `parts_inventory` | Stocks parts |
| `application_engineering` | Application engineers |

“Authorized reseller in California” ≠ “Integrator with demo units, install, and field service across the Southwest.”

Capture facts now. **Do not build Job Route Score yet.** Later:

```
Route score ∝ robot fit × territory × application fit × service capability × relationship confidence
```

---

## U.S. Channel Coverage (per OEM)

| Question | Field |
|----------|--------|
| Sells into U.S.? | `us_market` |
| Direct / channel / hybrid? | `us_go_to_market` |
| Which partners? | relationships |
| Which product lines? | `product_lines[]` |
| Territory? | `territory[]` |
| Industries / applications? | `industries[]` |
| Sell / integrate / deploy / train / service / stock? | `channel_capabilities[]` |
| Evidence grade / freshness | C1–C5 + `evidence_date` |

**Gap product (later):** jobs matched to OEM with **no** channel route in that territory → OEM recruit partner · distributor add line · SI represent locally.

---

## Distributor ICP (portfolio discovery)

```
Distributor website
  → Portfolio (Brand A robots… Brand B…)
  → RDD across portfolio
  → “We found 184 jobs for robots you sell”
       37 AMR · 24 palletizing · 18 cleaning · …
```

Often stronger than single-OEM discovery: continuous pipeline across many SKUs.

---

## Evidence grades

| Grade | Show |
|-------|------|
| C1 OEM confirms | Authorized |
| C2 Partner claims authorized | Authorized |
| C3 Joint announcement | Authorized |
| C4 Resells / commercial observed | Resells observed |
| C5 Inferred only | Do not claim authorized |

---

## Acquisition

1. OEM site first  
2. Reverse through every discovered partner site  
3. Industry / web to fill gaps  

After Batch 1 (10 OEMs): partners/OEM · C1–C3/OEM · products · territories · capabilities · **unique partners appearing on ≥2 OEMs** (network collapse).

---

## Routable Job (concept — do not score yet)

```
Robot Job → Robot Match → Channel Match → Routable Job
```

Gates: (1) partner carries a capable robot (2) territory (3) channel capability sell/integrate/deploy/service.  
Not every matched job is routable to every partner.

## Artifacts

| Path | Role |
|------|------|
| [`agibot_golden.json`](./agibot_golden.json) | Golden |
| [`batch1_10_oems_ledger.json`](./batch1_10_oems_ledger.json) | First 10 OEMs |
| [`batch1_us_channel_coverage.md`](./batch1_us_channel_coverage.md) | Coverage + multi-OEM |
| [`foreign_oem_us_wedge_50.md`](./foreign_oem_us_wedge_50.md) | Queue beyond 10 |
| [`DISTRIBUTOR_PRODUCT_EXPERIMENT.md`](./DISTRIBUTOR_PRODUCT_EXPERIMENT.md) | Reverse five |
| [`envelopes/cross_company.md`](./envelopes/cross_company.md) | Integrator envelope |
| Manipulation 25 | [`../product_sim/worksite/MANIPULATION_OPEN_WORLD_25.md`](../product_sim/worksite/MANIPULATION_OPEN_WORLD_25.md) |
| [`integrator_demo_fixture.json`](./integrator_demo_fixture.json) | Cross — jobs you can solve (fixture only) |
