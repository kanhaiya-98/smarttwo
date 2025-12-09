"""API endpoints for supplier discovery."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.medicine import Medicine
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.email_thread import EmailThread
from app.models.email_message import EmailMessage
from app.services.supplier_discovery_service import SupplierDiscoveryService
from app.services.email_service import EmailService
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()


class StartDiscoveryRequest(BaseModel):
    medicine_id: int
    quantity: int


class DiscoveryResponse(BaseModel):
    task_id: int
    status: str
    message: str
    suppliers_found: int


class SupplierInfo(BaseModel):
    id: int
    name: str
    website: str
    email: str  # display_email
    location: str
    status: str
    emails_sent: int
    emails_received: int
    last_activity: str


class EmailMessageInfo(BaseModel):
    id: int
    sender: str  # display_sender
    recipient: str  # display_recipient
    subject: str
    body: str
    is_from_agent: bool
    quoted_price: float = None
    delivery_days: int = None
    timestamp: str


@router.post("/start", response_model=DiscoveryResponse)
async def start_discovery(
    request: StartDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """Start supplier discovery and send quote requests."""
    
    # Get medicine
    medicine = db.query(Medicine).filter(Medicine.id == request.medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    logger.info(f"🚀 Starting discovery for {medicine.name} ({request.quantity} units)")
    
    # Discover suppliers
    discovery_service = SupplierDiscoveryService(db, demo_mode=True)
    suppliers = discovery_service.discover_suppliers(
        medicine=medicine,
        quantity=request.quantity
    )
    
    
    # NOTE: Emails are NOT sent automatically during discovery
    # User will manually trigger email sending via "Send Email" button
    
    # Email sending moved to separate endpoint /send-email/{supplier_id}
    
    return DiscoveryResponse(
        task_id=request.medicine_id,  # Using medicine_id as task_id for simplicity
        status="completed",
        message=f"Discovery complete. Found {len(suppliers)} suppliers and sent quote requests.",
        suppliers_found=len(suppliers)
    )


@router.get("/suppliers/{task_id}", response_model=List[SupplierInfo])
async def get_discovered_suppliers(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get list of discovered suppliers for a task."""
    
    # For simplicity, get all suppliers (in production, filter by task_id)
    suppliers = db.query(DiscoveredSupplier).filter(
        DiscoveredSupplier.procurement_task_id == task_id
    ).all()
    
    if not suppliers:
        # If no task-specific suppliers, return all (demo mode)
        suppliers = db.query(DiscoveredSupplier).limit(10).all()
    
    result = []
    for supplier in suppliers:
        # Determine status
        if supplier.emails_received > 0:
            status = "REPLIED"
        elif supplier.emails_sent > 0:
            status = "EMAIL_SENT"
        else:
            status = "DISCOVERED"
        
        # Last activity
        last_activity = supplier.last_response_time or supplier.last_email_sent_at or supplier.created_at
        
        result.append(SupplierInfo(
            id=supplier.id,
            name=supplier.name,
            website=supplier.website or "",
            email=supplier.display_email or "",  # Show display_email!
            location=supplier.location or "",
            status=status,
            emails_sent=supplier.emails_sent or 0,
            emails_received=supplier.emails_received or 0,
            last_activity=last_activity.isoformat() if last_activity else ""
        )
    )
    
    return result


@router.get("/emails/{supplier_id}", response_model=List[EmailMessageInfo])
async def get_supplier_emails(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """Get email thread with a supplier."""
    
    # Get thread for supplier
    thread = db.query(EmailThread).filter(
        EmailThread.supplier_id == supplier_id
    ).first()
    
    if not thread:
        return []
    
    # Get messages
    messages = db.query(EmailMessage).filter(
        EmailMessage.thread_id == thread.id
    ).order_by(EmailMessage.created_at).all()
    
    result = []
    for msg in messages:
        timestamp = msg.sent_at or msg.received_at or msg.created_at
        
        result.append(EmailMessageInfo(
            id=msg.id,
            sender=msg.display_sender or msg.sender,  # Show display addresses!
            recipient=msg.display_recipient or msg.recipient,
            subject=msg.subject or "",
            body=msg.body or "",
            is_from_agent=msg.is_from_agent or False,
            quoted_price=msg.quoted_price,
            delivery_days=msg.delivery_days,
            timestamp=timestamp.isoformat() if timestamp else ""
        ))
    
    return result



@router.post("/send-email/{supplier_id}")
async def send_email_to_supplier(
    supplier_id: int,
    quantity: int = 5000,
    db: Session = Depends(get_db)
):
    """
    Manually send quote request email to a specific supplier.
    User clicks 'Send Email' button to trigger this.
    """
    supplier = db.query(DiscoveredSupplier).filter_by(id=supplier_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get medicine (using first medicine for demo, or can pass medicine_id)
    medicine = db.query(Medicine).first()
    
    if not medicine:
        raise HTTPException(status_code=404, detail="No medicine found")
    
    # Send email
    email_service = EmailService(demo_mode=True)
    
    try:
        thread = email_service.send_quote_request(
            db=db,
            supplier=supplier,
            medicine=medicine,
            quantity=quantity
        )
        
        logger.info(f"📧 Email sent to {supplier.display_email} (supplier_id: {supplier_id})")
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Email sent to {supplier.name}",
            "thread_id": thread.id,
            "supplier_id": supplier_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {supplier.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/check-inbox")
async def check_inbox(db: Session = Depends(get_db)):
    """Manually trigger inbox check for new replies."""
    
    email_service = EmailService(demo_mode=True)
    new_messages = email_service.check_for_replies(db)
    
    return {
        "status": "success",
        "new_messages": len(new_messages),
        "message": f"Checked inbox. Found {len(new_messages)} new replies."
    }
