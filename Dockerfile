# Production container for CancerInfo API
FROM python:3.11-slim

WORKDIR /app

# Install system utilities and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application, documentation, database, and tests
COPY app/ ./app/
COPY docs/ ./docs/
COPY tests/ ./tests/
COPY rapidapi/ ./rapidapi/
COPY cancerinfo.db ./cancerinfo.db

EXPOSE 3000

ENV PORT=3000
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]

