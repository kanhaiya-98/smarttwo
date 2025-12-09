"""Purchase Order (PO) generation service."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.medicine import Medicine

logger = logging.getLogger(__name__)


class POService:
    """Service for generating and managing purchase orders."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_po_number(self) -> str:
        """
        Generate unique PO number in format: PO-YYYYMMDD-XXXXXX
        """
        today = datetime.utcnow().strftime('%Y%m%d')
        
        # Get count of POs created today
        from sqlalchemy import func
        today_count = self.db.query(func.count(Order.id)).filter(
            Order.po_number.like(f'PO-{today}%')
        ).scalar() or 0
        
        # Generate sequential number
        sequential = str(today_count + 1).zfill(6)
        po_number = f'PO-{today}-{sequential}'
        
        return po_number
    
    def generate_po_document(self, order_id: int) -> Dict:
        """
        Generate PO document data for PDF generation or email.
        
        Returns dictionary with PO details formatted for display/PDF.
        """
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
        medicine = self.db.query(Medicine).get(order.medicine_id)
        
        # Calculate expected delivery date
        expected_delivery = datetime.utcnow() + timedelta(days=order.expected_delivery_days)
        
        # Calculate payment due date (Net 30)
        payment_due = datetime.utcnow() + timedelta(days=30)
        
        po_document = {
            'po_number': order.po_number,
            'issue_date': order.created_at.strftime('%Y-%m-%d') if order.created_at else datetime.utcnow().strftime('%Y-%m-%d'),
            'status': order.status,
            
            # Supplier details
            'supplier': {
                'name': supplier.name if supplier else 'Unknown',
                'email': supplier.display_email if supplier else '',
                'domain': supplier.domain if supplier else '',
                'reliability_score': supplier.reliability_score if supplier else 0
            },
            
            # Medicine details
            'line_items': [{
                'item_number': 1,
                'description': medicine.name if medicine else 'Unknown Medicine',
                'dosage': medicine.dosage if medicine else '',
                'form': medicine.form if medicine else '',
                'quantity': order.quantity,
                'unit_price': order.unit_price,
                'total': order.total_amount
            }],
            
            # Pricing
            'subtotal': order.total_amount,
            'tax': 0.0,  # TODO: Calculate tax if applicable
            'shipping': 0.0,  # TODO: Add shipping if applicable
            'total': order.total_amount,
            
            # Terms
            'expected_delivery_date': expected_delivery.strftime('%Y-%m-%d'),
            'expected_delivery_days': order.expected_delivery_days,
            'payment_terms': 'Net 30',
            'payment_due_date': payment_due.strftime('%Y-%m-%d'),
            
            # Approval
            'approved_by': order.approved_by,
            'approval_date': order.approved_at.strftime('%Y-%m-%d') if order.approved_at else datetime.utcnow().strftime('%Y-%m-%d'),
            
            # Notes
            'notes': order.approval_notes or '',
            'special_instructions': self._get_special_instructions(order)
        }
        
        return po_document
    
    def _get_special_instructions(self, order: Order) -> str:
        """Generate special instructions based on order urgency"""
        from app.models.procurement_task import ProcurementTask
        
        task = self.db.query(ProcurementTask).get(order.procurement_task_id)
        
        instructions = []
        
        if task and task.urgency == 'CRITICAL':
            instructions.append("⚠️ URGENT: This is a critical order. Please prioritize delivery.")
        elif task and task.urgency == 'HIGH':
            instructions.append("Priority order - expedited delivery requested.")
        
        instructions.append("Please confirm receipt and provide tracking information.")
        instructions.append("Quality inspection required upon delivery.")
        instructions.append(f"Expiry date must be at least 12 months from delivery date.")
        
        return '\n'.join(instructions)
    
    def send_po_to_supplier(self, order_id: int) -> Dict:
        """
        Send PO to supplier via email.
        
        In production, this would generate PDF and email it.
        For this demo, we'll just log it.
        """
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
        po_doc = self.generate_po_document(order_id)
        
        # TODO: Generate PDF from po_doc
        # TODO: Send via email using EmailService
        
        # For now, just update order status
        order.status = 'SENT_TO_SUPPLIER'
        self.db.commit()
        
        logger.info(
            f"PO {order.po_number} sent to {supplier.name if supplier else 'supplier'} "
            f"at {supplier.display_email if supplier else 'email'}"
        )
        
        return {
            'status': 'sent',
            'po_number': order.po_number,
            'supplier_email': supplier.display_email if supplier else '',
            'sent_at': datetime.utcnow().isoformat()
        }
    
    def get_po_status(self, po_number: str) -> Dict:
        """Get status of a PO by number."""
        order = self.db.query(Order).filter(Order.po_number == po_number).first()
        
        if not order:
            raise ValueError(f"PO {po_number} not found")
        
        supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
        medicine = self.db.query(Medicine).get(order.medicine_id)
        
        return {
            'po_number': order.po_number,
            'status': order.status,
            'supplier_name': supplier.name if supplier else 'Unknown',
            'medicine_name': medicine.name if medicine else 'Unknown',
            'quantity': order.quantity,
            'total_amount': order.total_amount,
            'expected_delivery_days': order.expected_delivery_days,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
        }
