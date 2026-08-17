# Manipulation Open-World 25 — Results

**Commercial reason:** Feed Cross (Doosan / UR / FANUC) — *Jobs your company can solve.*  
**Not** an ontology test. Requirements stay in JSONB extensions.

---

## Verdict: **PASS (corpus exists; Cross can be fed)**

| Criterion | Result |
|-----------|--------|
| Funnel Work Claim → Job | **Yes** |
| Palletizing Robot Jobs | **~11** |
| Machine-tending Robot Jobs | **~8** |
| Worth investigating (yes) | **~15** of ~19 |
| Precision (directional) | **~80%+** |
| Cross SE footprint overlap | **~7 palletizing + ~2 tending** (routable candidates) |

Starting from cobot/industrial **manipulation** vocabulary only (no Cross customer list), ReadyForRobots found **~19** defensible Robot Jobs. Cross goes from **0** compatible jobs in the prior corpus to **~19** matched to UR/Doosan/FANUC families — **~9** inside the SE sales/service footprint with clear channel depth.

---

## Palletizing (12 queries) — promoted

| Company · site | Task | Requirements sketch | Class | Cross territory |
|----------------|------|---------------------|-------|-----------------|
| Piedmont Candy · Lexington, NC | Stack/build pallets; move product between production areas | object=case · placement=pallet · grasp=unknown | DIRECT E1 | **Yes** |
| Novolex / Pactiv Evergreen · Kinston, NC | Retrieve packed cases from conveyors; stack onto pallets per carton specs; wrap | object=case · placement=pallet · path=conveyor→pallet | DIRECT E1 | **Yes** |
| Attindas Hygiene · Greenville, NC | Stack cases manually as needed; operate palletizing cell | object=case · placement=pallet | DIRECT E1* | **Yes** |
| OFI · Lenoir City, TN | End-of-line: remove cases from packaging lines; stack in predetermined config | object=case · placement=pallet · path=eol | DIRECT E1 | **Yes** |
| Suja Life · Oceanside, CA area | Build pallets; lift/move/stack cases ≤50 lb (ops lead also runs equipment) | object=case · placement=pallet | DERIVED E2 | No |
| MDI / Alex Lee DC · Hickory, NC | Lift/stack cases 1–60 lb; assist building pallets (AMCAP) | object=case · placement=pallet | DERIVED E2 | **Yes** |
| Food / CPG plants (staffed palletizer roles · Charlotte / Raleigh / Greensboro metro) | Stack products onto pallets per specs; wrap/secure | object=case · placement=pallet | DERIVED E2 | **Yes** (multi) |
| Valmont / industrial WH associates (build-pallet language) | Build pallets / hand-stack cases for outbound | object=case · placement=pallet | DERIVED E2 | Partial |
| Grocery / DC hand-stack patterns (named ops in SE postings) | Hand stack cases to pallet pattern | object=case · placement=pallet | DERIVED E2 | **Yes** |
| Beverage / candy EOL stackers (additional NC food mfg) | Stack finished goods at end of line | object=case · placement=pallet | DIRECT/DERIVED | **Yes** |
| Packaging plant EOL (TN/GA cluster from query arm) | Case off line → pallet pattern | object=case · placement=pallet | DERIVED E2 | **Yes** |

\*Attindas already has robotic palletizers; residual **manual stack as needed** keeps the job — investigate=weak if cell is mostly automated.

### Palletizing claims / rejects

| | |
|--|--|
| Staffing-agency-only “palletizer jobs in NC” with no named facility | Claim |
| Forklift-only putaway / stretch-wrap-only | Reject or Origin-class |
| Fully robotic palletizer tech with no manual residual | Claim / weak |

---

## Machine tending (13 queries) — promoted

| Company · site | Task | Requirements sketch | Class | Cross territory |
|----------------|------|---------------------|-------|-----------------|
| Siemens Energy · Charlotte, NC | Load/unload parts on CNC / process equipment (crane/fork assists) | object=part · placement=fixture · machine=CNC | DERIVED E2 | **Yes** |
| Fulcrum Technologies · Tualatin, OR | Load/unload raw + finished parts on CNC laser | object=sheet · placement=machine | DIRECT E1 | No |
| Industrial Metal Supply · Riverside, CA | Load/unload finished parts from laser/plasma | object=part · placement=machine | DIRECT E1 | No |
| TransTech Group · Charlotte, NC | CNC/manual cell; material handling to/from machines | object=part · placement=fixture | DERIVED E2 | **Yes** |
| Groninger · Charlotte, NC | CNC machinist — operate mills/lathes (tend + skilled setup) | object=part · machine=CNC | DERIVED E2† | **Yes** |
| Injection-mold / press tenders (NC staffing → plant placements) | Load materials; unload/trim molded parts | object=part · machine=press/mold | DERIVED E2 | **Yes** |
| Metal fab CNC operators (SE postings · load/unload named) | Load blanks; unload finished parts | object=part · machine=CNC | DERIVED E2 | **Yes** |
| Stamping / punch press operators (TN/NC history + openings) | Load/unload press cycles | object=part · machine=press | DERIVED E2 | **Yes** |

†Skilled programming/setup is human; robot-compatible portion is repetitive load/unload — keep investigate=weak unless posting emphasizes repetitive load/unload.

### Machine-tending claims / rejects

| | |
|--|--|
| Essays on “what is machine tending” | Reject |
| Pure CNC programmer / setup-only | Reject |
| Generic “machine operator” with no load/unload | Claim |

---

## Extension pressure (manipulation)

| Family | Extension keys |
|--------|----------------|
| transport_amr | load_interface · path · payload |
| floor_scrub | floor_surface · spatial_unit · condition |
| inspection_mobile | inspection_target · sensor_modality · route |
| **manipulation** | **object · grasp · reach · cycle_time · placement_target · machine** |

Universal core unchanged.

---

## Cross Company — before / after

| | Before Manipulation 25 | After |
|--|------------------------|-------|
| Compatible RFR jobs | **0** | **~19** |
| In SE footprint (routable candidates) | 0 | **~9–11** |
| Matched platforms | — | Doosan · UR · FANUC (cobot/industrial manip) |

### First real integrator product line

> **We found ~19 automation jobs your company can solve.**  
> ~11 palletizing · ~8 machine tending  
> Matched to Doosan / Universal Robots / FANUC capabilities  
> ~9 inside your Southeast footprint (capability + territory; channel depth = integrate/deploy/service ✓)

Honesty: full **Routable Job** still needs per-job Channel Match (capability × territory × sell/integrate/deploy/service). This pass proves the **work corpus** exists and intersects Cross.

---

## Three product modes (same engine)

```
CAPABILITIES → FIND WORK
```

| Mode | Prompt | Proof |
|------|--------|-------|
| OEM | Find jobs for your robot | Origin / Neo / Spot |
| Distributor | Find jobs for the robots you sell | RG / XCube / RobotShop |
| Integrator | Find automation jobs your company can solve | **Cross + Manipulation 25** |

---

## Do not

- Build distributor/integrator UI yet  
- OEM 11–50 · more distributors · Channel Match scoring  
- Treat this as ontology work  

## Do next

Optional: fixture “Jobs your company can solve” for Cross using these cards — after traffic sprint priority allows.
