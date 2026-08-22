# RobCo experiment — Robot Job Cards

**Date:** 2026-08-22  
**Audience:** Lewis at RobCo  
**Sentence:** We found machine-tending jobs for RobCo robots.  
**Source:** `docs/product_sim/worksite/manipulation_open_world_25_ledger.json` + `app/data/robot_job_match_corpus.json`  
**Model:** [`docs/robot_employment_model.md`](../robot_employment_model.md)

The corpus currently holds **five named employers** with evidenced CNC / machine-tending work. We do not invent five more to say “10.” Unknown labor cost stays Unknown.

RobCo qualification is **pending** until Lewis submits the robot URL. These are jobs (work), not pre-scored leads.

---

## Job RFR-MT-001 — Siemens Energy

| Field | Value |
|-------|--------|
| Employer | Siemens Energy |
| Workplace | Charlotte, NC |
| Job | CNC / process machine loader |
| Work being performed | Load and unload parts on CNC / process machines (material handling assist). |
| Job requirements | Object: part. Placement: fixture. Machine: CNC. Payload: up to 50 lb (stated). Grasp: unknown. |
| Work volume | Unknown |
| Current labor | Unknown — posting describes a CNC/process operator using material-handling devices. |
| Evidence | Manipulation ledger E2 (derived). Corpus `manip_siemens_energy_charlotte_nc`. |
| Robot qualification | Pending robot résumé (submit RobCo URL). |
| Open questions | Part geometry · Fixture design · Skill vs tend split · Crane dependency |
| Next step | Site assessment: can a tending cell reach the fixture without the crane? |

## Job RFR-MT-002 — Fulcrum Technologies

| Field | Value |
|-------|--------|
| Employer | Fulcrum Technologies |
| Workplace | Tualatin, OR |
| Job | CNC laser loader / unloader |
| Work being performed | Load raw material and unload finished parts on a CNC laser. |
| Job requirements | Object: sheet metal. Placement: machine. Machine: CNC laser. |
| Work volume | Unknown |
| Current labor | Unknown — laser cutting operator explicitly loads/unloads raw and finished parts. |
| Evidence | Ledger E1 (direct). Corpus `manip_fulcrum_tualatin_or`. |
| Robot qualification | Pending robot résumé. |
| Open questions | Sheet size · Gripper · Nesting |
| Next step | Site assessment: sheet size vs gripper and cell envelope. |

## Job RFR-MT-003 — Industrial Metal Supply

| Field | Value |
|-------|--------|
| Employer | Industrial Metal Supply |
| Workplace | Riverside, CA |
| Job | Laser / plasma finished-part unloader |
| Work being performed | Load and unload finished parts from laser/plasma cutting machines. |
| Job requirements | Object: part. Placement: machine. Machine: laser/plasma. |
| Work volume | Unknown |
| Current labor | Unknown — laser operator loads/unloads within a training window. |
| Evidence | Ledger E1 (direct). Corpus `manip_ims_riverside_ca`. |
| Robot qualification | Pending robot résumé. |
| Open questions | Part mix · Weight · EOAT |
| Next step | Site assessment: part mix and end-of-arm tooling. |

## Job RFR-MT-004 — TransTech Group

| Field | Value |
|-------|--------|
| Employer | TransTech Group |
| Workplace | Charlotte, NC |
| Job | CNC and manual-cell workpiece mover |
| Work being performed | Move workpieces to and from CNC and manual machining cells. |
| Job requirements | Object: part. Placement: fixture. Machine: CNC. |
| Work volume | Unknown |
| Current labor | Unknown — CNC Quickmill operator also uses forklift/crane. |
| Evidence | Ledger E2 (derived). Corpus `manip_transtech_charlotte_nc`. Investigate: weak. |
| Robot qualification | Pending robot résumé. Conditional even after a URL if the role is skilled fab plus tend. |
| Open questions | Repetitive tend vs skilled fab mix |
| Next step | Qualify the job first: how much of the shift is repetitive load/unload? |

## Job RFR-MT-005 — groninger

| Field | Value |
|-------|--------|
| Employer | groninger |
| Workplace | Charlotte, NC |
| Job | CNC mill / lathe tender |
| Work being performed | Tend CNC mills/lathes — workpiece load/unload around the cycle. Setup stays human. |
| Job requirements | Object: part. Placement: fixture. Machine: CNC mill/lathe. |
| Work volume | Unknown |
| Current labor | Unknown — CNC machinist; robot portion is repetitive load/unload. |
| Evidence | Ledger E2 (derived). Corpus `manip_groninger_charlotte_nc`. Investigate: weak. |
| Robot qualification | Pending robot résumé. |
| Open questions | How much of the role is tend vs program |
| Next step | Site assessment: cycle-side load/unload vs programming time. |

---

## What we will not tell Lewis

- That these are leads or HOT buyers.
- That RobCo is already Qualified (no robot URL, no résumé).
- That each job is worth $N / year (no evidenced FTE or loaded cost).
- That we found 10 when we found 5.

## What we will tell Lewis

> Lewis — we found five machine-tending jobs. Each card is an employer, a workplace, and the work being performed. Submit the RobCo URL and we will qualify your robot against these jobs — capabilities against requirements, not a category guess.
