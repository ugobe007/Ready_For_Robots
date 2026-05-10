# Deploy and environment variables (step-by-step)

This project runs a **FastAPI backend** and a **Next.js static frontend** in one **Fly.io** app. The Dockerfile builds the frontend during `fly deploy`, so you do not need to run `npm run build` on your laptop first.

---

## 1. One-time: Fly.io CLI and login

1. Install the Fly CLI: [https://fly.io/docs/hands-on/install-flyctl/](https://fly.io/docs/hands-on/install-flyctl/)
2. Log in (opens the browser once):

```bash
flyctl auth login
```

3. From your **project root** (`Ready_For_Robots`), deploy:

```bash
cd /path/to/Ready_For_Robots
flyctl deploy
```

Fly reads `fly.toml` and `Dockerfile`, builds the image in the cloud, and rolls out the new version. Wait until the command finishes without errors.

---

## 2. Environment variables on Fly (secrets)

**Secrets** are private values (API keys, database URL). They are **not** committed to git. Set them on Fly so the running app can read them.

### Set a secret from your terminal

```bash
flyctl secrets set DATABASE_URL="postgresql://..." -a ready-2-robot
```

Replace `ready-2-robot` with your app name from `fly.toml` if different.

### Important variables for this codebase

| Variable | What it is |
|----------|------------|
| `DATABASE_URL` | Postgres connection string (e.g. Supabase). |
| `SUPABASE_JWT_SECRET` | Lets the API verify logged-in users (from Supabase project settings). |
| `OPENAI_API_KEY` | Optional. If set, the **industry strategic brief** uses OpenAI; if unset, a rule-based brief is used. |
| `NEWSLETTER_REGEN_SECRET` | Optional but **recommended in production**. Protects forced newsletter regeneration (see below). |
| `ADMIN_EMAILS` | Comma-separated emails allowed to use `/admin`. Already in `fly.toml` `[env]`; you can override with secrets if you prefer. |

List what Fly has (names only, not values):

```bash
flyctl secrets list -a ready-2-robot
```

---

## 3. `NEWSLETTER_REGEN_SECRET` (what it does and how to use it)

When this variable **is set** on Fly:

- `GET /api/newsletter/edition?refresh=true` **and**
- `POST /api/newsletter/generate`

only work if **either**:

1. The request includes header **`X-Newsletter-Regen-Key`** with the **same** value as `NEWSLETTER_REGEN_SECRET`, **or**
2. The request includes **`Authorization: Bearer <token>`** for a user whose email is in **`ADMIN_EMAILS`**.

**Generate a random secret** (macOS/Linux):

```bash
openssl rand -hex 32
```

Set it on Fly:

```bash
flyctl secrets set NEWSLETTER_REGEN_SECRET="paste-the-long-random-string-here" -a ready-2-robot
```

**Example: curl with the secret**

```bash
curl -sS -H "X-Newsletter-Regen-Key: YOUR_SECRET_HERE" \
  "https://YOUR_APP.fly.dev/api/newsletter/edition?refresh=true&limit=8"
```

When `NEWSLETTER_REGEN_SECRET` is **not** set (typical **local dev**), regeneration stays open so you do not need the header.

---

## 4. Frontend API URL (`NEXT_PUBLIC_*`) at build time

The static site needs to know **which host** to call for `/api/...`. That is baked in at **`npm run build`** (which runs **inside Docker** on deploy).

In `fly.toml`, under `[build.args]`, you can set:

- **`NEXT_PUBLIC_API_URL`** — full base URL of the API **as the browser will call it**, e.g. `https://ready-2-robot.fly.dev` or your custom domain. **No trailing slash.**
- **`NEXT_PUBLIC_SITE_URL`** — public site URL for share links / OG URLs, e.g. same as above or your marketing domain.

If you leave them empty, the app falls back to defaults in `frontend/nextjs/lib/apiBase.js` (see that file). For a Fly app, setting both to your **real public HTTPS URL** avoids confusion.

After changing `[build.args]` in `fly.toml`, run **`flyctl deploy` again** so the Next build picks up the new values.

### 4b. Vercel-only Next deployment (optional)

If the static site is built on **Vercel** while the API stays on **Fly**, set the same `NEXT_PUBLIC_*` variables in the Vercel project (see `frontend/nextjs/.env.example`). On Fly, **`CORS_ORIGINS`** must list the Vercel origin (e.g. `https://ready-for-robots-ax5i.vercel.app`) or the browser will block authenticated `fetch` calls. The default list in `app/main.py` and `fly.toml` `[env]` includes that host; add any custom domain or extra preview URL the same way.

---

## 5. Local quick check (optional)

Backend only:

```bash
cd /path/to/Ready_For_Robots
source .venv/bin/activate   # or .venv_new, etc.
uvicorn app.main:app --reload --port 8080
```

Open `http://127.0.0.1:8080/health` — should return OK.

---

## 6. Summary checklist for production

1. `flyctl auth login`
2. Set `DATABASE_URL`, `SUPABASE_JWT_SECRET`, and any optional keys (`OPENAI_API_KEY`, `NEWSLETTER_REGEN_SECRET`).
3. For CRM email sends: set **`RESEND_API_KEY`** and **`RESEND_FROM_EMAIL`** on Fly (`fly secrets set …`).
4. Set `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_SITE_URL` in `fly.toml` `[build.args]` to your live URLs (and mirror `NEXT_PUBLIC_*` on Vercel if you build there).
5. Ensure **`CORS_ORIGINS`** on Fly includes every frontend origin (marketing, Fly static, Vercel, localhost).
6. Run `flyctl deploy` from the project root.
7. Test the site and `/health`; test newsletter edition URL without `refresh=true` (should work for everyone).

For more command locations, see `BUILD_AND_DEPLOY.md`.
