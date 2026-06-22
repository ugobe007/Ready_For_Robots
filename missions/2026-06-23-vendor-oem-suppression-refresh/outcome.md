# Outcome: Vendor / OEM suppression refresh

**Date:** 2026-06-23  
**Status:** done

## Summary

Extended robotics OEM blocklist (Realman, AgiBot, Milagrow, ECOVACS, Serve Robotics, Skild AI, Physical Intelligence, Persona AI, CloudMinds, etc.). Humanoid catalog buyer deployers (Foxconn, Siemens, SoftBank, Toyota, Samsung, Tesla, …) are excluded from OEM vendor matching so pilot rows are not false-positive junk.

## Quarantine

| Metric | Value |
|--------|-------|
| Dry-run candidates | 28 |
| Applied (`--apply`) | 28 |
| Report | `reports/vendor_oem_quarantine_20260622_184030.csv` |

Sample IDs: 208 ECOVACS, 9852 Vention, 9878 Figure Ai, 9872 Apptronik, 9880 Geek+.

## Tests

`tests/test_robot_vendor_names.py` — 18 passed (new OEMs flagged; catalog buyer deployers + Tesla not vendor-blocked).

## Deploy

Not required — junk filter is server-side on ingest/classify; quarantine is DB-only. Next deploy will ship blocklist changes.

## Next

Rank 2: `rss-html-strip-and-report-filter` (960 Unknown industry rows).
