# Joinability Scorecard — Origin 18

**Run:** 2026-08-16T01:05:01Z · live_ats=True

| Metric | Value | Target |
|--------|------:|-------:|
| Location-bearing job rate | 0.167 | — |
| Join Precision | 1.0 | ≥0.90 |
| PWRR | 0.167 | ≥0.40 |
| Defensible joins | 1 | — |

**Bar:** PWRR≥40% ∩ Precision≥90% → FAIL (PWRR_pass=False, precision_pass=True)

Joinability is the bottleneck. Job-derived Level 2 Worksites (company+locality+function) are allowed bridges; PWRR must stay paired with Join Precision.

## Example cards

### Burris Logistics
```
Worksite: Orlando Distribution Center
Work: pick_cases
Evidence: Burris Logistics job posting: Orlando Distribution Center
Association: company + locality + facility function
Join confidence: 92%
Identity level: 2
```

See [JOINABILITY.md](./JOINABILITY.md).
