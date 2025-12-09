from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.negotiation import Quote, Negotiation
from app.models.supplier import Supplier
from app.models.negotiation import Decision as DecisionModel

router = APIRouter()

@router.get("/task/{task_id}/quotes")
async def get_task_quotes(task_id: int, db: Session = Depends(get_db)):
    """
    Get all quotes for a specific procurement task.
    Includes supplier details.
    """
    quotes = db.query(Quote, Supplier).join(
        Supplier, Quote.supplier_id == Supplier.id
    ).filter(
        Quote.procurement_task_id == task_id
    ).all()
    
    result = []
    for quote, supplier in quotes:
        result.append({
            "quote_id": quote.id,
            "supplier_name": supplier.name,
            "supplier_code": supplier.code,
            "unit_price": quote.unit_price,
            "delivery_days": quote.delivery_days,
            "quantity_available": quote.quantity_available,
            "reliability_score": supplier.reliability_score,
            "is_fast_delivery": supplier.is_fast_delivery,
            "response_time": quote.response_time_seconds,
            "valid_until": quote.quote_valid_until
        })
        
    return result

from app.models.medicine import ProcurementTask

@router.get("/active")
async def get_active_negotiation(db: Session = Depends(get_db)):
    """Get the most recent active negotiation task."""
    task = db.query(ProcurementTask).filter(
        ProcurementTask.status.in_([
            "NEGOTIATING", 
            "PENDING_APPROVAL", # Show quotes even during approval
            "COMPLETED" # Show recent history for demo effect
        ])
    ).order_by(ProcurementTask.created_at.desc()).first()
    
    if not task:
        return {"task_id": None}
        
    return {"task_id": task.id}

@router.get("/task/{task_id}/decision")
async def get_task_decision(task_id: int, db: Session = Depends(get_db)):
    """
    Get the final decision (if any) for a task.
    """
    decision = db.query(DecisionModel).filter(
        DecisionModel.procurement_task_id == task_id
    ).first()
    
    if not decision:
        return None
        
    return {
        "selected_supplier_id": decision.selected_supplier_id,
        "reasoning": decision.reasoning_text,
        "winning_score": decision.winning_score,
        "all_scores": decision.all_scores
    }
