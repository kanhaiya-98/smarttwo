"""Supplier database models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Supplier(Base):
    """Supplier master data."""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Contact information
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    
    # Integration
    api_endpoint = Column(String(500))  # For automated integration
    api_key = Column(String(255))
    has_api_integration = Column(Boolean, default=False)
    
    # Business terms
    payment_terms = Column(String(100))  # NET 30, NET 60, etc.
    credit_limit = Column(Float)
    minimum_order_value = Column(Float)
    
    # Characteristics
    typical_delivery_days = Column(Integer, default=7)
    is_bulk_supplier = Column(Boolean, default=False)
    is_fast_delivery = Column(Boolean, default=False)
    is_budget_supplier = Column(Boolean, default=False)
    
    # Performance metrics (updated regularly)
    reliability_score = Column(Float, default=0.0)  # 0-100
    on_time_delivery_rate = Column(Float, default=0.0)  # 0-1
    quality_rating = Column(Float, default=0.0)  # 0-5
    average_response_time_hours = Column(Float)
    total_orders_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_order_date = Column(DateTime(timezone=True))


class SupplierMedicine(Base):
    """Mapping of medicines available from suppliers."""
    __tablename__ = "supplier_medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    medicine_id = Column(Integer, nullable=False, index=True)
    
    # Availability
    is_available = Column(Boolean, default=True)
    current_stock = Column(Integer)
    lead_time_days = Column(Integer)
    
    # Pricing
    base_price = Column(Float)
    bulk_discount_threshold = Column(Integer)
    bulk_discount_price = Column(Float)
    
    # Last transaction
    last_quote_price = Column(Float)
    last_quote_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SupplierPerformance(Base):
    """Detailed performance tracking for suppliers."""
    __tablename__ = "supplier_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Metrics
    total_orders = Column(Integer, default=0)
    on_time_deliveries = Column(Integer, default=0)
    late_deliveries = Column(Integer, default=0)
    quality_issues = Column(Integer, default=0)
    invoice_accuracy_rate = Column(Float, default=1.0)
    
    # Calculated scores
    delivery_score = Column(Float)
    quality_score = Column(Float)
    price_competitiveness_score = Column(Float)
    overall_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
