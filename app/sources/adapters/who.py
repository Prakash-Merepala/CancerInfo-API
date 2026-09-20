"""
World Health Organization (WHO) Source Adapter
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from app.core.constants import TrustTier
from app.normalization.cleaner import clean_html_text
from app.normalization.hash import compute_content_hash
from app.normalization.taxonomy import normalize_category
from app.sources.base import BaseSourceAdapter, NormalizedDocument, NormalizedSection


class WHOAdapter(BaseSourceAdapter):
    source_id = "who-global"
    organization_name = "World Health Organization"
    source_name = "WHO Global Cancer Fact Sheets"
    base_url = "https://www.who.int"
    country_code = "GLOBAL"
    region = "Global"
    trust_tier = TrustTier.TIER_1.value
    authority_type = "United Nations Specialized International Public Health Agency"
    license_type = "WHO Open Access (CC BY-NC-SA 3.0 IGO)"
    license_status = "APPROVED"
    attribution_text = "Source: World Health Organization (WHO). Licensed under CC BY-NC-SA 3.0 IGO."

    async def discover_urls(self) -> List[Dict[str, str]]:
        return [
            {
                "url": "https://www.who.int/news-room/fact-sheets/detail/breast-cancer",
                "cancer_slug": "breast-cancer",
                "source_cancer_name": "Breast Cancer",
            },
            {
                "url": "https://www.who.int/news-room/fact-sheets/detail/lung-cancer",
                "cancer_slug": "lung-cancer",
                "source_cancer_name": "Lung Cancer",
            },
            {
                "url": "https://www.who.int/news-room/fact-sheets/detail/colorectal-cancer",
                "cancer_slug": "colorectal-cancer",
                "source_cancer_name": "Colorectal Cancer",
            },
            {
                "url": "https://www.who.int/news-room/fact-sheets/detail/cervical-cancer",
                "cancer_slug": "cervical-cancer",
                "source_cancer_name": "Cervical Cancer",
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
        doc_title = title.get_text(strip=True) if title else f"{source_cancer_name} - WHO"

        content_hash = compute_content_hash(html_content)
        sections: List[NormalizedSection] = []

        main_content = soup.find("article") or soup.find("div", class_="sf-detail-body-wrapper") or soup.body or soup

        headings = main_content.find_all(["h2", "h3", "h4"])
        if headings:
            for h in headings:
                heading_text = h.get_text(strip=True)
                canonical_cat = normalize_category(heading_text)

                content_parts = []
                sibling = h.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3", "h4"]:
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
                            audience="general_public",
                            disagreement_status="CONSISTENT",
                            quote_snippet=section_body[:300] if len(section_body) > 300 else section_body,
                            source_url=url,
                        )
                    )

        if not sections:
            body_text = clean_html_text(str(main_content))
            sections.append(
                NormalizedSection(
                    category="overview",
                    content=body_text[:1500],
                    content_type="STRUCTURED_EXTRACTION",
                    audience="general_public",
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
            country_code="GLOBAL",
            jurisdiction_scope="GLOBAL",
            content_hash=content_hash,
            sections=sections,
            source_updated_at=updated_at,
            published_at=updated_at,
        )
