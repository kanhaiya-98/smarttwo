"""Quote Response model for storing supplier quotes."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class QuoteResponse(Base):
    """Model for supplier quote responses."""
    
    __tablename__ = "quote_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"), nullable=False)
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=True)
    procurement_task_id = Column(Integer, nullable=False)
    
    # Quote details
    unit_price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    delivery_days = Column(Integer, nullable=False)
    stock_available = Column(Integer, nullable=True)
    
    # Additional terms
    payment_terms = Column(String(200), nullable=True)
    certifications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Negotiation tracking
    negotiation_round = Column(Integer, default=0)  # 0 = initial quote, 1-3 = negotiated
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
    email_message = relationship("EmailMessage")
