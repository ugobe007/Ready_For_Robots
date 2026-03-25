# OAuth & Social Login Setup

GitHub and Google OAuth are integrated on the login page. Configure each provider in both its platform and Supabase.

## Supabase callback URL (shared)

Your Supabase project's auth callback URL:

```
https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback
```

---

## GitHub

### 1. Create a GitHub OAuth App

1. Go to [GitHub OAuth Apps](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: `Ready For Robots`
   - **Homepage URL**: `https://readyforrobots.com`
   - **Authorization callback URL**: `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback`
4. Click **Register application**
5. Copy the **Client ID** and **Client secret**

### 2. Configure in Supabase

1. [Supabase](https://supabase.com/dashboard) → your project → **Authentication** → **Providers**
2. Expand **GitHub**, turn it ON
3. Enter Client ID and Client secret → **Save**

---

## Google

### 1. Create Google OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
4. If prompted, configure the **OAuth consent screen**:
   - User type: **External** (or Internal for workspace-only)
   - App name: `Ready For Robots`
   - Support email: your email
   - Add your domain under Authorized domains
5. Create OAuth client:
   - Application type: **Web application**
   - Name: `Ready For Robots`
   - **Authorized JavaScript origins**:
     - `https://readyforrobots.com`
     - `https://ready-2-robot.fly.dev`
     - `http://localhost:3000`
   - **Authorized redirect URIs**:
     - `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback`
6. Click **Create** → copy **Client ID** and **Client secret**

### 2. Configure in Supabase

1. [Supabase](https://supabase.com/dashboard) → your project → **Authentication** → **Providers**
2. Expand **Google**, turn it ON
3. Enter Client ID and Client secret → **Save**

---

## Redirect URLs (Supabase)

In **Authentication** → **URL Configuration** → **Redirect URLs**, ensure these are allowed:

- `https://readyforrobots.com/login`
- `https://ready-2-robot.fly.dev/**`
- `http://localhost:3000/login`

---

## Verify

1. Visit `/login`
2. Click **Sign in with Google** or **Sign in with GitHub**
3. You should be redirected to the provider, then back to the app after authorization

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **GitHub: "redirect_uri_mismatch"** | In [GitHub OAuth App](https://github.com/settings/developers) → your app → Authorization callback URL must be exactly `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback` (no trailing slash) |
| **"Redirect URL not allowed"** (Supabase) | Add ALL of these to Supabase **URL Configuration** → **Redirect URLs**: `https://readyforrobots.com/login`, `https://readyforrobots.com/**`, `https://ready-2-robot.fly.dev/login`, `https://ready-2-robot.fly.dev/**`, `http://localhost:3000/login` |
| "Invalid redirect URI" (Google) | Add `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback` to Authorized redirect URIs in Google Cloud Console |
| Provider not working | Enable the provider in Supabase **Providers** and save Client ID and secret |
| Auth not configured | Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local` |

### GitHub-specific checklist

1. **GitHub OAuth App** → Authorization callback URL: `https://lmoyydlhlgdyqbxkmkuz.supabase.co/auth/v1/callback`
2. **Supabase** → Authentication → Providers → GitHub: Enabled, Client ID and Secret saved
3. **Supabase** → URL Configuration → Redirect URLs: Include `https://readyforrobots.com/**` and `https://ready-2-robot.fly.dev/**`
