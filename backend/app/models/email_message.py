"""Email message model."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.sql import func
from app.database import Base


class EmailMessage(Base):
    """Individual email messages in a thread."""
    __tablename__ = "email_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey('email_threads.id'), nullable=False, index=True)
    
    # Email addresses
    sender = Column(String(255))  # Actual sender
    recipient = Column(String(255))  # Actual recipient
    display_sender = Column(String(255))  # What to show in UI
    display_recipient = Column(String(255))  # What to show in UI
    
    # Email content
    subject = Column(Text)
    body = Column(Text)
    html_body = Column(Text, nullable=True)
    
    # Direction
    is_from_agent = Column(Boolean, default=True)  # True if we sent, False if received
    
    # Parsed data from supplier responses
    parsed_data = Column(JSON, nullable=True)  # {quoted_price, delivery_days, conditions}
    quoted_price = Column(Float, nullable=True)
    delivery_days = Column(Integer, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
