# Deploying the static site (`out/`)

Production builds use Next.js **`output: 'export'`** (see `next.config.js`): `npm run build` writes a full static site under **`frontend/nextjs/out/`**.

## Recommended workflow

1. **Install deps** (when `package-lock.json` changes):  
   `npm install`

2. **Build** from this directory:  
   `npm run build`  
   This regenerates **`out/`** with a single consistent build id, chunks, and HTML.

3. **Commit** the updated **`out/`** tree **in one commit** with the source changes you intend to ship (or immediately after build). Partial or mixed exports (e.g. interrupted builds, manual “Duplicate” files from macOS Finder) leave broken paths; the repo ignores Finder-style names like `* 2.*` under `out/`.

4. **Deploy** by uploading or syncing the contents of **`out/`** to your host (S3, CloudFront, Netlify, nginx, etc.), per your infrastructure.

## Dev vs production

- **Development**: `npm run dev` — no static export; API calls can be proxied to the FastAPI backend.
- **Production build**: `npm run build` — static files only; no Node server required to serve the exported site.

## See also

- Root **`README.md`** — project overview and backend setup.
