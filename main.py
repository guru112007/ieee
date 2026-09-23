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

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_verifier import (
    get_vector_store,
    GreenwashVerifier,
    list_available_companies,
    PDF_DIR,
    DB_DIR,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load vector database and LLM chain once on boot."""
    print("[*] Initializing Chroma vector store and GreenwashVerifier...")
    v_store = get_vector_store(PDF_DIR, DB_DIR)
    app.state.verifier = GreenwashVerifier(v_store)
    print("[+] Model and database ready to serve requests.")
    yield

app = FastAPI(title="GreenClaim AI API", lifespan=lifespan)

# Allow cross-origin requests (e.g., from a React / Next.js / HTML frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerifyRequest(BaseModel):
    company: str
    claim: str

class VerifyResponse(BaseModel):
    company: str
    claim: str
    risk_score: Optional[int]
    verdict: Optional[str]
    explanation: str

@app.get("/")
def root():
    return {"status": "GreenClaim AI API running", "docs": "/docs"}

@app.get("/companies")
def companies():
    return {"companies": list_available_companies(PDF_DIR)}

@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest, request: Request):
    verifier: GreenwashVerifier = request.app.state.verifier
    if not verifier:
        raise HTTPException(status_code=503, detail="Verifier is not initialized.")

    valid_companies = list_available_companies(PDF_DIR)
    if req.company not in valid_companies:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown company '{req.company}'. Valid options: {valid_companies}",
        )
    if not req.claim.strip():
        raise HTTPException(status_code=400, detail="Claim must not be empty.")

    result = verifier.verify_claim(req.company, req.claim)
    return VerifyResponse(
        company=result.company,
        claim=result.claim,
        risk_score=result.risk_score,
        verdict=result.verdict,
        explanation=result.raw_output,
    )