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
import shutil
import tempfile
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from rag_verifier import (
    load_and_tag_brsr_pdfs,
    chunk_documents,
    HuggingFaceEmbeddings,
    Chroma,
    GreenwashVerifier,
    list_available_companies,
    PDF_DIR,
    DB_DIR,
)

# Shared embedding model to avoid reloading on each upload
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load default persistent vector database on boot."""
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        print("[*] Loading global persistent Chroma DB...")
        app.state.global_vstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        app.state.global_verifier = GreenwashVerifier(app.state.global_vstore)
    else:
        app.state.global_vstore = None
        app.state.global_verifier = None
    yield

app = FastAPI(title="GreenClaim AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoint 1: Upload a PDF and Verify Claim In Real-Time
# ---------------------------------------------------------------------------
@app.post("/audit-pdf")
async def audit_uploaded_pdf(
    company: str = Form(..., description="Name of the company"),
    claim: str = Form(..., description="Marketing or ESG claim to evaluate"),
    file: UploadFile = File(..., description="The BRSR / ESG PDF report")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 1. Save uploaded file to a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Extract and chunk text
        docs = load_and_tag_brsr_pdfs(temp_dir)
        if not docs:
            raise HTTPException(status_code=400, detail="Could not extract text from this PDF. Check if it's scanned.")

        chunks = chunk_documents(docs)

        # 3. Create an isolated in-memory vector store for this specific document
        temp_vstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        # 4. Verify claim using GreenwashVerifier
        verifier = GreenwashVerifier(temp_vstore)
        result = verifier.verify_claim(company=company, claim=claim)

        return {
            "company": result.company,
            "claim": result.claim,
            "risk_score": result.risk_score,
            "verdict": result.verdict,
            "explanation": result.raw_output
        }

    finally:
        # Clean up temporary PDF file and folder
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Endpoint 2: Minimal Web UI for Direct Customer Testing
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>GreenClaim AI - ESG Auditor</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 text-slate-800 min-h-screen p-8">
      <div class="max-w-3xl mx-auto bg-white p-8 rounded-xl shadow-md border border-slate-200">
        <h1 class="text-2xl font-bold text-emerald-800">GreenClaim AI Auditor</h1>
        <p class="text-sm text-slate-500 mb-6">Upload a corporate BRSR/ESG PDF report to audit claims for greenwashing.</p>
        
        <form id="auditForm" class="space-y-4">
          <div>
            <label class="block text-sm font-semibold mb-1">Company Name</label>
            <input type="text" id="company" required class="w-full border rounded-lg p-2.5 text-sm" placeholder="e.g. Tata Steel">
          </div>
          <div>
            <label class="block text-sm font-semibold mb-1">Environmental Claim</label>
            <textarea id="claim" rows="3" required class="w-full border rounded-lg p-2.5 text-sm" placeholder="e.g. We are 100% carbon neutral with near-zero Scope 1 emissions."></textarea>
          </div>
          <div>
            <label class="block text-sm font-semibold mb-1">Upload BRSR PDF</label>
            <input type="file" id="pdfFile" accept="application/pdf" required class="w-full border rounded-lg p-2 text-sm">
          </div>
          <button type="submit" id="submitBtn" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-lg text-sm transition">
            Run Audit Analysis
          </button>
        </form>

        <div id="loader" class="hidden mt-6 text-center text-sm font-medium text-emerald-700">
          Extracting text, embedding document, and querying audit model...
        </div>

        <div id="resultBox" class="hidden mt-6 p-4 rounded-lg border bg-slate-50">
          <div class="flex items-center justify-between border-b pb-2 mb-3">
            <span class="font-semibold text-sm">Verdict: <span id="resVerdict" class="font-bold"></span></span>
            <span class="text-sm">Risk Score: <span id="resScore" class="font-bold"></span>/100</span>
          </div>
          <pre id="resExplanation" class="text-xs whitespace-pre-wrap font-sans text-slate-700 leading-relaxed"></pre>
        </div>
      </div>

      <script>
        document.getElementById('auditForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const btn = document.getElementById('submitBtn');
          const loader = document.getElementById('loader');
          const resBox = document.getElementById('resultBox');

          btn.disabled = true;
          loader.classList.remove('hidden');
          resBox.classList.add('hidden');

          const formData = new FormData();
          formData.append('company', document.getElementById('company').value);
          formData.append('claim', document.getElementById('claim').value);
          formData.append('file', document.getElementById('pdfFile').files[0]);

          try {
            const res = await fetch('/audit-pdf', { method: 'POST', body: formData });
            const data = await res.json();
            
            document.getElementById('resVerdict').textContent = data.verdict || 'N/A';
            document.getElementById('resScore').textContent = data.risk_score !== null ? data.risk_score : 'N/A';
            document.getElementById('resExplanation').textContent = data.explanation;
            resBox.classList.remove('hidden');
          } catch (err) {
            alert('Audit failed: ' + err.message);
          } finally {
            btn.disabled = false;
            loader.classList.add('hidden');
          }
        });
      </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)