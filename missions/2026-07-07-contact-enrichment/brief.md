# Mission: Buyer-contact enrichment + verified-source-only send gate

**Date:** 2026-07-07 (started 2026-07-06)
**Type:** build
**Agents:** LeadQuality (contact resolution + gate), Orchestrator

## Why

Bounce forensics: **321 bounced / 208 unconfirmed / 53 delivered** (~55%). Of bounced
accounts, **91 bounced at the REAL domain** — the guessed *mailbox* (`info@`, `name@`)
does not exist. The recipient gate blocks fake *domains* but still trusts
domain-matched *mailbox guesses* (`edom == web` branch in `outreach_recipient_trusted`),
so the bounce pattern recurs.

Providers are already keyed on Fly (`HUNTER_API_KEY` set + enabled by default;
`Apollo_API_Key` present but opt-in via `CONTACT_USE_APOLLO`). No ZeroBounce key, so
`verify_email_deliverable` is DNS-only (passes guessed mailboxes at real domains).

## Goal

Cal should email **only real, observed/verified contact addresses** — never guessed
mailboxes — and we grow verified coverage via Hunter so Cal still has runway.

## Acceptance criteria

1. **Source fidelity:** `resolve_outreach_email` returns the *true* source of a stored
   `contact_email` (from `crm_metadata.outreach_email_source`), not a blanket
   `crm_contact`, so verified stored emails stay trusted and guesses do not launder.
2. **Hardened gate:** `outreach_recipient_trusted` trusts ONLY verified sources
   (apollo/hunter/hunter_domain/website_mailto/signal_email). Drop the `edom == web`
   blanket trust for guessed role/person inboxes.
3. **Enrichment path:** eligible buyers without a verified contact get a Hunter
   enrichment pass (domain search / finder) before Cal sends; measured hit rate.
4. **Metric:** report eligible buyers with a verified contact before/after; confirm
   Cal's send path now skips guessed mailboxes (skipped_unverified reflects it).
5. **Safety:** autopilot stays ON; no sends to guessed mailboxes; tests cover the
   hardened gate + stored-source fidelity.

## Verify

- `scripts/cal_contact_audit.py` before/after (verified-contact coverage).
- Targeted pytest for `outreach_recipient_trusted` + `resolve_outreach_email`.
- Deploy to `ready-2-robot`; re-run audit + a supervised live cycle.

## Outcome (2026-07-06)

### Shipped
1. **Source fidelity** — `resolve_outreach_email` now returns the true recorded
   source of a stored `contact_email` (from `crm_metadata.outreach_email_source`)
   and persists verified hits via `_remember`, so enriched emails stay trusted and
   guesses cannot launder as `crm_contact`.
2. **Hardened gate** — `outreach_recipient_trusted` trusts ONLY verified sources
   (apollo/hunter/**hunter_domain**/website_mailto/signal_email). Removed the
   `edom == web` branch that let guessed role/person inboxes on real domains send
   (the dominant bounce class). `hunter_domain` added to `_VERIFIED_EMAIL_SOURCES`.
3. Tests updated/added (`tests/test_lead_enrichment.py`, 13 pass).

### Measured
- Eligible buyers: **295**; verified stored contact: **2** → 293 need enrichment.
- **Hunter live hit-rate: 66% (8/12)** on sampled eligible buyers — real named
  people (knguyen@ups.com, sue.chau@ihg.com, bini.panicker@marriott.com,
  plucas@mgmresorts.com). Misses fall to guesses → now blocked, not bounced.
- Implication: hardened gate + live Hunter resolution ⇒ Cal reaches ~66% of
  eligible with REAL contacts; ~34% skipped safely.

### Remaining activation blocker
~100+ eligible buyers carry `outreach_sent_at` from the bounce era (sent to
guessed mailboxes that bounced), so the send loop skips them (`skipped_already_sent`).
Re-contacting them is now safe (verified-only gate). Activation = reset
bounced/never-delivered accounts so Cal re-contacts at verified Hunter emails,
throttled by `CAL_AUTONOMY_SEND_LIMIT`. Recommend a controlled ramp given prior
bounce-reputation damage.

### Diagnostics added
`scripts/cal_contact_audit.py`, `scripts/cal_contact_live_sample.py`.
