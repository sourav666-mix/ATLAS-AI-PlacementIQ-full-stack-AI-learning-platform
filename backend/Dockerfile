# Dockerfile - backend container image
# FILE: backend/Dockerfile
# BATCH 19 - FastAPI backend image (Railway builds this automatically).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /code

# System deps: mysql client libs for aiomysql healthchecks + reportlab fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
# Railway injects $PORT; local docker-compose uses the 8000 default.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]