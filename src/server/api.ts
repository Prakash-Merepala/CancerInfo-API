import { Router, Request, Response } from "express";
import fs from "fs";
import path from "path";

// Initialize Router
export const apiRouter = Router();

// In-memory database loaded from src/data/db.json
let dbData: any = null;

function loadDatabase() {
  if (dbData) return dbData;
  const dbPath = path.join(process.cwd(), "src/data/db.json");
  if (fs.existsSync(dbPath)) {
    const raw = fs.readFileSync(dbPath, "utf-8");
    dbData = JSON.parse(raw);
  } else {
    dbData = {
      sources: [],
      cancers: [],
      cancer_aliases: [],
      source_documents: [],
      content_records: [],
      source_health: [],
      content_sources: [],
      content_versions: [],
    };
  }
  return dbData;
}

export const CANONICAL_CATEGORIES: Record<string, { name: string; description: string }> = {
  overview: { name: "Overview", description: "High-level summary, definition, and introduction" },
  types_and_subtypes: { name: "Types & Subtypes", description: "Histological or anatomical subtypes" },
  symptoms: { name: "Symptoms", description: "Patient-reported indications and sensations" },
  signs: { name: "Signs", description: "Clinically observable physical indicators" },
  causes: { name: "Causes", description: "Known direct etiologies and biological mechanisms" },
  risk_factors: { name: "Risk Factors", description: "Lifestyle, genetic, and environmental factors that elevate risk" },
  prevention: { name: "Prevention", description: "Primary prevention measures and lifestyle interventions" },
  screening: { name: "Screening", description: "Population and targeted screening recommendations and guidelines" },
  early_detection: { name: "Early Detection", description: "Early diagnosis strategies and warning signs" },
  diagnosis: { name: "Diagnosis", description: "Diagnostic pathway and clinical confirmation" },
  diagnostic_tests: { name: "Diagnostic Tests", description: "Biopsies, imaging, blood tests, and scans" },
  grading: { name: "Grading", description: "Tumor differentiation grades (G1-G4)" },
  staging: { name: "Staging", description: "TNM staging, Roman numeral stages (0-IV)" },
  biomarkers: { name: "Biomarkers", description: "Molecular markers (e.g. HER2, ER/PR, EGFR, BRAF, PSA)" },
  genetics: { name: "Genetics", description: "Hereditary cancer syndromes and germline/somatic mutations" },
  treatment: { name: "Treatment", description: "General treatment modalities and overarching therapy strategies" },
  surgery: { name: "Surgery", description: "Surgical procedures, resections, and margins" },
  chemotherapy: { name: "Chemotherapy", description: "Systemic cytotoxic anti-cancer medications" },
  radiation_therapy: { name: "Radiation Therapy", description: "External beam, brachytherapy, and proton therapies" },
  immunotherapy: { name: "Immunotherapy", description: "Checkpoint inhibitors, CAR T-cell therapy, vaccines" },
  targeted_therapy: { name: "Targeted Therapy", description: "Small molecules, monoclonal antibodies targeting mutations" },
  hormone_therapy: { name: "Hormone Therapy", description: "Endocrine therapies (e.g. anti-estrogens, anti-androgens)" },
  stem_cell_transplant: { name: "Stem Cell Transplant", description: "Autologous and allogeneic bone marrow/stem cell transplants" },
  supportive_care: { name: "Supportive Care", description: "Management of treatment side effects and supportive care" },
  side_effects: { name: "Side Effects", description: "Adverse events and toxicities associated with therapies" },
  prognosis: { name: "Prognosis", description: "Prognostic outlook and factors influencing outcomes" },
  survival: { name: "Survival", description: "5-year and 10-year relative survival rates and data" },
  recurrence: { name: "Recurrence", description: "Local, regional, and distant cancer recurrence patterns" },
  follow_up: { name: "Follow-up", description: "Surveillance regimens and survivorship monitoring" },
  palliative_care: { name: "Palliative Care", description: "Specialized comfort care and symptom management" },
  living_with_cancer: { name: "Living with Cancer", description: "Quality of life, emotional wellness, diet, and exercise" },
  caregiver_information: { name: "Caregiver Information", description: "Guidance for family members, friends, and caregivers" },
  childhood_cancer: { name: "Childhood Cancer", description: "Pediatric-specific considerations and protocols" },
  research: { name: "Research", description: "Current scientific research initiatives and advancements" },
  statistics: { name: "Statistics", description: "Incidence, prevalence, and mortality statistics by region" },
  clinical_trials: { name: "Clinical Trials", description: "Investigational studies and registry resources" },
  terminology: { name: "Terminology", description: "Medical glossaries, abbreviations, and lay definitions" },
};

