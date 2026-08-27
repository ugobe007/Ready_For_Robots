# Tractor / combine implements are configurations

**Purpose:** an attachment on a tractor or combine is **hardware on a host
platform**, not a fake robot class and not a company category.

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES
```

## Host platforms (agriculture)

| Host | Typical work | Product class of the *vehicle* |
|------|----------------|--------------------------------|
| Autonomous **tractor** | Planting, crop harvest support, spray, tillage | `agriculture` / `agricultural_robot` |
| Autonomous **combine** | Grain harvest (header + threshing) | `agriculture` / `agricultural_robot` |
| Implement on tractor | Weeding, precision spray, see-and-spray | same class; **configuration** = implement-on-host |

## Configuration (not a class)

| Field | Values | Meaning |
|-------|--------|---------|
| `configuration_kind` | `standalone` \| `implement_on_host` | How the SKU is built |
| `host_platform` | `tractor` \| `combine` \| `none` | What the implement mounts on |

Example: Carbon Robotics **LaserWeeder** as a three-point-hitch weeder is
`configuration_kind=implement_on_host`, `host_platform=tractor`. The product
class is still `agricultural_robot`. We do **not** invent a class
`tractor_attachment` or treat “attachment companies” as a FIND tile.

Empty payload / reach / price stay `UNKNOWN`. R27: implement + tractor host →
`agriculture_task` (`DERIVED` / named), never fake `EXPLICIT` specs.

## Construction / aerospace hosts (same rule)

An autonomy kit on an excavator is a configuration of that excavator product.
A debris-capture arm on a servicing satellite is a configuration of that
satellite product. Same traversal. No fake “attachment class.”
