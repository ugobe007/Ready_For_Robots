# Ready for Robots — Full-stack Fly.io image
# Stage 1: Build readyforrobots-new (Vite) → static HTML/CSS/JS served by FastAPI
FROM node:20-slim AS frontend
WORKDIR /rfr
RUN npm install -g pnpm@10.4.1 --force

ARG VITE_PUBLIC_API_URL=""
ARG VITE_PUBLIC_SUPABASE_URL=""
ARG VITE_PUBLIC_SUPABASE_ANON_KEY=""
ENV VITE_PUBLIC_API_URL=$VITE_PUBLIC_API_URL
ENV VITE_PUBLIC_SUPABASE_URL=$VITE_PUBLIC_SUPABASE_URL
ENV VITE_PUBLIC_SUPABASE_ANON_KEY=$VITE_PUBLIC_SUPABASE_ANON_KEY

COPY readyforrobots-new/package.json readyforrobots-new/pnpm-lock.yaml ./
COPY readyforrobots-new/patches ./patches
RUN pnpm install --frozen-lockfile
COPY readyforrobots-new/ ./
# Vite @ontology alias resolves to ../app/data/ relative to readyforrobots-new/
COPY app/data/industry_sector_ontology.json /app/data/industry_sector_ontology.json
RUN pnpm run build
# Vite client output: /rfr/dist/public/

# Stage 2: FastAPI backend + static frontend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies + Playwright Chromium (required for hotel/job-board scrapers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Copy Python app code
COPY app/        ./app/
COPY worker/     ./worker/
COPY migrations  ./migrations/
COPY scripts/    ./scripts/
COPY alembic.ini .
COPY ["Robot Automation Signal Ontology.md", "./"]

# Copy built SPA static files
COPY --from=frontend /rfr/dist/public ./static/

EXPOSE 8080

# Start all services: app + celery worker + celery beat
CMD ["bash", "/code/scripts/start_all.sh"]
