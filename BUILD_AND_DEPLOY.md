# Build & Deploy — Command Order, Scripts, and Where to Run

## 1. Order of Commands

### Deploy to production (Fly.io)
```bash
# From project root — one command does everything
flyctl deploy
```
If the command hangs on **“Waiting for depot builder…”** (Depot capacity/timeouts), use the legacy builder instead:
```bash
flyctl deploy --depot=false
```
The Dockerfile builds the Next.js frontend and packages the FastAPI backend. No separate `npm run build` needed.

---

### Local development (optional)
```bash
# Terminal 1 — Backend
cd /Users/leguplabs/Desktop/Ready_For_Robots
source .venv_new/bin/activate   # or your venv
uvicorn app.main:app --reload --port 8080

# Terminal 2 — Frontend
cd /Users/leguplabs/Desktop/Ready_For_Robots
./start-frontend.sh
# Or: cd frontend/nextjs && npm run dev
```

---

### Build frontend only (for testing export)
```bash
cd /Users/leguplabs/Desktop/Ready_For_Robots/frontend/nextjs
npm run build
```
Output goes to `frontend/nextjs/out/`.

---

## 2. Scripts

| Script | Where | Purpose |
|--------|-------|---------|
| `flyctl deploy` | **Project root** | Deploy full app to Fly.io (handles Next.js + Python build) |
| `./start-frontend.sh` | **Project root** | Start Next.js dev server (port 3000) |
| `./scripts/start_all.sh` | Inside Docker | Starts uvicorn + Celery (used by Fly.io) |
| `./scripts/start_scraper_scheduler.sh` | **Project root** | Start Celery worker + beat for scrapers |
| `npm run build` | **frontend/nextjs/** | Build Next.js static export |
| `npm run dev` | **frontend/nextjs/** | Next.js dev server |

---

## 3. Where to Run Each Command

| Command | Directory |
|---------|-----------|
| `flyctl deploy` | `/Users/leguplabs/Desktop/Ready_For_Robots` (project root) |
| `npm run build` | `/Users/leguplabs/Desktop/Ready_For_Robots/frontend/nextjs` |
| `npm run dev` | `/Users/leguplabs/Desktop/Ready_For_Robots/frontend/nextjs` |
| `./start-frontend.sh` | `/Users/leguplabs/Desktop/Ready_For_Robots` |
| `uvicorn app.main:app ...` | `/Users/leguplabs/Desktop/Ready_For_Robots` |
| `./scripts/start_scraper_scheduler.sh` | `/Users/leguplabs/Desktop/Ready_For_Robots` |

---

## Quick reference

**Deploy to production:**
```bash
cd /Users/leguplabs/Desktop/Ready_For_Robots
flyctl deploy
```

**Why `npm run build` failed at root:** `package.json` is in `frontend/nextjs/`, not at the project root. Either:
- `cd frontend/nextjs && npm run build`, or
- Use `flyctl deploy` (Dockerfile runs the build in the correct context)
