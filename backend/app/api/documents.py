import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Document, Company
from backend.app.schemas import DocumentResponse
from backend.app.services.pdf_processor import PDFProcessor

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    company_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts an ESG / BRSR PDF file, saves it to local disk, extracts clean raw text page-by-page
    using PyMuPDF, and stores metadata in the database.
    """
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for BRSR extraction.")

    # Save to uploads directory
    safe_filename = f"{company.id}_{int(os.path.getmtime(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else 0)}_{os.path.basename(file.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")

    # Extract text with PyMuPDF
    try:
        extraction_result = PDFProcessor.extract_document(file_path)
        page_count = extraction_result.get("total_pages", 1)
        full_text = extraction_result.get("full_text", "")
    except Exception as e:
        # Cleanup uploaded file if extraction completely crashes
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"PyMuPDF text extraction failed: {str(e)}")

    # Save to database
    db_document = Document(
        company_id=company_id,
        file_name=file.filename,
        file_path=file_path,
        page_count=page_count,
        extracted_text=full_text
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return DocumentResponse(
        id=db_document.id,
        company_id=db_document.company_id,
        file_name=db_document.file_name,
        file_path=db_document.file_path,
        page_count=db_document.page_count,
        uploaded_at=db_document.uploaded_at,
        message=f"Successfully extracted {page_count} pages with PyMuPDF."
    )


@router.get("", response_model=List[DocumentResponse])
def get_documents(company_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve all uploaded BRSR and ESG documents with optional company filter."""
    query = db.query(Document)
    if company_id is not None:
        query = query.filter(Document.company_id == company_id)
    return query.order_by(Document.uploaded_at.desc()).all()
