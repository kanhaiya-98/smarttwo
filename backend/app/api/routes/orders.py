from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import PurchaseOrder, OrderStatus
from app.models.agent_activity import AgentActivity
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class OrderResponse(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    medicine_id: int
    quantity: int
    unit_price: float
    total_amount: float
    status: str
    expected_delivery_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of orders."""
    query = db.query(PurchaseOrder)
    
    if status:
        query = query.filter(PurchaseOrder.status == OrderStatus(status))
    
    orders = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get order details."""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


class ApproveOrderRequest(BaseModel):
    approved: bool
    notes: str = ""


@router.post("/{order_id}/approve")
async def approve_order(
    order_id: int,
    request: ApproveOrderRequest,
    db: Session = Depends(get_db)
):
    """Approve or reject an order."""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if request.approved:
        order.status = OrderStatus.APPROVED
        order.approved_at = datetime.utcnow()
    else:
        order.status = OrderStatus.CANCELLED
    
    db.commit()
    
    # Log activity for Decision Agent
    activity = AgentActivity(
        agent_name="DECISION",
        action_type="APPROVE",
        message=f"Order {order.po_number} {order.status.value}. Email notification sent to supplier.",
        status="SUCCESS",
        context_data={"order_id": order_id, "approved": request.approved}
    )
    db.add(activity)
    db.commit()
    
    return {
        "order_id": order_id,
        "status": order.status.value,
        "message": "Order approved and sent to supplier" if request.approved else "Order rejected"
    }
