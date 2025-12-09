"""Negotiation round tracking - multi-round negotiation with suppliers."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class NegotiationRound(Base):
    """Single round of negotiation with a supplier."""
    __tablename__ = "negotiation_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"))
    procurement_task_id = Column(Integer, nullable=True)
    
    round_number = Column(Integer)  # 1, 2, or 3
    
    # Our message (AI-generated)
    our_message = Column(Text)
    our_offer_price = Column(Float, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Supplier response
    supplier_response = Column(Text, nullable=True)
    supplier_counter_price = Column(Float, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="SENT")  
    # SENT, AWAITING_RESPONSE, ACCEPTED, REJECTED, COUNTER, TIMEOUT
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
