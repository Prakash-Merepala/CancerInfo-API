# Multi-stage production build for CancerInfo API
FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production runtime container
FROM python:3.10-slim

WORKDIR /app

# Install Node.js runtime for the API gateway & portal
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and compiled assets
COPY app/ ./app/
COPY --from=builder /app/dist/ ./dist/
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

ENV PORT=3000
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

CMD ["node", "dist/server.cjs"]
