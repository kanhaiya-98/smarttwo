"""Supplier scoring - weighted algorithm results."""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class SupplierScore(Base):
    """Weighted scoring results for supplier evaluation."""
    __tablename__ = "supplier_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"))
    quote_id = Column(Integer, ForeignKey("quote_responses.id"))
    procurement_task_id = Column(Integer, nullable=True)
    
    # Individual scores (0-100)
    price_score = Column(Float)
    speed_score = Column(Float)
    reliability_score = Column(Float)
    stock_score = Column(Float)
    
    # Weights used (for transparency)
    price_weight = Column(Float, default=0.40)
    speed_weight = Column(Float, default=0.25)
    reliability_weight = Column(Float, default=0.20)
    stock_weight = Column(Float, default=0.15)
    
    # Total weighted score
    total_score = Column(Float)
    
    # Ranking
    rank = Column(Integer)  # 1=best, 2=second, etc.
    
    # AI explanation
    reasoning = Column(Text, nullable=True)  # Gemini-generated explanation
    
    # Scenario context
    urgency_level = Column(String(20), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    budget_mode = Column(String(20), default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
    quote = relationship("QuoteResponse")