export const CATEGORY_ALIASES: Record<string, string> = {
  types: "types_and_subtypes",
  subtypes: "types_and_subtypes",
  "risk-factors": "risk_factors",
  "early-detection": "early_detection",
  "diagnostic-tests": "diagnostic_tests",
  radiation: "radiation_therapy",
  chemo: "chemotherapy",
  "targeted-therapy": "targeted_therapy",
  hormone: "hormone_therapy",
  "stem-cell-transplant": "stem_cell_transplant",
  supportive: "supportive_care",
  "side-effects": "side_effects",
  followup: "follow_up",
  palliative: "palliative_care",
  "living-with-cancer": "living_with_cancer",
  caregivers: "caregiver_information",
  childhood: "childhood_cancer",
  trials: "clinical_trials",
  stats: "statistics",
  genes: "genetics",
};

export const COUNTRIES: Record<string, { code: string; name: string; region: string; default_language: string }> = {
  US: { code: "US", name: "United States", region: "Americas", default_language: "en" },
  GB: { code: "GB", name: "United Kingdom", region: "Europe", default_language: "en" },
  AU: { code: "AU", name: "Australia", region: "Oceania", default_language: "en" },
  CA: { code: "CA", name: "Canada", region: "Americas", default_language: "en" },
  GLOBAL: { code: "GLOBAL", name: "Global / International", region: "Global", default_language: "en" },
};

export const MEDICAL_DISCLAIMER =
  "CancerInfo API provides public informational data aggregated from authoritative health organizations for developers and researchers. It does not provide medical diagnosis, personal treatment recommendations, individualized drug selection or dosage, or replace licensed medical professionals.";

