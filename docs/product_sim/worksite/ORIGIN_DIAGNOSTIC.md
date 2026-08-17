# Origin diagnostic — gate + footprint (2026-08-15)

**Loop:** Observe → classify → OperatingFootprintResolver + Acceptance Gate → rerun 22.  
**Not:** manual logos · SIGNAL→geography torture · recall without precision.

```bash
python3 scripts/worksite_origin_baseline.py
```

See also: [OPERATING_FOOTPRINT.md](./OPERATING_FOOTPRINT.md)

---

## Architecture

| Stream | Job |
|--------|-----|
| Supply | Robot → Capability → Compatible Work |
| Demand | Company → **Operating Footprint** → Worksite → Work |
| Timing | SIGNAL → Company/Worksite → WHY NOW |

SIGNAL should not discover the job.

---

## Worksite Acceptance Gate

ENTITY + OWNERSHIP + FUNCTION (function may be UNKNOWN).

Fixture: `Automation Engineering Warehouse` → **reject**.  
Fixture: `Riverside Distribution Center` (in company prose) → **accept**.

---

## Measured funnel (auto, no seeds)

| Stage | auto v0 | auto v0.1 + gate |
|-------|--------:|-----------------:|
| WRR | 0% | see JSON (expect ~0% until real footprint sources) |
| **WPR** | n/a | n/a or high if any accepted (junk must not pass) |
| WCR → WorkRR → ERR → JRR | starved | starved while WRR≈0 |

**Reading:** Dominant failure remains `no_worksite_known`. That is a **data-architecture** gap (need Operating Footprint corpus), not an invitation to invent places from SIGNAL.

---

## Excitement bar

Not: JRR 14% → 70% via research.

Yes: e.g. JRR ↑ with **WPR ≥ ~90%** and **0 manual company additions** — the machine learned where robots might work.
