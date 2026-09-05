# Robot Vertical / Environment Ontology

**Purpose:** the operating environments (industry verticals) a robot may target.
Users paste *all sorts* of robot URLs, so the front door must recognize every
vertical — even ones we don't yet match jobs for — instead of flattening them to
"commercial." A vertical is grounded from the `operating_environment` fact.

Machine-readable: [`vertical_ontology.v1.json`](vertical_ontology.v1.json).
Loaded by `app/services/robot_ontology.py`; emitted by
`app/services/robot_understanding_v1/facts.py` (`operating_environment`).

## Verticals

| Key | Vertical | In scope (jobs) | Example robots |
|-----|----------|:---:|----------------|
| `warehouse` | Warehouse / fulfillment / DC | ✅ | Locus, Brightpick, Hai, MiR |
| `manufacturing` | Manufacturing / factory | ✅ | Standard Bots, cobots, Digit |
| `retail` | Retail / grocery | ✅ | Simbe, shelf-scan AMRs |
| `hospitality` | Hospitality — hotels | ✅ | Aethon (hotel), bellhop robots |
| `restaurant` | Restaurant / foodservice | ✅ | Bear Servi, Keenon, Pudu, Miso, Richtech |
| `healthcare` | Hospitals, clinics, surgery, pharmacy, lab, nursing units, med-surg, OR, linen / unit-delivery | ✅ | Aethon TUG, Relay, Moxi |
| `eldercare` | Nursing home, senior/assisted living, rehab, PT | ✅ | Relay, service/companion robots |
| `airport` | Airport / transit hub | ✅ | cleaning + delivery AMRs |
| `commercial` | Offices / reception / facilities | ✅ | reception & delivery robots |
| `utilities` | Utilities / infrastructure inspection | ✅ | quadrupeds (Spot, DEEP) |
| `indoor` | Generic indoor | ✅ | — |
| `construction` | Construction / jobsite | ✅ | Dusty, Canvas, Built |
| `mining` | Mining / quarry | ✅ | autonomous haulage/drilling |
| `agriculture` | Agriculture / farm | ✅ | Carbon Robotics LaserWeeder, John Deere X9 / autonomous tractor, Naio Oz |
| `marine` | Marine / port / underwater | ✅ | Hull and quay work robots |
| `aviation` | Avionics — drones, eVTOL, autonomous aircraft | ✅ | Skydio X10, Joby eVTOL, Zipline |
| `aerospace` | Aerospace — satellites, rockets, orbital robots | ✅ | Astroscale ELSA-d / ADRAS-J, ClearSpace-1 |

## Rules
- The vertical is **descriptive context**, not a capability and not a job
  selector (same discipline as `product_class`). A hospital delivery robot
  matches transport/serve work via its **capabilities**, and the `healthcare`
  vertical labels *where*, not *what*.
- Recognizing work-domain verticals (`construction`/`mining`/`agriculture`/
  `marine`/`aviation`/`aerospace`) keeps the front door honest. They label
  *where*. Jobs still match from grounded task capabilities, never from the
  vertical tag and never from a SIGNAL industry hop.
- **Avionics vs aerospace** are distinct. Avionics = drones / eVTOL /
  autonomous aircraft. Aerospace = satellites / rockets / orbital debris and
  space-exploration robots. See [`ROBOT_AVIONICS_AEROSPACE.md`](ROBOT_AVIONICS_AEROSPACE.md).
- Tractor and combine **implements** are configurations (hardware on a host),
  not a vertical and not a FIND class. See [`ROBOT_TRACTOR_IMPLEMENT.md`](ROBOT_TRACTOR_IMPLEMENT.md).
- Healthcare and eldercare are separated because their work differs (clinical
  delivery / specimen transport vs. resident services / meal & linen delivery),
  though both are served today by the same `transport`/`serve` capabilities.
- **Work language (R33).** Distinctive hospital / clinical / pharmacy /
  nursing / patient / OR / med-surg / linen / unit-delivery terms live in
  [`industry_work_language.v1.json`](industry_work_language.v1.json). They
  classify the **configuration** after hardware. They do not invent Job Cards.
  Work-language / task-model evidence outranks generic humanoid morphology.

## Example — Aethon TUG
`autonomous mobile robots` → `product_class=amr` → `mobile`; "deliveries of
medication … specimens … meals, linens" → `claims_item_delivery` → `transport`;
"Healthcare" / "hospitality" → `operating_environment ∈ {healthcare, hospitality}`.
Result: a hospital/hotel delivery robot that matches transport / cart / serve work.
