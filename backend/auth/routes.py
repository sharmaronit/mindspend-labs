"""
Authentication Routes
- User registration
- Login
- Token refresh
- Logout
- Password reset (forgot/reset)
- Guest data migration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import json

from database import get_db
from models import User, PasswordResetToken, GuestDataMigration, UserTransaction, UserFinancialMetrics
from auth.schemas import (
    UserRegister, UserRegisterWithData, UserLogin, Token,
    TokenRefresh, ForgotPassword, ResetPassword, ChangePassword,
    UserResponse, MessageResponse
)
from auth.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_refresh_token, create_password_reset_token,
    verify_password_reset_token, verify_access_token
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Rate limiting storage (in production, use Redis)
login_attempts = {}


# ============================================
# Helper Functions
# ============================================

def check_rate_limit(request: Request, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """
    Check if IP has exceeded rate limit.
    Returns True if allowed, False if rate limited.
    """
    client_ip = request.client.host
    current_time = datetime.utcnow()
    
    if client_ip not in login_attempts:
        login_attempts[client_ip] = []
    
    # Remove old attempts outside the window
    login_attempts[client_ip] = [
        attempt for attempt in login_attempts[client_ip]
        if current_time - attempt < timedelta(minutes=window_minutes)
    ]
    
    # Check if limit exceeded
    if len(login_attempts[client_ip]) >= max_attempts:
        return False
    
    # Add current attempt
    login_attempts[client_ip].append(current_time)
    return True


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, username: Optional[str] = None) -> User:
    """Create new user"""
    hashed_pw = hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_pw,
        username=username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================
# Authentication Endpoints
# ============================================

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Strong password (8+ chars, uppercase, number, special char)
    - **username**: Optional display name
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = create_user(db, user_data.email, user_data.password, user_data.username)
    
    # Create empty financial metrics
    metrics = UserFinancialMetrics(user_id=user.id)
    db.add(metrics)
    db.commit()
    
    # Generate tokens
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/register-with-data", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_with_guest_data(user_data: UserRegisterWithData, db: Session = Depends(get_db)):
    """
    Register user and migrate guest data.
    
    - Migrates guest transactions to user account
    - Tracks migration for audit purposes
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = create_user(db, user_data.email, user_data.password, user_data.username)
    
    # Migrate guest transactions
    guest_transactions = user_data.guest_data.get("transactions", [])
    migrated_count = 0
    
    for trans in guest_transactions:
        transaction = UserTransaction(
            user_id=user.id,
            date=trans.get("date", ""),
            amount=trans.get("amount", 0),
            category=trans.get("category", ""),
            description=trans.get("description")
        )
        db.add(transaction)
        migrated_count += 1
    
    # Track migration
    migration = GuestDataMigration(
        user_id=user.id,
        guest_data=json.dumps(user_data.guest_data),
        transaction_count=migrated_count
    )
    db.add(migration)
    
    # Create financial metrics
    metrics = UserFinancialMetrics(user_id=user.id)
    db.add(metrics)
    
    db.commit()
    
    # Generate tokens
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    - Returns access token (15 min) and refresh token (7 days)
    - Rate limited to 5 attempts per 15 minutes per IP
    """
    # Check rate limit
    if not check_rate_limit(request, max_attempts=5, window_minutes=15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 15 minutes."
        )
    
    # Find user
    user = get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate tokens
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Issues new access token
    - Returns same refresh token
    """
    # Verify refresh token
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=token_data.refresh_token,
        token_type="bearer"
    )


@router.post("/logout", response_model=MessageResponse)
def logout():
    """
    Logout user.
    
    - Client should delete tokens from localStorage
    - Server-side token invalidation would require Redis/database
    """
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPassword, request: Request, db: Session = Depends(get_db)):
    """
    Request password reset link.
    
    - Sends email with reset token
    - Token valid for 1 hour
    - Rate limited to 3 requests per 15 minutes
    """
    # Check rate limit
    if not check_rate_limit(request, max_attempts=3, window_minutes=15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later."
        )
    
    # Find user
    user = get_user_by_email(db, data.email)
    if not user:
        # Don't reveal if email exists
        return MessageResponse(
            message="If that email exists, a password reset link has been sent.",
            success=True
        )
    
    # Generate reset token
    reset_token = create_password_reset_token(user.email)
    
    # Store token in database
    expires_at = datetime.utcnow() + timedelta(hours=1)
    db_token = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    # TODO: Send email with reset link
    # For now, just return success (implement SendGrid later)
    reset_link = f"http://localhost:8000/reset-password.html?token={reset_token}"
    print(f"Password reset link for {user.email}: {reset_link}")
    
    return MessageResponse(
        message="If that email exists, a password reset link has been sent.",
        success=True
    )


def get_current_user_auth(
    token: str = Depends(verify_access_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    Raises 401 if token invalid or user not found.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user_id = token.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user_auth),
    db: Session = Depends(get_db)
):
    """
    Change password (requires current password).
    
    - Validates current password
    - Updates to new password
    - Requires authentication
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    
    return MessageResponse(
        message="Password updated successfully",
        success=True
    )


def _get_current_user(token: dict, db: Session) -> User:
    """Helper function to get current user"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user_id = token.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """
    Reset password using token from email.
    
    - Validates reset token
    - Updates password
    - Marks token as used
    """
    # Verify token
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find token in database
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(data.new_password)
    db_token.used = True
    db.commit()
    
    return MessageResponse(
        message="Password reset successfully",
        success=True
    )
