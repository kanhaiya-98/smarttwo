"""Negotiation database models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base


# ==================== NEGOTIATION MODELS ====================

class Quote(Base):
    """Initial quotes from suppliers."""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    procurement_task_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    
    # Quote details
    unit_price = Column(Float, nullable=False)
    quantity_available = Column(Integer)
    delivery_days = Column(Integer)
    minimum_order_quantity = Column(Integer)
    
    # Additional terms
    bulk_discount_available = Column(Boolean, default=False)
    bulk_discount_price = Column(Float)
    bulk_discount_quantity = Column(Integer)
    
    # Status
    is_accepted = Column(Boolean, default=False)
    rejection_reason = Column(Text)
    
    # Metadata
    response_time_seconds = Column(Integer)
    quote_valid_until = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Negotiation(Base):
    """Negotiation sessions between buyer and supplier."""
    __tablename__ = "negotiations"
    
    id = Column(Integer, primary_key=True, index=True)
    procurement_task_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    quote_id = Column(Integer, index=True)
    
    # Negotiation status
    status = Column(String(50), default="IN_PROGRESS")
    # IN_PROGRESS, SUCCESSFUL, FAILED, TIMEOUT
    
    current_round = Column(Integer, default=1)
    max_rounds = Column(Integer, default=3)
    
    # Final offer
    final_unit_price = Column(Float)
    final_delivery_days = Column(Integer)
    final_quantity = Column(Integer)
    
    # Outcome
    is_successful = Column(Boolean)
    savings_amount = Column(Float)  # Compared to initial quote
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class NegotiationMessage(Base):
    """Individual messages in negotiation."""
    __tablename__ = "negotiation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    negotiation_id = Column(Integer, nullable=False, index=True)
    
    # Message details
    round_number = Column(Integer, nullable=False)
    sender = Column(String(50), nullable=False)  # BUYER_AGENT, SUPPLIER
    message_content = Column(Text, nullable=False)
    
    # Structured data
    offer_price = Column(Float)
    offer_delivery_days = Column(Integer)
    offer_quantity = Column(Integer)
    
    # AI metadata
    generated_by_ai = Column(Boolean, default=True)
    prompt_used = Column(Text)
    confidence_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Decision(Base):
    """Final decision made by decision agent."""
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    procurement_task_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Selected supplier
    selected_supplier_id = Column(Integer, nullable=False)
    selected_quote_id = Column(Integer)
    selected_negotiation_id = Column(Integer)
    
    # Scoring details (JSON for flexibility)
    all_scores = Column(JSON)  # All supplier scores
    winning_score = Column(Float)
    
    # Decision reasoning
    reasoning_text = Column(Text, nullable=False)
    decision_factors = Column(JSON)  # Detailed breakdown
    
    # Scenario applied
    urgency_level = Column(String(50))
    budget_constraint = Column(Float)
    scenario_weights = Column(JSON)  # Weight adjustments applied
    
    # Approval
    requires_approval = Column(Boolean, default=False)
    is_approved = Column(Boolean)
    approved_by = Column(String(255))
    approval_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
