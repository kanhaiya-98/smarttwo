"""Approval service for human-in-the-loop procurement decisions."""
import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.medicine import ProcurementTask
from app.models.quote_response import QuoteResponse
from app.models.supplier_score import SupplierScore
from app.models.discovered_supplier import DiscoveredSupplier

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for managing procurement approvals."""
    
    #Auto-approve threshold (orders below this don't need manual approval)
    AUTO_APPROVE_THRESHOLD = 1000.0
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_approval_request(
        self,
        task_id: int,
        selected_score: SupplierScore,
        decision_reasoning: str
    ) -> Dict:
        """
        Create an approval request for a procurement decision.
        
        Returns:
            {
                'requires_approval': bool,
                'approval_id': int or None,
                'auto_approved': bool,
                'order': Order object if auto-approved
            }
        """
        task = self.db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        quote = self.db.query(QuoteResponse).get(selected_score.quote_id)
        if not quote:
            raise ValueError(f"Quote {selected_score.quote_id} not found")
        
        supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        # Check if auto-approval is allowed
        if quote.total_price < self.AUTO_APPROVE_THRESHOLD:
            logger.info(
                f"Auto-approving order ${quote.total_price:.2f} "
                f"(below threshold ${self.AUTO_APPROVE_THRESHOLD:.2f})"
            )
            
            # Create order immediately
            order = self._create_order(
                task=task,
                quote=quote,
                supplier=supplier,
                decision_reasoning=decision_reasoning,
                approved_by="AUTO_SYSTEM"
            )
            
            task.status = 'APPROVED'
            self.db.commit()
            
            return {
                'requires_approval': False,
                'auto_approved': True,
                'order': order
            }
        
        # Manual approval required
        logger.info(
            f"Manual approval required for order ${quote.total_price:.2f} "
            f"(above threshold ${self.AUTO_APPROVE_THRESHOLD:.2f})"
        )
        
        task.status = 'PENDING_APPROVAL'
        task.notes = f"Awaiting approval - {decision_reasoning}"
        self.db.commit()
        
        return {
            'requires_approval': True,
            'auto_approved': False,
            'task_id': task_id,
            'quote_id': quote.id,
            'supplier_name': supplier.name if supplier else 'Unknown',
            'total_price': quote.total_price,
            'reasoning': decision_reasoning
        }
    
    def approve_order(
        self,
        task_id: int,
        approved_by: str,
        notes: Optional[str] = None
    ) -> Order:
        """Approve a pending procurement task."""
        task = self.db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status != 'PENDING_APPROVAL':
            raise ValueError(f"Task {task_id} is not pending approval (status: {task.status})")
        
        # Get the best score
        best_score = self.db.query(SupplierScore).filter(
            SupplierScore.procurement_task_id == task_id,
            SupplierScore.rank == 1
        ).first()
        
        if not best_score:
            raise ValueError("No supplier score found for this task")
        
        quote = self.db.query(QuoteResponse).get(best_score.quote_id)
        supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        # Create order
        order = self._create_order(
            task=task,
            quote=quote,
            supplier=supplier,
            decision_reasoning=best_score.reasoning or '',
            approved_by=approved_by,
            approval_notes=notes
        )
        
        task.status = 'APPROVED'
        if notes:
            task.notes = f"{task.notes or ''}\nApproval: {notes}"
        self.db.commit()
        
        logger.info(f"Order approved by {approved_by} for task {task_id}")
        
        return order
    
    def reject_order(
        self,
        task_id: int,
        rejected_by: str,
        reason: str
    ):
        """Reject a pending procurement task."""
        task = self.db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.status = 'REJECTED'
        task.notes = f"Rejected by {rejected_by}: {reason}"
        self.db.commit()
        
        logger.info(f"Task {task_id} rejected by {rejected_by}: {reason}")
    
    def override_decision(
        self,
        task_id: int,
        quote_id: int,
        overridden_by: str,
        reason: str
    ) -> Order:
        """Override AI decision and select a different supplier."""
        task = self.db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        quote = self.db.query(QuoteResponse).get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        # Log the override
        logger.warning(
            f"Decision overridden for task {task_id} by {overridden_by}: {reason}"
        )
        
        # Create order with override flag
        order = self._create_order(
            task=task,
            quote=quote,
            supplier=supplier,
            decision_reasoning=f"MANUAL OVERRIDE: {reason}",
            approved_by=overridden_by,
            approval_notes=f"Overridden - Original reasoning: {reason}"
        )
        
        task.status = 'APPROVED'
        task.notes = f"Decision overridden by {overridden_by}: {reason}"
        self.db.commit()
        
        return order
    
    def _create_order(
        self,
        task: ProcurementTask,
        quote: QuoteResponse,
        supplier: DiscoveredSupplier,
        decision_reasoning: str,
        approved_by: str,
        approval_notes: Optional[str] = None
    ) -> Order:
        """Internal method to create an order."""
        from app.services.po_service import POService
        
        # Generate PO number
        po_service = POService(self.db)
        po_number = po_service.generate_po_number()
        
        # Create order
        order = Order(
            po_number=po_number,
            procurement_task_id=task.id,
            supplier_id=quote.supplier_id,
            medicine_id=task.medicine_id,
            quantity=task.quantity_needed or 5000,
            unit_price=quote.unit_price,
            total_amount=quote.total_price,
            expected_delivery_days=quote.delivery_days,
            status='PLACED',
            approved_by=approved_by,
            decision_reasoning=decision_reasoning,
            approval_notes=approval_notes
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(
            f"Order created: {po_number} for ${quote.total_price:.2f} "
            f"from {supplier.name if supplier else 'Unknown'}"
        )
        
        return order
    
    def get_pending_approvals(self) -> list:
        """Get all tasks pending approval."""
        tasks = self.db.query(ProcurementTask).filter(
            ProcurementTask.status == 'PENDING_APPROVAL'
        ).all()
        
        result = []
        for task in tasks:
            # Get best score
            best_score = self.db.query(SupplierScore).filter(
                SupplierScore.procurement_task_id == task.id,
                SupplierScore.rank == 1
            ).first()
            
            if best_score:
                quote = self.db.query(QuoteResponse).get(best_score.quote_id)
                supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
                
                result.append({
                    'task_id': task.id,
                    'medicine_id': task.medicine_id,
                    'quantity': task.quantity_needed,
                    'urgency': task.urgency,
                    'supplier_name': supplier.name if supplier else 'Unknown',
                    'unit_price': quote.unit_price,
                    'total_price': quote.total_price,
                    'delivery_days': quote.delivery_days,
                    'reasoning': best_score.reasoning,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                })
        
        return result
