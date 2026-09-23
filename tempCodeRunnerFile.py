"""
main.py
-------
FastAPI backend for GreenClaim AI. Exposes the existing RAG pipeline
(rag_verifier.py) as HTTP endpoints so any separately-built frontend
(React, plain HTML/JS, etc.) can call it.

Run:
    uvicorn main:app --reload --port 8000

Then open http://localhost:8000/docs for an interactive test page,
or point your frontend at the endpoints below.

Endpoints:
    GET  /companies   -> list of indexed company names (for a dropdown)
    POST /verify       -> {company, claim} -> risk score + verdict + cited evidence
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_verifier import (
    get_vector_store,
    GreenwashVerifier,
    list_available_companies,
    PDF_DIR,
    DB_DIR,
)

app = FastAPI(title="GreenClaim AI API")

# Lets your frontend (e.g. React dev server on localhost:3000) call this API
# from the browser without CORS errors. Fine for local dev / an expo demo;
# tighten allow_origins to your actual frontend URL before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_verifier: Optional[GreenwashVerifier] = None


@app.on_event("startup")
def startup():
    """Load the embedding model + vector DB once, when the server starts -
    not on every request."""
    global _verifier
    v_store = get_vector_store(PDF_DIR, DB_DIR)
    _verifier = GreenwashVerifier(v_store)


class VerifyRequest(BaseModel):
    company: str
    claim: str


class VerifyResponse(BaseModel):
    company: str
    claim: str
    risk_score: Optional[int]
    verdict: Optional[str]
    explanation: str  # full formatted analysis (markdown) - safe to render as-is


@app.get("/")
def root():
    return {"status": "GreenClaim AI API running", "docs": "/docs"}


@app.get("/companies")
def companies():
    return {"companies": list_available_companies(PDF_DIR)}


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    valid_companies = list_available_companies(PDF_DIR)
    if req.company not in valid_companies:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown company '{req.company}'. Valid options: {valid_companies}",
        )
    if not req.claim.strip():
        raise HTTPException(status_code=400, detail="claim must not be empty.")

    result = _verifier.verify_claim(req.company, req.claim)
    return VerifyResponse(
        company=result.company,
        claim=result.claim,
        risk_score=result.risk_score,
        verdict=result.verdict,
        explanation=result.raw_output,
    )
