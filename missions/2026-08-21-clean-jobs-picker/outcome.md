# Outcome — Clean Jobs SKU picker

**Mission:** `missions/2026-08-21-clean-jobs-picker`  
**Type:** build  
**Date:** 2026-08-21

## What shipped

Indexed vendors: Jobs picker = vendor index SKUs only. Homepage nav (`Learn More`, `EULA`, `Industry`) and accessories (`4D LiDAR G1`) are omitted. Unknown OEMs still discover from the page, with the same noise filter.

Cache namespace `robot_profile_v9` so stale 14-product Unitree pickers expire.

## Tests

`pytest tests/test_product_href_discovery.py tests/test_vendor_robot_lookup.py tests/test_catalog_first_lookup.py tests/test_richtech_vendor_lookup.py tests/test_robot_job_search.py` — 40 passed.

## Follow-ups

- Seed real missing SKUs (Unitree B2, Servi Q / Servi Clean, MagicLab extras) into the index when we want them in the picker.
- Fly deploy after merge.
