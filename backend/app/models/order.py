"""Order database models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


# ==================== ORDER MODELS ====================

class OrderStatus(str, enum.Enum):
    """Order status enum."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    """Purchase orders."""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    
    # References
    procurement_task_id = Column(Integer, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    medicine_id = Column(Integer, nullable=False)
    
    # Order details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Delivery
    expected_delivery_days = Column(Integer)
    expected_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    
    # Payment
    payment_terms = Column(String(100))
    payment_due_date = Column(DateTime(timezone=True))
    payment_completed = Column(Boolean, default=False)
    
    # Tracking
    tracking_number = Column(String(255))
    supplier_confirmation_number = Column(String(255))
    
    # Quality & Receipt
    received_quantity = Column(Integer)
    quality_check_passed = Column(Boolean)
    quality_notes = Column(Text)
    
    # Decision metadata
    decision_score = Column(Float)
    decision_reasoning = Column(Text)
    selected_by_agent = Column(Boolean, default=True)
    override_reason = Column(Text)  # If human overrode AI decision
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    placed_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Approval workflow
    approved_by = Column(String(255))
    approval_notes = Column(Text)
    tracking_notes = Column(Text)


# Alias for backwards compatibility
Order = PurchaseOrder

