"""
Autonomous Agent Orchestrator
Manages multiple fraud detection agents and AI-powered investigation
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import anthropic

from app.core.config import settings
from app.schemas.schemas import InvestigationRequest, InvestigationResponse, RiskLevel

logger = logging.getLogger(__name__)

INVESTIGATION_SYSTEM_PROMPT = """You are FraudHunter AI, an expert autonomous fraud detection agent.

You analyze financial transactions and identify fraud patterns with precision. Your job is to:
1. Analyze all provided transaction data, features, and context
2. Identify specific fraud indicators and patterns
3. Cross-reference behavioral anomalies
4. Deliver a clear verdict with reasoning

Output format:
- Be concise and analytical
- List key findings as bullet points
- State confidence level (0-100%)
- Give a clear recommended action: BLOCK, FLAG FOR REVIEW, or CLEAR
- Reference specific data points in your reasoning

You are an autonomous AI agent — you make definitive decisions, not suggestions.
"""


class BaseAgent:
    """Base class for all fraud detection agents"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.is_running = False
        self.transactions_scanned = 0
        self.flags_raised = 0
        self.started_at: Optional[datetime] = None

    async def start(self):
        self.is_running = True
        self.started_at = datetime.utcnow()
        logger.info(f"Agent {self.agent_id} ({self.agent_type}) started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"Agent {self.agent_id} stopped. Scanned: {self.transactions_scanned}, Flagged: {self.flags_raised}")

    async def scan(self, transaction: Dict) -> Optional[Dict]:
        raise NotImplementedError


class TxSweeperAgent(BaseAgent):
    """
    High-throughput transaction sweeper.
    Applies fast rule-based checks on every incoming transaction.
    """
    RULES = [
        ("amount_over_10k", lambda tx: tx.get("amount", 0) > 10000),
        ("velocity_burst", lambda tx: tx.get("count_velocity_1h", 0) > 15),
        ("new_device_high_amount", lambda tx: tx.get("is_new_device") and tx.get("amount", 0) > 500),
        ("card_not_present_large", lambda tx: not tx.get("is_card_present") and tx.get("amount", 0) > 2000),
        ("round_amount_probe", lambda tx: tx.get("amount", 0) in [0.01, 0.10, 1.00]),
    ]

    async def scan(self, transaction: Dict) -> Optional[Dict]:
        self.transactions_scanned += 1
        triggered = []
        for rule_name, rule_fn in self.RULES:
            try:
                if rule_fn(transaction):
                    triggered.append(rule_name)
            except Exception:
                pass

        if triggered:
            self.flags_raised += 1
            return {
                "agent_id": self.agent_id,
                "rules_triggered": triggered,
                "flag_level": "high" if len(triggered) > 2 else "medium",
            }
        return None


class PatternNetAgent(BaseAgent):
    """
    Graph-based ring detection agent.
    Identifies coordinated fraud rings using account relationship graphs.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account_graph: Dict[str, List[str]] = {}  # account -> shared card/device accounts
        self.shared_device_map: Dict[str, List[str]] = {}

    async def scan(self, transaction: Dict) -> Optional[Dict]:
        self.transactions_scanned += 1
        account_id = transaction.get("account_id")
        device = transaction.get("device_fingerprint")
        card = transaction.get("card_last4")

        if device:
            accounts_on_device = self.shared_device_map.get(device, [])
            if account_id not in accounts_on_device:
                accounts_on_device.append(account_id)
            self.shared_device_map[device] = accounts_on_device

            if len(accounts_on_device) >= 5:
                self.flags_raised += 1
                return {
                    "agent_id": self.agent_id,
                    "pattern": "card_sharing_ring",
                    "accounts_involved": len(accounts_on_device),
                    "shared_device": device[-8:] + "...",
                    "confidence": min(0.7 + (len(accounts_on_device) - 5) * 0.05, 0.99),
                }
        return None


class GeoSentryAgent(BaseAgent):
    """
    Geographic anomaly detection agent.
    Flags impossible travel and cross-border patterns.
    """
    HIGH_RISK_COUNTRIES = {"NG", "GH", "RO", "BG", "PK", "VN", "ID"}

    async def scan(self, transaction: Dict) -> Optional[Dict]:
        self.transactions_scanned += 1
        origin = transaction.get("country_origin", "")
        merchant_country = transaction.get("country_merchant", "")

        findings = []
        if origin in self.HIGH_RISK_COUNTRIES:
            findings.append(f"High-risk origin country: {origin}")
        if origin and merchant_country and origin != merchant_country:
            findings.append(f"Cross-border: {origin} → {merchant_country}")
        geo_distance = transaction.get("geo_distance_km", 0)
        time_since = transaction.get("time_since_last_tx_min", 999)
        if geo_distance > 500 and time_since < 60:
            findings.append(f"Impossible travel: {geo_distance:.0f}km in {time_since:.0f} min")

        if findings:
            self.flags_raised += 1
            return {
                "agent_id": self.agent_id,
                "pattern": "geo_anomaly",
                "findings": findings,
                "confidence": 0.75 if len(findings) > 1 else 0.55,
            }
        return None


class VelocityCheckAgent(BaseAgent):
    """Velocity and burst pattern detection"""

    async def scan(self, transaction: Dict) -> Optional[Dict]:
        self.transactions_scanned += 1
        count_1h = transaction.get("count_velocity_1h", 0)
        amount_1h = transaction.get("amount_velocity_1h", 0)

        if count_1h > 20 or amount_1h > 50000:
            self.flags_raised += 1
            return {
                "agent_id": self.agent_id,
                "pattern": "velocity_alert",
                "count_1h": count_1h,
                "amount_1h": amount_1h,
                "confidence": min(0.6 + count_1h * 0.01, 0.98),
            }
        return None


class AIInvestigator:
    """
    Uses Claude API for deep autonomous investigation.
    Called for high-risk transactions needing reasoning.
    """

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def investigate(
        self,
        request: InvestigationRequest,
        transaction_data: Dict,
        agent_findings: List[Dict],
        account_history_summary: Dict,
    ) -> InvestigationResponse:
        start_time = time.monotonic()

        context = f"""
TRANSACTION DATA:
- ID: {transaction_data.get('external_id')}
- Amount: ${transaction_data.get('amount', 0):,.2f} {transaction_data.get('currency', 'USD')}
- Merchant: {transaction_data.get('merchant_name', 'Unknown')}
- Timestamp: {transaction_data.get('timestamp')}
- Card Present: {transaction_data.get('is_card_present')}
- Country Origin: {transaction_data.get('country_origin', 'Unknown')}
- Country Merchant: {transaction_data.get('country_merchant', 'Unknown')}
- IP: {transaction_data.get('ip_address', 'Unknown')}
- New Device: {transaction_data.get('is_new_device', False)}

ML RISK SCORE: {transaction_data.get('risk_score', 0):.1%}
RISK LEVEL: {transaction_data.get('risk_level', 'UNKNOWN')}

AGENT FINDINGS:
{chr(10).join(f"- Agent {f.get('agent_id')}: {f}" for f in agent_findings)}

ACCOUNT HISTORY (30 days):
- Avg transaction: ${account_history_summary.get('avg_amount', 0):,.2f}
- Total transactions: {account_history_summary.get('count', 0)}
- Previous fraud flags: {account_history_summary.get('fraud_flags', 0)}
- Account age days: {account_history_summary.get('account_age_days', 0)}
- Count last 1h: {transaction_data.get('count_velocity_1h', 0)}
- Amount last 1h: ${transaction_data.get('amount_velocity_1h', 0):,.2f}

ANALYST QUERY: {request.query or 'Perform full fraud analysis'}
"""

        message = await self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1000,
            system=INVESTIGATION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}],
        )

        reasoning = message.content[0].text
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # Parse verdict from response
        risk_score = transaction_data.get("risk_score", 0)
        if risk_score >= 0.9:
            verdict = RiskLevel.CRITICAL
            action = "BLOCK IMMEDIATELY"
        elif risk_score >= 0.7:
            verdict = RiskLevel.HIGH
            action = "FLAG FOR MANUAL REVIEW"
        elif risk_score >= 0.4:
            verdict = RiskLevel.MEDIUM
            action = "MONITOR AND FLAG"
        else:
            verdict = RiskLevel.LOW
            action = "CLEAR — CONTINUE MONITORING"

        findings = [f.get("pattern", "") or f.get("rules_triggered", []) for f in agent_findings]
        flat_findings = []
        for f in findings:
            if isinstance(f, list):
                flat_findings.extend(f)
            elif f:
                flat_findings.append(str(f))

        return InvestigationResponse(
            transaction_id=request.transaction_id,
            risk_verdict=verdict,
            confidence=risk_score,
            reasoning=reasoning,
            key_findings=flat_findings,
            recommended_action=action,
            investigation_time_ms=elapsed_ms,
        )


class AgentOrchestrator:
    """Manages lifecycle and coordination of all fraud agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.investigator = AIInvestigator()
        self._running = False
        self._setup_agents()

    def _setup_agents(self):
        self.agents = {
            "TxSweeper-01": TxSweeperAgent("TxSweeper-01", "tx_sweeper"),
            "PatternNet-03": PatternNetAgent("PatternNet-03", "pattern_net"),
            "GeoSentry-07": GeoSentryAgent("GeoSentry-07", "geo_sentry"),
            "VelocityCheck-12": VelocityCheckAgent("VelocityCheck-12", "velocity_check"),
        }

    async def start(self):
        self._running = True
        for agent in self.agents.values():
            await agent.start()
        logger.info(f"Orchestrator started {len(self.agents)} agents.")

    async def stop(self):
        self._running = False
        for agent in self.agents.values():
            await agent.stop()

    async def scan_transaction(self, transaction: Dict) -> List[Dict]:
        """Run all agents on a transaction, collect findings"""
        tasks = [agent.scan(transaction) for agent in self.agents.values() if agent.is_running]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r and not isinstance(r, Exception)]

    def active_agent_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.is_running)

    def get_status(self) -> List[Dict]:
        return [
            {
                "agent_id": a.agent_id,
                "agent_type": a.agent_type,
                "status": "running" if a.is_running else "stopped",
                "transactions_scanned": a.transactions_scanned,
                "flags_raised": a.flags_raised,
                "started_at": a.started_at.isoformat() if a.started_at else None,
            }
            for a in self.agents.values()
        ]
