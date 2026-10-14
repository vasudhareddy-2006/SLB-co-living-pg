from fastapi import APIRouter, Depends
from typing import Any
from backend.schemas.lead_schemas import LeadStatsResponse
from backend.auth.dependencies import get_current_admin
from backend.database import db_service

router = APIRouter(prefix="/api/stats", tags=["Dashboard Statistics"])

@router.get("", response_model=LeadStatsResponse)
async def get_dashboard_statistics(
    current_admin: dict[str, Any] = Depends(get_current_admin)
):
    """Protected Endpoint: Get counts of leads by status."""
    stats = await db_service.get_stats()
    return LeadStatsResponse(**stats)