export function normalizeCategory(rawTitle: string): string {
  const rawLower = rawTitle.trim().toLowerCase();
  const slugified = rawLower.replace(/\s+/g, "_").replace(/-/g, "_");
  if (CANONICAL_CATEGORIES[slugified]) return slugified;
  if (CATEGORY_ALIASES[rawLower]) return CATEGORY_ALIASES[rawLower];

  const heuristics: [RegExp, string][] = [
    [/\b(early detection|catching it early)\b/i, "early_detection"],
    [/\b(screens?|screening|mammograms?|colonoscop(y|ies)|pap smears?|psa tests?)\b/i, "screening"],
    [/\b(symptoms?|warning signs?|feeling|physical signs?)\b/i, "symptoms"],
    [/\b(signs?|clinical signs?|manifestations?)\b/i, "signs"],
    [/\b(risk factors?|causes?|etiolog(y|ies)|who is at risk)\b/i, "risk_factors"],
    [/\b(prevents?|prevention|reducing risks?|lifestyles?)\b/i, "prevention"],
    [/\b(diagnos(is|tic|ed)|finding cancer|how is it diagnosed|detect(ion)?)\b/i, "diagnosis"],
    [/\b(tests?|biops(y|ies)|scans?|mri|ct scans?|ultrasounds?|blood tests?|diagnostic tests?)\b/i, "diagnostic_tests"],
    [/\b(stages?|staging|tnm|metastasis|spread)\b/i, "staging"],
    [/\b(grades?|grading|differentiation)\b/i, "grading"],
    [/\b(biomarkers?|her2|er\/pr|egfr|braf|kras|msi|pdl1)\b/i, "biomarkers"],
    [/\b(genetics?|genetic testing|brca|lynch syndrome|hereditary)\b/i, "genetics"],
    [/\b(surger(y|ies)|surgical|mastectom(y|ies)|lumpectom(y|ies)|resections?|operations?)\b/i, "surgery"],
    [/\b(chemotherap(y|ies)|chemo|cytotoxics?)\b/i, "chemotherapy"],
    [/\b(radiat(ion|ing)|radiotherapy|beam)\b/i, "radiation_therapy"],
    [/\b(immunotherap(y|ies)|checkpoints?|car-t|pembrolizumab)\b/i, "immunotherapy"],
    [/\b(targeted therap(y|ies)|targeted drugs?|tyrosine kinase)\b/i, "targeted_therapy"],
    [/\b(hormone therap(y|ies)|endocrine|tamoxifen|aromatase)\b/i, "hormone_therapy"],
    [/\b(stem cells?|bone marrow|transplants?)\b/i, "stem_cell_transplant"],
    [/\b(side effects?|toxicit(y|ies)|adverse events?)\b/i, "side_effects"],
    [/\b(supportive care|support|palliative)\b/i, "supportive_care"],
    [/\b(prognos(is|tic)|outlooks?|life expectancy)\b/i, "prognosis"],
    [/\b(survivals?|survival rates?|5-year)\b/i, "survival"],
    [/\b(recurrences?|relapses?|cancer coming back)\b/i, "recurrence"],
    [/\b(follow-ups?|surveillance|monitoring)\b/i, "follow_up"],
    [/\b(treat(ment|ments|ing)?|options?|therap(y|ies)|management)\b/i, "treatment"],
    [/\b(types?|subtypes?|classifications?|histolog(y|ies))\b/i, "types_and_subtypes"],
    [/\b(statistics?|incidence|mortalit(y|ies)|rates?|numbers?|how common)\b/i, "statistics"],
    [/\b(clinical trials?|research stud(y|ies)|investigational)\b/i, "clinical_trials"],
    [/\b(caregivers?|famil(y|ies)|supporting someone)\b/i, "caregiver_information"],
    [/\b(living with|quality of life|coping|wellness)\b/i, "living_with_cancer"],
    [/\b(childhood|pediatric|children)\b/i, "childhood_cancer"],
    [/\b(terms?|glossar(y|ies)|definitions?|meaning)\b/i, "terminology"],
    [/\b(overviews?|about|what is|introductions?|summary|summaries)\b/i, "overview"],
  ];

  for (const [pattern, canonical] of heuristics) {
    if (pattern.test(rawLower)) return canonical;
  }

  return "overview";
}

const serverStartTime = Date.now();

// Helper: resolve cancer by slug, id, canonical_name, or alias
function resolveCancer(cancerQuery: string) {
  const db = loadDatabase();
  const qLower = cancerQuery.trim().toLowerCase();

  // 1. Direct match on slug
  let found = db.cancers.find((c: any) => c.slug.toLowerCase() === qLower);
  if (found) return found;

  // 2. Direct match on ID
  found = db.cancers.find((c: any) => c.id === cancerQuery);
  if (found) return found;

  // 3. Match on canonical name
  found = db.cancers.find((c: any) => c.canonical_name.toLowerCase() === qLower);
  if (found) return found;

  // 4. Match on alias
  const aliasMatch = db.cancer_aliases.find(
    (a: any) => a.alias.toLowerCase() === qLower
  );
  if (aliasMatch) {
    found = db.cancers.find((c: any) => c.id === aliasMatch.cancer_id);
    if (found) return found;
  }

  // 5. Partial match on alias or name
  const partialAlias = db.cancer_aliases.find(
    (a: any) => a.alias.toLowerCase().includes(qLower) || qLower.includes(a.alias.toLowerCase())
  );
  if (partialAlias) {
    found = db.cancers.find((c: any) => c.id === partialAlias.cancer_id);
    if (found) return found;
  }

  return null;
}

// -------------------------------------------------------------
// ENDPOINTS
// -------------------------------------------------------------

// 1. GET /v1/health
apiRouter.get("/health", (req: Request, res: Response) => {
  const db = loadDatabase();
  const uptimeSeconds = Math.round((Date.now() - serverStartTime) / 10) / 100;
  res.json({
    status: "healthy",
    api_name: "CancerInfo API",
    api_version: "1.0.0",
    database: "connected",
    timestamp: new Date().toISOString(),
    uptime_seconds: uptimeSeconds,
    environment: process.env.NODE_ENV || "development",
    source_registry_count: db.sources.length,
    approved_cancers_count: db.cancers.length,
  });
});

