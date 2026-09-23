import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Company, Document, ClaimAnalysis
from backend.app.schemas import (
    ClaimAnalyzeRequest,
    ClaimAnalysisResponse,
    ClaimHistoryItem,
    CitationItem,
    RiskFactorBreakdown
)
from backend.app.services.rag_stub import rag_engine

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("/analyze", response_model=ClaimAnalysisResponse)
def analyze_claim(payload: ClaimAnalyzeRequest, db: Session = Depends(get_db)):
    """
    Accepts an environmental or sustainability claim string and target company ID,
    runs evidence retrieval against statutory BRSR filings and standards via the RAG pipeline,
    computes calibrated greenwashing risk factors, stores the result, and returns an Explainable AI verdict report.
    """
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    # Check for any user-uploaded documents for this specific company
    latest_doc = (
        db.query(Document)
        .filter(Document.company_id == payload.company_id)
        .order_by(Document.uploaded_at.desc())
        .first()
    )
    custom_text = latest_doc.extracted_text if latest_doc else None

    # Run through evidence-grounded RAG pipeline
    rag_result = rag_engine.analyze_claim(
        claim_text=payload.claim_text,
        company_name=company.name,
        category=payload.category,
        custom_document_text=custom_text
    )

    # Prepare JSON serializations
    citations_data = rag_result.get("citations", [])
    factors_data = rag_result.get("factors", {})

    contradicting = "\n".join(rag_result.get("contradicting_evidence", [])) if rag_result.get("contradicting_evidence") else None
    missing = rag_result.get("missing_evidence")

    # Persist in DB
    db_analysis = ClaimAnalysis(
        company_id=company.id,
        claim_text=payload.claim_text.strip(),
        category=payload.category,
        risk_score=rag_result["risk_score"],
        verdict_status=rag_result["verdict_status"],
        explanation=rag_result.get("explanation", ""),
        missing_evidence=missing,
        contradicting_evidence=contradicting,
        confidence_score=rag_result.get("confidence_score", 0.88),
        citations_json=json.dumps(citations_data),
        factors_json=json.dumps(factors_data)
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return ClaimAnalysisResponse(
        id=db_analysis.id,
        company_id=company.id,
        company_name=company.name,
        claim_text=db_analysis.claim_text,
        category=db_analysis.category,
        risk_score=db_analysis.risk_score,
        verdict_status=db_analysis.verdict_status,
        explanation=db_analysis.explanation,
        missing_evidence=db_analysis.missing_evidence,
        contradicting_evidence=db_analysis.contradicting_evidence,
        confidence_score=db_analysis.confidence_score,
        citations=[CitationItem(**c) for c in citations_data],
        factors=RiskFactorBreakdown(**factors_data),
        created_at=db_analysis.created_at
    )


@router.get("/history", response_model=List[ClaimHistoryItem])
def get_claim_history(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    category: Optional[str] = Query(None, description="Filter by claim category"),
    db: Session = Depends(get_db)
):
    """Retrieve past verification analyses with optional filtering."""
    query = db.query(ClaimAnalysis).join(Company)
    if company_id is not None:
        query = query.filter(ClaimAnalysis.company_id == company_id)
    if category and category != "All":
        query = query.filter(ClaimAnalysis.category.ilike(category))

    records = query.order_by(ClaimAnalysis.created_at.desc()).all()

    return [
        ClaimHistoryItem(
            id=r.id,
            company_id=r.company_id,
            company_name=r.company.name,
            claim_text=r.claim_text,
            category=r.category,
            risk_score=r.risk_score,
            verdict_status=r.verdict_status,
            explanation=r.explanation,
            confidence_score=r.confidence_score,
            created_at=r.created_at
        )
        for r in records
    ]


@router.get("/{claim_id}", response_model=ClaimAnalysisResponse)
def get_claim_details(claim_id: int, db: Session = Depends(get_db)):
    """Retrieve full analysis report and citations for a specific historical claim."""
    analysis = db.query(ClaimAnalysis).filter(ClaimAnalysis.id == claim_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Claim analysis report not found.")

    citations_list = []
    if analysis.citations_json:
        try:
            citations_list = json.loads(analysis.citations_json)
        except Exception:
            citations_list = []

    factors_dict = {
        "evidence_strength": 50.0,
        "claim_specificity": 50.0,
        "source_reliability": 50.0,
        "contradictory_evidence": 50.0,
        "missing_information": 50.0
    }
    if analysis.factors_json:
        try:
            factors_dict = json.loads(analysis.factors_json)
        except Exception:
            pass

    return ClaimAnalysisResponse(
        id=analysis.id,
        company_id=analysis.company_id,
        company_name=analysis.company.name,
        claim_text=analysis.claim_text,
        category=analysis.category,
        risk_score=analysis.risk_score,
        verdict_status=analysis.verdict_status,
        explanation=analysis.explanation,
        missing_evidence=analysis.missing_evidence,
        contradicting_evidence=analysis.contradicting_evidence,
        confidence_score=analysis.confidence_score,
        citations=[CitationItem(**c) for c in citations_list],
        factors=RiskFactorBreakdown(**factors_dict),
        created_at=analysis.created_at
    )
