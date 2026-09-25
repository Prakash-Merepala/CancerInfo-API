# Production container for CancerInfo API
FROM python:3.11-slim

WORKDIR /app

# Install system utilities and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create durable data directory for container-local storage
RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Copy application code, documentation, and API specifications
COPY app/ ./app/
COPY docs/ ./docs/
COPY rapidapi/ ./rapidapi/

EXPOSE 3000

ENV PORT=3000
ENV ENVIRONMENT=production
ENV DATABASE_URL=sqlite:////app/data/cancerinfo.db
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
