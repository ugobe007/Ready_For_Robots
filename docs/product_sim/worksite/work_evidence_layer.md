# Work Evidence Layer V0

For each (Worksite, work_unit) pair:

| Status | Rule |
|--------|------|
| **EXPECTED** | Work unit appears in Work Pattern Library for this site type. No site-specific evidence yet. |
| **EVIDENCED** | Public text (job posting, ops page, article) supports that work at this company/site (keywords or explicit mention). |
| **CONFIRMED** | Source explicitly states the work at **this named worksite**. |
| **UNKNOWN** | Site type unclear OR work unit not in pattern and no evidence. |
| **CONTRADICTED** | Evidence indicates that work does not occur here (e.g. fully automated cell, outsourced, different process). |

## Upgrade path

```
EXPECTED ──(keyword / job match)──► EVIDENCED ──(named site + work)──► CONFIRMED
    │
    └──(counter-evidence)──► CONTRADICTED
```

## Origin matching rule

Match robots against **work units**, not company logos.

Prefer results where:

1. Worksite named
2. At least one Origin-relevant work unit is EVIDENCED or CONFIRMED
3. EXPECTED-only is allowed for discovery ranking but labeled clearly

## Do not claim

- Trips/shift, travel distance, payload distribution, WMS vendor, current automation inventory — those stay UNKNOWN until evidenced.
