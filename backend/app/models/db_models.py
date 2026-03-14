"""
SQLAlchemy ORM Models
"""
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    JSON, Text, ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CLEAR = "clear"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    CLEARED = "cleared"
    REVIEWING = "reviewing"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(64), index=True, nullable=False)
    merchant_id = Column(String(64), index=True)
    merchant_name = Column(String(256))
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    country_origin = Column(String(2))
    country_merchant = Column(String(2))
    ip_address = Column(String(45))
    device_fingerprint = Column(String(128))
    card_last4 = Column(String(4))
    is_card_present = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Risk scoring
    risk_score = Column(Float, default=0.0)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.CLEAR)
    status = Column(SAEnum(TransactionStatus), default=TransactionStatus.PENDING)

    # Feature vector (for ML audit)
    features = Column(JSON)

    # Agent findings
    agent_findings = Column(JSON)
    ai_reasoning = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    alerts = relationship("Alert", back_populates="transaction")
    case = relationship("FraudCase", back_populates="transactions")

    __table_args__ = (
        Index("ix_tx_account_timestamp", "account_id", "timestamp"),
        Index("ix_tx_risk_level", "risk_level"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("fraud_cases.id"), nullable=True)
    alert_type = Column(String(64), nullable=False)
    severity = Column(SAEnum(RiskLevel), nullable=False)
    message = Column(Text)
    agent_id = Column(String(64))
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="alerts")
    case = relationship("FraudCase", back_populates="alerts")


class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(32), unique=True, index=True)
    account_id = Column(String(64), index=True)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.OPEN)
    total_exposure = Column(Float, default=0.0)
    fraud_type = Column(String(64))
    assigned_to = Column(String(128))
    notes = Column(Text)
    evidence = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="case")
    alerts = relationship("Alert", back_populates="case")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(64), index=True)
    agent_type = Column(String(64))
    transactions_scanned = Column(Integer, default=0)
    flags_raised = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="running")
    metadata = Column(JSON)


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(32))
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    false_positive_rate = Column(Float)
    transactions_evaluated = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow)
