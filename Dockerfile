# Ready for Robots — FastAPI backend
# Fly.io deployment Dockerfile (project root)

FROM python:3.12-slim

# ── System dependencies ────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────
COPY app/        ./app/
COPY worker/     ./worker/
COPY migrations  ./migrations/
COPY alembic.ini .

# ── Runtime ───────────────────────────────────────────────────────────────
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
