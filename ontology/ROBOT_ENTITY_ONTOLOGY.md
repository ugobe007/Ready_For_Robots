# Robot Entity Ontology

**Purpose:** bind every fact and capability to a *specific* entity so "Locus"
never inherits every capability of every Locus product.

```
COMPANY → PRODUCT → CONFIGURATION → COMPONENTS
```

## Entities

### COMPANY
The organization (robot OEM / brand / RaaS). A company sells one or more products.
Company-level marketing copy is **not** a product capability.

- Fields: `name`, `primary_domain`, `aliases`, `vendor_role`, `country`.
- Code: `Manufacturer` (`app/models/robot_catalog.py`), `RobotCompany`
  dataclass (`app/services/robot_understanding_v1/models.py`).
- `vendor_role` ∈ `enums.v1.json::vendor_roles`
  (`robot_oem`, `robot_brand`, `white_label_brand`, `distributor`,
  `system_integrator`, `autonomy_provider`, `robot_as_a_service`,
  `component_supplier`).

### PRODUCT (model)
A named robot model. Capabilities are asserted **here**, not at the company.

- Fields: `name`, `slug`, `primary_class`, `product_url`, `commercial_maturity`,
  `family`.
- Code: `RobotModel` + `RobotFamily`. In-flight: `RobotProduct` / selected
  product on `RobotProfile`.
- `primary_class` is a **descriptor**, never a job selector (see
  [inference rules](ROBOT_INFERENCE_RULES.md)). Observed values today:
  `humanoid`, `quadruped`, `mobile_manipulator`, `amr`, `autonomous_scrubber`,
  `cleaning_robot`, `service_robot`, `cobot_arm`, `drone`, `construction_robot`,
  `autonomous_forklift`, `agricultural_robot`, `mining_robot`, `agv`.

### CONFIGURATION
A specific hardware build of a product. **Optional modules are configurations,
not universal product capabilities.** A Locus AMR with a telescoping grab is a
*configuration*; the base AMR is another.

- Fields: `slug`, `name`, `is_default`, `options`.
- Code: `RobotConfiguration` (default stub `{slug: "default", is_default: true}`).
- Status: 🟡 configuration modeling exists in the catalog schema; the live
  Understanding path currently resolves one selected product and does not yet
  split per-configuration modules — tracked as the subject-scoping work.

### COMPONENTS
The hardware present on a configuration → drives which capabilities can be
inferred. See [`ROBOT_HARDWARE_ONTOLOGY.md`](ROBOT_HARDWARE_ONTOLOGY.md).

## Subject scoping (the anti-leak rule) ✅

Facts belong to the **selected** product/configuration only:

- **Page-level gate:** an off-subject page contributes no capability facts
  (`sources.py::page_supports_subject`).
- **Sibling-SKU gate:** a fact whose evidence window names a *different* model is
  dropped (`facts.py::_evidence_names_sibling_sku`,
  mirrored in `robot_inference_engine.py::_phase1_detect`).
- **Numeric constraints** (`carrying_capacity`, `reach_or_workspace`, …) require
  the subject name near the evidence (`require_subject_near`).

**Rules enforced here:**
- Facts from sibling products may **not** flow into the selected product.
- Do **not** infer a capability from company-level copy when the selected product
  has no supporting hardware/evidence.

## Multi-product companies

When a company sells several models, the flow must go through **SELECT**
(`needs_product_choice=True`) — never collapse the company's union of
capabilities onto one product. Known limitation (🟡): multi-product *homepages*
(e.g. Bear: Servi + cleaning + warehouse lines) can still bleed capabilities
across products until per-product pages/configurations are resolved.

## Related
- Confidence vocabulary and inference: [`ROBOT_INFERENCE_RULES.md`](ROBOT_INFERENCE_RULES.md)
- Graph node families: [`rfr_graph.v1.json`](rfr_graph.v1.json)
