"""
User Data Routes
- Profile management
- Financial metrics (income, expenses)
- Transactions
- Account deletion
- Data export
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db
from models import User, UserTransaction, UserFinancialMetrics, UserAnalysis
from auth.schemas import (
    UserResponse, TransactionCreate, TransactionResponse,
    FinancialMetricsUpdate, FinancialMetricsResponse,
    AnalysisResponse, MessageResponse, UpdateProfile
)
from auth.security import verify_access_token

router = APIRouter(prefix="/user", tags=["user"])


# ============================================
# Authentication Dependency
# ============================================

def get_current_user(
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


# ============================================
# Profile Endpoints
# ============================================

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns user ID, email, username, creation date.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        bio=current_user.bio,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information.
    
    - Updates username, first_name, last_name, bio
    - All fields are optional
    """
    if data.username is not None:
        current_user.username = data.username
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.bio is not None:
        current_user.bio = data.bio
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        bio=current_user.bio,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.delete("/account", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account and all associated data.
    
    - Marks account as inactive (prevents login)
    - Deletes all transactions, metrics, analysis data
    - Cascade deletes handle relationships
    - Attempts to delete Supabase auth user (requires Service Role Key)
    - Cannot be undone
    """
    import os
    from dotenv import load_dotenv
    import requests
    
    user_id = current_user.id
    user_email = current_user.email
    
    print(f"\n🔄 Starting complete account deletion for: {user_email}")
    
    try:
        # Step 1: Delete all related data (transactions, metrics, analysis)
        print(f"⏳ Deleting user transactions...")
        db.query(UserTransaction).filter(UserTransaction.user_id == user_id).delete()
        
        print(f"⏳ Deleting user financial metrics...")
        db.query(UserFinancialMetrics).filter(UserFinancialMetrics.user_id == user_id).delete()
        
        print(f"⏳ Deleting user analysis data...")
        db.query(UserAnalysis).filter(UserAnalysis.user_id == user_id).delete()
        
        db.commit()
        print(f"✅ All user data deleted")
        
        # Step 2: Delete the user account itself
        print(f"⏳ Deleting user account from local database...")
        db.delete(current_user)
        db.commit()
        print(f"✅ User account deleted from local database")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during local deletion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )
    
    # Step 3: Attempt Supabase auth user deletion (optional - not critical)
    supabase_status = "⏭️ Skipped"
    try:
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        
        if supabase_url and supabase_service_key:
            print(f"⏳ Attempting Supabase auth deletion...")
            
            # Note: SUPABASE_SERVICE_KEY must be the Service Role Key (not publishable key)
            # Service Role Key can be found in: Supabase Dashboard → Settings → API
            
            headers = {
                "Authorization": f"Bearer {supabase_service_key}",
                "Content-Type": "application/json",
                "apikey": supabase_service_key
            }
            
            # Endpoint to list and delete users
            admin_url = f"{supabase_url}/auth/v1/admin/users"
            
            try:
                # Get users by email
                response = requests.get(
                    admin_url,
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    users = response.json()
                    # Find user by email
                    target_user = None
                    if isinstance(users, list):
                        target_user = next((u for u in users if u.get("email") == user_email), None)
                    elif isinstance(users, dict) and "users" in users:
                        target_user = next((u for u in users["users"] if u.get("email") == user_email), None)
                    
                    if target_user:
                        user_uid = target_user.get("id")
                        # Delete the user
                        del_response = requests.delete(
                            f"{admin_url}/{user_uid}",
                            headers=headers,
                            timeout=5
                        )
                        
                        if del_response.status_code in [200, 204]:
                            print(f"✅ Deleted Supabase auth user")
                            supabase_status = "✅ Supabase auth user deleted"
                        else:
                            print(f"⚠️ Supabase deletion status: {del_response.status_code}")
                            supabase_status = f"⚠️ Supabase: {del_response.status_code}"
                    else:
                        print(f"⚠️ User not found in Supabase")
                        supabase_status = "⚠️ User not found in Supabase"
                else:
                    print(f"⚠️ Could not query Supabase users: {response.status_code}")
                    supabase_status = f"⚠️ Query failed: {response.status_code}"
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Supabase request error: {str(e)}")
                supabase_status = f"⚠️ Request error: {str(e)}"
            except Exception as e:
                print(f"⚠️ Supabase deletion error: {str(e)}")
                supabase_status = f"⚠️ Error: {str(e)}"
        else:
            print("ℹ️ Supabase credentials not configured")
            supabase_status = "ℹ️ Credentials not configured"
    except Exception as e:
        print(f"⚠️ Unexpected error during Supabase operations: {str(e)}")
        supabase_status = f"⚠️ Unexpected error"
    
    print(f"📋 Supabase Status: {supabase_status}")
    print(f"✅ Account deletion completed - user data is permanently removed\n")
    
    return MessageResponse(
        message="Account and all associated data have been permanently deleted. You have been signed out.",
        success=True
    )


# ============================================
# Financial Metrics Endpoints
# ============================================

@router.get("/metrics", response_model=FinancialMetricsResponse)
def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's financial metrics.
    
    Returns income, expenses, disposable income, savings tips.
    """
    metrics = db.query(UserFinancialMetrics).filter(
        UserFinancialMetrics.user_id == current_user.id
    ).first()
    
    if not metrics:
        # Create default metrics if not exist
        metrics = UserFinancialMetrics(user_id=current_user.id)
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    
    return FinancialMetricsResponse(
        id=metrics.id,
        user_id=metrics.user_id,
        monthly_income=metrics.monthly_income,
        rent=metrics.rent,
        utilities=metrics.utilities,
        tuition=metrics.tuition,
        loans=metrics.loans,
        insurance=metrics.insurance,
        subscriptions=metrics.subscriptions,
        other_expenses=metrics.other_expenses,
        total_expenses=metrics.total_expenses,
        disposable_income=metrics.disposable_income,
        savings_tips=json.loads(metrics.savings_tips) if metrics.savings_tips else [],
        highest_category=metrics.highest_category,
        highest_amount=metrics.highest_amount,
        created_at=metrics.created_at,
        updated_at=metrics.updated_at
    )


@router.post("/metrics", response_model=FinancialMetricsResponse)
def update_metrics(
    data: FinancialMetricsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's financial metrics.
    
    - Updates income and expense categories
    - Calculates total expenses and disposable income
    - Generates savings tips based on thresholds
    """
    metrics = db.query(UserFinancialMetrics).filter(
        UserFinancialMetrics.user_id == current_user.id
    ).first()
    
    if not metrics:
        metrics = UserFinancialMetrics(user_id=current_user.id)
        db.add(metrics)
    
    # Update fields
    if data.monthly_income is not None:
        metrics.monthly_income = data.monthly_income
    if data.rent is not None:
        metrics.rent = data.rent
    if data.utilities is not None:
        metrics.utilities = data.utilities
    if data.tuition is not None:
        metrics.tuition = data.tuition
    if data.loans is not None:
        metrics.loans = data.loans
    if data.insurance is not None:
        metrics.insurance = data.insurance
    if data.subscriptions is not None:
        metrics.subscriptions = data.subscriptions
    if data.other_expenses is not None:
        metrics.other_expenses = data.other_expenses
    
    # Calculate totals
    total_expenses = (
        (metrics.rent or 0) +
        (metrics.utilities or 0) +
        (metrics.tuition or 0) +
        (metrics.loans or 0) +
        (metrics.insurance or 0) +
        (metrics.subscriptions or 0) +
        (metrics.other_expenses or 0)
    )
    metrics.total_expenses = total_expenses
    
    # Calculate disposable income
    income = metrics.monthly_income or 0
    metrics.disposable_income = income - total_expenses
    
    # Find highest expense category
    expense_categories = {
        "Rent": metrics.rent or 0,
        "Utilities": metrics.utilities or 0,
        "Tuition": metrics.tuition or 0,
        "Loans": metrics.loans or 0,
        "Insurance": metrics.insurance or 0,
        "Subscriptions": metrics.subscriptions or 0,
        "Other": metrics.other_expenses or 0
    }
    highest = max(expense_categories.items(), key=lambda x: x[1])
    metrics.highest_category = highest[0]
    metrics.highest_amount = highest[1]
    
    # Generate savings tips
    tips = []
    if income > 0:
        rent_pct = (metrics.rent or 0) / income * 100
        utilities_pct = (metrics.utilities or 0) / income * 100
        subscriptions_pct = (metrics.subscriptions or 0) / income * 100
        
        if rent_pct > 30:
            tips.append({
                "category": "Rent",
                "tip": f"Your rent is {rent_pct:.1f}% of income. Consider finding cheaper housing.",
                "severity": "high"
            })
        
        if utilities_pct > 10:
            tips.append({
                "category": "Utilities",
                "tip": f"Utilities are {utilities_pct:.1f}% of income. Review energy consumption.",
                "severity": "medium"
            })
        
        if subscriptions_pct > 5:
            tips.append({
                "category": "Subscriptions",
                "tip": f"Subscriptions are {subscriptions_pct:.1f}% of income. Cancel unused services.",
                "severity": "medium"
            })
        
        if metrics.disposable_income < 0:
            tips.append({
                "category": "Budget",
                "tip": "You're spending more than you earn. Cut expenses immediately.",
                "severity": "critical"
            })
        elif metrics.disposable_income < income * 0.1:
            tips.append({
                "category": "Savings",
                "tip": "Try to save at least 10-20% of your income.",
                "severity": "medium"
            })
    
    metrics.savings_tips = json.dumps(tips)
    
    db.commit()
    db.refresh(metrics)
    
    return FinancialMetricsResponse(
        id=metrics.id,
        user_id=metrics.user_id,
        monthly_income=metrics.monthly_income,
        rent=metrics.rent,
        utilities=metrics.utilities,
        tuition=metrics.tuition,
        loans=metrics.loans,
        insurance=metrics.insurance,
        subscriptions=metrics.subscriptions,
        other_expenses=metrics.other_expenses,
        total_expenses=metrics.total_expenses,
        disposable_income=metrics.disposable_income,
        savings_tips=tips,
        highest_category=metrics.highest_category,
        highest_amount=metrics.highest_amount,
        created_at=metrics.created_at,
        updated_at=metrics.updated_at
    )


# ============================================
# Transaction Endpoints
# ============================================

@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """
    Get user's transactions.
    
    - Paginated with limit/offset
    - Ordered by date descending (newest first)
    """
    transactions = db.query(UserTransaction).filter(
        UserTransaction.user_id == current_user.id
    ).order_by(UserTransaction.date.desc()).limit(limit).offset(offset).all()
    
    return [
        TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            date=t.date,
            amount=t.amount,
            category=t.category,
            description=t.description,
            created_at=t.created_at
        )
        for t in transactions
    ]


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    
    - Date, amount, category required
    - Description optional
    """
    transaction = UserTransaction(
        user_id=current_user.id,
        date=data.date,
        amount=data.amount,
        category=data.category,
        description=data.description
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        date=transaction.date,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        created_at=transaction.created_at
    )


# ============================================
# Data Export Endpoint
# ============================================

@router.get("/export")
def export_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all user data (GDPR compliance).
    
    Returns JSON with profile, transactions, metrics, analysis.
    """
    # Get transactions
    transactions = db.query(UserTransaction).filter(
        UserTransaction.user_id == current_user.id
    ).all()
    
    # Get metrics
    metrics = db.query(UserFinancialMetrics).filter(
        UserFinancialMetrics.user_id == current_user.id
    ).first()
    
    # Get analysis
    analysis = db.query(UserAnalysis).filter(
        UserAnalysis.user_id == current_user.id
    ).all()
    
    export_data = {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "created_at": current_user.created_at.isoformat(),
            "is_active": current_user.is_active
        },
        "transactions": [
            {
                "date": t.date,
                "amount": float(t.amount),
                "category": t.category,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ],
        "financial_metrics": {
            "monthly_income": float(metrics.monthly_income) if metrics and metrics.monthly_income else 0,
            "rent": float(metrics.rent) if metrics and metrics.rent else 0,
            "utilities": float(metrics.utilities) if metrics and metrics.utilities else 0,
            "tuition": float(metrics.tuition) if metrics and metrics.tuition else 0,
            "loans": float(metrics.loans) if metrics and metrics.loans else 0,
            "insurance": float(metrics.insurance) if metrics and metrics.insurance else 0,
            "subscriptions": float(metrics.subscriptions) if metrics and metrics.subscriptions else 0,
            "other_expenses": float(metrics.other_expenses) if metrics and metrics.other_expenses else 0,
            "total_expenses": float(metrics.total_expenses) if metrics and metrics.total_expenses else 0,
            "disposable_income": float(metrics.disposable_income) if metrics and metrics.disposable_income else 0,
            "savings_tips": json.loads(metrics.savings_tips) if metrics and metrics.savings_tips else []
        } if metrics else {},
        "analysis": [
            {
                "type": a.analysis_type,
                "content": a.content,
                "metadata": json.loads(a.analysis_metadata) if a.analysis_metadata else {},
                "created_at": a.created_at.isoformat()
            }
            for a in analysis
        ]
    }
    
    return export_data
