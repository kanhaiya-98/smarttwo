"""Quote response model - stores supplier quotes."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class QuoteResponse(Base):
    """Supplier quote/response to our request."""
    __tablename__ = "quote_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"))
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=True)
    procurement_task_id = Column(Integer, nullable=True)
    
    # Pricing details
    unit_price = Column(Float)  # Price per unit
    currency = Column(String(10), default="USD")
    total_price = Column(Float, nullable=True)
    
    # Delivery & stock
    delivery_days = Column(Integer)
    stock_available = Column(Integer, nullable=True)
    minimum_order = Column(Integer, nullable=True)
    
    # Additional terms
    payment_terms = Column(String(255), nullable=True)
    certifications = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    
    # Negotiation tracking
    is_final_offer = Column(Boolean, default=False)
    negotiation_round = Column(Integer, default=0)  # 0=initial, 1-3=negotiated
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
    email_message = relationship("EmailMessage")
