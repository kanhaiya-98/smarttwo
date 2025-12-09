"""Agent activity logging models for real-time tracking."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class AgentActivity(Base):
    """Real-time agent activity logs for dashboard display."""
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Agent identification
    agent_name = Column(String(50), nullable=False, index=True)
    # Values: MONITOR, BUYER, NEGOTIATOR, DECISION
    
    # Activity details
    action_type = Column(String(50), nullable=False, index=True)
    # Values: SCAN, DETECT, ALERT, REQUEST_QUOTE, SEND_MESSAGE, 
    #         CALCULATE_SCORE, MAKE_DECISION, IDLE, ERROR
    
    message = Column(Text, nullable=False)
    # Human-readable description: "Scanning inventory for low stock items..."
    
    # Contextual data
    context_data = Column("metadata", JSON, nullable=True)
    # Additional context: {"medicine_id": 1, "task_id": 5, "supplier_id": 3}
    
    # Status tracking
    status = Column(String(20), default="INFO")
    # Values: INFO, SUCCESS, WARNING, ERROR
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AgentActivity {self.agent_name} - {self.action_type}>"
