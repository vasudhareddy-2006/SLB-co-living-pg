from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Any
from backend.schemas.lead_schemas import (
    LeadCreateRequest,
    LeadUpdateRequest,
    LeadResponse,
)
from backend.auth.dependencies import get_current_admin
from backend.database import db_service

router = APIRouter(prefix="/api/leads", tags=["Call-back Leads"])

@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_callback_request(payload: LeadCreateRequest):
    """
    Public Endpoint:
    Visitors who are interested in SLB Coliving submit this form to request a call back.
    """
    try:
        lead = await db_service.create_lead(
            full_name=payload.fullName,
            phone=payload.phone,
            room_type=payload.roomType,
            move_in_date=payload.moveInDate,
            preferred_call_time=payload.preferredCallTime or "ASAP",
            requirements=payload.requirements,
        )
        return LeadResponse(**lead)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to register your call-back enquiry: {str(e)}",
        )

@router.get("", response_model=list[LeadResponse])
async def list_callback_leads(
    status: Optional[str] = Query(None, description="Filter by status: PENDING_CALL, CALLED, VISIT_SCHEDULED, BOOKED"),
    search: Optional[str] = Query(None, description="Search by lead name or phone number"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: dict[str, Any] = Depends(get_current_admin),
):
    """
    Protected Endpoint:
    PG Staff/Admin can view all call-back requests, filter by status, and search.
    """
    leads = await db_service.get_leads(status=status, search=search, limit=limit, offset=offset)
    return [LeadResponse(**lead) for lead in leads]

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_callback_lead(
    lead_id: str,
    current_admin: dict[str, Any] = Depends(get_current_admin),
):
    """Protected Endpoint: Get details of a specific lead."""
    lead = await db_service.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return LeadResponse(**lead)

@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_callback_lead(
    lead_id: str,
    payload: LeadUpdateRequest,
    current_admin: dict[str, Any] = Depends(get_current_admin),
):
    """
    Protected Endpoint:
    Update lead status (e.g. marked as CALLED, VISIT_SCHEDULED, BOOKED) and internal notes.
    """
    updated = await db_service.update_lead(
        lead_id=lead_id,
        status=payload.status,
        admin_notes=payload.adminNotes,
        assigned_to_id=payload.assignedToId,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or update failed",
        )
    return LeadResponse(**updated)

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_callback_lead(
    lead_id: str,
    current_admin: dict[str, Any] = Depends(get_current_admin),
):
    """Protected Endpoint: Remove an enquiry or archive it."""
    success = await db_service.delete_lead(lead_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or delete failed",
        )
    return None
