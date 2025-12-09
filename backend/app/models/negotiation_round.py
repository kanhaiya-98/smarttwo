"""Negotiation Round model for tracking negotiation exchanges."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class NegotiationStatus(str, enum.Enum):
    """Negotiation status enum."""
    SENT = "SENT"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COUNTER_OFFER = "COUNTER_OFFER"


class NegotiationRound(Base):
    """Model for individual negotiation rounds."""
    
    __tablename__ = "negotiation_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("discovered_suppliers.id"), nullable=False)
    quote_response_id = Column(Integer, ForeignKey("quote_responses.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    
    # Our negotiation message
    our_message = Column(Text, nullable=False)
    our_counter_price = Column(Float, nullable=True)
    
    # Supplier response
    supplier_response = Column(Text, nullable=True)
    supplier_counter_price = Column(Float, nullable=True)
    supplier_counter_delivery = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum(NegotiationStatus), default=NegotiationStatus.SENT)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("DiscoveredSupplier")
    quote = relationship("QuoteResponse")
