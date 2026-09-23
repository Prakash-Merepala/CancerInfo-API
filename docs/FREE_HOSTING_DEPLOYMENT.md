# Free Cloud Hosting Deployment Guide for CancerInfo API

## Current guidance, September 22, 2026

This guide applies to Python refactor `1199f735e3d77b5c1ada35e6451c7a5b4e36d063`. Current guidance below supersedes the prior draft retained at the end.

### Deployment and environments

Docker now builds a Python 3.11 slim image, installs requirements and starts app.main:app. It copies app, docs, tests, rapidapi and cancerinfo.db. Node and the archived React client are not installed by the API image. Image build/boot was not run because Docker is unavailable here.

The command hardcodes port 3000 despite setting PORT. Compose configures sqlite:///./cancerinfo.db, which resolves under /app, while its named volume mounts /app/data. Database persistence therefore requires correction and a restart test. Startup runs create_all plus seed_database; no versioned production migration exists.

CI uses Python 3.10; image uses 3.11; local validation used 3.12.2. Requirements have lower bounds and no Python lock was found. Confirm the supported version and reproducible dependency set. PostgreSQL is configurable through DATABASE_URL but no hosted PostgreSQL or production endpoint was verified. Choose a host based on actual durability, resource and cost constraints, not a guaranteed free-hosting claim.

### Operations runbook

Operate the FastAPI process and its configured database. Local startup creates tables and calls the seed routine; until production seeding and migrations are corrected, booting an empty database can create development content. Do not use startup as a production migration or publication procedure.

The two admin POST endpoints trigger seed and source ingestion. They accept an admin key through X-Admin-Key or Bearer authorization. The configuration has a development default; production must reject missing/default secrets and keep admin routes outside the public gateway. There is no committed scheduled ingestion workflow.

For each controlled ingestion, retain job metrics, exact document identity, before/after hashes, citation changes and publication review. Current SUCCESS is insufficient evidence because all-fetch failure was reproduced. Monitor API errors, database readiness, source failures, freshness, rights changes and backup restore. Use a reviewed dataset snapshot for rollback; no successful restore was demonstrated.

### Rollback and contingency

No tested rollback baseline exists for the Python deployment. Before release, capture a reviewed image digest, database backup, schema version, dataset manifest and public OpenAPI export. Demonstrate restore in an isolated environment and verify citations and representative endpoint output.

The committed SQLite file and automatic seed routine are development inputs, not a safe recovery plan. The compose volume currently mounts /app/data while the configured SQLite file lives at /app/cancerinfo.db. Recreating the container can therefore lose writes despite a named volume.

If September 27 gates are incomplete, keep the listing private and choose a smaller reviewed corpus or revise timing. September 28 is a six-day buffer before October 4. Never bypass publication/rights gates or use the removed Node JSON server as an assumed equivalent rollback.

### Provider decision and deployment sequence

Render, Cloud Run, Railway and Docker hosting remain candidates from the earlier draft; none is selected or verified by this assessment. Consult the chosen provider’s current official pricing and runtime/storage documentation before budgeting. Do not assume free persistent disks, a permanent free tier or the example URL below.

Choose one provider and database, record the supported Python version and image digest, configure production secrets and trusted proxy/origin behavior, run migrations separately, load only the reviewed corpus, then prove restart persistence and restore. Verify port handling, docs, public endpoints, admin exclusion and database failure behavior. Record the actual HTTPS origin before updating the marketplace artifact. Do not use the legacy deployment commands below as a production runbook.

## Historical draft, not current instructions or verified claims

The following original draft is retained to preserve review history. It may contain obsolete commands, unsupported numbers, clinical examples and unverified readiness claims. Do not execute or publish those claims without replacing them with the current accepted implementation and evidence.

## Free Cloud Hosting Deployment Guide for CancerInfo API

CancerInfo API is packaged as a standard containerized application (`Dockerfile` & `docker-compose.yml`) that can be deployed for **$0/month** on major cloud hosting platforms.

---

### 1. Deploy to Render (Recommended — Easiest Free Setup)

[Render](https://render.com) provides a free Web Service tier:

1. Push this repository to your GitHub account.
2. Sign in to [dashboard.render.com](https://dashboard.render.com/) and click **New + > Web Service**.
3. Connect your GitHub repository.
4. Configure settings:
   - **Name**: `cancerinfo-api`
   - **Region**: Oregon (US West) or Frankfurt (EU Central)
   - **Branch**: `main`
   - **Environment**: `Docker` (or Node + Python)
   - **Instance Type**: **Free** ($0/month)
5. Under **Environment Variables**, add:
   - `ENVIRONMENT`: `production`
   - `DATABASE_URL`: `sqlite:///./cancerinfo.db` (or Neon PostgreSQL free tier URL)
6. Click **Create Web Service**.
7. Render will automatically build the container and provide a public HTTPS URL:
   `https://cancerinfo-api.onrender.com`
8. Verify by opening `https://cancerinfo-api.onrender.com/v1/health` and `https://cancerinfo-api.onrender.com/docs`.

---

### 2. Deploy to Google Cloud Run (2 Million Requests/Month Forever Free)

Google Cloud Run offers a generous free tier (2,000,000 requests/month free every month):

```bash
## 1. Build & submit container image to Google Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cancerinfo-api

## 2. Deploy to Cloud Run with public ingress
gcloud run deploy cancerinfo-api \
  --image gcr.io/YOUR_PROJECT_ID/cancerinfo-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi
```

---

### 3. Deploy to Railway

1. Sign in to [Railway.app](https://railway.app).
2. Click **New Project > Deploy from GitHub repo**.
3. Select `cancerinfo-api`.
4. Railway detects the `Dockerfile` automatically and deploys the service.
5. In the service settings, click **Generate Domain** to get a public `railway.app` URL.

---

### 4. Deploy to Hugging Face Spaces (Docker Free Tier)

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces).
2. Select **Docker** as the Space SDK.
3. Push this repository to the Hugging Face Space git remote.
4. Hugging Face builds and hosts the API with public HTTPS access.

---

### 5. Self-Hosting with Docker Compose (1-Command)

Run locally or on any cheap VPS (DigitalOcean, Hetzner, AWS Lightsail):

```bash
## Clone and launch in detached mode
git clone https://github.com/cancerinfo-api/cancerinfo-api.git
cd cancerinfo-api
docker compose up -d

## Verify health
curl -s http://localhost:3000/v1/health
```
