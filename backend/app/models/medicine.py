from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base
from enum import Enum

class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    dosage = Column(String, nullable=False)
    form = Column(String, nullable=False)
    category = Column(String, nullable=False)
    
    current_stock = Column(Integer, default=0)
    average_daily_sales = Column(Float, default=0.0)
    safety_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    
    last_purchase_price = Column(Float, nullable=True)
    average_price = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True)
    requires_quality_check = Column(Boolean, default=False)
    min_expiry_months = Column(Integer, default=12)

    # Seasonality and forecasting
    seasonality_index = Column(Float, default=1.0)
    peak_season_months = Column(JSON, nullable=True)
    last_forecast_update = Column(DateTime(timezone=True), nullable=True)

    # Enhanced tracking
    stockout_count = Column(Integer, default=0)
    last_stockout_date = Column(DateTime(timezone=True), nullable=True)

    # Alert configuration
    custom_reorder_days = Column(Integer, nullable=True)
    is_critical = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProcurementTask(Base):
    __tablename__ = "procurement_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, index=True)
    required_quantity = Column(Integer)
    urgency_level = Column(String) 
    days_of_supply_remaining = Column(Float)
    status = Column(String, default="QUEUED")
    current_stage = Column(String)
    error_message = Column(String, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
