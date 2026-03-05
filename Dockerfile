# Ready for Robots — Full-stack Fly.io image
# Stage 1: Build Next.js frontend (SSR mode - not static export)
FROM node:20-slim AS frontend
WORKDIR /frontend

# Supabase public keys
ARG NEXT_PUBLIC_SUPABASE_URL=""
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=""
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

COPY frontend/nextjs/package*.json ./
RUN npm ci
COPY frontend/nextjs/ ./
RUN npm run build
# output: /frontend/.next/ (production build with SSR support)

# Stage 2: Runtime image with both Python backend and Node.js frontend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Install Node.js, gcc, and postgres client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python app code
COPY app/        ./app/
COPY worker/     ./worker/
COPY migrations  ./migrations/
COPY scripts/    ./scripts/
COPY alembic.ini .

# Copy built Next.js app and node_modules from build stage
COPY --from=frontend /frontend/.next ./frontend/.next
COPY --from=frontend /frontend/node_modules ./frontend/node_modules
COPY --from=frontend /frontend/package.json ./frontend/package.json
COPY --from=frontend /frontend/next.config.js ./frontend/next.config.js
COPY --from=frontend /frontend/public ./frontend/public

EXPOSE 8080

# Start all services: app + celery worker + celery beat + Next.js server
CMD ["bash", "/code/scripts/start_all.sh"]
