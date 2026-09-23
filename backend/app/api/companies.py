from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Company
from backend.app.schemas import CompanyResponse, CompanyCreate

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=List[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    """Retrieve all monitored companies (e.g. NSE-listed entities)."""
    return db.query(Company).order_by(Company.name.asc()).all()


@router.post("", response_model=CompanyResponse, status_code=201)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Register a new enterprise for BRSR / ESG claim monitoring."""
    existing = db.query(Company).filter(Company.name.ilike(company.name.strip())).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already registered.")

    db_company = Company(
        name=company.name.strip(),
        sector=company.sector.strip(),
        ticker=company.ticker.strip().upper() if company.ticker else None,
        description=company.description
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company
