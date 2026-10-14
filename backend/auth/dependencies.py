from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any
from backend.auth.jwt_handler import decode_access_token
from backend.database import db_service

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict[str, Any]:
    """Dependency to retrieve the current authenticated user from Bearer JWT."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = await db_service.get_user_by_id(user_id)
    if not user:
        # Also check by email if sub was email
        user = await db_service.get_user_by_email(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return user

async def get_current_admin(
    user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Dependency requiring ADMIN role."""
    if user.get("role") not in ("ADMIN", "STAFF"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Staff or Admin role required.",
        )
    return user
