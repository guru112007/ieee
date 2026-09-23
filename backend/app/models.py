from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    sector = Column(String(100), nullable=False, index=True)
    ticker = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    claim_analyses = relationship("ClaimAnalysis", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    company = relationship("Company", back_populates="documents")


class ClaimAnalysis(Base):
    __tablename__ = "claim_analyses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    claim_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # Climate, Waste, Energy, Water, Product
    risk_score = Column(Float, nullable=False)  # 0 to 100
    verdict_status = Column(String(100), nullable=False)  # Verified, Partially Supported, Unsupported, High Risk
    explanation = Column(Text, nullable=False)
    missing_evidence = Column(Text, nullable=True)
    contradicting_evidence = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.85, nullable=False)
    citations_json = Column(Text, nullable=True)  # JSON-encoded array of page-level citations
    factors_json = Column(Text, nullable=True)    # JSON-encoded dictionary of 5 weighted factors
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    company = relationship("Company", back_populates="claim_analyses")
