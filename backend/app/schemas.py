from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Company Schemas
class CompanyBase(BaseModel):
    name: str = Field(..., examples=["Tata Steel"])
    sector: str = Field(..., examples=["Metals & Mining"])
    ticker: Optional[str] = Field(None, examples=["TATASTEEL"])
    description: Optional[str] = Field(None, examples=["Indian multinational steel-making company"])


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    company_id: int
    file_name: str
    file_path: str
    page_count: int
    uploaded_at: datetime
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Citation & Evidence Schemas
class CitationItem(BaseModel):
    doc_name: str = Field(..., examples=["Tata_Steel_BRSR_FY2024-25.pdf"])
    page: int = Field(..., examples=[42])
    section: str = Field(..., examples=["Principle 6 - Scope 1 & 2 Emissions"])
    snippet: str = Field(..., examples=["Scope 1 direct greenhouse gas emissions totaled 26.4 million MTCO2e..."])
    relevance: float = Field(..., examples=[0.92])  # 0.0 - 1.0
    type: str = Field(..., examples=["Contradicting"])  # Supporting, Contradicting, Context


class RiskFactorBreakdown(BaseModel):
    evidence_strength: float = Field(..., description="Weight 30%: Directness & depth of retrieved evidence", ge=0, le=100)
    claim_specificity: float = Field(..., description="Weight 20%: Penalizes vague marketing buzzwords", ge=0, le=100)
    source_reliability: float = Field(..., description="Weight 20%: Audited BRSR disclosures vs PR", ge=0, le=100)
    contradictory_evidence: float = Field(..., description="Weight 20%: Direct conflicts with disclosures", ge=0, le=100)
    missing_information: float = Field(..., description="Weight 10%: Absence of baseline or Scope 3 metrics", ge=0, le=100)


# Claim Analysis Request & Response
class ClaimAnalyzeRequest(BaseModel):
    company_id: int = Field(..., description="Target company ID")
    claim_text: str = Field(..., min_length=5, description="Environmental claim string to evaluate")
    category: str = Field(default="Climate", description="Climate, Waste, Energy, Water, or Product")


class ClaimAnalysisResponse(BaseModel):
    id: int
    company_id: int
    company_name: str
    claim_text: str
    category: str
    risk_score: float = Field(..., description="Greenwashing risk score between 0 and 100")
    verdict_status: str = Field(..., description="Verified | Partially Supported | Unsupported | High Risk")
    explanation: str
    missing_evidence: Optional[str] = None
    contradicting_evidence: Optional[str] = None
    confidence_score: float = Field(default=0.88, ge=0, le=1.0)
    citations: List[CitationItem] = []
    factors: RiskFactorBreakdown
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimHistoryItem(BaseModel):
    id: int
    company_id: int
    company_name: str
    claim_text: str
    category: str
    risk_score: float
    verdict_status: str
    explanation: str
    confidence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
