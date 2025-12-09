"""API routes for procurement approvals."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApproveRequest(BaseModel):
    approved_by: str
    notes: str | None = None


class RejectRequest(BaseModel):
    rejected_by: str
    reason: str


class OverrideRequest(BaseModel):
    quote_id: int
    overridden_by: str
    reason: str


class PendingApproval(BaseModel):
    task_id: int
    medicine_id: int
    quantity: int
    urgency: str
    supplier_name: str
    unit_price: float
    total_price: float
    delivery_days: int
    reasoning: str
    created_at: str | None


@router.get("/pending", response_model=List[PendingApproval])
def get_pending_approvals(db: Session = Depends(get_db)):
    """Get all tasks pending approval."""
    approval_service = ApprovalService(db)
    pending = approval_service.get_pending_approvals()
    return pending


@router.post("/{task_id}/approve")
def approve_order(
    task_id: int,
    request: ApproveRequest,
    db: Session = Depends(get_db)
):
    """Approve a pending procurement task."""
    approval_service = ApprovalService(db)
    
    try:
        order = approval_service.approve_order(
            task_id=task_id,
            approved_by=request.approved_by,
            notes=request.notes
        )
        
        return {
            "status": "approved",
            "order_id": order.id,
            "po_number": order.po_number,
            "total_amount": order.total_amount,
            "message": f"Order {order.po_number} approved successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/reject")
def reject_order(
    task_id: int,
    request: RejectRequest,
    db: Session = Depends(get_db)
):
    """Reject a pending procurement task."""
    approval_service = ApprovalService(db)
    
    try:
        approval_service.reject_order(
            task_id=task_id,
            rejected_by=request.rejected_by,
            reason=request.reason
        )
        
        return {
            "status": "rejected",
            "task_id": task_id,
            "message": "Order rejected successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/override")
def override_decision(
    task_id: int,
    request: OverrideRequest,
    db: Session = Depends(get_db)
):
    """Override AI decision and select a different supplier."""
    approval_service = ApprovalService(db)
    
    try:
        order = approval_service.override_decision(
            task_id=task_id,
            quote_id=request.quote_id,
            overridden_by=request.overridden_by,
            reason=request.reason
        )
        
        return {
            "status": "overridden",
            "order_id": order.id,
            "po_number": order.po_number,
            "total_amount": order.total_amount,
            "message": f"Decision overridden, order {order.po_number} created"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/threshold")
def get_auto_approve_threshold():
    """Get the current auto-approve threshold."""
    return {
        "auto_approve_threshold": ApprovalService.AUTO_APPROVE_THRESHOLD,
        "currency": "USD",
        "message": f"Orders below ${ApprovalService.AUTO_APPROVE_THRESHOLD:.2f} are auto-approved"
    }
