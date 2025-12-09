"""Email thread tracking model."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class EmailThread(Base):
    """Track email conversations with suppliers."""
    __tablename__ = "email_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('discovered_suppliers.id'), nullable=False, index=True)
    procurement_task_id = Column(Integer, index=True)
    
    # Display vs Actual addresses (for demo)
    display_recipient = Column(String(255))  # Show in UI: "sales@medpharma.com"
    actual_recipient = Column(String(255))   # Actually send to: "kanhacet@gmail.com"
    
    # Email subject and tracking
    subject = Column(Text)
    thread_identifier = Column(String(255))  # Email message ID for tracking replies
    
    # Status tracking
    status = Column(String(50), default="SENT")  # SENT, AWAITING_REPLY, REPLIED, NEGOTIATING, CLOSED
    round_number = Column(Integer, default=1)  # Negotiation round
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
