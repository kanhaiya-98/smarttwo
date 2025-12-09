"""Order tracking and lifecycle management service."""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.medicine import Medicine
from app.models.medicine import ProcurementTask

logger = logging.getLogger(__name__)


class OrderTrackingService:
    """Service for tracking order lifecycle and delivery status."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_order_status(
        self,
        order_id: int,
        new_status: str,
        notes: Optional[str] = None
    ):
        """
        Update order status through lifecycle.
        
        Valid statuses: PLACED → CONFIRMED → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
        """
        valid_statuses = [
            'PLACED', 'SENT_TO_SUPPLIER', 'CONFIRMED',
            'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'
        ]
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        old_status = order.status
        order.status = new_status
        
        if notes:
            order.tracking_notes = f"{order.tracking_notes or ''}\n{datetime.utcnow().isoformat()}: {notes}"
        
        # Set delivered_at if status is DELIVERED
        if new_status == 'DELIVERED' and not order.delivered_at:
            order.delivered_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Order {order.po_number} status: {old_status} → {new_status}")
    
    def mark_delivered(
        self,
        order_id: int,
        received_by: str,
        quality_check_passed: bool = True,
        quantity_verified: bool = True,
        notes: Optional[str] = None
    ):
        """Mark order as delivered with verification details."""
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.status = 'DELIVERED'
        order.delivered_at = datetime.utcnow()
        
        delivery_notes = f"Received by: {received_by}\n"
        delivery_notes += f"Quality check: {'✓ Passed' if quality_check_passed else '✗ Failed'}\n"
        delivery_notes += f"Quantity verified: {'✓ Correct' if quantity_verified else '✗ Mismatch'}\n"
        
        if notes:
            delivery_notes += f"Notes: {notes}"
        
        order.tracking_notes = f"{order.tracking_notes or ''}\n{delivery_notes}"
        
        self.db.commit()
        
        # Log supplier performance
        self._log_delivery_performance(order)
        
        logger.info(f"Order {order.po_number} marked as delivered")
    
    def _log_delivery_performance(self, order: Order):
        """Log supplier performance metrics for this delivery."""
        if not order.delivered_at or not order.created_at:
            return
        
        # Calculate actual delivery time
        actual_delivery_days = (order.delivered_at - order.created_at).days
        expected_delivery_days = order.expected_delivery_days
        
        # Determine if delivery was on time
        on_time = actual_delivery_days <= expected_delivery_days
        
        # Update supplier statistics
        supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
        if supplier:
            # Update delivery count
            if not hasattr(supplier, 'total_deliveries'):
                supplier.total_deliveries = 0
                supplier.on_time_deliveries = 0
            
            supplier.total_deliveries += 1
            
            if on_time:
                supplier.on_time_deliveries += 1
            
            # Update reliability score (simple percentage for now)
            if supplier.total_deliveries > 0:
                supplier.reliability_score = (supplier.on_time_deliveries / supplier.total_deliveries) * 100
            
            self.db.commit()
        
        logger.info(
            f"Delivery performance logged: {actual_delivery_days} days "
            f"(expected: {expected_delivery_days}, on-time: {on_time})"
        )
    
    def get_order_timeline(self, order_id: int) -> List[Dict]:
        """Get timeline of events for an order."""
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        timeline = []
        
        # Order placed
        if order.created_at:
            timeline.append({
                'event': 'Order Placed',
                'timestamp': order.created_at.isoformat(),
                'status': 'PLACED',
                'icon': '📝'
            })
        
        # Order approved
        if order.approved_at:
            timeline.append({
                'event': 'Order Approved',
                'timestamp': order.approved_at.isoformat(),
                'status': 'APPROVED',
                'icon': '✅',
                'details': f'Approved by {order.approved_by}'
            })
        
        # Estimated delivery
        if order.expected_delivery_days:
            expected_date = (order.created_at or datetime.utcnow()) + timedelta(days=order.expected_delivery_days)
            timeline.append({
                'event': 'Expected Delivery',
                'timestamp': expected_date.isoformat(),
                'status': 'EXPECTED',
                'icon': '📦',
                'is_estimate': True
            })
        
        # Delivered
        if order.delivered_at:
            timeline.append({
                'event': 'Delivered',
                'timestamp': order.delivered_at.isoformat(),
                'status': 'DELIVERED',
                'icon': '✅'
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def get_active_orders(self) -> List[Dict]:
        """Get all orders that are not yet delivered."""
        orders = self.db.query(Order).filter(
            Order.status.in_(['PLACED', 'SENT_TO_SUPPLIER', 'CONFIRMED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY'])
        ).all()
        
        result = []
        for order in orders:
            supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
            medicine = self.db.query(Medicine).get(order.medicine_id)
            
            # Calculate days until expected delivery
            if order.created_at:
                expected_delivery = order.created_at + timedelta(days=order.expected_delivery_days)
                days_remaining = (expected_delivery - datetime.utcnow()).days
            else:
                days_remaining = None
            
            result.append({
                'order_id': order.id,
                'po_number': order.po_number,
                'status': order.status,
                'supplier_name': supplier.name if supplier else 'Unknown',
                'medicine_name': medicine.name if medicine else 'Unknown',
                'quantity': order.quantity,
                'total_amount': order.total_amount,
                'expected_delivery_days': order.expected_delivery_days,
                'days_remaining': days_remaining,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        return result
    
    def check_delayed_orders(self) -> List[Dict]:
        """Check for orders that are past their expected delivery date."""
        delayed = []
        
        orders = self.db.query(Order).filter(
            Order.status.in_(['PLACED', 'SENT_TO_SUPPLIER', 'CONFIRMED', 'IN_TRANSIT']),
            Order.delivered_at.is_(None)
        ).all()
        
        for order in orders:
            if not order.created_at:
                continue
            
            expected_delivery = order.created_at + timedelta(days=order.expected_delivery_days)
            
            if datetime.utcnow() > expected_delivery:
                days_delayed = (datetime.utcnow() - expected_delivery).days
                
                supplier = self.db.query(DiscoveredSupplier).get(order.supplier_id)
                
                delayed.append({
                    'order_id': order.id,
                    'po_number': order.po_number,
                    'supplier_name': supplier.name if supplier else 'Unknown',
                    'days_delayed': days_delayed,
                    'expected_delivery': expected_delivery.isoformat(),
                    'status': order.status
                })
        
        return delayed
