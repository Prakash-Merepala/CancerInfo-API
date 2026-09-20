"""
Taxonomy, Normalization, and Adapter Tests
"""
from app.normalization.cleaner import clean_html_text
from app.normalization.hash import compute_content_hash
from app.normalization.taxonomy import normalize_category
from app.sources.adapters.nci import NCIAdapter
from app.sources.adapters.who import WHOAdapter


def test_taxonomy_normalization():
    assert normalize_category("Symptoms of Breast Cancer") == "symptoms"
    assert normalize_category("Early Detection and Warning Signs") == "early_detection"
    assert normalize_category("Screening Guidelines") == "screening"
    assert normalize_category("Surgical Treatment Options") == "surgery"
    assert normalize_category("Chemotherapy and Targeted Therapies") == "chemotherapy"
    assert normalize_category("Understanding TNM Staging") == "staging"
    assert normalize_category("General Overview") == "overview"


def test_hash_stability():
    h1 = compute_content_hash("Breast cancer symptoms include a lump.")
    h2 = compute_content_hash("  breast   CANCER symptoms include a lump.  ")
    assert h1 == h2


def test_clean_html():
    raw_html = "<div><h2>Title</h2><p>Paragraph with <script>alert(1)</script>text.</p></div>"
    cleaned = clean_html_text(raw_html)
    assert "alert" not in cleaned
    assert "Paragraph with text." in cleaned


def test_nci_adapter_parsing():
    adapter = NCIAdapter()
    sample_html = """
    <html>
      <body>
        <h1>Breast Cancer</h1>
        <h2>Symptoms</h2>
        <p>A painless lump in the breast is the most common symptom.</p>
        <h2>Screening</h2>
        <p>Mammograms are recommended starting at age 40.</p>
      </body>
    </html>
    """
    doc = adapter.parse_document(
        html_content=sample_html,
        url="https://www.cancer.gov/types/breast",
        cancer_slug="breast-cancer",
        source_cancer_name="Breast Cancer",
    )
    assert doc.cancer_slug == "breast-cancer"
    assert len(doc.sections) == 2
    categories = [s.category for s in doc.sections]
    assert "symptoms" in categories
    assert "screening" in categories


def test_who_adapter_parsing():
    adapter = WHOAdapter()
    sample_html = """
    <article>
      <h1>Cervical Cancer</h1>
      <h2>Causes and Risk Factors</h2>
      <p>Nearly all cervical cancer cases are linked to infection with high-risk HPV.</p>
      <h2>Prevention</h2>
      <p>HPV vaccination is highly effective.</p>
    </article>
    """
    doc = adapter.parse_document(
        html_content=sample_html,
        url="https://www.who.int/news-room/fact-sheets/detail/cervical-cancer",
        cancer_slug="cervical-cancer",
        source_cancer_name="Cervical Cancer",
    )
    assert doc.cancer_slug == "cervical-cancer"
    assert doc.country_code == "GLOBAL"
    assert len(doc.sections) == 2
    categories = [s.category for s in doc.sections]
    assert "risk_factors" in categories
    assert "prevention" in categories
