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

ENV PORT=8000
EXPOSE 8000

# Direct shell command — no script file, no CRLF issues
CMD sh -c "echo '=== Starting CS Control Plane ===' && echo 'PORT='$PORT && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info"
