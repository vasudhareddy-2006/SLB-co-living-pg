from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    role: Optional[str] = "ADMIN"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    createdAt: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
