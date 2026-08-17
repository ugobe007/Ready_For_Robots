# Batch 1 — U.S. Channel Coverage (10 foreign OEMs)

**Goal:** Is the graph cheap to construct? Does it collapse onto multi-OEM partners?  
**Not a directory sprint.** Coverage + route facts only.

## Mix

| OEM | Region / type |
|-----|----------------|
| AGIBOT | CN · humanoid / general |
| Unitree | CN · quadruped / humanoid |
| Dobot | CN · cobot |
| JAKA | CN · cobot |
| MiR | EU · AMR |
| Anybotics | EU · inspection |
| Pudu | CN · service / cleaning |
| Techman | TW · cobot |
| Doosan Robotics | KR · cobot |
| Franka Robotics | EU · manipulation (thin public US list) |

Ledger: [`batch1_10_oems_ledger.json`](./batch1_10_oems_ledger.json)

---

## Coverage scoreboard (directional)

| OEM | US GTM | Named partners (C1–C3 focus) | Territory signal | Capabilities signal | Effort note |
|-----|--------|------------------------------|------------------|---------------------|-------------|
| AGIBOT | Channel | 2 (RobotShop, Useabot) | US+CA / US | VAD: deploy, train, support | **Cheap** — press + OEM posts |
| Unitree | Channel | 3+ (Futurology, TVC, RoboStore) | US / US+CA | sales, support, some integrate | Medium — partner-claimed; OEM list opaque |
| Dobot | Hybrid (Dobot USA + channel) | DB Cobots (C3) + HQ Carrollton TX | US / Mid-Atlantic stock | sales, stock, service | Medium — master distributor era; network large |
| JAKA | Hybrid (US office + channel) | Industrial Automation Co., AMD Machines, KAKOU, MCC | SE / TX / national SI | sales, integrate | Medium — announcements |
| MiR | Channel (partner locator) | RG Group, R.R. Floody (+ many gated) | Regional | sales, integrate, service | **Harder** — OEM hides full list behind form |
| Anybotics | Channel + US office | Gresco (GA), Watch Robotics (TX/LA), OEM partners page | GA, AZ, CA, TX/LA | deploy, train, RaaS, field | Good — OEM publishes regional partners |
| Pudu | Hybrid (US HQ + 300+ dist) | XCube, Inland Global, RuTech | CA / nationwide claims | sales, deploy, warranty, parts | Noisy — many C2 claims; need OEM confirm |
| Techman | Channel | Telamon/Telabotics, Accu Tech USA | IN / NC+ | sales, integrate, train | Medium |
| Doosan | Channel (dense) | Cross, Van Meter, IAS, Ellison, Doig… | SE, Midwest, NE, national importer | sales, integrate, service, platinum tiers | Easy volume, **directory risk** — sample only |
| Franka | Channel / certified partners | Thin in this pass | Unresolved | Unresolved | **Gap** — needs OEM partner directory pass |

### Summary metrics (Batch 1)

| Metric | Approx |
|--------|--------|
| OEMs with clear US channel | 9 / 10 |
| C1–C3 relationships captured (named) | ~25 (sampled, not exhaustive) |
| OEMs with usable territory resolution | ~7 / 10 |
| OEMs with ≥3 capability flags | ~8 / 10 |
| OEMs where OEM site lists partners openly | Anybotics strong; MiR/Doosan gated or huge |
| Multi-OEM partners in this sample | **0 confirmed** across these 10 |

**Finding:** Graph is **recoverable** for announcement-heavy foreign OEMs (AGIBOT, Anybotics, Techman, JAKA). It becomes a **data-acquisition monster** when the OEM only offers “Contact a partner” forms (MiR) or hundreds of regional dealers (Doosan/Pudu) — then we must sample for coverage, not scrape everyone.

**Multi-OEM collapse:** Not visible inside this 10 yet. Likely appears when we reverse from large NA automation houses (Cross, RG Group, Accu Tech, RobotShop) outward. Next research move: pick 5 high-leverage partners and list **all** robot brands they carry.

---

## Coverage gaps (product seeds)

| Pattern | Example | Commercial meaning |
|---------|---------|-------------------|
| Channel exists, territory thin | Anybotics strong in energy belt / GA; weak elsewhere | Jobs outside partner footprints = recruit / expand |
| Hybrid OEM office + partners | Dobot TX, Pudu CA, JAKA NY | Direct vs partner routing |
| Opaque partner graph | MiR form wall | Coverage unknown → treat as incomplete |
| Capability-rich VAD | RobotShop / Useabot / Cross | Prefer for job route when capabilities match |

---

## Do next (still parallel to traffic)

1. **Done:** Reverse five partners — [`DISTRIBUTOR_PRODUCT_EXPERIMENT.md`](./DISTRIBUTOR_PRODUCT_EXPERIMENT.md)  
2. Build distributor demo UI fixture (RG / XCube / RobotShop) — data ready in [`distributor_demo_fixture.json`](./distributor_demo_fixture.json)  
3. Capability-directed batch for Cross-style partners (palletizing / machine tending) — later  
4. Stop OEM 11–50 until distributor product is tested  
5. No Job Route Score yet
