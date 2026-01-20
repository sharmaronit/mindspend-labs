"""
JWT Authentication Dependency
- Extracts and validates JWT from Authorization header
- Used as FastAPI dependency for protected routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.security import verify_access_token

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Extract and verify JWT access token from Authorization header.
    
    Usage in routes:
        @router.get("/protected")
        def protected_route(token: dict = Depends(get_current_user_token)):
            user_id = token.get("user_id")
            ...
    
    Raises:
        401 Unauthorized if token is invalid or expired
    """
    token = credentials.credentials
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload
