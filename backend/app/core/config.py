"""
Core configuration — reads from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FraudHunter AI"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fraud:fraud@localhost:5432/fraudhunter"
    REDIS_URL: str = "redis://localhost:6379"

    # Kafka / Stream
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_TRANSACTIONS: str = "transactions.raw"
    KAFKA_TOPIC_ALERTS: str = "fraud.alerts"

    # AI / Claude
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # ML Model
    MODEL_PATH: str = "./models/fraud_model.pkl"
    RISK_THRESHOLD_CRITICAL: float = 0.90
    RISK_THRESHOLD_HIGH: float = 0.70
    RISK_THRESHOLD_MEDIUM: float = 0.40

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Allow all origins for easier deployment

    # Agent settings
    AGENT_SCAN_INTERVAL_MS: int = 200
    MAX_CONCURRENT_AGENTS: int = 10

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 1000

    class Config:
        env_file = ".env"


settings = Settings()
