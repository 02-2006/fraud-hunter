"""
Transactions API Router
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.schemas.schemas import (
    TransactionIngest, TransactionResponse, TransactionDecision,
    InvestigationRequest, InvestigationResponse, FraudScore
)
from app.services.stream_processor import StreamProcessor
from app.agents.orchestrator import AgentOrchestrator, AIInvestigator

router = APIRouter()
logger = logging.getLogger(__name__)

stream_processor = StreamProcessor()
investigator = AIInvestigator()


@router.post("/ingest", response_model=FraudScore, status_code=202)
async def ingest_transaction(
    tx: TransactionIngest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a single transaction for real-time fraud scoring.
    Returns immediate risk score. Full analysis happens async.
    """
    try:
        result = await stream_processor.process_transaction(tx.model_dump())
        return FraudScore(
            transaction_id=tx.external_id,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            confidence=result["risk_score"],
            features_triggered=result.get("features_triggered", []),
            model_version="4.2.0",
        )
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/batch", status_code=202)
async def ingest_batch(
    transactions: List[TransactionIngest],
    background_tasks: BackgroundTasks,
):
    """Batch ingest up to 1000 transactions"""
    if len(transactions) > 1000:
        raise HTTPException(status_code=400, detail="Max batch size is 1000")

    async def process_batch():
        for tx in transactions:
            await stream_processor.process_transaction(tx.model_dump())

    background_tasks.add_task(process_batch)
    return {"accepted": len(transactions), "status": "processing"}


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List transactions with optional risk level filter"""
    # In production: query DB with filters
    return []


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific transaction by ID"""
    raise HTTPException(status_code=404, detail="Transaction not found")


@router.post("/{transaction_id}/decide", response_model=TransactionResponse)
async def decide_transaction(
    transaction_id: UUID,
    decision: TransactionDecision,
    db: AsyncSession = Depends(get_db),
):
    """Analyst decision: block, flag, clear, or review"""
    logger.info(f"Decision on {transaction_id}: {decision.action}")
    # In production: update DB record + trigger downstream actions
    raise HTTPException(status_code=404, detail="Transaction not found")


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_transaction(
    request: InvestigationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Deep AI investigation of a transaction using Claude.
    Returns full reasoning and verdict.
    """
    # In production: load transaction + history from DB
    mock_tx = {
        "external_id": str(request.transaction_id),
        "amount": 8500.00,
        "currency": "USD",
        "merchant_name": "Unknown Crypto Exchange",
        "timestamp": "2026-03-14T03:14:00Z",
        "is_card_present": False,
        "country_origin": "NG",
        "country_merchant": "US",
        "ip_address": "41.203.xxx.xxx",
        "is_new_device": True,
        "risk_score": 0.94,
        "risk_level": "critical",
        "count_velocity_1h": 12,
        "amount_velocity_1h": 24500.00,
    }
    mock_findings = [
        {"agent_id": "TxSweeper-01", "rules_triggered": ["card_not_present_large", "amount_over_10k"]},
        {"agent_id": "GeoSentry-07", "pattern": "geo_anomaly", "findings": ["High-risk country: NG"]},
    ]
    mock_history = {"avg_amount": 120.0, "count": 45, "fraud_flags": 0, "account_age_days": 92}

    return await investigator.investigate(request, mock_tx, mock_findings, mock_history)
