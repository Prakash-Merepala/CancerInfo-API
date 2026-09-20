"""
HTML and Text Cleaning and Normalization
"""
import re
from bs4 import BeautifulSoup


def clean_html_text(html_content: str) -> str:
    """
    Extracts text from HTML while removing script, style, and navigation noise.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove irrelevant tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse consecutive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_bullet_points(raw_items: list[str]) -> list[str]:
    """
    Cleans and normalizes list of bullet points.
    """
    cleaned = []
    for item in raw_items:
        c = re.sub(r"^[•\-\*\d\.\)]+\s*", "", item.strip())
        c = re.sub(r"\s+", " ", c).strip()
        if len(c) > 5 and c not in cleaned:
            cleaned.append(c)
    return cleaned
