# SCOUT HubSpot app (Developer Projects / CLI)

OAuth app for `/integrations/hubspot` on Ready For Robots. Uses HubSpot's **projects framework** ([create an app with the CLI](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app)).

This directory is pre-configured for SCOUT (`app-hsmeta.json` redirect + scopes match `app/services/hubspot_oauth.py`).

## Prerequisites

```bash
npm install -g @hubspot/cli@latest
hs account auth
```

When `hs account auth` opens the browser, copy the **full** personal access key from HubSpot (not a portal ID or partial value). If auth fails, remove `~/.hscli/config.yml` and retry.

## Option A — use this repo project (recommended)

```bash
cd integrations/hubspot-scout-app
hs project upload
hs project open
```

In the HubSpot UI: **Project Components** → `scout_crm_sync` → **Auth** → copy **Client ID** and **Client secret**.

## Option B — create from CLI prompts

```bash
hs project create
```

| Prompt | SCOUT choice |
|--------|----------------|
| Base contents | **App** |
| Distribution | **Private** (specific accounts, not Marketplace) |
| Auth | **OAuth** |
| Features | **None** for CRM sync only (skip cards, webhooks, etc.) |

Then replace generated `src/app/app-hsmeta.json` with this repo's file (or set `redirectUrls` and scopes to match).

```bash
hs project upload
```

## Wire credentials to Fly

```bash
fly secrets set \
  'HUBSPOT_CLIENT_ID=...' \
  'HUBSPOT_CLIENT_SECRET=...' \
  'HUBSPOT_REDIRECT_URI=https://ready-2-robot.fly.dev/api/integrations/hubspot/callback' \
  'PUBLIC_SITE_URL=https://readyforrobots.com' \
  -a ready-2-robot
```

## Install & test

1. In HubSpot **Development** → **Projects** → your project → app UID → **Distribution**.
2. **Standard install** → **Install now** on portal `246418942` (or use a developer test account first).
3. On SCOUT: sign in → `/integrations/hubspot` → **Connect HubSpot automatically**.

## Local dev (optional)

```bash
hs project dev
```

Not required for SCOUT OAuth; production callback is on Fly.
