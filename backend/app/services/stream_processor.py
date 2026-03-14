"""
Real-time transaction stream processor
Consumes from Kafka, scores, persists, and broadcasts alerts
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.schemas.schemas import TransactionIngest, RiskLevel

logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    Consumes transactions from Kafka (or HTTP webhook fallback),
    runs fraud scoring pipeline, persists results.
    """

    def __init__(self):
        self.is_running = False
        self._consumer = None
        self._stats = {
            "processed": 0,
            "flagged": 0,
            "blocked": 0,
            "tx_per_min": 0.0,
        }

    async def start(self):
        self.is_running = True
        logger.info("Stream processor started.")
        # In production: connect to Kafka consumer here
        # self._consumer = AIOKafkaConsumer(
        #     settings.KAFKA_TOPIC_TRANSACTIONS,
        #     bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        # )
        # await self._consumer.start()
        # await self._consume_loop()

    async def stop(self):
        self.is_running = False
        if self._consumer:
            await self._consumer.stop()
        logger.info("Stream processor stopped.")

    async def process_transaction(self, raw: dict) -> dict:
        """
        Full pipeline:
        1. Parse & validate
        2. Load account history from Redis cache
        3. Run ML scoring
        4. Run agent sweep
        5. Persist to DB
        6. Publish alert if high risk
        7. Return enriched transaction
        """
        from app.services.fraud_model import fraud_model
        from app.agents.orchestrator import AgentOrchestrator

        tx = TransactionIngest(**raw)
        self._stats["processed"] += 1

        # 1. Fetch account history (Redis or DB)
        account_history = await self._get_account_history(tx.account_id)
        device_history = await self._get_device_history(tx.account_id)
        merchant_stats = await self._get_merchant_stats(tx.merchant_id or "")

        # 2. ML Scoring
        risk_score, triggered_features = await fraud_model.score(
            tx, account_history, device_history, merchant_stats
        )
        risk_level = fraud_model.level_from_score(risk_score)

        # 3. Agent sweep
        orchestrator = AgentOrchestrator()
        tx_dict = tx.model_dump()
        tx_dict["risk_score"] = risk_score
        agent_findings = await orchestrator.scan_transaction(tx_dict)

        # 4. Build result
        result = {
            **tx.model_dump(),
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "features_triggered": triggered_features,
            "agent_findings": agent_findings,
            "processed_at": datetime.utcnow().isoformat(),
        }

        # 5. Track stats
        if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            self._stats["flagged"] += 1

        # 6. Publish alert to Kafka (if risk is high enough)
        if risk_level == RiskLevel.CRITICAL:
            await self._publish_alert(result)
            self._stats["blocked"] += 1

        return result

    async def _get_account_history(self, account_id: str) -> list:
        # In production: Redis LRANGE or DB query with time filter
        return []

    async def _get_device_history(self, account_id: str) -> list:
        return []

    async def _get_merchant_stats(self, merchant_id: str) -> dict:
        return {"risk_score": 0.1}

    async def _publish_alert(self, transaction: dict):
        # In production: AIOKafkaProducer to settings.KAFKA_TOPIC_ALERTS
        logger.warning(
            f"FRAUD ALERT: {transaction['external_id']} | "
            f"Score: {transaction['risk_score']:.2%} | "
            f"Amount: ${transaction['amount']:,.2f}"
        )

    def get_stats(self) -> dict:
        return self._stats
