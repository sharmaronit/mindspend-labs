#!/usr/bin/env python
"""Simple backend server - run this directly"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import SessionLocal, init_db
from auth.schemas import UserRegister, UserLogin, Token
from auth.security import hash_password, verify_password, create_access_token, create_refresh_token

load_dotenv()

app = FastAPI(title="Personal Behavioral Analyst API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
try:
    init_db()
    print("✅ Database ready")
except Exception as e:
    print(f"⚠️ DB: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "API running"}

@app.post("/auth/register", response_model=Token, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    from models import User, UserFinancialMetrics
    
    # Check if exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        return {"error": "Email exists"}
    
    # Create user
    user = User(email=user_data.email, password_hash=hash_password(user_data.password), username=user_data.username)
    db.add(user)
    db.flush()
    
    # Add metrics
    metrics = UserFinancialMetrics(user_id=user.id)
    db.add(metrics)
    db.commit()
    db.refresh(user)
    
    access = create_access_token({"sub": user.email, "user_id": user.id})
    refresh = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    from models import User
    
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.password_hash):
        return {"error": "Invalid"}
    
    access = create_access_token({"sub": user.email, "user_id": user.id})
    refresh = create_refresh_token({"sub": user.email, "user_id": user.id})
    
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@app.post("/auth/refresh", response_model=Token)
def refresh(data: dict, db: Session = Depends(get_db)):
    from auth.security import verify_refresh_token
    from models import User
    
    payload = verify_refresh_token(data.get("refresh_token"))
    if not payload:
        return {"error": "Invalid token"}
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        return {"error": "User not found"}
    
    access = create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": access, "refresh_token": data.get("refresh_token"), "token_type": "bearer"}