// 2. GET /v1/cancers
apiRouter.get("/cancers", (req: Request, res: Response) => {
  const db = loadDatabase();
  const site = typeof req.query.site === "string" ? req.query.site.toLowerCase() : null;
  const page = Math.max(1, parseInt(req.query.page as string) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit as string) || 20));

  let filtered = db.cancers;
  if (site) {
    filtered = filtered.filter((c: any) => c.anatomical_site.toLowerCase().includes(site));
  }

  const total = filtered.length;
  const skip = (page - 1) * limit;
  const pageItems = filtered.slice(skip, skip + limit);

  const data = pageItems.map((c: any) => {
    const aliases = db.cancer_aliases
      .filter((a: any) => a.cancer_id === c.id)
      .map((a: any) => a.alias);
    return {
      id: c.id,
      slug: c.slug,
      canonical_name: c.canonical_name,
      anatomical_site: c.anatomical_site,
      aliases,
    };
  });

  const total_pages = Math.ceil(total / limit) || 1;

  res.json({
    data,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: data.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
    pagination: {
      page,
      limit,
      total_records: total,
      total_pages,
      has_next: page < total_pages,
      has_prev: page > 1,
    },
  });
});

// 3. GET /v1/cancers/:cancer
apiRouter.get("/cancers/:cancer", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = req.params.cancer;
  const cancer = resolveCancer(cancerParam);

  if (!cancer) {
    return res.status(404).json({
      error: {
        code: "CANCER_NOT_FOUND",
        message: `Cancer entity '${cancerParam}' was not found in the canonical cancer registry.`,
      },
    });
  }

  const aliases = db.cancer_aliases
    .filter((a: any) => a.cancer_id === cancer.id)
    .map((a: any) => ({
      alias: a.alias,
      language: a.language,
      alias_type: a.alias_type,
      country_code: a.country_code,
      confidence: a.confidence,
    }));

  const records = db.content_records.filter(
    (r: any) => r.canonical_cancer_id === cancer.id && r.active !== 0
  );

  const countsMap: Record<string, number> = {};
  for (const r of records) {
    countsMap[r.category] = (countsMap[r.category] || 0) + 1;
  }

  const availableCategories = Object.keys(countsMap);

  let taxonomyCodes = cancer.taxonomy_codes;
  if (typeof taxonomyCodes === "string") {
    try {
      taxonomyCodes = JSON.parse(taxonomyCodes);
    } catch {
      taxonomyCodes = {};
    }
  }

  res.json({
    data: {
      id: cancer.id,
      slug: cancer.slug,
      canonical_name: cancer.canonical_name,
      description: cancer.description,
      anatomical_site: cancer.anatomical_site,
      aliases,
      taxonomy_codes: taxonomyCodes || {},
      available_categories: availableCategories,
      record_counts_by_category: countsMap,
    },
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: 1,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 4. GET /v1/cancers/:cancer/sections
apiRouter.get("/cancers/:cancer/sections", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = req.params.cancer;
  const cancer = resolveCancer(cancerParam);

  if (!cancer) {
    return res.status(404).json({
      error: {
        code: "CANCER_NOT_FOUND",
        message: `Cancer entity '${cancerParam}' was not found.`,
      },
    });
  }

  const records = db.content_records.filter(
    (r: any) => r.canonical_cancer_id === cancer.id && r.active !== 0
  );

  const catMap: Record<string, { count: number; countries: Set<string> }> = {};
  for (const r of records) {
    if (!catMap[r.category]) {
      catMap[r.category] = { count: 0, countries: new Set() };
    }
    catMap[r.category].count++;
    if (r.country_code) catMap[r.category].countries.add(r.country_code);
  }

  const sectionsOut = Object.entries(catMap).map(([cat, info]) => {
    const meta = CANONICAL_CATEGORIES[cat] || { name: cat, description: "" };
    return {
      category: cat,
      name: meta.name,
      description: meta.description,
      record_count: info.count,
      countries_represented: Array.from(info.countries),
    };
  });

  res.json({
    data: sectionsOut,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: sectionsOut.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 5. GET /v1/cancers/:cancer/sources
apiRouter.get("/cancers/:cancer/sources", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = req.params.cancer;
  const cancer = resolveCancer(cancerParam);

  if (!cancer) {
    return res.status(404).json({
      error: {
        code: "CANCER_NOT_FOUND",
        message: `Cancer entity '${cancerParam}' was not found.`,
      },
    });
  }

  const records = db.content_records.filter(
    (r: any) => r.canonical_cancer_id === cancer.id && r.active !== 0
  );
  const recordIds = new Set(records.map((r: any) => r.id));

  const contentSources = db.content_sources.filter((cs: any) => recordIds.has(cs.content_record_id));
  const sourceIds = new Set(contentSources.map((cs: any) => cs.source_id));

  const sources = db.sources.filter((s: any) => sourceIds.has(s.id));

  res.json({
    data: sources,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: sources.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 6. GET /v1/cancers/:cancer/versions
apiRouter.get("/cancers/:cancer/versions", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = req.params.cancer;
  const cancer = resolveCancer(cancerParam);

  if (!cancer) {
    return res.status(404).json({
      error: {
        code: "CANCER_NOT_FOUND",
        message: `Cancer entity '${cancerParam}' was not found.`,
      },
    });
  }

  const records = db.content_records.filter((r: any) => r.canonical_cancer_id === cancer.id);
  const recordIds = new Set(records.map((r: any) => r.id));

  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit as string) || 50));
  const versions = db.content_versions
    .filter((v: any) => recordIds.has(v.content_record_id))
    .slice(0, limit)
    .map((v: any) => ({
      version_number: v.version_number,
      content: v.content,
      change_type: v.change_type,
      change_reason: v.change_reason,
      content_hash: v.content_hash,
      created_at: v.created_at,
    }));

  res.json({
    data: versions,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: versions.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 7. GET /v1/cancers/:cancer/:category
apiRouter.get("/cancers/:cancer/:category", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = req.params.cancer;
  const rawCat = req.params.category;

  const cancer = resolveCancer(cancerParam);
  if (!cancer) {
    return res.status(404).json({
      error: {
        code: "CANCER_NOT_FOUND",
        message: `Cancer entity '${cancerParam}' was not found.`,
      },
    });
  }

  const normCat = normalizeCategory(rawCat);
  if (!CANONICAL_CATEGORIES[normCat]) {
    return res.status(404).json({
      error: {
        code: "CATEGORY_NOT_FOUND",
        message: `Knowledge category '${rawCat}' is not a recognized canonical category.`,
      },
    });
  }

  const country = typeof req.query.country === "string" ? req.query.country.toUpperCase() : null;
  const audience = typeof req.query.audience === "string" ? req.query.audience.toLowerCase() : null;
  const sourceId = typeof req.query.source === "string" ? req.query.source.toLowerCase() : null;
  const page = Math.max(1, parseInt(req.query.page as string) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit as string) || 50));

  let records = db.content_records.filter(
    (r: any) => r.canonical_cancer_id === cancer.id && r.category === normCat && r.active !== 0
  );

  if (country) {
    records = records.filter(
      (r: any) => r.country_code === country || r.jurisdiction_scope === "GLOBAL"
    );
  }

  if (audience) {
    records = records.filter((r: any) => r.audience === audience);
  }

  if (sourceId) {
    records = records.filter((r: any) => {
      const rels = db.content_sources.filter((cs: any) => cs.content_record_id === r.id);
      return rels.some((cs: any) => cs.source_id === sourceId);
    });
  }

  const total = records.length;
  const skip = (page - 1) * limit;
  const pageRecords = records.slice(skip, skip + limit);

  // Hydrate with sources
  const recordsOut = pageRecords.map((r: any) => {
    const rels = db.content_sources.filter((cs: any) => cs.content_record_id === r.id);
    const sourcesOut = rels.map((cs: any) => {
      const src = db.sources.find((s: any) => s.id === cs.source_id) || {};
      return {
        source_id: src.id || cs.source_id,
        organization: src.organization_name || "",
        source_name: src.source_name || "",
        url: cs.source_url,
        trust_tier: src.trust_tier || "Tier 1 - Primary Authoritative",
        source_updated_at: cs.source_updated_at || null,
        retrieved_at: cs.retrieved_at,
        last_verified_at: cs.last_verified_at,
        license_status: src.license_status || "APPROVED",
        attribution_text: cs.attribution_text || src.attribution_text || "",
        quote_snippet: cs.quote_snippet || null,
      };
    });

    return {
      id: r.id,
      category: r.category,
      subcategory: r.subcategory || null,
      content: r.content,
      content_type: r.content_type || "SOURCE_CONTENT",
      jurisdiction: {
        scope: r.jurisdiction_scope,
        country: r.country_code,
        region: r.region_code || null,
      },
      language: r.language || "en",
      audience: r.audience || "general_public",
      disagreement_status: r.disagreement_status || "CONSISTENT",
      disagreement_notes: r.disagreement_notes || null,
      version_number: r.version_number || 1,
      updated_at: r.updated_at,
      sources: sourcesOut,
    };
  });

  const catMeta = CANONICAL_CATEGORIES[normCat];
  const aliases = db.cancer_aliases
    .filter((a: any) => a.cancer_id === cancer.id)
    .map((a: any) => a.alias);

  const total_pages = Math.ceil(total / limit) || 1;

  res.json({
    data: {
      cancer: {
        id: cancer.id,
        slug: cancer.slug,
        canonical_name: cancer.canonical_name,
        anatomical_site: cancer.anatomical_site,
        aliases,
      },
      category: normCat,
      category_name: catMeta.name,
      category_description: catMeta.description,
      records: recordsOut,
    },
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: recordsOut.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
    pagination: {
      page,
      limit,
      total_records: total,
      total_pages,
      has_next: page < total_pages,
      has_prev: page > 1,
    },
  });
});

// 8. GET /v1/search
apiRouter.get("/search", (req: Request, res: Response) => {
  const db = loadDatabase();
  const q = typeof req.query.q === "string" ? req.query.q.trim().toLowerCase() : "";
  if (!q) {
    return res.status(400).json({
      error: {
        code: "INVALID_QUERY",
        message: "Query parameter 'q' must not be empty.",
      },
    });
  }

  const catFilter = typeof req.query.category === "string" ? normalizeCategory(req.query.category) : null;
  const countryFilter = typeof req.query.country === "string" ? req.query.country.toUpperCase() : null;
  const limit = Math.min(50, Math.max(1, parseInt(req.query.limit as string) || 20));

  const results: any[] = [];
  const matchedCancerIds = new Set<string>();

  const tokens = q.split(/\s+/).filter(Boolean);

  // 1. Check exact or alias cancer matches
  for (const c of db.cancers) {
    const aliases = db.cancer_aliases.filter((a: any) => a.cancer_id === c.id);
    const aliasList = aliases.map((a: any) => a.alias);
    const nameMatch = c.canonical_name.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q);
    const tokenNameMatch = tokens.some((t) => t.length > 2 && (c.canonical_name.toLowerCase().includes(t) || c.slug.toLowerCase().includes(t)));
    const matchedAlias = aliases.find((a: any) => a.alias.toLowerCase().includes(q) || q.includes(a.alias.toLowerCase()) || tokens.some((t) => t.length > 2 && a.alias.toLowerCase().includes(t)));

    if (nameMatch || tokenNameMatch || matchedAlias) {
      matchedCancerIds.add(c.id);
      results.push({
        match_type: matchedAlias ? "alias_match" : "canonical_name",
        score: matchedAlias ? 0.95 : 1.0,
        cancer: {
          id: c.id,
          slug: c.slug,
          canonical_name: c.canonical_name,
          anatomical_site: c.anatomical_site,
          aliases: aliasList,
        },
        matched_terms: [matchedAlias ? matchedAlias.alias : c.canonical_name],
      });
    }
  }

  // 2. Check record content matches
  for (const r of db.content_records) {
    if (r.active === 0) continue;
    if (catFilter && r.category !== catFilter) continue;
    if (countryFilter && r.country_code !== countryFilter && r.jurisdiction_scope !== "GLOBAL") continue;

    const contentMatches = r.content.toLowerCase().includes(q);
    const categoryMatches = r.category.toLowerCase().includes(q) || (r.subcategory && r.subcategory.toLowerCase().includes(q));
    const tokenMatches = tokens.some((t) => t.length > 2 && (r.content.toLowerCase().includes(t) || r.category.toLowerCase().includes(t)));

    if (contentMatches || categoryMatches || tokenMatches) {
      const c = db.cancers.find((item: any) => item.id === r.canonical_cancer_id);
      if (!c) continue;

      const aliases = db.cancer_aliases.filter((a: any) => a.cancer_id === c.id).map((a: any) => a.alias);
      const rels = db.content_sources.filter((cs: any) => cs.content_record_id === r.id);
      const sourcesOut = rels.map((cs: any) => {
        const src = db.sources.find((s: any) => s.id === cs.source_id) || {};
        return {
          source_id: src.id || cs.source_id,
          organization: src.organization_name || "",
          source_name: src.source_name || "",
          url: cs.source_url,
          trust_tier: src.trust_tier || "Tier 1 - Primary Authoritative",
          source_updated_at: cs.source_updated_at || null,
          retrieved_at: cs.retrieved_at,
          last_verified_at: cs.last_verified_at,
          license_status: src.license_status || "APPROVED",
          attribution_text: cs.attribution_text || src.attribution_text || "",
          quote_snippet: cs.quote_snippet || null,
        };
      });

      const recordOut = {
        id: r.id,
        category: r.category,
        subcategory: r.subcategory,
        content: r.content,
        content_type: r.content_type,
        jurisdiction: {
          scope: r.jurisdiction_scope,
          country: r.country_code,
          region: r.region_code,
        },
        language: r.language,
        audience: r.audience,
        disagreement_status: r.disagreement_status,
        disagreement_notes: r.disagreement_notes,
        version_number: r.version_number,
        updated_at: r.updated_at,
        sources: sourcesOut,
      };

      // Create a readable snippet
      const idx = r.content.toLowerCase().indexOf(q);
      let snippet = "";
      if (idx !== -1) {
        const start = Math.max(0, idx - 40);
        const end = Math.min(r.content.length, idx + q.length + 80);
        snippet = (start > 0 ? "..." : "") + r.content.substring(start, end).trim() + (end < r.content.length ? "..." : "");
      } else {
        snippet = r.content.substring(0, 120) + "...";
      }

      results.push({
        match_type: "content_record",
        score: 0.85,
        cancer: {
          id: c.id,
          slug: c.slug,
          canonical_name: c.canonical_name,
          anatomical_site: c.anatomical_site,
          aliases,
        },
        category: r.category,
        snippet,
        record: recordOut,
        matched_terms: [q],
      });
    }
  }

  const finalResults = results.slice(0, limit);

  res.json({
    data: {
      query: q,
      filters_applied: {
        category: catFilter || undefined,
        country: countryFilter || undefined,
      },
      results: finalResults,
    },
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: finalResults.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 9. GET /v1/sources
apiRouter.get("/sources", (req: Request, res: Response) => {
  const db = loadDatabase();
  const country = typeof req.query.country === "string" ? req.query.country.toUpperCase() : null;
  const tier = typeof req.query.tier === "string" ? req.query.tier : null;
  const page = Math.max(1, parseInt(req.query.page as string) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit as string) || 20));

  let sources = db.sources.filter((s: any) => s.active !== 0);
  if (country) {
    sources = sources.filter((s: any) => s.country_code === country || s.country_code === "GLOBAL");
  }
  if (tier) {
    sources = sources.filter((s: any) => s.trust_tier.toLowerCase().includes(tier.toLowerCase()));
  }

  const total = sources.length;
  const skip = (page - 1) * limit;
  const pageItems = sources.slice(skip, skip + limit);
  const total_pages = Math.ceil(total / limit) || 1;

  res.json({
    data: pageItems,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: pageItems.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
    pagination: {
      page,
      limit,
      total_records: total,
      total_pages,
      has_next: page < total_pages,
      has_prev: page > 1,
    },
  });
});

// 10. GET /v1/sources/:id
apiRouter.get("/sources/:id", (req: Request, res: Response) => {
  const db = loadDatabase();
  const id = req.params.id;
  const source = db.sources.find((s: any) => s.id === id);

  if (!source) {
    return res.status(404).json({
      error: {
        code: "SOURCE_NOT_FOUND",
        message: `Authoritative source '${id}' was not found.`,
      },
    });
  }

  const docCount = db.source_documents.filter((d: any) => d.source_id === id).length;
  const recCount = db.content_sources.filter((cs: any) => cs.source_id === id).length;
  const health = db.source_health.find((h: any) => h.source_id === id);

  let supportedLangs = source.supported_languages;
  if (typeof supportedLangs === "string") {
    try {
      supportedLangs = JSON.parse(supportedLangs);
    } catch {
      supportedLangs = ["en"];
    }
  }

  res.json({
    data: {
      ...source,
      supported_languages: supportedLangs || ["en"],
      document_count: docCount,
      records_supported_count: recCount,
      health_status: health && health.is_reachable ? "healthy" : "degraded",
    },
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: 1,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 11. GET /v1/categories
apiRouter.get("/categories", (req: Request, res: Response) => {
  const aliasMap: Record<string, string[]> = {};
  for (const [alias, cat] of Object.entries(CATEGORY_ALIASES)) {
    if (!aliasMap[cat]) aliasMap[cat] = [];
    aliasMap[cat].push(alias);
  }

  const data = Object.entries(CANONICAL_CATEGORIES).map(([slug, info]) => ({
    category: slug,
    name: info.name,
    description: info.description,
    recognized_aliases: aliasMap[slug] || [],
  }));

  res.json({
    data,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: data.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 12. GET /v1/countries
apiRouter.get("/countries", (req: Request, res: Response) => {
  const db = loadDatabase();
  const activeCountries = new Set(db.content_records.map((r: any) => r.country_code));

  const data = Object.entries(COUNTRIES).map(([code, info]) => ({
    code,
    name: info.name,
    region: info.region,
    default_language: info.default_language,
    has_active_records: activeCountries.has(code),
  }));

  res.json({
    data,
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: data.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});

// 13. GET /v1/coverage
apiRouter.get("/coverage", (req: Request, res: Response) => {
  const db = loadDatabase();
  const cancerParam = typeof req.query.cancer === "string" ? req.query.cancer : null;

  let cancers = db.cancers;
  if (cancerParam) {
    const resolved = resolveCancer(cancerParam);
    if (resolved) {
      cancers = [resolved];
    } else {
      cancers = [];
    }
  }

  const cancerItems = cancers.map((c: any) => {
    const recs = db.content_records.filter((r: any) => r.canonical_cancer_id === c.id && r.active !== 0);
    const catSet = new Set<string>();
    const countrySet = new Set<string>();
    const srcSet = new Set<string>();
    let latestVerification = "2026-09-12T06:23:36Z";

    for (const r of recs) {
      catSet.add(r.category);
      if (r.country_code) countrySet.add(r.country_code);
      const rels = db.content_sources.filter((cs: any) => cs.content_record_id === r.id);
      for (const cs of rels) {
        srcSet.add(cs.source_id);
        if (cs.last_verified_at && cs.last_verified_at > latestVerification) {
          latestVerification = cs.last_verified_at;
        }
      }
    }

    return {
      slug: c.slug,
      canonical_name: c.canonical_name,
      total_records: recs.length,
      categories_covered: Array.from(catSet),
      countries: Array.from(countrySet),
      supporting_sources: Array.from(srcSet),
      last_verified_at: latestVerification,
    };
  });

  const tierMap: Record<string, number> = {};
  for (const s of db.sources) {
    tierMap[s.trust_tier] = (tierMap[s.trust_tier] || 0) + 1;
  }

  res.json({
    data: {
      total_cancers: db.cancers.length,
      total_sources: db.sources.length,
      total_content_records: db.content_records.length,
      total_source_documents: db.source_documents.length,
      countries_represented: Object.keys(COUNTRIES),
      categories_available: Object.keys(CANONICAL_CATEGORIES).length,
      sources_by_trust_tier: tierMap,
      cancers: cancerItems,
    },
    meta: {
      api_version: "1.0.0",
      timestamp: new Date().toISOString(),
      result_count: cancerItems.length,
      disclaimer: MEDICAL_DISCLAIMER,
    },
  });
});
