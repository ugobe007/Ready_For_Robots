# Outcome: Cal Voice Loop Stage 1

**Date:** 2026-08-13  
**Status:** complete

## Shipped

- `app/services/cal_voice_rubric.py` — heuristic 6-dimension + Accuracy gate
- `scripts/cal_score_draft.py` — score file/stdin/variant; `--gate`
- `scripts/cal_log_learning.py` — append learning-log rows
- `scripts/cal_preflight.py` — advisory `[1b] Voice rubric` sample
- `docs/cal_stage1_operator_card.md` — daily operator loop
- Tests: `tests/test_cal_voice_rubric.py`

## Verify

```bash
./venv/bin/python scripts/cal_score_draft.py \
  --variant bottleneck_first \
  --name "Performance Food Group" \
  --industry "Food Distribution / Wholesale" \
  --gate
# → PASS ≥24/30
```

Label-stack anti-pattern fails gate and suggests connect-observations rule.

## Next

Stage 2: hard-block sends on rubric fail (optional LLM judge). Grow corpus situations.
