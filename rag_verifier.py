"""
rag_verifier.py
----------------
GreenClaim AI - RAG pipeline that verifies a corporate environmental claim
against that company's BRSR/ESG report and returns a Greenwashing Risk
Score (0-100) with citation-backed evidence.

Fixes applied vs. the original version:
  1. API key loaded from environment (.env) - never hardcoded
  2. Portable paths - works for every teammate without editing the script
  3. Risk Score (0-100) added to the prompt and parsed out for the UI
  4. Retrieval filtered by company metadata, so a claim about Tata Steel
     can't accidentally get evidence from JSW Steel or UltraTech
  5. Non-deprecated imports (langchain_huggingface / langchain_chroma)

Setup:
    pip install -r requirements.txt
    cp .env.example .env          # then paste your Groq key into .env
    # put your BRSR PDFs in ./reports  (one PDF per company)
    python rag_verifier.py
"""

import os
import re
import glob
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from pypdf import PdfReader

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# ---------------------------------------------------------------------------
# Config - everything below is portable across teammates' machines.
# Override any of it with env vars instead of editing the file.
# ---------------------------------------------------------------------------
load_dotenv()  # reads a local .env file into the environment, if present

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.environ.get("BRSR_PDF_DIR", os.path.join(BASE_DIR, "brsr_reports"))
DB_DIR = os.environ.get("BRSR_DB_DIR", os.path.join(BASE_DIR, "brsr_chroma_db"))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY not set. Copy .env.example to .env and paste your key in, "
        "or run: export GROQ_API_KEY=your_key_here"
    )


# ---------------------------------------------------------------------------
# 1. PDF Parser & Loader
# ---------------------------------------------------------------------------
COMPANY_MAP_PATH = os.environ.get("BRSR_COMPANY_MAP", os.path.join(BASE_DIR, "company_map.csv"))


def _load_company_map(path: str) -> dict:
    """filename -> company name, from a CSV with columns: filename,company.
    NSE/BSE bulk downloads are named by numeric security code (e.g. BRSR_500470_...pdf),
    not by company name, so this map is what makes retrieval by company name work at all."""
    mapping = {}
    if os.path.exists(path):
        import csv
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mapping[row["filename"].strip()] = row["company"].strip()
    return mapping


_COMPANY_MAP = _load_company_map(COMPANY_MAP_PATH)


def derive_company_name(filename: str) -> str:
    """Look up the real company name for this filename. Falls back to a
    best-effort guess from the filename itself if it's not in company_map.csv -
    but that fallback will usually be wrong for NSE/BSE bulk-download filenames,
    so add missing files to company_map.csv rather than relying on it."""
    if filename in _COMPANY_MAP:
        return _COMPANY_MAP[filename]

    name = os.path.splitext(filename)[0]
    for tag in ("_BRSR", "-BRSR", "_brsr", "-brsr"):
        name = name.replace(tag, "")
    name = name.replace("_", " ").replace("-", " ")
    guess = " ".join(name.split()).strip()
    print(f"[!] '{filename}' not found in company_map.csv - guessing company name as '{guess}'. "
          f"Add a row to company_map.csv for an accurate name.")
    return guess


def list_available_companies(pdf_dir: str) -> List[str]:
    """What your Streamlit dropdown (or CLI) should offer as valid inputs."""
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    return sorted({derive_company_name(os.path.basename(f)) for f in pdf_files})


def load_and_tag_brsr_pdfs(pdf_dir: str) -> List[Document]:
    documents = []
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

    if not pdf_files:
        print(f"[!] Warning: No PDF files found in {pdf_dir}. Add files to proceed.")
        return documents

    print(f"[*] Found {len(pdf_files)} PDF(s). Extracting text...")

    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        company_name = derive_company_name(filename)

        reader = PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if len(text.strip()) > 50:
                doc = Document(
                    page_content=text,
                    metadata={
                        "company": company_name,
                        "source": filename,
                        "page": page_idx + 1,
                    },
                )
                documents.append(doc)

    print(f"[*] Loaded {len(documents)} valid page(s).")
    return documents


# ---------------------------------------------------------------------------
# 2. Text Chunking
# ---------------------------------------------------------------------------
def chunk_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[*] Generated {len(chunks)} contextual chunks.")
    return chunks


# ---------------------------------------------------------------------------
# 3. Vector Database (ChromaDB)
# ---------------------------------------------------------------------------
def get_vector_store(pdf_dir: str, persist_dir: str) -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        print("[*] Loading existing vector database from disk...")
        return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    print("[*] Building new vector store...")
    docs = load_and_tag_brsr_pdfs(pdf_dir)
    if not docs:
        raise ValueError(f"No valid text found in {pdf_dir}. Check your PDF files.")

    chunks = chunk_documents(docs)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    print("[*] Vector store built and saved to disk.")
    return vector_store


