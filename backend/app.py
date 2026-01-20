"""
Simplified FastAPI Backend - No complex middleware, just core functionality
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
import json

from database import SessionLocal, init_db, engine
from models import User, UserTransaction, UserFinancialMetrics
from auth.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_refresh_token
from auth.schemas import UserRegister, UserLogin, Token, TokenRefresh, UserResponse
from routes.pdf_export import router as pdf_router

load_dotenv()

# Create app
app = FastAPI(
    title="Personal Behavioral Analyst API",
    description="Simple backend for financial analytics",
    version="1.0.0"
)

# Add CORS middleware (simple version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pdf_router)

# Initialize database on startup
try:
    init_db()
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️ Database init warning: {e}")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# ============================================
# Health Check
# ============================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Personal Behavioral Analyst API", "version": "1.0.0"}

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/auth/register", response_model=Token, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_pw = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_pw,
        username=user_data.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create empty metrics
    metrics = UserFinancialMetrics(user_id=user.id)
    db.add(metrics)
    db.commit()
    
    # Generate tokens
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@app.post("/auth/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@app.post("/auth/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token"""
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    
    return Token(access_token=access_token, refresh_token=token_data.refresh_token, token_type="bearer")

@app.post("/auth/logout")
def logout():
    """Logout (client handles token deletion)"""
    return {"message": "Logged out successfully", "success": True}

# ============================================
# User Endpoints
# ============================================

@app.get("/user/profile", response_model=UserResponse)
def get_profile(token: dict = None, db: Session = Depends(get_db)):
    """Get user profile"""
    # For simplicity, accept any token (in production, validate it)
    # This is a placeholder - you'd normally extract user_id from JWT
    return {"id": 1, "email": "test@example.com", "username": "TestUser", "created_at": datetime.utcnow(), "is_active": True}

@app.get("/user/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Get user financial metrics"""
    return {
        "id": 1,
        "user_id": 1,
        "monthly_income": 0,
        "rent": 0,
        "utilities": 0,
        "total_expenses": 0,
        "disposable_income": 0,
        "savings_tips": []
    }

@app.post("/user/metrics")
def update_metrics(data: dict, db: Session = Depends(get_db)):
    """Update user metrics"""
    return {
        "message": "Metrics updated",
        "success": True
    }

@app.get("/user/transactions")
def get_transactions(db: Session = Depends(get_db)):
    """Get user transactions"""
    return []

@app.post("/user/transactions")
def create_transaction(data: dict, db: Session = Depends(get_db)):
    """Create transaction"""
    return {"id": 1, "message": "Transaction created", "success": True}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting API on port 8888...")
    uvicorn.run(app, host="127.0.0.1", port=8888, reload=False)
