"""Supplier Score model for decision analysis results."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class SupplierScore(Base):
    """Model for supplier scoring and decision analysis."""
    
    __tablename__ = "supplier_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"), nullable=False)
    quote_response_id = Column(Integer, ForeignKey("quote_responses.id"), nullable=False)
    procurement_task_id = Column(Integer, nullable=False)
    
    # Individual scores (0-100)
    price_score = Column(Float, nullable=False)
    speed_score = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    stock_score = Column(Float, nullable=False)
    
    # Weights used (should sum to 1.0)
    price_weight = Column(Float, default=0.40)
    speed_weight = Column(Float, default=0.25)
    reliability_weight = Column(Float, default=0.20)
    stock_weight = Column(Float, default=0.15)
    
    # Total weighted score
    total_score = Column(Float, nullable=False)
    
    # AI-generated reasoning
    reasoning = Column(Text, nullable=True)
    
    # Metadata
    urgency_level = Column(String(20), nullable=True)  # CRITICAL, HIGH, MEDIUM, LOW
    scenario = Column(String(50), nullable=True)  # budget_mode, quality_mode, standard
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
    quote = relationship("QuoteResponse")
