# Stage 1 — Cal Voice Loop (manual Evaluate → Learn)

**Date:** 2026-08-13  
**Type:** build  
**Spec:** `docs/CAL_LEARNING_SYSTEM.md`

## Goal

Make Stage 1 operational: every draft can be scored before send, and every correction can be logged as a general Cal rule.

## Acceptance

1. `python scripts/cal_score_draft.py --variant bottleneck_first --name "Performance Food Group" --industry "Food Distribution" --gate` exits 0
2. Label-stack anti-pattern scores below gate / flags the connect-observations rule
3. `scripts/cal_log_learning.py` can append a learning-log row
4. `cal_preflight.py` reports Stage 1 rubric sample (1b)
5. Tests for rubric pass

## Operator loop (daily)

```bash
# Score a generated variant
./venv/bin/python scripts/cal_score_draft.py \
  --variant bottleneck_first \
  --name "Performance Food Group" \
  --industry "Food Distribution / Wholesale" \
  --gate

# Score a pasted draft
./venv/bin/python scripts/cal_score_draft.py --file /tmp/cal_draft.txt --company "PFG" --gate

# After correcting Cal, log the rule
./venv/bin/python scripts/cal_log_learning.py \
  --original '...' \
  --correction '...' \
  --why '...' \
  --rule '...' \
  --outcome 'pending'
```

Ask every time: **What general rule did we just learn?**
