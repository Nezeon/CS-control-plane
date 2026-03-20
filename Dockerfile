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

# Make start script executable
RUN chmod +x start.sh

# Port from Railway
ENV PORT=8000
EXPOSE 8000

# Start via script with logging
CMD ["bash", "start.sh"]
