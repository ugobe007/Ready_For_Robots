# Outcome: RSS HTML strip and market-report filter

**Date:** 2026-06-23  
**Status:** done

## Summary

Enhanced Google News RSS HTML normalization (anchor-text preference, font tag strip, `#6f6f6f` artifact removal) and market-report junk detection. Quarantined Unknown-industry display junk while sparing known-brand deployers (Novartis, etc.).

## Signal HTML strip

| Metric | Value |
|--------|-------|
| Signals scanned | 1,716 |
| Rewritten (`--apply`) | 1,714 |
| Companies touched | 1,174 |

## Quarantine

| Metric | Value |
|--------|-------|
| Candidates | 704 |
| Applied | 704 |
| Buckets | 703 `display_junk`, 1 `junk_name` |
| Report | `reports/unknown_rss_quarantine_20260622_192936.csv` |

## Snapshot delta

| Metric | Before | After |
|--------|--------|-------|
| Unknown industry w/ signals | ~865 | **153** |

## Deploy

Not required — normalization + quarantine are DB-side. Ingest benefits on next deploy when blocklist/strip logic ships.

## Next

Rank 2: `partnership-quarantine-sweep`; rank 3: `industry-rescue-ontology` on remaining ~153 Unknown rows.
