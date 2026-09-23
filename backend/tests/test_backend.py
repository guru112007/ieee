import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.main import app, seed_database
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import Company, ClaimAnalysis
from backend.app.services.scorer import GreenwashingScorer
from backend.app.services.pdf_processor import PDFProcessor


client = TestClient(app)


def setup_module(module):
    """Ensure database is seeded before running tests."""
    seed_database()


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    companies = response.json()
    assert len(companies) >= 12
    names = [c["name"] for c in companies]
    assert "Tata Steel" in names
    assert "Hindustan Unilever" in names
    assert "NTPC Limited" in names


def test_scorer_logic():
    # Vague ungrounded claim should yield elevated risk
    vague_result = GreenwashingScorer.calculate_score(
        claim_text="We are 100% eco-friendly and have zero impact on the planet.",
        citations=[],
        has_audited_source=False,
        has_direct_contradiction=True,
        missing_scope_or_baseline=True
    )
    assert vague_result["risk_score"] > 70.0
    assert vague_result["verdict_status"] in ["Unsupported", "High Risk"]

    # Specific audited claim with supporting evidence should yield low risk
    verified_result = GreenwashingScorer.calculate_score(
        claim_text="Committed to net-zero operations by 2045 with 40% reduction by 2030 across Scope 1 emissions.",
        citations=[{"type": "Supporting", "relevance": 0.95}],
        has_audited_source=True,
        has_direct_contradiction=False,
        missing_scope_or_baseline=False
    )
    assert verified_result["risk_score"] <= 25.0
    assert verified_result["verdict_status"] == "Verified"


def test_analyze_claim_api_tata_steel_high_risk():
    # Fetch Tata Steel company ID
    companies = client.get("/api/v1/companies").json()
    ts = next(c for c in companies if c["name"] == "Tata Steel")

    payload = {
        "company_id": ts["id"],
        "claim_text": "Already carbon-neutral with near-zero Scope 1 emissions across all steel plants.",
        "category": "Climate"
    }
    response = client.post("/api/v1/claims/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Tata Steel"
    assert data["risk_score"] >= 75.0
    assert data["verdict_status"] in ["Unsupported", "High Risk"]
    assert len(data["citations"]) >= 1
    assert data["factors"]["evidence_strength"] > 50


def test_analyze_claim_api_tata_steel_verified():
    companies = client.get("/api/v1/companies").json()
    ts = next(c for c in companies if c["name"] == "Tata Steel")

    payload = {
        "company_id": ts["id"],
        "claim_text": "Has committed to net-zero operations by 2045 with capital transition roadmaps.",
        "category": "Climate"
    }
    response = client.post("/api/v1/claims/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] <= 25.0
    assert data["verdict_status"] == "Verified"
    assert len(data["citations"]) >= 1


def test_get_claim_history():
    response = client.get("/api/v1/claims/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 4  # Includes pre-seeded benchmark items


def test_pdf_processor_synthetic():
    """Verify PyMuPDF extraction on a synthetic test PDF created in-memory."""
    import pymupdf as fitz
    test_pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")

    # Generate small 2-page test PDF
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Tata Steel Sustainability Report FY25. Direct Scope 1 emissions totaled 26.4 MTCO2e.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Principle 6 Disclosures: Renewable power purchasing increased to 450 MW.")
    doc.save(test_pdf_path)
    doc.close()

    try:
        extracted = PDFProcessor.extract_document(test_pdf_path)
        assert extracted["total_pages"] == 2
        assert "26.4 MTCO2e" in extracted["full_text"]
        assert len(extracted["pages"]) == 2
    finally:
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
