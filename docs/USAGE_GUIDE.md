# CancerInfo API Multi-Language Usage Guide

This guide provides practical code snippets in popular languages for integrating CancerInfo API directly or via RapidAPI Hub.

---

## 1. cURL / Shell

```bash
# Get symptoms with fact-level provenance
curl -X GET "http://localhost:3000/v1/cancers/breast-cancer/symptoms?country=US" \
  -H "Accept: application/json"
```

---

## 2. Python (requests & httpx)

```python
import requests

BASE_URL = "http://localhost:3000/v1"

# 1. Search for a cancer or abbreviation
response = requests.get(f"{BASE_URL}/search", params={"q": "CRC"})
data = response.json()
print("Matched Cancer:", data["data"]["results"][0]["cancer"]["canonical_name"])

# 2. Fetch screening guidelines with source citation
screening_res = requests.get(
    f"{BASE_URL}/cancers/colorectal-cancer/screening",
    params={"country": "GB"}
)
screening_data = screening_res.json()
records = screening_data["data"]["records"]

for rec in records:
    print("\n--- Guideline ---")
    print(rec["content"])
    print("Source:", rec["sources"][0]["organization"])
    print("Source URL:", rec["sources"][0]["url"])
```

---

## 3. TypeScript / Node.js (fetch)

```typescript
interface CancerResponse {
  data: {
    cancer: {
      canonical_name: string;
      slug: string;
    };
    records: Array<{
      content: string;
      sources: Array<{
        organization: string;
        url: string;
        attribution_text: string;
      }>;
    }>;
  };
}

async function getCancerSymptoms(slug: string, country: string = "US"): Promise<void> {
  const url = `http://localhost:3000/v1/cancers/${slug}/symptoms?country=${country}`;
  
  const res = await fetch(url, {
    headers: { "Accept": "application/json" }
  });
  
  if (!res.ok) {
    throw new Error(`API Error: ${res.statusText}`);
  }
  
  const data: CancerResponse = await res.json();
  console.log(`Cancer: ${data.data.cancer.canonical_name}`);
  
  data.data.records.forEach((record, index) => {
    console.log(`\n[Record ${index + 1}]: ${record.content}`);
    console.log(`Citation: ${record.sources[0]?.organization} (${record.sources[0]?.url})`);
  });
}

getCancerSymptoms("breast-cancer", "US");
```

---

## 4. Go

```go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type HealthResponse struct {
	Status    string `json:"status"`
	ApiName   string `json:"api_name"`
	Database  string `json:"database"`
}

func main() {
	resp, err := http.Get("http://localhost:3000/v1/health")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var health HealthResponse
	json.Unmarshal(body, &health)

	fmt.Printf("API Name: %s\nStatus: %s\nDatabase: %s\n", health.ApiName, health.Status, health.Database)
}
```

---

## 5. Android (Kotlin / Retrofit)

```kotlin
interface CancerInfoService {
    @GET("v1/cancers/{cancer}/symptoms")
    suspend fun getSymptoms(
        @Path("cancer") cancerSlug: String,
        @Query("country") country: String? = "US"
    ): Response<CancerKnowledgeResponse>
}
```

---

## 6. iOS (Swift / URLSession)

```swift
import Foundation

struct CancerSource: Codable {
    let organization: String
    let url: String
}

struct CancerRecord: Codable {
    let content: String
    let sources: [CancerSource]
}

func fetchCancerSymptoms(cancer: String) async throws {
    let url = URL(string: "http://localhost:3000/v1/cancers/\(cancer)/symptoms?country=US")!
    let (data, _) = try await URLSession.shared.data(from: url)
    print("Received payload: \(data.count) bytes")
}
```
