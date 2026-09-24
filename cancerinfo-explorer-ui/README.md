# CancerInfo Explorer UI: archived demonstration

This React/Vite client is retained for a possible follow-up project. The launch product is the Python API in the repository root. Do not install this client to run the API or count its features as launch acceptance.

## Current archive status, September 22, 2026

The source directory and ZIP were created in Python refactor `1199f735e3d77b5c1ada35e6451c7a5b4e36d063`. A standalone build has not been validated. `src/components/GoogleDriveSync.tsx` imports a missing `../services/googleDrive` module and Firebase APIs not declared in this archive’s package manifest. These are follow-up issues even if the component is not visible in the UI.

`vite.config.ts` proxies `/v1` to localhost:3000. `VITE_API_BASE_URL` changes the fetch base; the health call uses `/health` when set, which returns a different shape from `/v1/health`. Verify the base path and response contract before reviving the app. Do not add a static clinical database to work around API gaps.

A future demo should show real API responses, source documents, country context and honest empty coverage. It needs its own dependency review, lockfile, build, contract tests and deployment decision. The original feature list and commands below are historical intent, not a promise that this archive works.

## Historical README

## 🎗️ CancerInfo Explorer UI

An open-source interactive Developer Portal & Knowledge Explorer for the **CancerInfo API**.

This frontend provides:
- **Interactive API Testing Console**: Execute live REST queries and inspect headers, latency, and status codes.
- **Clinical Fact Explorer**: Browse cancer types, stages, treatments, and screening guidelines.
- **Fact-Level Provenance Inspector**: Trace medical statements directly to clinical sources (NCI, WHO, NHS, Cancer Australia).
- **RapidAPI & Documentation Hub**: Fast integration guides, code snippets, and direct links to OpenAPI schemas.

---

### 🚀 Quickstart

#### 1. Install Dependencies
```bash
npm install
```

#### 2. Configure API Endpoint
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Set the URL of your CancerInfo API backend:
```env
VITE_API_BASE_URL=http://localhost:3000
```
*(If you run the CancerInfo API backend locally on port 3000, Vite's dev server will automatically proxy `/v1` requests).*

#### 3. Start Development Server
```bash
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

#### 4. Build for Production
```bash
npm run build
```
Static assets will be compiled into the `dist/` directory, ready to deploy to Vercel, Netlify, Cloudflare Pages, or AWS S3 / CloudFront.

---

### 📜 License
MIT License. Dedicated to public cancer health education and open science.
