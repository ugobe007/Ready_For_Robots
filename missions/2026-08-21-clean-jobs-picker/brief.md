# Clean Jobs SKU picker

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface + Understanding integrity  
**ICP:** Robot OEM submits URL on Jobs FIND → picker shows real SKUs

## Goal

Indexed vendor pickers list **catalog robots only**. Homepage nav (`Learn More`, `EULA`, `Industry`) and accessories (`4D LiDAR G1`) must not appear. Unknown OEMs still discover SKUs from the page, with the same noise filter.

## Acceptance

1. Unitree / Bear / Pudu / Boston Dynamics / Richtech pickers equal index names (no nav extras).
2. `_discover_product_names` drops Learn More / EULA / LiDAR labels.
3. Targeted pytest green. Cache namespace bumped so stale 14-product Unitree pickers expire.

## Out of scope

- Seeding every missing real SKU (Servi Q, Unitree B2, MagicLab extras)
- Extractor retune / SIGNAL / Qualify
