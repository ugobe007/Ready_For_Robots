# OAuth & Social Login Setup

GitHub and Google OAuth on `/login`. **Google Calendar sync** on `/calendar` is a separate flow (Fly API, not Supabase).

## Critical: use the Ready For Robots Supabase project

Production (`readyforrobots.com`, Fly, Vercel) is wired to **this** project only:

| Setting | Value |
|---------|--------|
| **Project ref** | `lmoyydlhlgdyqbxkmkuz` |
| **Dashboard** | https://supabase.com/dashboard/project/lmoyydlhlgdyqbxkmkuz |
| **Auth callback (Google Cloud)** | `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback` |

If your Supabase Google provider shows a callback like `https://fvmpmozybmtzjvikrctq.supabase.co/auth/v1/callback`, you are in a **different Supabase project** (e.g. Merlin Energy). Google credentials there will not fix sign-in on Ready For Robots.

### Local frontend env (Vite)

Supabase’s “Connect to your project” snippet uses `NEXT_PUBLIC_*`. This repo’s Vite app uses **`VITE_PUBLIC_*`** instead. See `readyforrobots-new/.env.example` — copy to `readyforrobots-new/.env.local` and paste your publishable or anon key from the dashboard.

---

## Two different Google flows (do not mix them up)

| What you want | Where OAuth happens | Redirect URI goes in **Google Cloud** |
|---------------|---------------------|----------------------------------------|
| **Sign in with Google** (login) | Supabase Auth | `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback` |
| **Connect Google Calendar** (`/calendar`) | Ready For Robots API (Fly) | `https://ready-2-robot.fly.dev/api/integrations/google-calendar/callback` |

The Supabase callback URL is **never** added to Supabase “Redirect URLs”. It only goes in **Google Cloud Console**.

---

## Google sign-in (Supabase)

### Step A — Google Cloud Console

1. [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
2. Open your **Web application** OAuth client (or create one)
3. **Authorized JavaScript origins** (examples):
   - `https://readyforrobots.com`
   - `http://localhost:3000`
4. **Authorized redirect URIs** — add **both** (exact match, no trailing slash):
   ```
   https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback
   https://ready-2-robot.fly.dev/api/integrations/google-calendar/callback
   ```
5. Copy **Client ID** and **Client secret** (starts with `GOCSPX-`)

Optional: [Google Auth Platform](https://console.cloud.google.com/auth) → **Data Access** → ensure scopes include `openid`, `userinfo.email`, `userinfo.profile`.

### Step B — Supabase Dashboard (Google provider)

1. [Supabase Dashboard](https://supabase.com/dashboard) → project **lmoyydlhlgdyqbxkmkuz**
2. **Authentication** → **Providers** → **Google**
3. Turn **Enable Sign in with Google** on
4. Paste **Client ID** and **Client secret** from Google Cloud → **Save**
5. On that same Google provider screen, Supabase shows a **Callback URL** (for Google). It should be:
   ```
   https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback
   ```
   That exact URL must already be in Google Cloud (Step A). You do **not** paste it into Supabase Redirect URLs.

### Step C — Supabase Dashboard (URL Configuration)

1. **Authentication** → **URL Configuration**
2. **Site URL**: `https://readyforrobots.com`
3. **Redirect URLs** — add one wildcard entry (covers `/auth/callback`, `/login`, etc.):
   ```
   https://readyforrobots.com/**
   ```
   For local dev, also add:
   ```
   http://localhost:3000/**
   ```

Our app sends users to `https://readyforrobots.com/auth/callback?next=...` after Google sign-in. That path must match the allow list above.

Official reference: [Supabase Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls), [Login with Google](https://supabase.com/docs/guides/auth/social-login/auth-google).

---

## Google Calendar (Fly — not Supabase)

1. Fly secrets (production):
   ```bash
   fly secrets set \
     GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com" \
     GOOGLE_CLIENT_SECRET="GOCSPX-..." \
     -a ready-2-robot
   ```
2. Signed-in user → `/calendar` → **Connect Google Calendar** (not “Sign in with Google”)

---

## GitHub sign-in

### GitHub OAuth App

- **Authorization callback URL**: `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback`

### Supabase

- **Authentication** → **Providers** → **GitHub** → Client ID + secret → Save

---

## Verify

1. Incognito → [readyforrobots.com/login](https://readyforrobots.com/login) → **Sign in with Google**
2. Should hit `/auth/callback` briefly, then `/pipeline`
3. `/calendar` → **Connect Google Calendar** (separate button, after signed in)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `redirect_uri_mismatch` (Google screen) | Fly or Supabase callback missing in **Google Cloud** | Add the exact URI from the error screen to Google Cloud redirect URIs |
| `Unable to exchange external code` | Client secret in **Supabase → Providers → Google** does not match Google Cloud (even if it looks correct) | **Reset** the secret in Google Cloud → Credentials → your Web client → **Reset secret** → copy the new `GOCSPX-…` → paste into Supabase Google provider → **Save**. Then update Fly: `fly secrets set GOOGLE_CLIENT_SECRET="GOCSPX-..." -a ready-2-robot`. Re-copying the old secret often fails if Supabase stored a stale value. |
| Redirect URL not allowed | App `redirectTo` not in Supabase allow list | **URL Configuration** → add `https://readyforrobots.com/**` |
| Calendar connect fails | Used Sign in with Google instead of Connect button | Use **Connect Google Calendar** on `/calendar` while signed in |
| Error on `/calendar` about sign-in | Stray OAuth params | Use magic link or fix Google provider first, then connect calendar |

**Do not** add `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback` to Supabase Redirect URLs — that belongs only in Google Cloud.
