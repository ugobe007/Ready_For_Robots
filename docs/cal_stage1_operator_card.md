# Stage 1 operator card — Cal Voice Loop

Spec: [CAL_LEARNING_SYSTEM.md](./CAL_LEARNING_SYSTEM.md)

## Before any Cal send

1. Generate or open the draft.
2. Score it:

```bash
./venv/bin/python scripts/cal_score_draft.py --file DRAFT.txt --company "Company Name" --gate
```

3. Need **≥ 24/30** voice + **Accuracy PASS**.
4. If it fails: rewrite, then ask *what general rule did we learn?*
5. Log the rule:

```bash
./venv/bin/python scripts/cal_log_learning.py \
  --original 'broken behavior' \
  --correction 'what worked' \
  --why 'one sentence' \
  --rule 'general Cal rule' \
  --outcome 'pending'
```

6. If the rule is durable, promote into persona + templates (see Learning System §9).

## Rubric (1–5 each)

| Dimension | Ask |
|-----------|-----|
| Human | Knowledgeable person, not an AI agent? |
| Insight | Something worth talking about? |
| Relevance | Specific to this company/industry? |
| Reasoning | Explains why it matters (connects dots)? |
| Restraint | Helping, not overselling? |
| Conversation | Naturally want to respond? |

Accuracy is separate — never trade rigor for persuasion.

## Corpus

- Excellent: `docs/cal_corpus/excellent/`
- Not Cal: `docs/cal_corpus/not_cal/`
