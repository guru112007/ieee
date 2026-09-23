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

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from rag_verifier import (
    get_vector_store,
    load_and_tag_brsr_pdfs,
    chunk_documents,
    HuggingFaceEmbeddings,
    Chroma,
    GreenwashVerifier,
    BRSRAnomalyAuditor,
    list_available_companies,
    PDF_DIR,
    DB_DIR,
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
anomaly_auditor = BRSRAnomalyAuditor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Loading vector store...")
    app.state.v_store = get_vector_store(PDF_DIR, DB_DIR)
    app.state.verifier = GreenwashVerifier(app.state.v_store)
    print("[+] Ready to serve.")
    yield

app = FastAPI(title="GreenClaim AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerifyRequest(BaseModel):
    company: str
    claim: str

@app.get("/companies")
def get_companies():
    return {"companies": list_available_companies(PDF_DIR)}

# 1. Verify against pre-indexed database
@app.post("/verify")
def verify_claim(req: VerifyRequest, request: Request):
    verifier: GreenwashVerifier = request.app.state.verifier
    res = verifier.verify_claim(req.company, req.claim)
    return {
        "company": res.company,
        "claim": res.claim,
        "risk_score": res.risk_score,
        "verdict": res.verdict,
        "explanation": res.raw_output,
    }

# 2. Upload PDF & Scan for Internal Anomalies
@app.post("/scan-anomalies")
async def scan_anomalies(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        docs = load_and_tag_brsr_pdfs(temp_dir)
        if not docs:
            raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

        chunks = chunk_documents(docs)
        audit_res = anomaly_auditor.audit_document(chunks)
        return {
            "filename": file.filename,
            "integrity_score": audit_res["integrity_score"],
            "anomaly_flag": audit_res["anomaly_flag"],
            "audit_report": audit_res["report"],
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# 3. Interactive Web Portal
@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>GreenClaim AI - ESG & Anomaly Auditor</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 p-8 text-slate-800">
      <div class="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow border">
        <h1 class="text-3xl font-bold text-emerald-800">GreenClaim AI</h1>
        <p class="text-slate-500 mb-6">Autonomous ESG Claim Verification & Forensic PDF Anomaly Audit</p>
        
        <div class="flex border-b mb-6 space-x-4">
          <button id="tab1Btn" onclick="switchTab(1)" class="pb-2 border-b-2 border-emerald-600 font-semibold text-emerald-700">1. Verify Claim</button>
          <button id="tab2Btn" onclick="switchTab(2)" class="pb-2 border-b-2 border-transparent font-semibold text-slate-500 hover:text-emerald-600">2. Scan PDF for Anomalies</button>
        </div>

        <!-- TAB 1: Claim Verifier -->
        <div id="tab1">
          <form id="verifyForm" class="space-y-4">
            <div>
              <label class="block text-sm font-semibold mb-1">Company Name</label>
              <input type="text" id="vCompany" required class="w-full border p-2.5 rounded-lg" placeholder="e.g. Adani Green Energy">
            </div>
            <div>
              <label class="block text-sm font-semibold mb-1">Claim</label>
              <textarea id="vClaim" rows="3" required class="w-full border p-2.5 rounded-lg" placeholder="e.g. Our operational renewable energy portfolio reached over 8 GW."></textarea>
            </div>
            <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 px-6 rounded-lg">Verify Claim</button>
          </form>
        </div>

        <!-- TAB 2: PDF Anomaly Scanner -->
        <div id="tab2" class="hidden">
          <form id="anomalyForm" class="space-y-4">
            <div>
              <label class="block text-sm font-semibold mb-1">Upload Corporate BRSR / ESG PDF</label>
              <input type="file" id="aFile" accept="application/pdf" required class="w-full border p-2 rounded-lg bg-slate-50">
            </div>
            <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 px-6 rounded-lg">Audit Document for Anomalies</button>
          </form>
        </div>

        <div id="loader" class="hidden mt-6 text-center text-emerald-700 font-semibold animate-pulse">Running audit pipeline...</div>
        
        <div id="resultBox" class="hidden mt-6 p-6 rounded-xl border bg-slate-50">
          <div class="flex justify-between items-center border-b pb-3 mb-4">
            <span class="font-bold text-sm">Status: <span id="resBadge" class="text-emerald-700"></span></span>
            <span class="font-bold text-sm">Score: <span id="resScore" class="text-rose-600"></span></span>
          </div>
          <pre id="resContent" class="text-xs whitespace-pre-wrap font-sans text-slate-700 leading-relaxed"></pre>
        </div>
      </div>

      <script>
        function switchTab(tab) {
          document.getElementById('tab1').classList.toggle('hidden', tab !== 1);
          document.getElementById('tab2').classList.toggle('hidden', tab !== 2);
          document.getElementById('tab1Btn').className = tab === 1 ? 'pb-2 border-b-2 border-emerald-600 font-semibold text-emerald-700' : 'pb-2 border-b-2 border-transparent font-semibold text-slate-500';
          document.getElementById('tab2Btn').className = tab === 2 ? 'pb-2 border-b-2 border-emerald-600 font-semibold text-emerald-700' : 'pb-2 border-b-2 border-transparent font-semibold text-slate-500';
          document.getElementById('resultBox').classList.add('hidden');
        }

        document.getElementById('verifyForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          runAudit('/verify', { company: document.getElementById('vCompany').value, claim: document.getElementById('vClaim').value }, false);
        });

        document.getElementById('anomalyForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const fd = new FormData();
          fd.append('file', document.getElementById('aFile').files[0]);
          runAudit('/scan-anomalies', fd, true);
        });

        async function runAudit(url, body, isFormData) {
          const loader = document.getElementById('loader');
          const box = document.getElementById('resultBox');
          loader.classList.remove('hidden'); box.classList.add('hidden');

          try {
            const opts = isFormData ? { method: 'POST', body } : { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) };
            const r = await fetch(url, opts);
            const data = await r.json();

            document.getElementById('resBadge').textContent = data.verdict || data.anomaly_flag || 'Completed';
            document.getElementById('resScore').textContent = data.risk_score !== undefined ? `${data.risk_score}/100 Risk` : `${data.integrity_score}/100 Integrity`;
            document.getElementById('resContent').textContent = data.explanation || data.audit_report;
            box.classList.remove('hidden');
          } catch(err) {
            alert('Error: ' + err.message);
          } finally {
            loader.classList.add('hidden');
          }
        }
      </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)