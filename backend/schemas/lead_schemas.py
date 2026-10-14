from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class LeadCreateRequest(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=100, description="Full name of interested visitor")
    phone: str = Field(..., description="10-15 digit phone number")
    roomType: str = Field(..., description="Single sharing, Double sharing, Triple sharing, or Other / not sure")
    moveInDate: str = Field(..., description="Expected check-in date (YYYY-MM-DD)")
    preferredCallTime: Optional[str] = Field("ASAP", description="ASAP, Morning, Afternoon, Evening")
    requirements: Optional[str] = Field(None, max_length=1000, description="Any specific notes or questions")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean_phone = re.sub(r"[\s()\-]", "", v)
        if not re.match(r"^\+?[0-9]{10,15}$", clean_phone):
            raise ValueError("Phone number must contain 10 to 15 digits.")
        return clean_phone

class LeadUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="PENDING_CALL, CALLED, VISIT_SCHEDULED, BOOKED, CANCELLED")
    adminNotes: Optional[str] = Field(None, description="Staff follow-up notes")
    assignedToId: Optional[str] = None

class LeadResponse(BaseModel):
    id: str
    fullName: str
    phone: str
    roomType: str
    moveInDate: str
    preferredCallTime: str
    requirements: Optional[str] = None
    status: str
    adminNotes: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class LeadStatsResponse(BaseModel):
    total: int
    pendingCalls: int
    called: int
    visitsScheduled: int
    booked: int
