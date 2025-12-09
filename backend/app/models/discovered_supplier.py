"""Discovered supplier model for hackathon demo."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base


class DiscoveredSupplier(Base):
    """Suppliers found via Google search for demo."""
    __tablename__ = "discovered_suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Company information
    name = Column(String(255), nullable=False)  # "MedPharma Solutions"
    website = Column(String(500))  # "https://medpharma.com"
    phone = Column(String(50))
    location = Column(String(100))  # "Mumbai, India"
    
    # Email addresses - THE DEMO MAGIC
    display_email = Column(String(255))  # "sales@medpharma.com" - SHOW IN UI
    actual_email = Column(String(255))  # "kanhacet@gmail.com" - ACTUALLY USE
    
    # Discovery metadata
    found_via_search = Column(Boolean, default=True)
    search_query = Column(String(500))
    search_rank = Column(Integer)  # 1-10 (position in search results)
    discovery_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Demo mode flag
    is_demo_mode = Column(Boolean, default=True)
    demo_identifier = Column(String(100))  # "MedPharma" - for [DEMO: X] prefix
    
    # Status tracking
    emails_sent = Column(Integer, default=0)
    emails_received = Column(Integer, default=0)
    last_email_sent_at = Column(DateTime(timezone=True))
    last_response_time = Column(DateTime(timezone=True))
    is_responsive = Column(Boolean, default=None)
    
    # Procurement task linkage
    procurement_task_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