# ---------------------------------------------------------------------------
# 4. Greenwash Verifier Chain
# ---------------------------------------------------------------------------
@dataclass
class VerificationResult:
    company: str
    claim: str
    risk_score: Optional[int]   # 0-100, None if parsing failed
    verdict: Optional[str]      # VERIFIED / MISLEADING / UNSUPPORTED, None if parsing failed
    raw_output: str             # full formatted analysis, safe to display as-is


class GreenwashVerifier:
    def __init__(self, vector_store: Chroma):
        self.vector_store = vector_store

        self.llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.0,
        )

        self.prompt = ChatPromptTemplate.from_template("""
You are an expert ESG and Greenwashing Audit Analyst. Your task is to verify a corporate environmental marketing claim against the company's official BRSR disclosures.

CLAIM TO VERIFY:
Company: {company}
Claim: "{claim}"

OFFICIAL BRSR EVIDENCE EXTRACTS:
{context}

EVALUATION INSTRUCTIONS:
1. Identify the specific metric category: Carbon/GHG Emissions (Scope 1/2/3), Renewable Energy %, or Waste/Recycling.
2. Cross-reference the marketing claim with quantitative figures in the extract.
3. Classify into: VERIFIED, MISLEADING, or UNSUPPORTED.
4. Provide Key Facts & Numbers (cite exact figures and page numbers from the extract).
5. Provide a Risk Analysis explaining why it is or isn't greenwashing.
6. Assign a Greenwashing Risk Score from 0 to 100, where 0 means fully verified / no risk
   and 100 means severe, clearly unsupported greenwashing.

Write your full analysis first, in clear sections. Then finish your answer with
EXACTLY this block as the last two lines, with the labels unchanged and only the
brackets filled in (no extra text on these two lines):

RISK_SCORE: [integer 0-100]
VERDICT: [VERIFIED or MISLEADING or UNSUPPORTED]
""")
        self.chain = self.prompt | self.llm | StrOutputParser()

    def verify_claim(self, company: str, claim: str, top_k: int = 5) -> VerificationResult:
        # Filter retrieval to this company's chunks only, so a Tata Steel
        # claim can't be "supported" by evidence pulled from JSW Steel's report.
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k, "filter": {"company": company}},
        )
        retrieved_docs = retriever.invoke(claim)

        if not retrieved_docs:
            return VerificationResult(
                company=company,
                claim=claim,
                risk_score=None,
                verdict=None,
                raw_output=(
                    f"No indexed evidence found for '{company}'. Check that this exact "
                    f"name appears in list_available_companies() and that the PDF was ingested."
                ),
            )

        context_str = "\n\n---\n\n".join(
            f"[Source: {d.metadata.get('source')} | Page: {d.metadata.get('page')}]\n{d.page_content}"
            for d in retrieved_docs
        )

        raw_output = self.chain.invoke({
            "company": company,
            "claim": claim,
            "context": context_str,
        })

        return VerificationResult(
            company=company,
            claim=claim,
            risk_score=self._parse_risk_score(raw_output),
            verdict=self._parse_verdict(raw_output),
            raw_output=raw_output,
        )

    @staticmethod
    def _parse_risk_score(text: str) -> Optional[int]:
        match = re.search(r"RISK_SCORE:\s*\[?(\d{1,3})\]?", text)
        if not match:
            return None
        score = int(match.group(1))
        return max(0, min(100, score))  # clamp to 0-100 in case the model drifts

    @staticmethod
    def _parse_verdict(text: str) -> Optional[str]:
        match = re.search(r"VERDICT:\s*\[?(VERIFIED|MISLEADING|UNSUPPORTED)\]?", text, re.IGNORECASE)
        return match.group(1).upper() if match else None


# ---------------------------------------------------------------------------
# 5. Main - demo run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    v_store = get_vector_store(pdf_dir=PDF_DIR, persist_dir=DB_DIR)

    print("\nIndexed companies:", list_available_companies(PDF_DIR))

    verifier = GreenwashVerifier(v_store)

    # One claim likely to fail verification, one likely to pass -
    # showing both directions is more convincing at the expo than only "gotcha" cases.
    test_cases = [
        ("Tata Steel", "We are already a carbon-neutral steelmaker with near-zero Scope 1 emissions."),
        ("Tata Steel", "We are committed to achieving Net Zero emissions across all our operations by 2045."),
    ]

    for company, claim in test_cases:
        result = verifier.verify_claim(company, claim)
        print("\n" + "=" * 70)
        print(f"{result.company}: \"{result.claim}\"")
        print("-" * 70)
        print(result.raw_output)
        print(f"\n>>> Parsed Risk Score: {result.risk_score}  |  Verdict: {result.verdict}")