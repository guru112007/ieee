import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import engine, Base, SessionLocal
from backend.app.models import Company, ClaimAnalysis
from backend.app.api.companies import router as companies_router
from backend.app.api.documents import router as documents_router
from backend.app.api.claims import router as claims_router


# NSE Benchmark corporate seed dataset
SEED_COMPANIES = [
    {"name": "Tata Steel", "sector": "Metals & Mining", "ticker": "TATASTEEL", "description": "Global steel manufacturer with operations in Jamshedpur, Kalinganagar, and Europe."},
    {"name": "Hindustan Unilever", "sector": "FMCG", "ticker": "HINDUNILVR", "description": "India's largest consumer goods company with focus on circular packaging."},
    {"name": "NTPC Limited", "sector": "Energy & Power", "ticker": "NTPC", "description": "India's largest power utility expanding thermal and renewable generation."},
    {"name": "Reliance Industries", "sector": "Diversified & Energy", "ticker": "RELIANCE", "description": "Hydrocarbon refining, petrochemicals, telecommunications, and retail conglomerate."},
    {"name": "ITC Limited", "sector": "FMCG & Agri", "ticker": "ITC", "description": "Multi-business conglomerate recognized for carbon and water positive achievements."},
    {"name": "JSW Steel", "sector": "Metals & Mining", "ticker": "JSWSTEEL", "description": "Leading integrated steel producer with decarbonization capital roadmaps."},
    {"name": "UltraTech Cement", "sector": "Building Materials", "ticker": "ULTRACEMCO", "description": "Largest manufacturer of grey cement, Ready Mix Concrete, and white cement in India."},
    {"name": "Adani Green Energy", "sector": "Renewable Energy", "ticker": "ADANIGREEN", "description": "Pure-play utility-scale solar and wind power generation platform."},
    {"name": "Tata Power", "sector": "Energy & Power", "ticker": "TATAPOWER", "description": "Integrated power company scaling rooftop solar and EV charging infrastructure."},
    {"name": "Asian Paints", "sector": "Paints & Chemicals", "ticker": "ASIANPAINT", "description": "Paints, coatings, and home decor enterprise monitoring VOC reduction."},
    {"name": "Britannia Industries", "sector": "FMCG", "ticker": "BRITANNIA", "description": "Food and packaged goods manufacturer targeting zero waste to landfill."},
    {"name": "Titan Company", "sector": "Consumer Goods", "ticker": "TITAN", "description": "Jewellery, watches, and eyewear manufacturer monitoring responsible sourcing."}
]


