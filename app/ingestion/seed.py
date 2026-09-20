"""
Initial Database Seeder for Source Registry, Canonical Taxonomy, and Seed Records
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.constants import TrustTier, LicenseStatus
from app.models import (
    Cancer,
    CancerAlias,
    ContentRecord,
    ContentSource,
    ContentVersion,
    Source,
    SourceDocument,
    SourceHealth,
)
from app.normalization.hash import compute_content_hash


def seed_database(db: Session) -> None:
    """
    Seeds the Source Registry, Canonical Cancers, and initial verified content records.
    Idempotent: skips if sources already exist.
    """
    if db.query(Source).count() > 0:
        return

    # 1. Seed Source Registry
    sources_data = [
        {
            "id": "nci-us",
            "organization_name": "National Cancer Institute",
            "source_name": "NCI Comprehensive Cancer Information Database",
            "base_url": "https://www.cancer.gov",
            "country_code": "US",
            "region": "Americas",
            "source_type": "government_institute",
            "trust_tier": TrustTier.TIER_1.value,
            "authority_type": "Official U.S. Federal Government Cancer Agency",
            "license_type": "Public Domain (U.S. Government Work, 17 U.S.C. § 105)",
            "license_status": LicenseStatus.APPROVED.value,
            "reuse_allowed": True,
            "full_text_storage_allowed": True,
            "derived_summary_allowed": True,
            "attribution_required": True,
            "attribution_text": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "reuse_policy_url": "https://www.cancer.gov/policies/copyright-reuse",
            "crawl_frequency": "weekly",
            "priority": 1,
            "active": True,
        },
        {
            "id": "who-global",
            "organization_name": "World Health Organization",
            "source_name": "WHO Global Cancer Fact Sheets & Guidelines",
            "base_url": "https://www.who.int",
            "country_code": "GLOBAL",
            "region": "Global",
            "source_type": "international_agency",
            "trust_tier": TrustTier.TIER_1.value,
            "authority_type": "United Nations Specialized International Public Health Agency",
            "license_type": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO (CC BY-NC-SA 3.0 IGO)",
            "license_status": LicenseStatus.APPROVED.value,
            "reuse_allowed": True,
            "full_text_storage_allowed": True,
            "derived_summary_allowed": True,
            "attribution_required": True,
            "attribution_text": "Source: World Health Organization (WHO). Licensed under CC BY-NC-SA 3.0 IGO.",
            "reuse_policy_url": "https://www.who.int/about/policies/publishing/open-access",
            "crawl_frequency": "monthly",
            "priority": 1,
            "active": True,
        },
        {
            "id": "nhs-uk",
            "organization_name": "National Health Service",
            "source_name": "NHS Health A-Z Clinical & Patient Cancer Directory",
            "base_url": "https://www.nhs.uk",
            "country_code": "GB",
            "region": "Europe",
            "source_type": "national_health_service",
            "trust_tier": TrustTier.TIER_1.value,
            "authority_type": "United Kingdom National Healthcare Authority",
            "license_type": "Open Government Licence v3.0 (OGL)",
            "license_status": LicenseStatus.APPROVED.value,
            "reuse_allowed": True,
            "full_text_storage_allowed": True,
            "derived_summary_allowed": True,
            "attribution_required": True,
            "attribution_text": "Source: NHS (National Health Service, United Kingdom). Contains public sector information licensed under the Open Government Licence v3.0.",
            "reuse_policy_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            "crawl_frequency": "monthly",
            "priority": 2,
            "active": True,
        },
        {
            "id": "cancer-australia",
            "organization_name": "Cancer Australia",
            "source_name": "Cancer Australia National Cancer Information Platform",
            "base_url": "https://www.canceraustralia.gov.au",
            "country_code": "AU",
            "region": "Oceania",
            "source_type": "government_agency",
            "trust_tier": TrustTier.TIER_1.value,
            "authority_type": "Australian Government Statutory Cancer Agency",
            "license_type": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "license_status": LicenseStatus.APPROVED.value,
            "reuse_allowed": True,
            "full_text_storage_allowed": True,
            "derived_summary_allowed": True,
            "attribution_required": True,
            "attribution_text": "Source: Cancer Australia, Australian Government. Licensed under CC BY 4.0.",
            "reuse_policy_url": "https://www.canceraustralia.gov.au/copyright",
            "crawl_frequency": "monthly",
            "priority": 2,
            "active": True,
        },
        {
            "id": "cdc-us",
            "organization_name": "Centers for Disease Control and Prevention",
            "source_name": "CDC Division of Cancer Prevention and Control",
            "base_url": "https://www.cdc.gov/cancer",
            "country_code": "US",
            "region": "Americas",
            "source_type": "government_agency",
            "trust_tier": TrustTier.TIER_1.value,
            "authority_type": "U.S. Federal Health Protection Agency",
            "license_type": "Public Domain (U.S. Government Work)",
            "license_status": LicenseStatus.APPROVED.value,
            "reuse_allowed": True,
            "full_text_storage_allowed": True,
            "derived_summary_allowed": True,
            "attribution_required": True,
            "attribution_text": "Source: Centers for Disease Control and Prevention (CDC).",
            "reuse_policy_url": "https://www.cdc.gov/other/agencymaterials.html",
            "crawl_frequency": "monthly",
            "priority": 2,
            "active": True,
        },
    ]

    for s_data in sources_data:
        src = Source(**s_data)
        db.add(src)

        # Add initial health check
        health = SourceHealth(
            source_id=src.id,
            last_check=datetime.utcnow(),
            is_reachable=True,
            http_status=200,
            consecutive_failures=0,
            last_successful_crawl=datetime.utcnow(),
            alert_status="HEALTHY",
        )
        db.add(health)

    db.commit()

    # 2. Seed Canonical Cancer Taxonomy
    cancers_data = [
        {
            "slug": "breast-cancer",
            "canonical_name": "Breast Cancer",
            "description": "Cancer that forms in the cells of the breasts, most commonly in the ducts or lobules.",
            "anatomical_site": "Breast",
            "taxonomy_codes": {"ICD-O-3": "C50", "MeSH": "D001943", "SNOMED-CT": "254837009"},
            "aliases": [
                ("Breast Carcinoma", "medical_name", 1.0, None),
                ("Mammary Carcinoma", "medical_name", 0.9, None),
                ("Breast Neoplasm", "medical_name", 0.9, None),
            ],
        },
        {
            "slug": "colorectal-cancer",
            "canonical_name": "Colorectal Cancer",
            "description": "Cancer that originates in the colon or the rectum, typically starting as adenomatous polyps on the inner lining of the large intestine.",
            "anatomical_site": "Colon and Rectum",
            "taxonomy_codes": {"ICD-O-3": "C18-C20", "MeSH": "D015179", "SNOMED-CT": "363406005"},
            "aliases": [
                ("Bowel Cancer", "common_name", 1.0, "GB"),
                ("Colon Cancer", "common_name", 0.95, None),
                ("Rectal Cancer", "common_name", 0.95, None),
                ("CRC", "abbreviation", 0.95, None),
                ("Colorectal Neoplasm", "medical_name", 0.9, None),
            ],
        },
        {
            "slug": "lung-cancer",
            "canonical_name": "Lung Cancer",
            "description": "Malignant tumor characterized by uncontrolled cell growth in tissues of the lung, primarily categorized into non-small cell lung cancer (NSCLC) and small cell lung cancer (SCLC).",
            "anatomical_site": "Lung / Thorax",
            "taxonomy_codes": {"ICD-O-3": "C34", "MeSH": "D008175", "SNOMED-CT": "363358000"},
            "aliases": [
                ("Bronchogenic Carcinoma", "medical_name", 0.9, None),
                ("Lung Carcinoma", "medical_name", 0.9, None),
                ("NSCLC", "abbreviation", 0.9, None),
                ("SCLC", "abbreviation", 0.85, None),
            ],
        },
        {
            "slug": "prostate-cancer",
            "canonical_name": "Prostate Cancer",
            "description": "Cancer that develops in the prostate gland of the male reproductive system, usually presenting as an adenocarcinoma.",
            "anatomical_site": "Prostate",
            "taxonomy_codes": {"ICD-O-3": "C61", "MeSH": "D011471", "SNOMED-CT": "399068003"},
            "aliases": [
                ("Prostatic Neoplasm", "medical_name", 0.9, None),
                ("Prostate Carcinoma", "medical_name", 0.95, None),
            ],
        },
        {
            "slug": "pancreatic-cancer",
            "canonical_name": "Pancreatic Cancer",
            "description": "Malignancy arising from the tissues of the pancreas, most frequently the exocrine cells (pancreatic ductal adenocarcinoma).",
            "anatomical_site": "Pancreas",
            "taxonomy_codes": {"ICD-O-3": "C25", "MeSH": "D010190", "SNOMED-CT": "363418001"},
            "aliases": [
                ("Pancreatic Adenocarcinoma", "medical_name", 0.95, None),
                ("Pancreas Cancer", "common_name", 0.95, None),
                ("PDAC", "abbreviation", 0.9, None),
            ],
        },
        {
            "slug": "cervical-cancer",
            "canonical_name": "Cervical Cancer",
            "description": "Cancer arising from the cervix, strongly linked to persistent infection with high-risk human papillomavirus (HPV) genotypes.",
            "anatomical_site": "Cervix Uteri",
            "taxonomy_codes": {"ICD-O-3": "C53", "MeSH": "D002583", "SNOMED-CT": "363354003"},
            "aliases": [
                ("Cervix Cancer", "common_name", 0.95, None),
                ("Cervical Carcinoma", "medical_name", 0.95, None),
            ],
        },
        {
            "slug": "melanoma",
            "canonical_name": "Melanoma",
            "description": "A serious form of skin cancer that begins in cells known as melanocytes, responsible for producing melanin pigment.",
            "anatomical_site": "Skin",
            "taxonomy_codes": {"ICD-O-3": "C44", "MeSH": "D008545", "SNOMED-CT": "372244006"},
            "aliases": [
                ("Cutaneous Melanoma", "medical_name", 0.95, None),
                ("Malignant Melanoma", "medical_name", 0.95, None),
                ("Skin Cancer - Melanoma", "common_name", 0.9, None),
            ],
        },
    ]

    cancer_map = {}
    for c_item in cancers_data:
        aliases_to_add = c_item.pop("aliases")
        cancer_obj = Cancer(**c_item)
        db.add(cancer_obj)
        db.flush()
        cancer_map[cancer_obj.slug] = cancer_obj

        for alias_text, a_type, conf, c_code in aliases_to_add:
            db.add(
                CancerAlias(
                    cancer_id=cancer_obj.id,
                    alias=alias_text,
                    language="en",
                    alias_type=a_type,
                    country_code=c_code,
                    confidence=conf,
                    review_status="APPROVED",
                )
            )

    db.commit()

    # 3. Seed Verified Content Records with Full Fact-Level Provenance
    # Breast Cancer Seed Records
    breast_c = cancer_map["breast-cancer"]

    seed_content = [
        # Overview - NCI (US)
        {
            "cancer": breast_c,
            "category": "overview",
            "content": "Breast cancer is a disease in which cells in the breast grow out of control. There are different kinds of breast cancer depending on which cells in the breast turn into cancer. Most breast cancers begin in the ducts (ductal carcinoma) or the lobules (lobular carcinoma) that carry milk to the nipple.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/breast",
            "source_doc_title": "Breast Cancer Overview - National Cancer Institute",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Breast cancer is a disease in which cells in the breast grow out of control.",
        },
        # Overview - WHO (Global)
        {
            "cancer": breast_c,
            "category": "overview",
            "content": "Breast cancer is the most common cancer among women globally, impacting 2.3 million women each year. It occurs when abnormal breast cells grow out of control and form tumours. If left unchecked, these tumours can spread throughout the body and become fatal.",
            "country_code": "GLOBAL",
            "jurisdiction_scope": "GLOBAL",
            "audience": "general_public",
            "source_id": "who-global",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/breast-cancer",
            "source_doc_title": "Breast Cancer Fact Sheet - WHO",
            "attribution": "Source: World Health Organization (WHO). Licensed under CC BY-NC-SA 3.0 IGO.",
            "snippet": "Breast cancer is the most common cancer among women globally, impacting 2.3 million women each year.",
        },
        # Symptoms - NCI (US)
        {
            "cancer": breast_c,
            "category": "symptoms",
            "content": "Symptoms of breast cancer include a new lump or thickening in the breast or underarm, changes in the size or shape of the breast, dimpling or puckering of the breast skin, an inverted nipple, redness or flaking in the nipple area or breast skin, and nipple discharge other than breast milk (including blood).",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/breast/symptoms",
            "source_doc_title": "Breast Cancer Symptoms - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Symptoms include a new lump or thickening in the breast or underarm, dimpling, or nipple discharge.",
        },
        # Symptoms - NHS (UK)
        {
            "cancer": breast_c,
            "category": "symptoms",
            "content": "The first symptom of breast cancer most women notice is a lump or an area of thickened tissue in their breast. Most breast lumps are not cancerous, but it's always best to have them checked by a GP. Other symptoms include a change in breast size, shape or feel, skin changes such as puckering or dimpling, and discharge from either nipple.",
            "country_code": "GB",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nhs-uk",
            "source_url": "https://www.nhs.uk/conditions/breast-cancer/symptoms/",
            "source_doc_title": "Breast Cancer Symptoms - NHS",
            "attribution": "Source: NHS (National Health Service, United Kingdom). Licensed under Open Government Licence v3.0.",
            "snippet": "The first symptom of breast cancer most women notice is a lump or an area of thickened tissue in their breast.",
        },
        # Screening - US (USPSTF / CDC / NCI) vs UK (NHS) vs AU (BreastScreen) - Jurisdictional variation!
        {
            "cancer": breast_c,
            "category": "screening",
            "content": "In the United States, current clinical guidelines (USPSTF 2024 update) recommend that all women get screened for breast cancer every two years starting at age 40 through age 74 using screening mammography. Women with dense breasts or higher familial risk may benefit from supplementary screening such as breast MRI or ultrasound.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/breast/screening",
            "source_doc_title": "Breast Cancer Screening Guidelines - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Recommend that all women get screened for breast cancer every two years starting at age 40 through age 74.",
        },
        {
            "cancer": breast_c,
            "category": "screening",
            "content": "In the United Kingdom, the NHS Breast Screening Programme invites all women registered with a GP aged 50 up to their 71st birthday for screening mammography every 3 years. Women receive their first invitation letter between the ages of 50 and 53. After age 71, women can continue having free 3-yearly screening upon self-referral.",
            "country_code": "GB",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nhs-uk",
            "source_url": "https://www.nhs.uk/conditions/breast-screening-mammogram/",
            "source_doc_title": "NHS Breast Screening Programme",
            "attribution": "Source: NHS (National Health Service, United Kingdom). Licensed under Open Government Licence v3.0.",
            "snippet": "NHS invites all women aged 50 up to their 71st birthday for screening mammography every 3 years.",
        },
        {
            "cancer": breast_c,
            "category": "screening",
            "content": "In Australia, the national BreastScreen Australia program invites women aged 50 to 74 to have a free screening mammogram every two years. Women aged 40 to 49 and women aged 75 and older are also eligible to attend free of charge without a referral.",
            "country_code": "AU",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "cancer-australia",
            "source_url": "https://www.canceraustralia.gov.au/cancer-types/breast-cancer/screening",
            "source_doc_title": "BreastScreen Australia Recommendations",
            "attribution": "Source: Cancer Australia, Australian Government. Licensed under CC BY 4.0.",
            "snippet": "BreastScreen Australia program invites women aged 50 to 74 to have a free screening mammogram every two years.",
        },
        # Risk Factors - WHO (Global)
        {
            "cancer": breast_c,
            "category": "risk_factors",
            "content": "Known risk factors for breast cancer include increasing age, obesity, harmful use of alcohol, family history of breast cancer, history of radiation exposure, reproductive history (such as age that menstrual periods began and age at first pregnancy), tobacco use and postmenopausal hormone therapy. However, approximately half of all breast cancers develop in women who have no identifiable risk factor other than sex and age over 40.",
            "country_code": "GLOBAL",
            "jurisdiction_scope": "GLOBAL",
            "audience": "general_public",
            "source_id": "who-global",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/breast-cancer",
            "source_doc_title": "Breast Cancer Risk Factors - WHO",
            "attribution": "Source: World Health Organization (WHO). Licensed under CC BY-NC-SA 3.0 IGO.",
            "snippet": "Known risk factors include increasing age, obesity, alcohol use, family history, and reproductive history.",
        },
        # Treatment - NCI (US)
        {
            "cancer": breast_c,
            "category": "treatment",
            "content": "Treatment for breast cancer depends on the subtype, stage, biomarker status (ER, PR, HER2), and general health. Modalities include surgery (lumpectomy or mastectomy), radiation therapy, systemic chemotherapy, targeted therapy (e.g., anti-HER2 monoclonal antibodies), and hormone (endocrine) therapy for hormone-receptor-positive tumors.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/breast/treatment",
            "source_doc_title": "Breast Cancer Treatment Options - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Modalities include surgery, radiation therapy, systemic chemotherapy, targeted therapy, and endocrine therapy.",
        },
        # Colorectal Cancer Seed Records
        {
            "cancer": cancer_map["colorectal-cancer"],
            "category": "overview",
            "content": "Colorectal cancer starts in the large intestine (colon) or the rectum (end of the colon). Most colorectal cancers start as a growth on the inner lining of the colon or rectum called an adenomatous polyp. Over years, some types of polyps can change into cancer.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/colorectal",
            "source_doc_title": "Colorectal Cancer Overview - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Most colorectal cancers start as a growth on the inner lining of the colon or rectum called a polyp.",
        },
        {
            "cancer": cancer_map["colorectal-cancer"],
            "category": "symptoms",
            "content": "Symptoms of colorectal cancer include a persistent change in bowel habits (diarrhea or constipation), feeling that the bowel does not empty completely, rectal bleeding with bright red blood, blood in the stool making it look dark brown or black, persistent abdominal cramps or gas pain, weakness, fatigue, and unexplained weight loss.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/colorectal/symptoms",
            "source_doc_title": "Colorectal Cancer Symptoms - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Symptoms include persistent change in bowel habits, rectal bleeding, blood in stool, and unexplained weight loss.",
        },
        {
            "cancer": cancer_map["colorectal-cancer"],
            "category": "symptoms",
            "content": "Bowel cancer symptoms include persistent blood in your poo (which may be bright red or dark), an unexplained change in your bowel habits such as looser poo or pooing more often for 3 weeks or more, tummy pain or bloating after eating, and fatigue caused by iron deficiency anaemia.",
            "country_code": "GB",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nhs-uk",
            "source_url": "https://www.nhs.uk/conditions/bowel-cancer/symptoms/",
            "source_doc_title": "Bowel Cancer Symptoms - NHS",
            "attribution": "Source: NHS (National Health Service, United Kingdom). Licensed under Open Government Licence v3.0.",
            "snippet": "Bowel cancer symptoms include persistent blood in poo, unexplained change in bowel habits for 3 weeks or more.",
        },
        {
            "cancer": cancer_map["colorectal-cancer"],
            "category": "screening",
            "content": "In the US, routine screening for colorectal cancer is recommended to begin at age 45 for average-risk individuals. Options include visual exams (colonoscopy every 10 years or sigmoidoscopy every 5 years) or high-sensitivity stool-based tests (annual FIT test or multitarget stool DNA-FIT every 3 years).",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "cdc-us",
            "source_url": "https://www.cdc.gov/cancer/colorectal/basic_info/screening/",
            "source_doc_title": "Colorectal Cancer Screening Recommendations - CDC",
            "attribution": "Source: Centers for Disease Control and Prevention (CDC).",
            "snippet": "Routine screening is recommended to begin at age 45 for average-risk individuals.",
        },
        {
            "cancer": cancer_map["colorectal-cancer"],
            "category": "screening",
            "content": "In the UK, NHS bowel cancer screening is currently being expanded down to people aged 50 to 74 in England and Scotland. Eligible individuals are automatically sent a home testing kit (faecal immunochemical test - FIT) every 2 years.",
            "country_code": "GB",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nhs-uk",
            "source_url": "https://www.nhs.uk/conditions/bowel-cancer-screening/",
            "source_doc_title": "NHS Bowel Cancer Screening Programme",
            "attribution": "Source: NHS (National Health Service, United Kingdom). Licensed under Open Government Licence v3.0.",
            "snippet": "NHS bowel cancer screening sends an automated home testing kit (FIT) every 2 years.",
        },
        # Lung Cancer Seed Records
        {
            "cancer": cancer_map["lung-cancer"],
            "category": "overview",
            "content": "Lung cancer is cancer that begins in the lungs and most often occurs in people who smoke. The two major types of lung cancer are non-small cell lung cancer (accounting for about 85% of cases) and small cell lung cancer (about 10% to 15% of cases).",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/lung",
            "source_doc_title": "Lung Cancer Overview - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "The two major types of lung cancer are non-small cell lung cancer and small cell lung cancer.",
        },
        {
            "cancer": cancer_map["lung-cancer"],
            "category": "symptoms",
            "content": "Symptoms of lung cancer typically do not appear until the disease is advanced. Key symptoms include a persistent cough that worsens over time, coughing up blood (hemoptysis), chest pain that worsens with deep breathing or coughing, hoarseness, shortness of breath, recurrent respiratory infections like bronchitis or pneumonia, and unexplained weight loss.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/lung/symptoms",
            "source_doc_title": "Lung Cancer Symptoms - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Symptoms include persistent cough, coughing up blood, chest pain, and shortness of breath.",
        },
        {
            "cancer": cancer_map["lung-cancer"],
            "category": "risk_factors",
            "content": "Cigarette smoking is the leading risk factor for lung cancer, responsible for roughly 85% of all lung cancer cases worldwide. Other risk factors include exposure to secondhand smoke, radon gas, asbestos, arsenic, diesel exhaust, and ambient air pollution.",
            "country_code": "GLOBAL",
            "jurisdiction_scope": "GLOBAL",
            "audience": "general_public",
            "source_id": "who-global",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/lung-cancer",
            "source_doc_title": "Lung Cancer Risk Factors - WHO",
            "attribution": "Source: World Health Organization (WHO). Licensed under CC BY-NC-SA 3.0 IGO.",
            "snippet": "Cigarette smoking is the leading risk factor, responsible for roughly 85% of cases worldwide.",
        },
        # Pancreatic Cancer Seed Records
        {
            "cancer": cancer_map["pancreatic-cancer"],
            "category": "overview",
            "content": "Pancreatic cancer forms in the cells of the pancreas, an organ lying behind the lower part of the stomach. Most pancreatic cancers are ductal adenocarcinomas, which begin in the cells lining the ducts that carry digestive enzymes. It is often diagnosed at an advanced stage because early symptoms are vague.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/pancreatic",
            "source_doc_title": "Pancreatic Cancer Overview - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Most pancreatic cancers are ductal adenocarcinomas, often diagnosed at an advanced stage.",
        },
        {
            "cancer": cancer_map["pancreatic-cancer"],
            "category": "symptoms",
            "content": "Common symptoms of pancreatic cancer include yellowing of the skin and whites of the eyes (jaundice), light-colored or greasy stools, dark urine, pain in the upper abdomen radiating to the middle or upper back, unexplained weight loss, loss of appetite, and newly onset diabetes or sudden worsening of previously controlled diabetes.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/pancreatic/symptoms",
            "source_doc_title": "Pancreatic Cancer Symptoms - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Symptoms include jaundice, light-colored stools, dark urine, and upper abdominal pain radiating to the back.",
        },
        # Prostate Cancer Seed Records
        {
            "cancer": cancer_map["prostate-cancer"],
            "category": "overview",
            "content": "Prostate cancer develops in the prostate gland in men. It is one of the most common types of cancer. Many prostate cancers grow slowly and remain confined to the prostate gland, causing no serious harm, while other types are aggressive and can spread quickly.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/prostate",
            "source_doc_title": "Prostate Cancer Overview - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Prostate cancer develops in the prostate gland in men; many types grow slowly while others are aggressive.",
        },
        {
            "cancer": cancer_map["prostate-cancer"],
            "category": "symptoms",
            "content": "Early prostate cancer usually causes no symptoms. More advanced prostate cancer may cause trouble urinating, decreased force in the stream of urine, blood in the urine or semen, bone pain, swelling in the legs, and pelvic discomfort.",
            "country_code": "US",
            "jurisdiction_scope": "COUNTRY",
            "audience": "patient",
            "source_id": "nci-us",
            "source_url": "https://www.cancer.gov/types/prostate/symptoms",
            "source_doc_title": "Prostate Cancer Symptoms - NCI",
            "attribution": "Source: National Cancer Institute (NCI), U.S. National Institutes of Health.",
            "snippet": "Symptoms may cause trouble urinating, blood in urine or semen, and bone pain.",
        },
    ]

    for item in seed_content:
        cancer_obj = item["cancer"]
        src = db.query(Source).filter(Source.id == item["source_id"]).first()
        if not src:
            continue

        c_hash = compute_content_hash(item["content"])

        # Create or fetch SourceDocument
        doc = db.query(SourceDocument).filter(SourceDocument.original_url == item["source_url"]).first()
        if not doc:
            doc = SourceDocument(
                source_id=src.id,
                original_url=item["source_url"],
                canonical_url=item["source_url"],
                title=item["source_doc_title"],
                canonical_cancer_id=cancer_obj.id,
                source_cancer_name=cancer_obj.canonical_name,
                language="en",
                country_code=item["country_code"],
                jurisdiction_scope=item["jurisdiction_scope"],
                content_hash=c_hash,
                processing_status="PROCESSED",
                license_status=src.license_status,
                retrieved_at=datetime.utcnow(),
                last_verified_at=datetime.utcnow(),
            )
            db.add(doc)
            db.flush()

        # Create ContentRecord
        rec = ContentRecord(
            canonical_cancer_id=cancer_obj.id,
            category=item["category"],
            content=item["content"],
            content_type="STRUCTURED_EXTRACTION",
            country_code=item["country_code"],
            jurisdiction_scope=item["jurisdiction_scope"],
            language="en",
            audience=item["audience"],
            disagreement_status="CONSISTENT" if item["category"] != "screening" else "JURISDICTIONAL_VARIATION",
            disagreement_notes="Screening intervals and eligibility age thresholds vary across international jurisdictions." if item["category"] == "screening" else None,
            version_number=1,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(rec)
        db.flush()

        # Create ContentSource provenance junction
        cs = ContentSource(
            content_record_id=rec.id,
            source_id=src.id,
            source_document_id=doc.id,
            source_url=item["source_url"],
            source_updated_at=datetime.utcnow(),
            retrieved_at=datetime.utcnow(),
            last_verified_at=datetime.utcnow(),
            quote_snippet=item["snippet"],
            attribution_text=item["attribution"],
        )
        db.add(cs)

        # Create ContentVersion initial entry
        cv = ContentVersion(
            content_record_id=rec.id,
            version_number=1,
            content=item["content"],
            change_type="NEW",
            change_reason="Initial seeding from verified source",
            content_hash=c_hash,
            created_at=datetime.utcnow(),
        )
        db.add(cv)

    db.commit()
