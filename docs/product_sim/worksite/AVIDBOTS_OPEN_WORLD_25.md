# Avidbots Neo — Open-World Transfer 25

**Input:** robot + vocabulary only ([avidbots_neo.md](../envelopes/avidbots_neo.md) · [avidbots_neo_work_translation.md](../envelopes/avidbots_neo_work_translation.md))  
**No company list. No known Avidbots customers. No seeded airport/hospital/retailer accounts.**

**Question this run answers:**

> Does robot-directed discovery transfer beyond Origin — or was Origin 100 an AMR search hack?

---

## Architecture (unchanged)

```
Queries
  → candidate documents
  → inspected documents
  → accepted LWOs
  → Work Claims
  → Automation Interpretation
  → Robot Jobs
  → Fit / ranked
```

Core objects stay: **Work Claim · Evidence · Automation Interpretation · Robot Job**.  
Neo-specific requirement fields live *under* Robot Job (`floor_surface`, `spatial_unit`, `operating_context`, `condition`) — not Origin `load_interface`.

**Do not** modify shared ontology to “fit cleaning” before the run. Let results tell us what the grammar needs.

---

## Budget

- **25 queries** (transfer test — not 100)  
- ≤5 docs inspected / query  
- Dual-arm: ~12 EXPLOIT (scrubber / floor-tech / overnight machine) + ~13 EXPLORE (EVS / custodian / night porter / hard-floor maintenance)

---

## Promotion gate (from Neo envelope)

Robot Job only if:

1. DIRECT **or** DERIVED ≥ E2  
2. `floor_surface` **or** `spatial_unit` named  
3. `commercial_availability` set (may be unknown)  
4. `investigate`: yes / weak / no  

Else → Work Claim.

---

## Explicit rejects

- Carpet-primary · restroom-only · outdoor · fogging-only  
- Generic “cleaner” with no floor evidence (claim OK)  
- Naming known Neo customers as search seeds  
- Declaring “clean the building” as the robot action  

---

## Success frame (locked)

> Starting only with Avidbots Neo’s capabilities, ReadyForRobots searched the open economy and found **X** defensible floor-scrub Robot Jobs across **Y** companies and **Z** locations; **W** were worth investigating.

Transfer **passes** if:

1. Promotion precision among Robot Jobs ≥ **70%** worth investigating  
2. Jobs appear in **≥3** distinct operating-context types (not one vertical)  
3. At least **~4** investigate=yes jobs / 10 queries (density floor for small-n)  
4. Zero dependence on known-customer seeding  

Transfer **fails** if:

- Only generic janitor claims, or  
- Only one context type, or  
- Gate cannot be applied without inventing Origin-like load fields, or  
- Discovery requires account lists to work  

---

## What we are *not* doing

- Persist schema / homepage / Cal / CRM  
- Another Origin search  
- Pre-designing ACTION×TARGET×CONTEXT as product ontology  

---

## Deliverables

| Artifact | Path |
|----------|------|
| Protocol | this file |
| Results | [`avidbots_open_world_25_results.md`](./avidbots_open_world_25_results.md) |
| Ledger | [`avidbots_open_world_25_ledger.json`](./avidbots_open_world_25_ledger.json) |
| Transfer verdict | in results — vs Origin 100 |

After verdict: either green-light persistence of core objects + family extensions, or document why transfer failed.
