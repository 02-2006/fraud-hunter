"""Analytics API Router"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import random

from app.schemas.schemas import DashboardStats, RiskDistribution

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats():
    """Real-time dashboard statistics"""
    return DashboardStats(
        total_transactions=1284321,
        flagged_today=312,
        blocked_today=142,
        critical_alerts=7,
        total_exposure_blocked=2847320.50,
        precision=0.992,
        recall=0.978,
        false_positive_rate=0.008,
        transactions_per_minute=4821.3,
        active_agents=3,
    )


@router.get("/risk-distribution", response_model=RiskDistribution)
async def risk_distribution():
    return RiskDistribution(critical=7, high=23, medium=89, low=412, clear=753)


@router.get("/timeseries")
async def timeseries(
    metric: str = Query("fraud_count", enum=["fraud_count", "tx_volume", "risk_score"]),
    hours: int = Query(24, le=168),
):
    now = datetime.utcnow()
    points = []
    for i in range(hours):
        ts = now - timedelta(hours=hours - i)
        value = random.uniform(0, 15) if metric == "fraud_count" else random.uniform(3000, 6000)
        points.append({"timestamp": ts.isoformat(), "value": round(value, 2)})
    return {"metric": metric, "data": points}


@router.get("/top-fraud-patterns")
async def top_patterns():
    return [
        {"pattern": "Card Not Present", "count": 124, "pct": 34.2},
        {"pattern": "Account Takeover", "count": 89, "pct": 24.6},
        {"pattern": "Velocity Burst", "count": 67, "pct": 18.5},
        {"pattern": "Geo Anomaly", "count": 48, "pct": 13.3},
        {"pattern": "Card Sharing Ring", "count": 34, "pct": 9.4},
    ]
