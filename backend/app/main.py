"""
FraudHunter AI - Main FastAPI Application
Autonomous Fraud Detection Engine
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.api import transactions, agents, alerts, analytics, cases
from app.core.config import settings
from app.core.database import init_db
from app.services.stream_processor import StreamProcessor
from app.agents.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stream_processor = StreamProcessor()
orchestrator = AgentOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FraudHunter AI Engine...")
    await init_db()
    asyncio.create_task(stream_processor.start())
    asyncio.create_task(orchestrator.start())
    logger.info("All agents online.")
    yield
    logger.info("Shutting down agents...")
    await stream_processor.stop()
    await orchestrator.stop()


app = FastAPI(
    title="FraudHunter AI",
    description="Autonomous Fraud Detection Engine with AI Agents",
    version="4.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])


# WebSocket for real-time transaction stream
connected_clients: list[WebSocket] = []

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"Client connected. Total: {len(connected_clients)}")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "acknowledged", "data": data})
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(connected_clients)}")


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "agents_running": orchestrator.active_agent_count(),
        "stream_active": stream_processor.is_running,
        "version": "4.2.0",
    }
