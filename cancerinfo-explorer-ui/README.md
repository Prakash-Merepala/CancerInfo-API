# 🎗️ CancerInfo Explorer UI

An open-source interactive Developer Portal & Knowledge Explorer for the **CancerInfo API**.

This frontend provides:
- **Interactive API Testing Console**: Execute live REST queries and inspect headers, latency, and status codes.
- **Clinical Fact Explorer**: Browse cancer types, stages, treatments, and screening guidelines.
- **Fact-Level Provenance Inspector**: Trace medical statements directly to clinical sources (NCI, WHO, NHS, Cancer Australia).
- **RapidAPI & Documentation Hub**: Fast integration guides, code snippets, and direct links to OpenAPI schemas.

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure API Endpoint
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Set the URL of your CancerInfo API backend:
```env
VITE_API_BASE_URL=http://localhost:3000
```
*(If you run the CancerInfo API backend locally on port 3000, Vite's dev server will automatically proxy `/v1` requests).*

### 3. Start Development Server
```bash
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

### 4. Build for Production
```bash
npm run build
```
Static assets will be compiled into the `dist/` directory, ready to deploy to Vercel, Netlify, Cloudflare Pages, or AWS S3 / CloudFront.

---

## 📜 License
MIT License. Dedicated to public cancer health education and open science.
