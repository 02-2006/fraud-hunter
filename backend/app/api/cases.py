"""Fraud Cases API Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import uuid
from datetime import datetime

from app.core.database import get_db
from app.schemas.schemas import CaseCreate, CaseResponse

router = APIRouter()


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(case: CaseCreate, db: AsyncSession = Depends(get_db)):
    case_num = f"FH-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    return CaseResponse(
        id=uuid.uuid4(),
        case_number=case_num,
        account_id=case.account_id,
        status="open",
        total_exposure=0.0,
        fraud_type=case.fraud_type,
        created_at=datetime.utcnow(),
    )


@router.get("/", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    return []


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=404, detail="Case not found")


@router.post("/{case_id}/escalate")
async def escalate_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    return {"case_id": str(case_id), "status": "escalated", "escalated_at": datetime.utcnow()}
