"""
National Cancer Institute (NCI) Source Adapter
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from app.core.constants import TrustTier
from app.normalization.cleaner import clean_html_text
from app.normalization.hash import compute_content_hash
from app.normalization.taxonomy import normalize_category
from app.sources.base import BaseSourceAdapter, NormalizedDocument, NormalizedSection


class NCIAdapter(BaseSourceAdapter):
    source_id = "nci-us"
    organization_name = "National Cancer Institute"
    source_name = "NCI Cancer Information Database"
    base_url = "https://www.cancer.gov"
    country_code = "US"
    region = "Americas"
    trust_tier = TrustTier.TIER_1.value
    authority_type = "Federal National Cancer Research & Clinical Institute"
    license_type = "Public Domain (U.S. Government Work, 17 U.S.C. § 105)"
    license_status = "APPROVED"
    attribution_text = "Source: National Cancer Institute (NCI), U.S. National Institutes of Health."

    async def discover_urls(self) -> List[Dict[str, str]]:
        return [
            {
                "url": "https://www.cancer.gov/types/breast",
                "cancer_slug": "breast-cancer",
                "source_cancer_name": "Breast Cancer",
            },
            {
                "url": "https://www.cancer.gov/types/lung",
                "cancer_slug": "lung-cancer",
                "source_cancer_name": "Lung Cancer",
            },
            {
                "url": "https://www.cancer.gov/types/colorectal",
                "cancer_slug": "colorectal-cancer",
                "source_cancer_name": "Colorectal Cancer",
            },
            {
                "url": "https://www.cancer.gov/types/prostate",
                "cancer_slug": "prostate-cancer",
                "source_cancer_name": "Prostate Cancer",
            },
            {
                "url": "https://www.cancer.gov/types/pancreatic",
                "cancer_slug": "pancreatic-cancer",
                "source_cancer_name": "Pancreatic Cancer",
            },
        ]

    def parse_document(
        self,
        html_content: str,
        url: str,
        cancer_slug: str,
        source_cancer_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NormalizedDocument:
        soup = BeautifulSoup(html_content, "html.parser")
        meta = metadata or {}

        title = soup.find("h1")
        doc_title = title.get_text(strip=True) if title else f"{source_cancer_name} - NCI"

        content_hash = compute_content_hash(html_content)
        sections: List[NormalizedSection] = []

        # Find major content containers
        main_content = soup.find("article") or soup.find("main") or soup.body or soup

        # Parse by heading elements (h2, h3)
        headings = main_content.find_all(["h2", "h3"])
        if headings:
            for h in headings:
                heading_text = h.get_text(strip=True)
                canonical_cat = normalize_category(heading_text)

                # Collect sibling content until the next heading
                content_parts = []
                sibling = h.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3"]:
                    if sibling.name in ["p", "ul", "ol", "div"]:
                        text = clean_html_text(str(sibling))
                        if text:
                            content_parts.append(text)
                    sibling = sibling.find_next_sibling()

                if content_parts:
                    section_body = "\n\n".join(content_parts)
                    sections.append(
                        NormalizedSection(
                            category=canonical_cat,
                            subcategory=heading_text,
                            content=section_body,
                            content_type="STRUCTURED_EXTRACTION",
                            audience="patient",
                            disagreement_status="CONSISTENT",
                            quote_snippet=section_body[:300] if len(section_body) > 300 else section_body,
                            source_url=url,
                        )
                    )

        # Fallback if no headings were structured
        if not sections:
            body_text = clean_html_text(str(main_content))
            sections.append(
                NormalizedSection(
                    category="overview",
                    content=body_text[:1500],
                    content_type="STRUCTURED_EXTRACTION",
                    audience="patient",
                    source_url=url,
                )
            )

        updated_at = meta.get("updated_at") or datetime.utcnow()

        return NormalizedDocument(
            source_id=self.source_id,
            original_url=url,
            canonical_url=url,
            title=doc_title,
            cancer_slug=cancer_slug,
            source_cancer_name=source_cancer_name,
            language="en",
            country_code=self.country_code,
            jurisdiction_scope="COUNTRY",
            content_hash=content_hash,
            sections=sections,
            source_updated_at=updated_at,
            published_at=updated_at,
        )
