# Ready for Robots

## Overview
Ready for Robots is an intelligent lead discovery engine designed to identify companies that are ready to adopt robotics solutions in various industries, including hospitality, logistics, and service sectors. The system leverages advanced scraping techniques, natural language processing, and scoring algorithms to detect buying intent signals.

## Project Structure
The project is organized into several key directories:

- **app/**: Contains the main application code, including models, services, scrapers, and API endpoints.
- **worker/**: Contains the Celery worker and task definitions for handling background jobs.
- **readyforrobots-new/**: Contains the canonical Vite web application for marketing, admin, CRM, sales console, supply pipeline, and marketplace routes.
- **frontend/**: Contains the legacy Next.js frontend application files.
- **infra/**: Contains infrastructure-related files, including Docker and Kubernetes configurations.
- **migrations/**: Contains database migration scripts.
- **tests/**: Contains unit and integration tests for the application.
- **scripts/**: Contains utility scripts for setting up and running the application.
- **requirements.txt**: Lists the Python dependencies required for the project.
- **pyproject.toml**: Contains project metadata and dependencies for Python packaging.
- **alembic.ini**: Configuration settings for Alembic, the database migration tool.
- **.env.example**: Example environment variable configuration.

## Features
- **Lead Scoring**: Calculates scores based on automation keywords, labor pain signals, and expansion news.
- **Data Enrichment**: Enhances company and contact data by pulling additional information from external sources.
- **Scraping**: Implements various scrapers to gather data from hotel directories, job boards, news articles, and Google SERP.
- **API Endpoints**: Provides RESTful API endpoints for managing leads, companies, and scoring operations.
- **Background Processing**: Utilizes Celery for running scrapers and recalculating scores asynchronously.

## Getting Started
1. **Clone the Repository**: 
   ```
   git clone <repository-url>
   cd ready-for-robots
   ```

2. **Set Up Environment**: 
   Copy the `.env.example` to `.env` and configure your environment variables.

3. **Install Dependencies**: 
   ```
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**: 
   ```
   alembic upgrade head
   ```

5. **Start the Application**: 
   ```
   uvicorn app.main:app --reload
   ```

6. **Run Background Worker**: 
   ```
   celery -A worker.celery_worker worker --loglevel=info
   ```

## Frontend

The canonical web app lives under **`readyforrobots-new/`**. Vercel (`readyforrobots.com`) and Fly (`ready-2-robot.fly.dev`) should both serve this same Vite app so routes like `/admin`, `/crm`, `/sales-console`, `/supply-pipeline`, and `/marketplace` match across domains.

Fly remains the FastAPI backend/runtime. The Vite app should call `https://ready-2-robot.fly.dev` for API requests when it is served from `readyforrobots.com`.

Root scripts now target the canonical Vite app:

```
npm run install:web
npm run dev
npm run check
npm run build
```

Legacy Next.js commands are still available with the `legacy:next:*` script names for reference or migration work.

### Vercel settings

The Vercel project for `readyforrobots.com` must be a **static** deploy (0 serverless functions):

- **Root Directory:** repository root (`.`) **or** `readyforrobots-new` (both have `vercel.json` — static Vite only).
- **Do not** set Root Directory to `frontend/nextjs` (legacy Next.js creates 12+ serverless routes on Hobby).
- **Framework Preset:** Other (not Next.js / not Python).
- API lives on Fly (`ready-2-robot.fly.dev`); `/api/*` is rewritten in `vercel.json`, not implemented on Vercel.

If the build fails with “No more than 12 Serverless Functions”, the project is building server/API code on Vercel — fix Root Directory and redeploy.

- Framework preset: Vite or Other
- Install command: `npx --yes pnpm@10.4.1 install --frozen-lockfile -C readyforrobots-new`
- Build command: `cd readyforrobots-new && VITE_PUBLIC_API_URL=https://ready-2-robot.fly.dev npx --yes pnpm@10.4.1 exec vite build`
- Output directory: `readyforrobots-new/dist/public`
- Environment variable: `VITE_PUBLIC_API_URL=https://ready-2-robot.fly.dev`

After deployment, verify these URLs load the same Vite surface:

- `https://readyforrobots.com/admin`
- `https://readyforrobots.com/crm`
- `https://readyforrobots.com/sales-console`
- `https://readyforrobots.com/supply-pipeline`
- `https://ready-2-robot.fly.dev/admin`

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.