def seed_database():
    """Initializes tables and populates benchmark companies and case study analyses."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed companies if empty
        if db.query(Company).count() == 0:
            print("🌱 Seeding default NSE benchmark companies...")
            for comp_data in SEED_COMPANIES:
                company = Company(**comp_data)
                db.add(company)
            db.commit()

        # Seed sample benchmark analyses for immediate evaluation
        if db.query(ClaimAnalysis).count() == 0:
            print("🌱 Seeding benchmark claim analyses (Tata Steel, HUL, NTPC)...")
            ts = db.query(Company).filter(Company.name == "Tata Steel").first()
            hul = db.query(Company).filter(Company.name == "Hindustan Unilever").first()
            ntpc = db.query(Company).filter(Company.name == "NTPC Limited").first()

            if ts:
                # Benchmark 1: Tata Steel - High Risk Claim (Slide 10 Case Study)
                db.add(ClaimAnalysis(
                    company_id=ts.id,
                    claim_text="Already carbon-neutral with near-zero Scope 1 emissions across our steel manufacturing facilities.",
                    category="Climate",
                    risk_score=82.5,
                    verdict_status="High Risk",
                    explanation="The company discloses a Net Zero target for 2045, not present-day carbon neutrality. Claiming near-zero Scope 1 emissions directly conflicts with audited statutory BRSR Principle 6 filings reporting over 26 million MTCO2e.",
                    missing_evidence="Third-party audit trail for voluntary carbon offset retirements or near-zero blast furnace claims.",
                    contradicting_evidence="Disclosures report 26.38 Million MTCO2e in direct emissions — the company is not currently carbon-neutral.\nPresent operations depend predominantly on metallurgical coking coal and blast furnaces.",
                    confidence_score=0.94,
                    citations_json=json.dumps([
                        {
                            "doc_name": "Tata_Steel_BRSR_FY2024-25.pdf",
                            "page": 42,
                            "section": "Principle 6 - Scope 1 & Scope 2 Emissions Disclosures",
                            "snippet": "Direct Scope 1 emissions for FY 2024-25 stood at 26.38 Million Metric Tonnes CO2e, primarily from blast furnace iron-making operations at Jamshedpur and Kalinganagar plants.",
                            "relevance": 0.94,
                            "type": "Contradicting"
                        }
                    ]),
                    factors_json=json.dumps({
                        "evidence_strength": 88.0,
                        "claim_specificity": 75.0,
                        "source_reliability": 15.0,
                        "contradictory_evidence": 85.0,
                        "missing_information": 75.0
                    })
                ))

                # Benchmark 2: Tata Steel - Verified Rephrased Claim (Slide 10 Case Study)
                db.add(ClaimAnalysis(
                    company_id=ts.id,
                    claim_text="Has committed to net-zero operations by 2045 with capital allocation for scrap-based EAF transitions.",
                    category="Climate",
                    risk_score=14.5,
                    verdict_status="Verified",
                    explanation="Claim accurately represents the company's verified statutory target. The 2045 net-zero target is supported with dedicated capital expenditure and technology roadmaps in the official BRSR disclosure.",
                    missing_evidence="Granular Scope 3 supplier emission accounting is in nascent reporting stages.",
                    contradicting_evidence=None,
                    confidence_score=0.96,
                    citations_json=json.dumps([
                        {
                            "doc_name": "Tata_Steel_BRSR_FY2024-25.pdf",
                            "page": 14,
                            "section": "Principle 6 - Climate Transition Plan & Decarbonization",
                            "snippet": "Tata Steel has formally targeted Net Zero GHG Emissions across all global manufacturing facilities by 2045, benchmarked against FY 2020-21 baselines.",
                            "relevance": 0.96,
                            "type": "Supporting"
                        }
                    ]),
                    factors_json=json.dumps({
                        "evidence_strength": 8.0,
                        "claim_specificity": 18.0,
                        "source_reliability": 15.0,
                        "contradictory_evidence": 10.0,
                        "missing_information": 20.0
                    })
                ))

            if hul:
                # Benchmark 3: HUL - Moderate Risk Claim
                db.add(ClaimAnalysis(
                    company_id=hul.id,
                    claim_text="100% of our plastic packaging is recyclable and plastic-neutral nationwide.",
                    category="Waste",
                    risk_score=46.2,
                    verdict_status="Partially Supported",
                    explanation="The claim of 100% recyclable packaging is partially supported by EPR collection quotas, but conflates volume offsetting/co-processing with circular recyclability.",
                    missing_evidence="Clear percentage breakdown of true circular closed-loop recycling vs energy recovery/incineration.",
                    contradicting_evidence="A notable percentage of collected plastic is co-incinerated in cement kilns rather than mechanically recycled into circular packaging.",
                    confidence_score=0.91,
                    citations_json=json.dumps([
                        {
                            "doc_name": "HUL_BRSR_Report_FY24.pdf",
                            "page": 58,
                            "section": "Principle 2 - Extended Producer Responsibility (EPR)",
                            "snippet": "HUL facilitated the collection and environmentally sound processing of 100% post-consumer plastic packaging equivalent (120,000+ tonnes) in compliance with CPCB guidelines.",
                            "relevance": 0.92,
                            "type": "Supporting"
                        }
                    ]),
                    factors_json=json.dumps({
                        "evidence_strength": 40.0,
                        "claim_specificity": 60.0,
                        "source_reliability": 15.0,
                        "contradictory_evidence": 55.0,
                        "missing_information": 45.0
                    })
                ))

            if ntpc:
                # Benchmark 4: NTPC - Unsupported Claim
                db.add(ClaimAnalysis(
                    company_id=ntpc.id,
                    claim_text="Zero-emission power producer leading India's clean energy transition.",
                    category="Energy",
                    risk_score=78.4,
                    verdict_status="High Risk",
                    explanation="Broad claims of zero-emission generation are unsupported. While NTPC is expanding green capacity, statutory filings show thermal coal remains the core commercial generation asset.",
                    missing_evidence="Retirement schedule for subcritical coal plants commissioned prior to 2010.",
                    contradicting_evidence="Over 85% of total commercial generation remains unabated pulverized coal power.",
                    confidence_score=0.92,
                    citations_json=json.dumps([
                        {
                            "doc_name": "NTPC_Integrated_Report_FY24-25.pdf",
                            "page": 72,
                            "section": "Power Generation Portfolio & Fuel Mix",
                            "snippet": "Total installed commercial capacity stood at 73,824 MW, with thermal coal accounting for 87.2% of total electricity generation in FY24.",
                            "relevance": 0.95,
                            "type": "Contradicting"
                        }
                    ]),
                    factors_json=json.dumps({
                        "evidence_strength": 85.0,
                        "claim_specificity": 80.0,
                        "source_reliability": 15.0,
                        "contradictory_evidence": 85.0,
                        "missing_information": 65.0
                    })
                ))

            db.commit()
    except Exception as e:
        print("Error during database seeding:", e)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: execute database tables initialization & seed data
    seed_database()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="GreenClaim AI API",
    description="Evidence-Grounded Greenwashing Detection and Analysis Platform using RAG and BRSR Disclosures",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development with React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev (http://localhost:5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Sub-routers
app.include_router(companies_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(claims_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": "GreenClaim AI API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_v1_endpoints": [
            "/api/v1/companies",
            "/api/v1/documents/upload",
            "/api/v1/claims/analyze",
            "/api/v1/claims/history"
        ]
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "GreenClaim AI", "rag_engine": "active"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
