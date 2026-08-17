# Robot market graph — vendor seed

**Locked 2026-08-10.** Seed target: **500 robot vendors** (not a calibration-only list).

## Hierarchy

```
VENDOR → FAMILY → MODEL → CONFIGURATION → CAPABILITIES → PHYSICAL PRIMITIVES → WORK ENVELOPES
```

Match query path: Work → Robot class → Robots that can do it → Vendors → Availability.  
Reverse path: Vendor → Robot → Capabilities → Envelope → Human work → Facilities → Opportunities.

## Separate robot sellers from ecosystem

| Include in vendor seed | Exclude (or tag separately) |
| --- | --- |
| Robot OEM / brand / RaaS selling machines | Pure system integrators with no robot SKU |
| White-label robot brands | Component-only (unless flagged `component_supplier`) |
| Autonomy providers shipping robot products | AI-software-only, research labs without products |

`vendor_role`: `robot_oem` | `robot_brand` | `white_label_brand` | `distributor` | `system_integrator` | `autonomy_provider` | `robot_as_a_service` | `component_supplier`

## Seed deliverable

[`docs/calibration/ReadyForRobots_Robot_Vendor_Seed_v1.xlsx`](../calibration/ReadyForRobots_Robot_Vendor_Seed_v1.xlsx)

| Sheet | Purpose |
| --- | --- |
| Vendors | 500 companies + role/category/maturity/US/sales/source |
| Robot Models | Tier-1 deep models + primary_robots stubs (expand to 1,500–2,500) |
| Category Ontology | Allocation targets by robot category |
| Vendor Coverage Dashboard | Fill vs target |

Rebuild: `python scripts/build_robot_vendor_seed_xlsx.py`  
Import: `PYTHONPATH=. python scripts/import_robot_vendor_seed.py` (`--dry-run` supported)

Seed assembly **dedupes by company name and website host** so product-line pads (e.g. six Unitree SKUs) do not inflate the vendor graph. Top-up list supplies additional unique OEMs to hit 500.

## Category allocation (500)

AMR/AGV 80 · Autonomous forklifts 40 · Industrial arms 55 · Cobots 40 · Picking/manipulation 40 · Humanoids 50 · Cleaning 30 · Hospitality/foodservice 35 · Inspection/security 25 · Agriculture 35 · Construction 25 · Healthcare service 20 · Last-mile 15 · Specialty 10

## DB mapping

`manufacturers` holds vendor graph identity (+ `vendor_role`, geographies, maturity).  
`robot_companies` remains GTM leads. Tier-1 calibration remains the deep capability subset.
