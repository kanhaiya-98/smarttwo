from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.medicine import Medicine, ProcurementTask
from app.models.negotiation import Decision
from app.models.order import PurchaseOrder

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    # Count active tasks
    active_tasks = db.query(ProcurementTask).filter(
        ProcurementTask.status.in_(["QUEUED", "IN_PROGRESS", "NEGOTIATING"])
    ).count()
    
    # Count pending approvals
    pending_approvals = db.query(Decision).filter(
        Decision.requires_approval == True,
        Decision.is_approved == None
    ).count()
    
    # Count low stock items
    low_stock_count = 0
    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    for med in medicines:
        if med.average_daily_sales > 0:
            days_supply = med.current_stock / med.average_daily_sales
            if days_supply < 7:
                low_stock_count += 1
    
    # Recent orders
    recent_orders = db.query(PurchaseOrder).order_by(
        PurchaseOrder.created_at.desc()
    ).limit(5).all()
    
    return {
        "active_tasks": active_tasks,
        "pending_approvals": pending_approvals,
        "low_stock_items": low_stock_count,
        "recent_orders": [
            {
                "po_number": o.po_number,
                "status": o.status.value,
                "total_amount": o.total_amount,
                "created_at": o.created_at
            }
            for o in recent_orders
        ]
    }


@router.get("/agent-status")
async def get_agent_status(db: Session = Depends(get_db)):
    """Get current agent status."""
    # Get tasks by stage
    tasks_by_stage = db.query(
        ProcurementTask.current_stage,
        func.count(ProcurementTask.id)
    ).filter(
        ProcurementTask.status.in_(["IN_PROGRESS", "NEGOTIATING"])
    ).group_by(ProcurementTask.current_stage).all()
    
    agent_status = {
        "monitor": "IDLE",
        "buyer": "IDLE",
        "negotiator": "IDLE",
        "decision": "IDLE"
    }
    
    for stage, count in tasks_by_stage:
        if stage == "BUYER_AGENT" and count > 0:
            agent_status["buyer"] = "ACTIVE"
        elif stage == "NEGOTIATOR_AGENT" and count > 0:
            agent_status["negotiator"] = "ACTIVE"
        elif stage == "DECISION_AGENT" and count > 0:
            agent_status["decision"] = "ACTIVE"
    
    return agent_status
