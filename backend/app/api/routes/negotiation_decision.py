"""API endpoints for negotiation and decision making."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.quote_response import QuoteResponse
from app.models.negotiation_round import NegotiationRound
from app.models.supplier_score import SupplierScore
from app.agents.negotiator_agent_v2 import NegotiatorAgent
from app.agents.decision_agent import DecisionAgent
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class QuoteCreate(BaseModel):
    supplier_id: int
    unit_price: float
    delivery_days: int
    stock_available: int = None
    procurement_task_id: int = 1


class NegotiationStart(BaseModel):
    procurement_task_id: int


class DecisionRequest(BaseModel):
    procurement_task_id: int
    urgency: str = "MEDIUM"
    budget_mode: bool = False


class QuoteInfo(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    unit_price: float
    delivery_days: int
    stock_available: int
    total_score: float = None


class ScoreInfo(BaseModel):
    supplier_id: int
    supplier_name: str
    total_score: float
    price_score: float
    speed_score: float
    reliability_score: float
    stock_score: float
    rank: int


@router.post("/quotes/create")
async def create_quote(quote: QuoteCreate, db: Session = Depends(get_db)):
    """Manually create a quote (for testing/demo)."""
    new_quote = QuoteResponse(
        supplier_id=quote.supplier_id,
        unit_price=quote.unit_price,
        delivery_days=quote.delivery_days,
        stock_available=quote.stock_available,
        procurement_task_id=quote.procurement_task_id,
        negotiation_round=0
    )
    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)
    
    return {"status": "success", "quote_id": new_quote.id}


@router.get("/quotes/{task_id}", response_model=List[QuoteInfo])
async def get_quotes(task_id: int, db: Session = Depends(get_db)):
    """Get all quotes for a procurement task."""
    from app.models.discovered_supplier import DiscoveredSupplier
    
    quotes = db.query(QuoteResponse).filter_by(procurement_task_id=task_id).all()
    
    result = []
    for quote in quotes:
        supplier = db.query(DiscoveredSupplier).get(quote.supplier_id)
        result.append(QuoteInfo(
            id=quote.id,
            supplier_id=quote.supplier_id,
            supplier_name=supplier.name if supplier else "Unknown",
            unit_price=quote.unit_price,
            delivery_days=quote.delivery_days,
            stock_available=quote.stock_available or 0,
            total_score=None
        ))
    
    return result


@router.post("/negotiation/start")
async def start_negotiation(request: NegotiationStart, db: Session = Depends(get_db)):
    """Start negotiation with all relevant suppliers."""
    
    # Get all quotes for this task
    quotes = db.query(QuoteResponse).filter_by(
        procurement_task_id=request.procurement_task_id
    ).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="No quotes found for this task")
    
    # Initialize negotiator
    negotiator = NegotiatorAgent(db)
    
    # Analyze which suppliers to negotiate with
    strategies = negotiator.analyze_quotes(quotes)
    
    # Start negotiations
    rounds_created = []
    for supplier_id, strategy in strategies.items():
        if strategy == "skip":
            continue
        
        quote = next((q for q in quotes if q.supplier_id == supplier_id), None)
        if quote:
            try:
                round_record = negotiator.start_negotiation(
                    supplier_id=supplier_id,
                    quote_id=quote.id,
                    all_quotes=quotes,
                    strategy=strategy
                )
                rounds_created.append(round_record.id)
                logger.info(f"Started negotiation with supplier {supplier_id}")
            except Exception as e:
                logger.error(f"Failed to start negotiation: {e}")
    
    return {
        "status": "success",
        "negotiations_started": len(rounds_created),
        "round_ids": rounds_created
    }


@router.get("/negotiation/rounds/{supplier_id}")
async def get_negotiation_rounds(supplier_id: int, db: Session = Depends(get_db)):
    """Get all negotiation rounds for a supplier."""
    rounds = db.query(NegotiationRound).filter_by(supplier_id=supplier_id).order_by(
        NegotiationRound.round_number
    ).all()
    
    return [{
        "id": r.id,
        "round_number": r.round_number,
        "our_message": r.our_message,
        "our_offer_price": r.our_offer_price,
        "supplier_response": r.supplier_response,
        "supplier_counter_price": r.supplier_counter_price,
        "status": r.status,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None
    } for r in rounds]


@router.post("/decision/analyze")
async def analyze_decision(request: DecisionRequest, db: Session = Depends(get_db)):
    """Run decision algorithm and get recommendation."""
    
    # Get all quotes
    quotes = db.query(QuoteResponse).filter_by(
        procurement_task_id=request.procurement_task_id
    ).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="No quotes found")
    
    # Run decision algorithm
    decision_agent = DecisionAgent(db)
    best_score, explanation = decision_agent.make_decision(
        quotes=quotes,
        required_quantity=5000,
        urgency=request.urgency
    )
    
    if not best_score:
        raise HTTPException(status_code=500, detail="Decision analysis failed")
    
    # Get all scores for comparison
    all_scores = db.query(SupplierScore).filter_by(
        procurement_task_id=request.procurement_task_id
    ).order_by(SupplierScore.rank).all()
    
    from app.models.discovered_supplier import DiscoveredSupplier
    
    score_list = []
    for score in all_scores:
        supplier = db.query(DiscoveredSupplier).get(score.supplier_id)
        score_list.append(ScoreInfo(
            supplier_id=score.supplier_id,
            supplier_name=supplier.name if supplier else "Unknown",
            total_score=score.total_score,
            price_score=score.price_score,
            speed_score=score.speed_score,
            reliability_score=score.reliability_score,
            stock_score=score.stock_score,
            rank=score.rank
        ))
    
    return {
        "recommended_supplier_id": best_score.supplier_id,
        "total_score": best_score.total_score,
        "explanation": explanation,
        "all_scores": score_list
    }


@router.get("/decision/recommendation/{task_id}")
async def get_recommendation(task_id: int, db: Session = Depends(get_db)):
    """Get the latest decision recommendation for a task."""
    
    scores = db.query(SupplierScore).filter_by(
        procurement_task_id=task_id
    ).order_by(SupplierScore.rank).all()
    
    if not scores:
        return {"status": "no_decision", "message": "No decision has been made yet"}
    
    best = scores[0]
    from app.models.discovered_supplier import DiscoveredSupplier
    supplier = db.query(DiscoveredSupplier).get(best.supplier_id)
    
    return {
        "supplier_id": best.supplier_id,
        "supplier_name": supplier.name if supplier else "Unknown",
        "total_score": best.total_score,
        "reasoning": best.reasoning,
        "rank": best.rank
    }
