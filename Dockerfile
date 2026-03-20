FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2, chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code + config
COPY backend/ .

# Port from Railway
ENV PORT=8000
EXPOSE 8000

# Run: migrate then start
CMD alembic upgrade head && gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
