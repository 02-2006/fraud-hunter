"""
FraudHunter AI — Test Suite
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.fraud_model import FeatureEngineer, FraudDetectionModel
from app.agents.orchestrator import TxSweeperAgent, GeoSentryAgent, PatternNetAgent
from app.schemas.schemas import TransactionIngest, RiskLevel


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_transaction():
    return TransactionIngest(
        external_id="TEST-001",
        account_id="ACC-12345",
        merchant_id="MERCH-99",
        merchant_name="Amazon",
        amount=150.00,
        currency="USD",
        country_origin="US",
        country_merchant="US",
        ip_address="192.168.1.1",
        device_fingerprint="abc123",
        card_last4="4242",
        is_card_present=True,
    )


@pytest.fixture
def high_risk_transaction():
    return TransactionIngest(
        external_id="TEST-RISK-001",
        account_id="ACC-99999",
        merchant_id="MERCH-CRYPTO",
        merchant_name="Unknown Crypto Exchange",
        amount=12500.00,
        currency="USD",
        country_origin="NG",
        country_merchant="US",
        ip_address="41.203.0.1",
        device_fingerprint="new-unknown-device",
        card_last4="0000",
        is_card_present=False,
    )


@pytest.fixture
def account_history():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    return [
        {"amount": 120.0, "timestamp": now - timedelta(days=5), "merchant_id": "MERCH-AMAZON"},
        {"amount": 85.0, "timestamp": now - timedelta(days=10), "merchant_id": "MERCH-UBER"},
        {"amount": 210.0, "timestamp": now - timedelta(days=20), "merchant_id": "MERCH-NETFLIX"},
    ]


# ─── Feature Engineering Tests ───────────────────────────────────────────────

class TestFeatureEngineer:

    @pytest.mark.asyncio
    async def test_country_mismatch_detected(self, high_risk_transaction, account_history):
        fe = FeatureEngineer()
        fv = await fe.extract(high_risk_transaction, account_history, [], {})
        assert fv.country_mismatch is True

    @pytest.mark.asyncio
    async def test_no_mismatch_same_country(self, sample_transaction, account_history):
        fe = FeatureEngineer()
        fv = await fe.extract(sample_transaction, account_history, [], {})
        assert fv.country_mismatch is False

    @pytest.mark.asyncio
    async def test_new_device_detected(self, sample_transaction, account_history):
        fe = FeatureEngineer()
        known_devices = ["device-old-1", "device-old-2"]
        fv = await fe.extract(sample_transaction, account_history, known_devices, {})
        assert fv.is_new_device is True

    @pytest.mark.asyncio
    async def test_known_device_not_flagged(self, sample_transaction, account_history):
        fe = FeatureEngineer()
        known_devices = ["abc123"]  # matches sample_transaction fingerprint
        fv = await fe.extract(sample_transaction, account_history, known_devices, {})
        assert fv.is_new_device is False

    @pytest.mark.asyncio
    async def test_amount_zscore_computed(self, high_risk_transaction, account_history):
        fe = FeatureEngineer()
        fv = await fe.extract(high_risk_transaction, account_history, [], {})
        # $12,500 vs avg ~$138 = very high zscore
        assert fv.amount_zscore > 5.0

    @pytest.mark.asyncio
    async def test_feature_array_shape(self, sample_transaction, account_history):
        fe = FeatureEngineer()
        fv = await fe.extract(sample_transaction, account_history, [], {})
        arr = fe.to_array(fv)
        assert arr.shape == (20,)


# ─── ML Model Tests ───────────────────────────────────────────────────────────

class TestFraudModel:

    @pytest.mark.asyncio
    async def test_high_risk_tx_scores_high(self, high_risk_transaction):
        model = FraudDetectionModel()
        score, findings = await model.score(high_risk_transaction, [], [], {})
        assert score >= 0.7, f"Expected high risk score, got {score}"
        assert len(findings) > 0

    @pytest.mark.asyncio
    async def test_normal_tx_scores_low(self, sample_transaction, account_history):
        model = FraudDetectionModel()
        score, findings = await model.score(sample_transaction, account_history, ["abc123"], {"risk_score": 0.05})
        assert score < 0.5, f"Expected low risk score, got {score}"

    def test_risk_level_mapping(self):
        model = FraudDetectionModel()
        assert model.level_from_score(0.95) == RiskLevel.CRITICAL
        assert model.level_from_score(0.75) == RiskLevel.HIGH
        assert model.level_from_score(0.50) == RiskLevel.MEDIUM
        assert model.level_from_score(0.20) == RiskLevel.LOW
        assert model.level_from_score(0.05) == RiskLevel.CLEAR

    @pytest.mark.asyncio
    async def test_velocity_burst_flagged(self):
        model = FraudDetectionModel()
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        history = [{"amount": 100, "timestamp": now - timedelta(minutes=i), "merchant_id": "M"} for i in range(20)]
        tx = TransactionIngest(external_id="VEL-001", account_id="ACC-VEL", amount=100, is_card_present=True)
        score, findings = await model.score(tx, history, [], {})
        assert any("velocity" in f.lower() or "burst" in f.lower() for f in findings)


# ─── Agent Tests ──────────────────────────────────────────────────────────────

class TestTxSweeperAgent:

    @pytest.mark.asyncio
    async def test_flags_large_amount(self):
        agent = TxSweeperAgent("test-sweeper", "tx_sweeper")
        await agent.start()
        result = await agent.scan({"amount": 15000, "is_card_present": True, "count_velocity_1h": 0})
        assert result is not None
        assert "amount_over_10k" in result["rules_triggered"]

    @pytest.mark.asyncio
    async def test_flags_velocity_burst(self):
        agent = TxSweeperAgent("test-sweeper", "tx_sweeper")
        await agent.start()
        result = await agent.scan({"amount": 100, "count_velocity_1h": 20, "is_card_present": True})
        assert result is not None
        assert "velocity_burst" in result["rules_triggered"]

    @pytest.mark.asyncio
    async def test_clears_normal_transaction(self):
        agent = TxSweeperAgent("test-sweeper", "tx_sweeper")
        await agent.start()
        result = await agent.scan({"amount": 50, "count_velocity_1h": 2, "is_card_present": True, "is_new_device": False})
        assert result is None


class TestGeoSentryAgent:

    @pytest.mark.asyncio
    async def test_flags_high_risk_country(self):
        agent = GeoSentryAgent("test-geo", "geo_sentry")
        await agent.start()
        result = await agent.scan({"country_origin": "NG", "country_merchant": "US", "geo_distance_km": 0, "time_since_last_tx_min": 999})
        assert result is not None

    @pytest.mark.asyncio
    async def test_flags_impossible_travel(self):
        agent = GeoSentryAgent("test-geo", "geo_sentry")
        await agent.start()
        result = await agent.scan({"country_origin": "US", "country_merchant": "US", "geo_distance_km": 8000, "time_since_last_tx_min": 15})
        assert result is not None
        assert any("impossible" in f.lower() for f in result["findings"])

    @pytest.mark.asyncio
    async def test_clears_domestic_transaction(self):
        agent = GeoSentryAgent("test-geo", "geo_sentry")
        await agent.start()
        result = await agent.scan({"country_origin": "US", "country_merchant": "US", "geo_distance_km": 10, "time_since_last_tx_min": 120})
        assert result is None


class TestPatternNetAgent:

    @pytest.mark.asyncio
    async def test_detects_card_sharing_ring(self):
        agent = PatternNetAgent("test-pattern", "pattern_net")
        await agent.start()
        device = "shared-device-abc"
        # Simulate 6 different accounts on same device
        for i in range(6):
            result = await agent.scan({"account_id": f"ACC-{i}", "device_fingerprint": device, "card_last4": f"{i}000"})
        assert result is not None
        assert result["pattern"] == "card_sharing_ring"
        assert result["accounts_involved"] >= 5


# ─── API Integration Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_ingest_valid_transaction():
    tx_data = {
        "external_id": "PYTEST-001",
        "account_id": "ACC-TEST",
        "amount": 99.99,
        "currency": "USD",
        "is_card_present": True,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transactions/ingest", json=tx_data)
    assert resp.status_code == 202
    data = resp.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0


@pytest.mark.asyncio
async def test_ingest_rejects_negative_amount():
    tx_data = {
        "external_id": "PYTEST-NEG",
        "account_id": "ACC-TEST",
        "amount": -100,
        "is_card_present": True,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transactions/ingest", json=tx_data)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_analytics_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_transactions" in data
    assert data["precision"] <= 1.0


@pytest.mark.asyncio
async def test_agents_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/agents/")
    assert resp.status_code == 200
    agents = resp.json()
    assert isinstance(agents, list)
