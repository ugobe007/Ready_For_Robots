# Supabase Auth email (magic links)

Project ref: `lmoyydlhlgdyqbxkmkuz`.

Supabase’s bounce warning is **Auth transactional mail** (magic links / OTP), not Cal/SIGNAL outreach. Outreach already goes through **Resend** on Fly. Auth still uses Supabase’s shared sender until Custom SMTP is set in the dashboard.

That shared sender is why a handful of bad OTP addresses can freeze the whole project’s mail.

## What the app does in code

- Login and signup validate format before `signInWithOtp`.
- Disposable / RFC example addresses never call Auth.
- Login OTP uses `shouldCreateUser: false` so a typo on `/login` does not create a user and bounce a letter to a mailbox that does not exist.
- Resend cooldown on login/signup cuts burst retries.

Google / GitHub OAuth send **no** Auth email. Prefer that path for ICP.

## Operator step that code cannot do — Custom SMTP

Dashboard: [Authentication → Emails](https://supabase.com/dashboard/project/lmoyydlhlgdyqbxkmkuz/auth/templates) → **SMTP Settings**.

Use the same Resend account as Fly, on a **verified** domain (ideally a subdomain so Auth reputation stays off Cal outreach):

| Field | Value |
|-------|--------|
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Resend API key (same family as `RESEND_API_KEY` on Fly) |
| Sender email | e.g. `login@mail.readyforrobots.com` (must be verified in Resend) |
| Sender name | Ready For Robots |

Docs: [Supabase Custom SMTP](https://supabase.com/docs/guides/auth/auth-smtp) · [Resend SMTP](https://resend.com/docs/send-with-smtp).

Also in Auth settings:

- If magic link is the email path, **do not** also send a separate “confirm your email” letter — that doubles volume and bounces.
- Confirm Site URL / redirect allow list still include `https://readyforrobots.com`.

## Hygiene that is not this pipe

| Pipe | Transport | Bounce handling |
|------|-----------|-----------------|
| Auth magic link | Supabase (or Custom SMTP) | This doc |
| Cal / CRM outreach | Resend on Fly | `app/services/resend_email.py`, suppression tests |
| Harness notify | Resend | `scripts/harness_notify.py` |

Do not test Auth against fake or live personal inboxes from CI. Use Google OAuth or a mailbox you control.
