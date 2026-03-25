"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CLEAR = "clear"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    CLEARED = "cleared"
    REVIEWING = "reviewing"


# ─── Transaction Schemas ─────────────────────────────────────────────────────

class TransactionIngest(BaseModel):
    """Incoming transaction from payment processor"""
    external_id: str = Field(..., min_length=1, max_length=64)
    account_id: str = Field(..., min_length=1)
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    country_origin: Optional[str] = Field(None, max_length=2)
    country_merchant: Optional[str] = Field(None, max_length=2)
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    card_last4: Optional[str] = Field(None, max_length=4)
    is_card_present: bool = True
    timestamp: Optional[datetime] = None

    @field_validator("amount")
    @classmethod
    def amount_precision(cls, v):
        return round(v, 2)


class TransactionResponse(BaseModel):
    id: UUID
    external_id: str
    account_id: str
    merchant_name: Optional[str]
    amount: float
    currency: str
    risk_score: float
    risk_level: RiskLevel
    status: TransactionStatus
    agent_findings: Optional[Dict[str, Any]]
    ai_reasoning: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionDecision(BaseModel):
    """Analyst action on a transaction"""
    action: TransactionStatus
    reason: Optional[str] = None
    analyst_id: Optional[str] = None


class FraudScore(BaseModel):
    """ML model output"""
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence: float
    features_triggered: List[str]
    model_version: str


# ─── Alert Schemas ────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    alert_type: str
    severity: RiskLevel
    message: str
    agent_id: str
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Case Schemas ─────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    account_id: str
    fraud_type: str
    transaction_ids: List[UUID]
    notes: Optional[str] = None


class CaseResponse(BaseModel):
    id: UUID
    case_number: str
    account_id: str
    status: str
    total_exposure: float
    fraud_type: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Agent Schemas ────────────────────────────────────────────────────────────

class AgentStatus(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    transactions_scanned: int
    flags_raised: int
    started_at: datetime


class AgentCommand(BaseModel):
    command: str  # "start", "stop", "pause", "configure"
    config: Optional[Dict[str, Any]] = None


# ─── Analytics Schemas ────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_transactions: int
    flagged_today: int
    blocked_today: int
    critical_alerts: int
    total_exposure_blocked: float
    precision: float
    recall: float
    false_positive_rate: float
    transactions_per_minute: float
    active_agents: int


class RiskDistribution(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    clear: int


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float
    label: Optional[str] = None


# ─── AI Investigation ─────────────────────────────────────────────────────────

class InvestigationRequest(BaseModel):
    transaction_id: str
    query: Optional[str] = "Perform full fraud analysis"


class InvestigationResponse(BaseModel):
    transaction_id: str
    risk_verdict: RiskLevel
    confidence: float
    reasoning: str
    key_findings: List[str]
    recommended_action: str
    investigation_time_ms: int
