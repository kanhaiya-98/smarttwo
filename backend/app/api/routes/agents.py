"""API routes for agent activity monitoring."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.agent_activity import AgentActivity
from app.models.medicine import ProcurementTask

router = APIRouter()


# Response Models
class ActivityLogResponse(BaseModel):
    id: int
    agent_name: str
    action_type: str
    message: str
    status: str
    context_data: dict = Field(alias="metadata", default={})
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class AgentStatusResponse(BaseModel):
    agent: str
    status: str  # ACTIVE, IDLE
    last_activity: Optional[str]
    last_activity_time: Optional[datetime]
    active_tasks: int
    recent_activities: List[str] = [] # New field for chat feed


class AgentStatsResponse(BaseModel):
    agent: str
    total_activities_24h: int
    successful_actions: int
    errors: int
    warnings: int
    last_scan_time: Optional[datetime]


@router.get("/activity/{agent_name}", response_model=List[ActivityLogResponse])
async def get_agent_activity(
    agent_name: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get recent activity logs for a specific agent.
    
    Args:
        agent_name: Agent name (MONITOR, BUYER, NEGOTIATOR, DECISION)
        limit: Maximum number of logs to return (max 200)
        offset: Number of logs to skip (for pagination)
        action_type: Filter by action type (optional)
        status: Filter by status (INFO, SUCCESS, WARNING, ERROR)
    
    Returns:
        List of activity logs
    """
    # Validate agent name
    valid_agents = ["MONITOR", "BUYER", "NEGOTIATOR", "DECISION"]
    agent_name = agent_name.upper()
    
    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
        )
    
    # Map API agent names to Database agent names
    # MONITOR and BUYER use uppercase in DB (set in their __init__)
    # NEGOTIATOR and DECISION use Title Case in DB (set in BaseAgent super calls)
    db_agent_name_map = {
        "MONITOR": "MONITOR",
        "BUYER": "BUYER",
        "NEGOTIATOR": "Negotiator Agent",
        "DECISION": "Decision Agent"
    }
    
    db_name = db_agent_name_map.get(agent_name, agent_name)
    
    # Build query
    query = db.query(AgentActivity).filter(
        AgentActivity.agent_name == db_name
    )
    
    if action_type:
        query = query.filter(AgentActivity.action_type == action_type.upper())
    
    if status:
        query = query.filter(AgentActivity.status == status.upper())
    
    # Get logs
    activities = query.order_by(
        AgentActivity.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return activities


@router.get("/status", response_model=List[AgentStatusResponse])
async def get_all_agent_status(db: Session = Depends(get_db)):
    """
    Get current status of all agents.
    
    Returns:
        List of agent statuses
    """
    # Mapping between API keys and DB Agent Names
    agents_map = {
        "MONITOR": "MONITOR",
        "BUYER": "BUYER",
        "NEGOTIATOR": "Negotiator Agent",
        "DECISION": "Decision Agent"
    }
    
    statuses = []
    
    two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
    
    for agent_key, db_agent_name in agents_map.items():
        # Check recent activity using the DB name
        recent_activity = db.query(AgentActivity).filter(
            AgentActivity.agent_name == db_agent_name,
            AgentActivity.created_at >= two_minutes_ago
        ).first()
        
        status = "ACTIVE" if recent_activity else "IDLE"
        
        # Get last 5 activities for the feed
        activities_query = db.query(AgentActivity).filter(
            AgentActivity.agent_name == db_agent_name
        ).order_by(AgentActivity.created_at.desc()).limit(5).all()
        
        last_activity = activities_query[0] if activities_query else None
        
        # Format recent activities as strings
        recent_logs = []
        if activities_query:
            for act in activities_query:
                time_str = act.created_at.strftime("%H:%M:%S")
                recent_logs.append(f"[{time_str}] {act.message}")
        
        # Count active tasks for this agent
        active_tasks = 0
        if agent_key == "BUYER":
            active_tasks = db.query(ProcurementTask).filter(
                ProcurementTask.status == "IN_PROGRESS",
                ProcurementTask.current_stage == "BUYER_AGENT"
            ).count()
        elif agent_key == "NEGOTIATOR":
            active_tasks = db.query(ProcurementTask).filter(
                ProcurementTask.status == "NEGOTIATING"
            ).count()
        elif agent_key == "DECISION":
            active_tasks = db.query(ProcurementTask).filter(
                ProcurementTask.current_stage == "DECISION_AGENT"
            ).count()
        
        statuses.append(AgentStatusResponse(
            agent=agent_key, # Keep key uppercase for frontend compatibility
            status=status,
            last_activity=last_activity.message if last_activity else None,
            last_activity_time=last_activity.created_at if last_activity else None,
            active_tasks=active_tasks,
            recent_activities=recent_logs
        ))
    
    return statuses


@router.get("/stats", response_model=List[AgentStatsResponse])
async def get_agent_statistics(db: Session = Depends(get_db)):
    """
    Get activity statistics for all agents in the last 24 hours.
    
    Returns:
        List of agent statistics
    """
    agents = ["MONITOR", "BUYER", "NEGOTIATOR", "DECISION"]
    stats = []
    
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    for agent in agents:
        # Total activities in 24h
        total = db.query(AgentActivity).filter(
            AgentActivity.agent_name == agent,
            AgentActivity.created_at >= twenty_four_hours_ago
        ).count()
        
        # Successful actions
        successful = db.query(AgentActivity).filter(
            AgentActivity.agent_name == agent,
            AgentActivity.status == "SUCCESS",
            AgentActivity.created_at >= twenty_four_hours_ago
        ).count()
        
        # Errors
        errors = db.query(AgentActivity).filter(
            AgentActivity.agent_name == agent,
            AgentActivity.status == "ERROR",
            AgentActivity.created_at >= twenty_four_hours_ago
        ).count()
        
        # Warnings
        warnings = db.query(AgentActivity).filter(
            AgentActivity.agent_name == agent,
            AgentActivity.status == "WARNING",
            AgentActivity.created_at >= twenty_four_hours_ago
        ).count()
        
        # Last scan time (for Monitor)
        last_scan = None
        if agent == "MONITOR":
            last_scan_activity = db.query(AgentActivity).filter(
                AgentActivity.agent_name == agent,
                AgentActivity.action_type == "SCAN",
                AgentActivity.message.like("%complete%")
            ).order_by(AgentActivity.created_at.desc()).first()
            
            if last_scan_activity:
                last_scan = last_scan_activity.created_at
        
        stats.append(AgentStatsResponse(
            agent=agent,
            total_activities_24h=total,
            successful_actions=successful,
            errors=errors,
            warnings=warnings,
            last_scan_time=last_scan
        ))
    
    return stats


@router.delete("/activity/{agent_name}")
async def clear_agent_activity(
    agent_name: str,
    older_than_days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Clear old activity logs for an agent (maintenance endpoint).
    
    Args:
        agent_name: Agent name
        older_than_days: Clear logs older than N days
    
    Returns:
        Number of logs deleted
    """
    agent_name = agent_name.upper()
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
    
    deleted = db.query(AgentActivity).filter(
        AgentActivity.agent_name == agent_name,
        AgentActivity.created_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "agent": agent_name,
        "deleted_count": deleted,
        "older_than_days": older_than_days
    }


@router.post("/run/{agent_name}")
async def run_agent_manually(
    agent_name: str,
    background_tasks: bool = True
):
    """
    Manually trigger an agent to run immediately.
    """
    agent_name = agent_name.upper()
    valid_agents = ["MONITOR", "BUYER", "NEGOTIATOR", "DECISION"]
    
    if agent_name not in valid_agents:
        raise HTTPException(status_code=400, detail="Invalid agent name.")
        
    task_id = None
    if agent_name == "MONITOR":
        from app.tasks.inventory_tasks import check_inventory
        task = check_inventory.delay()
        task_id = task.id
    elif agent_name == "BUYER":
        from app.tasks.procurement_tasks import run_buyer_agent
        task = run_buyer_agent.delay()
        task_id = task.id
    elif agent_name == "NEGOTIATOR":
        from app.tasks.procurement_tasks import run_negotiator_agent
        task = run_negotiator_agent.delay()
        task_id = task.id
    elif agent_name == "DECISION":
        from app.tasks.procurement_tasks import run_decision_agent
        task = run_decision_agent.delay()
        task_id = task.id
        
    return {
        "message": f"{agent_name} agent triggered successfully",
        "task_id": str(task_id),
        "status": "QUEUED"
    }
