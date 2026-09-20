# Free Cloud Hosting Deployment Guide for CancerInfo API

CancerInfo API is packaged as a standard containerized application (`Dockerfile` & `docker-compose.yml`) that can be deployed for **$0/month** on major cloud hosting platforms.

---

## 1. Deploy to Render (Recommended — Easiest Free Setup)

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

## 2. Deploy to Google Cloud Run (2 Million Requests/Month Forever Free)

Google Cloud Run offers a generous free tier (2,000,000 requests/month free every month):

```bash
# 1. Build & submit container image to Google Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cancerinfo-api

# 2. Deploy to Cloud Run with public ingress
gcloud run deploy cancerinfo-api \
  --image gcr.io/YOUR_PROJECT_ID/cancerinfo-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi
```

---

## 3. Deploy to Railway

1. Sign in to [Railway.app](https://railway.app).
2. Click **New Project > Deploy from GitHub repo**.
3. Select `cancerinfo-api`.
4. Railway detects the `Dockerfile` automatically and deploys the service.
5. In the service settings, click **Generate Domain** to get a public `railway.app` URL.

---

## 4. Deploy to Hugging Face Spaces (Docker Free Tier)

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces).
2. Select **Docker** as the Space SDK.
3. Push this repository to the Hugging Face Space git remote.
4. Hugging Face builds and hosts the API with public HTTPS access.

---

## 5. Self-Hosting with Docker Compose (1-Command)

Run locally or on any cheap VPS (DigitalOcean, Hetzner, AWS Lightsail):

```bash
# Clone and launch in detached mode
git clone https://github.com/cancerinfo-api/cancerinfo-api.git
cd cancerinfo-api
docker compose up -d

# Verify health
curl -s http://localhost:3000/v1/health
```
