from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.negotiation import Negotiation, NegotiationMessage
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class NegotiationResponse(BaseModel):
    id: int
    procurement_task_id: int
    supplier_id: int
    status: str
    current_round: int
    final_unit_price: float = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NegotiationMessageResponse(BaseModel):
    id: int
    round_number: int
    sender: str
    message_content: str
    offer_price: float = None
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/task/{task_id}", response_model=List[NegotiationResponse])
async def get_negotiations_for_task(task_id: int, db: Session = Depends(get_db)):
    """Get all negotiations for a procurement task."""
    negotiations = db.query(Negotiation).filter(
        Negotiation.procurement_task_id == task_id
    ).all()
    
    return negotiations


@router.get("/{negotiation_id}/messages", response_model=List[NegotiationMessageResponse])
async def get_negotiation_messages(negotiation_id: int, db: Session = Depends(get_db)):
    """Get all messages in a negotiation."""
    messages = db.query(NegotiationMessage).filter(
        NegotiationMessage.negotiation_id == negotiation_id
    ).order_by(NegotiationMessage.created_at).all()
    
    return messages
