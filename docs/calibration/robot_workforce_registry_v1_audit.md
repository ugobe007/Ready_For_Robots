# Robot Workforce Registry v1 — audit

**File:** [readyforrobots_robot_workforce_registry_v1.xlsx](./readyforrobots_robot_workforce_registry_v1.xlsx)  
**JSON:** [robot_workforce_registry_overlay_v1.json](./robot_workforce_registry_overlay_v1.json)  
**Verdict:** Keep as a **researcher overlay**. Do not replace [robot_employment_universe_v1.json](./robot_employment_universe_v1.json) or write claimed SKUs into FIND / `primary_robots`.

The workbook is the right *shape* (employment, not a 500-vendor directory). It is the wrong *epistemic status* to treat as catalog: one product cell per company, every source stamped official, 172 of 200 marked available for work now.

## What it is

Four sheets: `Robot Workforce Registry` (200 rows), `Dashboard`, `Employment Model`, `Research Notes`.

Columns match the employment spine we want: company → robot → class → work families → capabilities → commercialization → geography → source URL.

The Employment Model sheet is aligned with R4R: a robot is qualified by the work it can perform, not by OEM marketing category. The Research Notes sheet already says commercialization is a working classification and the next pass should add payload, runtime, and deployment evidence. That caveat is correct — the Dashboard does not follow it.

## Dashboard vs placement-ready

| Dashboard claim | Count | R4R reading |
|-----------------|-------|-------------|
| Companies | 200 | Same target as the compiled universe; different membership |
| High placement priority | 172 | Too high. Includes “UR Series”, “CRX / LR Mate / M Series”, Cat MineStar, AES Maximo |
| Available for work now | 172 | Same 172 as High. Availability is a copy of priority, not evidence |
| Conditional | 14 | Includes Figure 03 — more honest than Digit-as-scaled |
| Research / validate | 14 | Includes Tesla Optimus and Boston Dynamics Atlas/Spot |

Readiness scores cluster at 4–5 (97 + 75). All 200 `Source Type` values are “Official company/product site”. Additional Categories is filled on **7** rows. Robot Class equals Primary Employment Category on **17** rows (category leakage).

18 primary categories vs our **19**. Hotel / housekeeping is missing (Relay is filed under restaurant / hospitality). Savioke and Relay Robotics are the same product line listed twice.

## Shape vs catalog rule

FIND and the compiled universe cap at **three named robots per OEM**, copied from catalog. This workbook is **one row per company**:

- Pudu dumps six products in one cell (`CC1 / MT1 / SH1 / BellaBot / FlashBot / HolaBot`).
- Boston Dynamics is `Atlas / Spot` on the Atlas URL, marked Research / not yet. **Stretch is absent** — the warehouse robot we can actually place.
- Figure is `03` only (catalog has 01 / 02 / 03).
- Universal Robots / FANUC / ABB / KUKA / Yaskawa are series labels, not SKUs.
- Geek+ is a workflow slogan (`Shelf-to-Person`) instead of P800 / PopPick.
- Dexterity is `Dexterity AI Robots`.
- Caterpillar is MineStar Command; AES is Maximo — both High / Yes / score 5.

## Vs compiled universe (200)

Name match (normalized company / host): **141 overlap**, **59 overlay-only**, **59 universe-only**.

SKU comparison on the overlap (claimed cell vs catalog `robots[]`):

| Result | n | Meaning |
|--------|---|---------|
| Exact-ish | 20 | Same names (Digit, FieldPrinter, da Vinci, Flippy, …) |
| Partial overlap | 52 | Extra or missing siblings in the cell |
| Different string | 34 | Series / slogan vs named SKU |
| Catalog empty, overlay names a product | 35 | **Unverified.** Do not ingest without OEM-page check |

The 35 newly named core gaps include plausible OEM pages (SlipBot, Chef, LIFTBOT, Amiga, Maestro, BlueROV2) and weak labels (AES Maximo, “Waste Sorting Robots”, “Autonomous Haulage System”). Those 35 are the only overlay rows worth a verification pass — still not catalog until the source URL shows the name.

### Overlay-only names that may belong (placeable labor, not in the 200)

Keep out of FIND until cataloged. Candidates to *consider* for roster swaps, not auto-add:

Nomagic, OTTO (Rockwell / Clearpath lineage), Aethon TUG, Skydio X10, Hilti Jaibot, Elite / Mecademic / Productive cobots, Tompkins tSort, ICE Cobotics, Nala, CivDot, Ecorobotix ARA, Percepto, Kiwibot.

Many overlay-only rows fail the placeable-labor bar or duplicate an existing universe OEM (Savioke ≈ Relay; OTTO ≈ Clearpath OTTO already in fill).

### Universe-only (keep)

Dusty’s category peers that the workbook dropped, plus named-product fill: MiR, Magazino, Fetch/Zebra, 6 River Chuck, Reflex, Rainbow HUBO2, LG CLOi, CenoBots, Sparkoz, Vanderlande, and the industrial-arm fill set. The compiled roster preferred **named catalog SKUs** over ChatGPT’s 200-name list.

## Spotlight

| Company | Overlay | Compiled universe | Call |
|---------|---------|-------------------|------|
| Dusty | FieldPrinter, construction layout, High / Yes | FieldPrinter, `construction` | Good |
| Agility | Digit, tote handling, High / Yes | Digit | Good |
| Miso | Flippy | Flippy | Good |
| Intuitive | da Vinci | da Vinci | Good as a named product; surgical placement is a separate ICP question |
| Figure | 03 only, Conditional / Medium | 01 / 02 / 03 | Overlay availability is more honest than Digit-as-scaled; do not drop 01/02 |
| Boston Dynamics | Atlas / Spot, Research, Atlas URL | Spot + Stretch + Atlas | **Miss.** Stretch is the warehouse candidate |
| Pudu | 6 names, cleaning primary | BellaBot, PuduBot 2, KettyBot | Split rows; cap 3 |
| Universal Robots | UR Series | UR3e / UR5e / UR10e | Series ≠ robot |
| ABB | GoFa / SWIFTI / IRB | ASTI AMR only in our catalog | Do not invent the rest |
| Geek+ | Shelf-to-Person | P800, PopPick | Slogan ≠ SKU |
| AES | Maximo, High / Yes / 5 | empty `robots[]` | Not catalog; not “available now” |
| Caterpillar | MineStar Command, High / Yes / 5 | named haulage fill | Platform, not a placeable robot résumé |

## What to do next (does not auto-ingest)

1. Leave compiled `robots[]` as catalog-only.
2. Use overlay company names as a **research queue**, not a FIND index.
3. Verify the 35 empty-catalog claims on the `source_url`. Accept at most three **page-visible** names.
4. Split multi-product cells (Pudu, KEENON, Boston Dynamics Stretch vs Spot vs Atlas) into one row per robot.
5. Re-score Available for Work from deployment evidence, not from “Commercial / Scale” marketing language.
6. Decide roster swaps (Nomagic, Aethon, Skydio, Hilti, …) against the placeable-labor bar — not against a 200-name quota.

Rebuild overlay JSON from the workbook:

```bash
python3 scripts/export_workforce_registry_overlay.py
```
