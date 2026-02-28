# Ready for Robots — Full-stack Fly.io image
# Stage 1: Build Next.js frontend → static HTML/CSS/JS
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/nextjs/package*.json ./
RUN npm ci
COPY frontend/nextjs/ ./
RUN npm run build
# output: /frontend/out/

# Stage 2: FastAPI backend + static frontend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/        ./app/
COPY worker/     ./worker/
COPY migrations  ./migrations/
COPY alembic.ini .

# Copy built Next.js static files
COPY --from=frontend /frontend/out ./static/

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
