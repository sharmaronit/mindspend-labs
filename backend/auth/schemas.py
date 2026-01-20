"""
Pydantic Schemas for Request/Response Validation
- Request bodies
- Response models
- Data validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

# ============================================
# Authentication Schemas
# ============================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserRegisterWithData(UserRegister):
    """User registration with guest data migration"""
    guest_data: dict = Field(..., description="Guest transaction data to migrate")


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class ForgotPassword(BaseModel):
    """Password reset request"""
    email: EmailStr


class ResetPassword(BaseModel):
    """Password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class ChangePassword(BaseModel):
    """Change password request (requires current password)"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UpdateProfile(BaseModel):
    """Update user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    """User data response"""
    id: int
    email: str
    username: Optional[str]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# ============================================
# Transaction Schemas
# ============================================

class TransactionCreate(BaseModel):
    """Create transaction"""
    date: str
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Transaction response"""
    id: int
    user_id: int
    date: str
    amount: float
    category: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Financial Metrics Schemas
# ============================================

class FinancialMetricsUpdate(BaseModel):
    """Update financial metrics"""
    monthly_income: Optional[float] = Field(None, ge=0)
    rent: Optional[float] = Field(None, ge=0)
    utilities: Optional[float] = Field(None, ge=0)
    tuition: Optional[float] = Field(None, ge=0)
    loans: Optional[float] = Field(None, ge=0)
    insurance: Optional[float] = Field(None, ge=0)
    subscriptions: Optional[float] = Field(None, ge=0)
    other_expenses: Optional[float] = Field(None, ge=0)


class FinancialMetricsResponse(BaseModel):
    """Financial metrics response"""
    id: int
    user_id: int
    monthly_income: float
    rent: float
    utilities: float
    tuition: float
    loans: float
    insurance: float
    subscriptions: float
    other_expenses: float
    total_expenses: float
    disposable_income: float
    savings_tips: Optional[str]
    highest_category: Optional[str]
    highest_amount: float
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Analysis Schemas
# ============================================

class AnalysisResponse(BaseModel):
    """Analysis data response"""
    id: int
    user_id: int
    analysis_type: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Generic Responses
# ============================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    success: bool = False
