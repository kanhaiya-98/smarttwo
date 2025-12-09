"""Demand forecasting models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class DemandForecast(Base):
    """Demand forecasting data for intelligent reordering."""
    __tablename__ = "demand_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer,  # ForeignKey("medicines.id")? User prompt didn't specify FK but said "proper foreign keys".
                         # I should add ForeignKey constraint. 
                         ForeignKey("medicines.id"),
                         nullable=False, index=True)
    
    # Forecast data
    forecast_date = Column(DateTime(timezone=True), nullable=False, index=True)
    predicted_units = Column(Integer, nullable=False)
    confidence_score = Column(Integer, default=85)  # 0-100
    
    # Seasonality and trends
    seasonality_factor = Column(Integer, default=100)  # 100 = normal, >100 = high season
    trend = Column(String(20), default="STABLE")  # INCREASING, DECREASING, STABLE
    
    # Forecast metadata
    forecast_method = Column(String(50), default="MOVING_AVERAGE")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Special events
    special_event = Column(String(100), nullable=True)
    # Example: "Flu Season", "Festival Period", "Government Campaign"
    
    def __repr__(self):
        return f"<DemandForecast medicine_id={self.medicine_id} date={self.forecast_date}>"
