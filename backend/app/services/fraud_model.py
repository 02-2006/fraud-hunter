"""
Fraud Detection ML Service
Handles feature engineering, model inference, and risk scoring
"""
import numpy as np
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.schemas import TransactionIngest, FraudScore, RiskLevel

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Engineered features for fraud detection"""
    amount: float
    amount_log: float
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    is_night: bool                   # 11pm - 5am
    is_card_present: bool
    country_mismatch: bool
    amount_velocity_1h: float        # sum of tx in last 1hr for account
    count_velocity_1h: int           # count of tx in last 1hr
    amount_velocity_24h: float
    count_velocity_24h: int
    avg_tx_amount_30d: float         # rolling avg for account
    std_tx_amount_30d: float         # rolling std dev
    amount_zscore: float             # how many std devs from mean
    is_new_device: bool
    is_new_merchant: bool
    merchant_risk_score: float       # merchant-level risk (0–1)
    geo_distance_km: float           # distance from last tx location
    time_since_last_tx_min: float


class FeatureEngineer:
    """Computes features from raw transaction + account history"""

    async def extract(
        self,
        tx: TransactionIngest,
        account_history: List[Dict],
        device_history: List[str],
        merchant_stats: Dict,
    ) -> FeatureVector:
        now = tx.timestamp or datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        thirty_days_ago = now - timedelta(days=30)

        recent_1h = [t for t in account_history if t["timestamp"] >= one_hour_ago]
        recent_24h = [t for t in account_history if t["timestamp"] >= one_day_ago]
        recent_30d = [t for t in account_history if t["timestamp"] >= thirty_days_ago]

        amounts_30d = [t["amount"] for t in recent_30d] or [tx.amount]
        avg_amount = np.mean(amounts_30d)
        std_amount = np.std(amounts_30d) or 1.0
        zscore = (tx.amount - avg_amount) / std_amount

        last_tx = account_history[-1] if account_history else None
        time_since_last = (
            (now - last_tx["timestamp"]).total_seconds() / 60
            if last_tx else 999.0
        )

        geo_distance = self._compute_geo_distance(
            tx.ip_address,
            last_tx.get("ip_address") if last_tx else None
        )

        return FeatureVector(
            amount=tx.amount,
            amount_log=np.log1p(tx.amount),
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
            is_weekend=now.weekday() >= 5,
            is_night=now.hour >= 23 or now.hour <= 5,
            is_card_present=tx.is_card_present,
            country_mismatch=(
                tx.country_origin != tx.country_merchant
                if tx.country_origin and tx.country_merchant else False
            ),
            amount_velocity_1h=sum(t["amount"] for t in recent_1h),
            count_velocity_1h=len(recent_1h),
            amount_velocity_24h=sum(t["amount"] for t in recent_24h),
            count_velocity_24h=len(recent_24h),
            avg_tx_amount_30d=avg_amount,
            std_tx_amount_30d=std_amount,
            amount_zscore=zscore,
            is_new_device=tx.device_fingerprint not in device_history,
            is_new_merchant=tx.merchant_id not in [t.get("merchant_id") for t in recent_30d],
            merchant_risk_score=merchant_stats.get("risk_score", 0.1),
            geo_distance_km=geo_distance,
            time_since_last_tx_min=time_since_last,
        )

    def to_array(self, fv: FeatureVector) -> np.ndarray:
        return np.array([
            fv.amount, fv.amount_log, fv.hour_of_day, fv.day_of_week,
            int(fv.is_weekend), int(fv.is_night), int(fv.is_card_present),
            int(fv.country_mismatch), fv.amount_velocity_1h, fv.count_velocity_1h,
            fv.amount_velocity_24h, fv.count_velocity_24h, fv.avg_tx_amount_30d,
            fv.std_tx_amount_30d, fv.amount_zscore, int(fv.is_new_device),
            int(fv.is_new_merchant), fv.merchant_risk_score,
            fv.geo_distance_km, fv.time_since_last_tx_min,
        ], dtype=np.float32)

    def _compute_geo_distance(self, ip1: Optional[str], ip2: Optional[str]) -> float:
        # In production: use MaxMind GeoIP2 to get lat/lon then haversine distance
        # Placeholder: returns 0 if same IP, 999 if very different
        if not ip1 or not ip2:
            return 0.0
        if ip1 == ip2:
            return 0.0
        if ip1.split(".")[0] != ip2.split(".")[0]:
            return 5000.0  # Different /8 block = likely cross-continental
        return 50.0


class FraudDetectionModel:
    """
    Ensemble fraud detection model.
    In production: XGBoost + Isolation Forest + GNN for ring detection.
    """
    def __init__(self):
        self.model = None
        self.model_version = "4.2.0"
        self.feature_engineer = FeatureEngineer()
        self._load_model()

    def _load_model(self):
        try:
            self.model = joblib.load(settings.MODEL_PATH)
            logger.info(f"Loaded model from {settings.MODEL_PATH}")
        except FileNotFoundError:
            logger.warning("No saved model found — using rule-based scorer.")
            self.model = None

    async def score(
        self,
        tx: TransactionIngest,
        account_history: List[Dict],
        device_history: List[str],
        merchant_stats: Dict,
    ) -> Tuple[float, List[str]]:
        """
        Returns (risk_score 0.0–1.0, list of triggered rules/features)
        """
        fv = await self.feature_engineer.extract(
            tx, account_history, device_history, merchant_stats
        )

        if self.model:
            arr = self.feature_engineer.to_array(fv).reshape(1, -1)
            score = float(self.model.predict_proba(arr)[0][1])
        else:
            score = self._rule_based_score(fv)

        triggered = self._explain(fv, score)
        return score, triggered

    def _rule_based_score(self, fv: FeatureVector) -> float:
        """Fallback rule engine when ML model unavailable"""
        score = 0.05

        if fv.amount > 10000:
            score += 0.25
        elif fv.amount > 5000:
            score += 0.15
        elif fv.amount > 1000:
            score += 0.05

        if fv.amount_zscore > 4:
            score += 0.30
        elif fv.amount_zscore > 2.5:
            score += 0.15

        if fv.count_velocity_1h > 10:
            score += 0.35
        elif fv.count_velocity_1h > 5:
            score += 0.20

        if fv.country_mismatch:
            score += 0.20
        if not fv.is_card_present:
            score += 0.10
        if fv.is_night:
            score += 0.05
        if fv.is_new_device:
            score += 0.15
        if fv.geo_distance_km > 1000:
            score += 0.25
        if fv.merchant_risk_score > 0.7:
            score += 0.15

        return min(score, 0.99)

    def _explain(self, fv: FeatureVector, score: float) -> List[str]:
        """Return human-readable list of triggered risk factors"""
        findings = []
        if fv.amount_zscore > 2.5:
            findings.append(f"Amount ${fv.amount:.0f} is {fv.amount_zscore:.1f}σ above account baseline")
        if fv.count_velocity_1h > 5:
            findings.append(f"Velocity burst: {fv.count_velocity_1h} transactions in last hour")
        if fv.country_mismatch:
            findings.append("Country mismatch between cardholder and merchant")
        if fv.is_new_device:
            findings.append("Unrecognized device fingerprint")
        if fv.geo_distance_km > 1000:
            findings.append(f"Geo anomaly: {fv.geo_distance_km:.0f}km from last known location")
        if fv.is_night:
            findings.append(f"Unusual hour: {fv.hour_of_day}:00 local time")
        if not fv.is_card_present:
            findings.append("Card-not-present transaction")
        if fv.merchant_risk_score > 0.7:
            findings.append("High-risk merchant category")
        if fv.time_since_last_tx_min < 2:
            findings.append(f"Rapid succession: {fv.time_since_last_tx_min:.1f} min since last tx")
        return findings

    def level_from_score(self, score: float) -> RiskLevel:
        if score >= settings.RISK_THRESHOLD_CRITICAL:
            return RiskLevel.CRITICAL
        if score >= settings.RISK_THRESHOLD_HIGH:
            return RiskLevel.HIGH
        if score >= settings.RISK_THRESHOLD_MEDIUM:
            return RiskLevel.MEDIUM
        if score > 0.1:
            return RiskLevel.LOW
        return RiskLevel.CLEAR


# Singleton
fraud_model = FraudDetectionModel()
