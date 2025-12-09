"""API endpoints for negotiation and decision workflows."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.database import get_db
from app.models.quote_response import QuoteResponse
from app.models.negotiation_round import NegotiationRound
from app.models.supplier_score import SupplierScore
from app.models.discovered_supplier import DiscoveredSupplier
from app.agents.negotiator_agent_v2 import NegotiatorAgent
from app.agents.decision_agent import DecisionAgent

router = APIRouter(prefix="/negotiation-decision", tags=["Negotiation & Decision"])
logger = logging.getLogger(__name__)


# Pydantic models
class QuoteCreate(BaseModel):
    supplier_id: int
    procurement_task_id: int = 1
    unit_price: float
    delivery_days: int
    stock_available: Optional[int] = None
    currency: str = "USD"


class DecisionRequest(BaseModel):
    procurement_task_id: int
    urgency: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    budget_mode: bool = False


# Quote endpoints
@router.post("/quotes/create")
async def create_quote(request: QuoteCreate, db: Session = Depends(get_db)):
    """Manually create a quote (for testing)."""
    quote = QuoteResponse(**request.dict())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    return {
        "status": "success",
        "quote_id": quote.id,
        "supplier_id": quote.supplier_id
    }


@router.get("/quotes/{task_id}")
async def get_quotes(task_id: int, db: Session = Depends(get_db)):
    """Get all quotes for a procurement task."""
    quotes = db.query(QuoteResponse).filter_by(procurement_task_id=task_id).all()
    
    result = []
    for quote in quotes:
        supplier = db.query(DiscoveredSupplier).get(quote.supplier_id)
        result.append({
            "quote_id": quote.id,
            "supplier_id": quote.supplier_id,
            "supplier_name": supplier.name if supplier else "Unknown",
            "unit_price": quote.unit_price,
            "delivery_days": quote.delivery_days,
            "stock_available": quote.stock_available,
            "created_at": quote.created_at.isoformat()
        })
    
    return result


# Negotiation endpoints
@router.post("/negotiation/start")
async def start_negotiation(
    procurement_task_id: int,
    db: Session = Depends(get_db)
):
    """Start negotiation for all quotes in a task."""
    quotes = db.query(QuoteResponse).filter_by(
        procurement_task_id=procurement_task_id,
        negotiation_round=0
    ).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="No quotes found")
    
    negotiator = NegotiatorAgent(db)
    strategies = negotiator.analyze_quotes(quotes)
    
    started = []
    for quote in quotes:
        strategy = strategies.get(quote.supplier_id)
        if strategy and strategy != "skip":
            neg_round = negotiator.start_negotiation(quote.id)
            if neg_round:
                started.append({
                    "supplier_id": quote.supplier_id,
                    "strategy": strategy,
                    "round_id": neg_round.id
                })
    
    return {
        "status": "success",
        "negotiations_started": len(started),
        "details": started
    }


@router.get("/negotiation/rounds/{supplier_id}")
async def get_negotiation_rounds(supplier_id: int, db: Session = Depends(get_db)):
    """Get negotiation history for a supplier."""
    rounds = db.query(NegotiationRound).filter_by(
        supplier_id=supplier_id
    ).order_by(NegotiationRound.round_number).all()
    
    return [{
        "round_number": r.round_number,
        "our_message": r.our_message,
        "our_counter_price": r.our_counter_price,
        "supplier_response": r.supplier_response,
        "supplier_counter_price": r.supplier_counter_price,
        "status": r.status,
        "created_at": r.created_at.isoformat()
    } for r in rounds]


# Decision endpoints
@router.post("/decision/analyze")
async def analyze_decision(request: DecisionRequest, db: Session = Depends(get_db)):
    """Run decision algorithm and get recommendation."""
    quotes = db.query(QuoteResponse).filter_by(
        procurement_task_id=request.procurement_task_id
    ).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="No quotes found")
    
    decision_agent = DecisionAgent(db)
    
    try:
        best_score, explanation = decision_agent.make_decision(
            quotes=quotes,
            required_quantity=5000,  # TODO: Get from task
            urgency=request.urgency,
            budget_mode=request.budget_mode
        )
        
        supplier = db.query(DiscoveredSupplier).get(best_score.supplier_id)
        
        return {
            "status": "success",
            "recommended_supplier_id": best_score.supplier_id,
            "supplier_name": supplier.name if supplier else "Unknown",
            "total_score": best_score.total_score,
            "price_score": best_score.price_score,
            "speed_score": best_score.speed_score,
            "reliability_score": best_score.reliability_score,
            "stock_score": best_score.stock_score,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Decision analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision/recommendation/{task_id}")
async def get_recommendation(task_id: int, db: Session = Depends(get_db)):
    """Get latest decision recommendation for a task."""
    scores = db.query(SupplierScore).filter_by(
        procurement_task_id=task_id
    ).order_by(SupplierScore.total_score.desc()).all()
    
    if not scores:
        raise HTTPException(status_code=404, detail="No decision made yet")
    
    best = scores[0]
    supplier = db.query(DiscoveredSupplier).get(best.supplier_id)
    
    return {
        "supplier_id": best.supplier_id,
        "supplier_name": supplier.name if supplier else "Unknown",
        "total_score": best.total_score,
        "explanation": best.reasoning,
        "created_at": best.created_at.isoformat()
    }
