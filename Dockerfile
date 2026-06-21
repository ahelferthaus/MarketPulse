FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY docs/ ./docs/
COPY data/ ./data/

# Create data directories
RUN mkdir -p data/cache data/exports data/static_site_payloads

# Environment
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data
ENV DUCKDB_PATH=/app/data/marketpulse.duckdb
ENV CACHE_PATH=/app/data/cache.sqlite
ENV EXPORTS_DIR=/app/data/exports
ENV STATIC_PAYLOADS_DIR=/app/data/static_site_payloads
ENV MARKETPULSE_MODE=public
ENV LOG_LEVEL=INFO

EXPOSE 8000

CMD ["python", "-m", "backend.main"]
