"""API routes for order tracking."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.services.order_tracking_service import OrderTrackingService
from app.services.po_service import POService

router = APIRouter(prefix="/tracking", tags=["tracking"])


class UpdateStatusRequest(BaseModel):
    new_status: str
    notes: str | None = None


class MarkDeliveredRequest(BaseModel):
    received_by: str
    quality_check_passed: bool = True
    quantity_verified: bool = True
    notes: str | None = None


@router.get("/order/{order_id}")
def get_order_tracking(order_id: int, db: Session = Depends(get_db)):
    """Get tracking information for an order."""
    tracking_service = OrderTrackingService(db)
    
    try:
        timeline = tracking_service.get_order_timeline(order_id)
        
        from app.models.order import Order
        order = db.query(Order).get(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "order_id": order_id,
            "po_number": order.po_number,
            "status": order.status,
            "timeline": timeline,
            "tracking_notes": order.tracking_notes
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/order/{order_id}/status")
def update_order_status(
    order_id: int,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """Update order status."""
    tracking_service = OrderTrackingService(db)
    
    try:
        tracking_service.update_order_status(
            order_id=order_id,
            new_status=request.new_status,
            notes=request.notes
        )
        
        return {
            "status": "updated",
            "order_id": order_id,
            "new_status": request.new_status
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/order/{order_id}/delivered")
def mark_delivered(
    order_id: int,
    request: MarkDeliveredRequest,
    db: Session = Depends(get_db)
):
    """Mark order as delivered with verification details."""
    tracking_service = OrderTrackingService(db)
    
    try:
        tracking_service.mark_delivered(
            order_id=order_id,
            received_by=request.received_by,
            quality_check_passed=request.quality_check_passed,
            quantity_verified=request.quantity_verified,
            notes=request.notes
        )
        
        return {
            "status": "delivered",
            "order_id": order_id,
            "message": "Order marked as delivered"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active")
def get_active_orders(db: Session = Depends(get_db)):
    """Get all active (non-delivered) orders."""
    tracking_service = OrderTrackingService(db)
    orders = tracking_service.get_active_orders()
    return {"active_orders": orders}


@router.get("/delayed")
def get_delayed_orders(db: Session = Depends(get_db)):
    """Get orders past their expected delivery date."""
    tracking_service = OrderTrackingService(db)
    delayed = tracking_service.check_delayed_orders()
    return {"delayed_orders": delayed}


@router.get("/po/{po_number}")
def get_po_status(po_number: str, db: Session = Depends(get_db)):
    """Get PO status by PO number."""
    po_service = POService(db)
    
    try:
        status = po_service.get_po_status(po_number)
        return status
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/po/{po_number}/document")
def get_po_document(po_number: str, db: Session = Depends(get_db)):
    """Get PO document."""
    from app.models.order import Order
    order = db.query(Order).filter(Order.po_number == po_number).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="PO not found")
    
    po_service = POService(db)
    document = po_service.generate_po_document(order.id)
    
    return document


@router.get("/analytics")
def get_tracking_analytics(db: Session = Depends(get_db)):
    """Get analytics on orders and deliveries."""
    from app.models.order import Order
    from sqlalchemy import func
    
    # Count orders by status
    status_counts = db.query(
        Order.status, func.count(Order.id)
    ).group_by(Order.status).all()
    
    # Get active orders
    tracking_service = OrderTrackingService(db)
    active_orders = tracking_service.get_active_orders()
    delayed_orders = tracking_service.check_delayed_orders()
    
    # Calculate average delivery time for delivered orders
    from datetime import datetime
    delivered_orders = db.query(Order).filter(
        Order.status == 'DELIVERED',
        Order.delivered_at.isnot(None),
        Order.created_at.isnot(None)
    ).all()
    
    if delivered_orders:
        total_days = sum([
            (order.delivered_at - order.created_at).days
            for order in delivered_orders
        ])
        avg_delivery_days = total_days / len(delivered_orders)
    else:
        avg_delivery_days = None
    
    return {
        "status_breakdown": dict(status_counts),
        "active_orders_count": len(active_orders),
        "delayed_orders_count": len(delayed_orders),
        "delivered_orders_count": len(delivered_orders),
        "average_delivery_days": avg_delivery_days,
        "on_time_percentage": None  # TODO: Calculate from supplier performance
    }
