from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas.auth_schemas import UserLoginRequest, UserCreateRequest, UserResponse, TokenResponse
from backend.auth.security import verify_password, hash_password
from backend.auth.jwt_handler import create_access_token
from backend.auth.dependencies import get_current_user, get_current_admin
from backend.database import db_service
from backend.config import settings
from typing import Any

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginRequest):
    """Authenticate admin or staff user and return a JWT access token."""
    user = await db_service.get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not verify_password(credentials.password, user.get("passwordHash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "ADMIN"),
            "name": user.get("name", "Admin")
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict[str, Any] = Depends(get_current_user)):
    """Retrieve currently logged in admin user profile."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
    )

@router.post("/register", response_model=UserResponse)
async def register_staff_user(
    new_user: UserCreateRequest,
    current_admin: dict[str, Any] = Depends(get_current_admin)
):
    """Admin-only endpoint to register additional staff members."""
    existing = await db_service.get_user_by_email(new_user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    hashed = hash_password(new_user.password)
    created = await db_service.create_user(
        email=new_user.email,
        password_hash=hashed,
        name=new_user.name,
        role=new_user.role or "STAFF"
    )
    return UserResponse(
        id=created["id"],
        email=created["email"],
        name=created["name"],
        role=created["role"]
    )

@router.post("/seed-admin")
async def seed_admin_endpoint():
    """Helper endpoint to reset/ensure demo admin credentials exist for setup."""
    existing = await db_service.get_user_by_email(settings.ADMIN_DEFAULT_EMAIL)
    if not existing:
        hashed = hash_password(settings.ADMIN_DEFAULT_PASSWORD)
        await db_service.create_user(
            email=settings.ADMIN_DEFAULT_EMAIL,
            password_hash=hashed,
            name=settings.ADMIN_DEFAULT_NAME,
            role="ADMIN"
        )
    return {
        "message": "Admin account ready",
        "email": settings.ADMIN_DEFAULT_EMAIL,
        "defaultPassword": settings.ADMIN_DEFAULT_PASSWORD
    }
