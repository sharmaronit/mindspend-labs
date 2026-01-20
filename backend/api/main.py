from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import io
import csv
from datetime import datetime

from backend.ingestion.parser import parse_csv_bytes
from backend.analysis.detection import analyze_transactions
from backend.insights.engine import synthesize_insights
from backend.challenges.engine import propose_challenges
from backend.integrations.sheets import SheetsClient
from backend.integrations.firebase import FirebaseClient
from backend.insights.summary import make_summary
from models.schema import Transaction, AnalysisResult, FullAnalysisResponse
from models.schema import ExportRequest, ExportResponse, AnalyzeExportRequest, AnalyzeExportResponse
from configs.settings import CORS_ORIGINS, GOOGLE_SHEETS_CREDENTIALS, FIREBASE_SERVICE_ACCOUNT, FIREBASE_PROJECT_ID, REQUIRE_AUTH, DEV_BYPASS_TOKEN
import logging

app = FastAPI()
logger = logging.getLogger("pfba")
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firebase_client = FirebaseClient(project_id=FIREBASE_PROJECT_ID, service_account_path=FIREBASE_SERVICE_ACCOUNT)
sheets_client = SheetsClient(credentials_json=GOOGLE_SHEETS_CREDENTIALS)

def _get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1]
    return None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest", response_model=List[Transaction])
async def ingest(request: Request, file: UploadFile = File(...)):
    if REQUIRE_AUTH:
        token = _get_bearer_token(request)
        if DEV_BYPASS_TOKEN and token == DEV_BYPASS_TOKEN:
            pass
        elif not firebase_client.verify_token(token or ""):
            raise HTTPException(status_code=401, detail="Unauthorized")
    content = await file.read()
    if content and len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    transactions = parse_csv_bytes(content)
    return transactions

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: Request, transactions: List[Transaction]):
    if REQUIRE_AUTH:
        token = _get_bearer_token(request)
        if DEV_BYPASS_TOKEN and token == DEV_BYPASS_TOKEN:
            pass
        elif not firebase_client.verify_token(token or ""):
            raise HTTPException(status_code=401, detail="Unauthorized")
    result = analyze_transactions(transactions)
    if not transactions:
        raise HTTPException(status_code=422, detail="No transactions provided")
    return result

@app.post("/analyze_full", response_model=FullAnalysisResponse)
async def analyze_full(request: Request, transactions: List[Transaction]):
    if REQUIRE_AUTH:
        token = _get_bearer_token(request)
        if DEV_BYPASS_TOKEN and token == DEV_BYPASS_TOKEN:
            pass
        elif not firebase_client.verify_token(token or ""):
            raise HTTPException(status_code=401, detail="Unauthorized")
    if not transactions:
        raise HTTPException(status_code=422, detail="No transactions provided")
    base = analyze_transactions(transactions)
    insights = synthesize_insights(base.patterns, base.triggers)
    challenges = propose_challenges(insights)
    return FullAnalysisResponse(
        patterns=base.patterns,
        triggers=base.triggers,
        insights=insights,
        challenges=challenges,
    )

@app.post("/export/sheets", response_model=ExportResponse)
async def export_sheets(request: Request, req: ExportRequest):
    if REQUIRE_AUTH:
        token = _get_bearer_token(request)
        if not firebase_client.verify_token(token or ""):
            raise HTTPException(status_code=401, detail="Unauthorized")
    url = sheets_client.export_summary(user_id=req.user_id, summary=req.summary)
    return ExportResponse(url=url)

@app.post("/analyze_export", response_model=AnalyzeExportResponse)
async def analyze_export(request: Request, req: AnalyzeExportRequest):
    if REQUIRE_AUTH:
        token = _get_bearer_token(request)
        if DEV_BYPASS_TOKEN and token == DEV_BYPASS_TOKEN:
            pass
        elif not firebase_client.verify_token(token or ""):
            raise HTTPException(status_code=401, detail="Unauthorized")
    base = analyze_transactions(req.transactions)
    if not req.transactions:
        raise HTTPException(status_code=422, detail="No transactions provided")
    insights = synthesize_insights(base.patterns, base.triggers)
    challenges = propose_challenges(insights)
    full = FullAnalysisResponse(
        patterns=base.patterns,
        triggers=base.triggers,
        insights=insights,
        challenges=challenges,
    )
    summary = make_summary(req.transactions, base.patterns, base.triggers, insights)
    url = sheets_client.export_summary(user_id=req.user_id, summary=summary)
    try:
        firebase_client.save_analysis(user_id=req.user_id, data={"summary": summary, "analysis": full.model_dump()})
    except Exception as e:
        logger.warning(f"Failed to persist analysis: {e}")
    return AnalyzeExportResponse(url=url, summary=summary, analysis=full)
