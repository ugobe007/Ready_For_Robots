# Outcome: Drop junk report-download leads

**Date:** 2026-08-25
**Status:** done
**Type:** build

## Diff

- New `app/services/form_spam.py`: honeypot, disposable inboxes, generated mash names/companies/categories.
- `POST /api/leads/report-download` returns `{ok: true, ignored: true}` for spam — no waitlist row, no owner email, no report email.
- About page report form has a hidden `website` honeypot.

## Tests

- `PYTHONPATH=. ./venv/bin/python -m pytest tests/test_form_spam.py tests/test_report_download_spam.py -q` — 9 passed

## Follow-ups

Operator mailbox still has historical junk; this only stops new notifies. Newsletter subscribe is a separate capture path.
