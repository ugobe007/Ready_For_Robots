# Foreign OEM → U.S. channel wedge (50)

**Purpose:** Research queue for Channel Graph v0.  
**Not** a claim that all partners are known. Fill `oem_channel_relationship` rows as evidence appears.

Protocol per OEM:

1. OEM site: Partners / Where to Buy / Distributors (C1)  
2. Known NA partners’ brand pages (C2)  
3. Press / announcements (C3)  
4. Catalog / storefront without auth (C4)  
5. Skip C5 into “authorized”

Golden complete: **AGIBOT** → see [`agibot_golden.json`](./agibot_golden.json)

---

## ~25 Chinese / Greater China

Start with **Batch 1** (10 OEMs) before expanding: [`batch1_us_channel_coverage.md`](./batch1_us_channel_coverage.md)

| # | OEM | Notes / start URLs |
|---|-----|--------------------|
| 1 | AGIBOT | Golden — RobotShop, Useabot |
| 2 | Unitree | US dealers / education + industrial |
| 3 | Dobot | Global distributor network |
| 4 | Elephant Robotics | myCobot channel |
| 5 | AgileX / LimX | mobile / wheeled |
| 6 | Deep Robotics | quadruped |
| 7 | Fourier Intelligence | GR-series |
| 8 | EngineAI | humanoid |
| 9 | LimX Dynamics | |
| 10 | Keenon | service / delivery |
| 11 | Pudu Robotics | service |
| 12 | OrionStar | service |
| 13 | UBTECH | |
| 14 | CloudMinds | |
| 15 | Siasun | industrial |
| 16 | Estun | industrial |
| 17 | Inovance | |
| 18 | Rokae | |
| 19 | JAKA | cobot |
| 20 | Elite Robots | cobot |
| 21 | Han’s Robot | |
| 22 | Densowave / related CN brands | verify legal entity |
| 23 | Gabot / Galbot | |
| 24 | Astribot | |
| 25 | MagicLab / other CN humanoid | verify public OEM |

## ~15 European

| # | OEM | Notes |
|---|-----|--------|
| 26 | Universal Robots (DK) | Dense certified partner graph — template for SI/distributor |
| 27 | Mobile Industrial Robots / MiR (DK) | |
| 28 | Franka Emika (DE) | |
| 29 | Neura Robotics (DE) | |
| 30 | AGILE ROBOTS (DE) | |
| 31 | Pal Robotics (ES) | |
| 32 | Anybotics (CH) | inspection — partner list |
| 33 | ANYmal channel | same family |
| 34 | Blue Ocean Robotics / UVD (DK) | |
| 35 | Robotise (DE) | |
| 36 | MetraLabs (DE) | |
| 37 | Shadow Robot (UK) | |
| 38 | Ocado / robotics spinouts (UK) | careful — may be captive |
| 39 | SoftBank Robotics Europe lineage | verify current entity |
| 40 | Asyril (CH) | publishes distributor records |

## ~10 Japan / Korea / other Asia

| # | OEM | Notes |
|---|-----|--------|
| 41 | Fanuc (JP) | integrator-heavy |
| 42 | Yaskawa / Motoman (JP) | |
| 43 | Kawasaki Robotics (JP) | |
| 44 | Mitsubishi Electric (JP) | |
| 45 | Doosan Robotics (KR) | |
| 46 | Rainbow Robotics (KR) | |
| 47 | Hyundai Robotics (KR) | |
| 48 | Techman Robot (TW) | |
| 49 | HIWIN Robotics (TW) | |
| 50 | TurtleBot ecosystem / Open Robotics regional distributors | directory pattern (not one OEM) — use as acquisition pattern reference |

---

## Batching

| Batch | Size | Goal |
|-------|------|------|
| B0 | AGIBOT golden | Prove recoverable graph |
| B1 | 10 CN OEMs | OEM-site partner pages first |
| B2 | 10 EU OEMs | |
| B3 | 10 JP/KR/TW | |
| B4 | Fill to 50 | Reverse discovery from known NA distributors |

Track fill in ledger copies of [`channel_graph_ledger.template.json`](./channel_graph_ledger.template.json).
