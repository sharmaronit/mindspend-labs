"""
Database Models
- User accounts
- Transactions
- Analysis results
- Financial metrics
- Password reset tokens
- Guest data migration tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transactions = relationship("UserTransaction", back_populates="user", cascade="all, delete-orphan")
    analysis = relationship("UserAnalysis", back_populates="user", cascade="all, delete-orphan")
    financial_metrics = relationship("UserFinancialMetrics", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserTransaction(Base):
    """User transaction records"""
    __tablename__ = "user_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="transactions")
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_user_category', 'user_id', 'category'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount})>"


class UserAnalysis(Base):
    """AI-generated analysis and insights"""
    __tablename__ = "user_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # 'patterns', 'triggers', 'recommendations'
    content = Column(Text, nullable=False)
    analysis_metadata = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="analysis")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, user_id={self.user_id}, type={self.analysis_type})>"


class UserFinancialMetrics(Base):
    """User financial dashboard metrics"""
    __tablename__ = "user_financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Income & Expenses
    monthly_income = Column(Float, default=0.0)
    rent = Column(Float, default=0.0)
    utilities = Column(Float, default=0.0)
    tuition = Column(Float, default=0.0)
    loans = Column(Float, default=0.0)
    insurance = Column(Float, default=0.0)
    subscriptions = Column(Float, default=0.0)
    other_expenses = Column(Float, default=0.0)
    
    # Calculated fields
    total_expenses = Column(Float, default=0.0)
    disposable_income = Column(Float, default=0.0)
    
    # Savings tips
    savings_tips = Column(Text, nullable=True)  # JSON array of tips
    
    # Highest spending category
    highest_category = Column(String(100), nullable=True)
    highest_amount = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="financial_metrics")
    
    def __repr__(self):
        return f"<FinancialMetrics(user_id={self.user_id}, income={self.monthly_income})>"


class PasswordResetToken(Base):
    """Password reset tokens with expiration"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, used={self.used})>"


class GuestDataMigration(Base):
    """Track guest data migrations to user accounts"""
    __tablename__ = "guest_data_migration"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    guest_data = Column(Text, nullable=False)  # JSON string of guest transactions
    migrated_at = Column(DateTime, default=datetime.utcnow)
    transaction_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<GuestMigration(user_id={self.user_id}, transactions={self.transaction_count})>"
