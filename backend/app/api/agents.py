"""Agents API Router"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.schemas import AgentStatus, AgentCommand
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter()
orchestrator = AgentOrchestrator()


@router.get("/", response_model=List[dict])
async def list_agents():
    return orchestrator.get_status()


@router.post("/{agent_id}/command")
async def command_agent(agent_id: str, cmd: AgentCommand):
    agent = orchestrator.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if cmd.command == "stop":
        await agent.stop()
    elif cmd.command == "start":
        await agent.start()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {cmd.command}")
    return {"agent_id": agent_id, "command": cmd.command, "status": "executed"}


@router.get("/count")
async def agent_count():
    return {"active": orchestrator.active_agent_count(), "total": len(orchestrator.agents)}
