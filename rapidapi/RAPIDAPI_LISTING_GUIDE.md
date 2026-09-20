# RapidAPI Publisher Guide for CancerInfo API

This guide provides step-by-step instructions for listing **CancerInfo API** on [RapidAPI Hub](https://rapidapi.com/hub) (and similar API marketplaces like Postman Public API Network, APILayer, and ProgrammableWeb) to serve the global developer and healthcare community 100% free of charge.

---

## 1. Prerequisites

1. A free publisher account at [RapidAPI.com](https://rapidapi.com/).
2. A deployed production URL for CancerInfo API (see `docs/FREE_HOSTING_DEPLOYMENT.md` for Render, Railway, Fly.io, or Cloud Run setup).
3. The prepared schema in `rapidapi/rapidapi-openapi.json` and collection in `rapidapi/postman_collection.json`.

---

## 2. Step-by-Step RapidAPI Hub Listing

### Step 1: Add New API in RapidAPI Provider Dashboard
1. Log in to [RapidAPI Studio / Provider Dashboard](https://rapidapi.com/provider).
2. Click **"Add New API"** in the top right.
3. Complete the API Identity details:
   - **API Name**: `CancerInfo API`
   - **Short Description**: `Free, global, source-transparent cancer knowledge REST API with fact-level provenance from NCI, WHO, NHS, and Cancer Australia.`
   - **Category**: `Health and Fitness`
   - **Specify using**: Select **OpenAPI / Swagger Document**.
   - **Upload File**: Select `rapidapi/rapidapi-openapi.json` from this repository.
4. Click **Add API**. RapidAPI will automatically parse all paths, query parameters, descriptions, and schemas.

---

### Step 2: Configure Base Target URL
1. Navigate to the **Hub Listing > Target URLs** tab in RapidAPI Studio.
2. Enter your deployed server address as the default target URL:
   - Example: `https://cancerinfo-api.onrender.com`
   - Test connection by clicking **Ping Target**.

---

### Step 3: Configure 100% Free Community Pricing Plan
Our core mission is to empower researchers, developers, students, and patients free of charge.
1. Navigate to **Monetization > Plans & Pricing**.
2. Under the **Basic Plan** (Free):
   - **Plan Price**: `$0 / month`
   - **Requests Quota**: Set to **Unlimited** or generous community rate (e.g. `100,000 requests/month`).
   - **Rate Limit**: `120 requests/minute` (matches CancerInfo API's internal rate-limiter).
   - **Overage Fee**: `$0.00`.
3. Disable all paid tiers (Pro, Ultra, Mega) or mark them as hidden, ensuring developers never hit surprise paywalls.

---

### Step 4: RapidAPI Hub Listing Enrichment
In the **Hub Listing > Overview** tab, enrich the presentation:

- **Logo**: Upload the CancerInfo badge icon (`/public/icon.png` or ribbon emblem).
- **Long Description**:
  ```markdown
  ### CancerInfo API — Global Cancer Knowledge with Provenance

  CancerInfo API is a free, structured public REST API delivering verified clinical cancer knowledge from world-leading public health organizations.

  #### Why Developers Use CancerInfo API:
  - 🔍 **Fact-Level Provenance**: Every symptom, screening guideline, and treatment record includes exact source URLs, retrieval dates, and legal attributions.
  - 🌐 **International Jurisdictions**: Compare health guidance between the US (NCI), UK (NHS), Australia (Cancer Australia), and WHO (Global).
  - 🧬 **Taxonomy Normalization**: Resolves acronyms (e.g., CRC -> Colorectal Cancer) and maps aliases across 37 standardized cancer categories.
  - 🛡️ **100% Free & Open**: Dedicated in honor of cancer fighters and their families.
  ```
- **Website Link**: Your GitHub repository URL.
- **Terms of Service**: Open Source (MIT) with standard clinical disclaimer: *"CancerInfo API provides informational data only and does not provide medical diagnosis or personal treatment advice."*

---

### Step 5: Test and Publish
1. Go to the **Endpoints** tab and click **Test Endpoint** on `/v1/health` and `/v1/cancers`.
2. Confirm the response status is `200 OK` and returns verified JSON.
3. Toggle the API status from **Draft** to **Public**.
4. CancerInfo API will immediately be live and searchable by over 4,000,000 developers worldwide!

---

## 3. Alternative Free API Directories to Submit To

To maximize reach, submit CancerInfo API to these high-traffic public API directories:

1. **GitHub `public-apis/public-apis` Repository**:
   - Submit a Pull Request to the popular [public-apis](https://github.com/public-apis/public-apis) repository under the **Health** category.
   - Entry format:
     `| CancerInfo | Free, source-transparent cancer knowledge with fact-level provenance | No | HTTPS | Yes |`
2. **Postman Public API Network**:
   - In Postman, import `rapidapi/postman_collection.json`, click **Share Collection > Via Public API Network**.
3. **APIs.guru Directory**:
   - Submit `rapidapi/rapidapi-openapi.json` to the Wikipedia of Web APIs.
