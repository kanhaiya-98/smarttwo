"""Quote management service."""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.quote_response import QuoteResponse
from app.models.medicine import ProcurementTask
from app.models.discovered_supplier import DiscoveredSupplier

logger = logging.getLogger(__name__)


class QuoteService:
    """Service for managing supplier quotes."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_quotes_for_task(self, task_id: int) -> List[QuoteResponse]:
        """Get all quotes for a procurement task."""
        return self.db.query(QuoteResponse).filter(
            QuoteResponse.procurement_task_id == task_id
        ).all()
    
    def get_quote_summary(self, task_id: int) -> Dict:
        """Get summary of quotes for a task."""
        quotes = self.get_quotes_for_task(task_id)
        
        if not quotes:
            return {
                'total_quotes': 0,
                'awaiting_quotes': True,
                'timeout_reached': self._check_timeout(task_id)
            }
        
        prices = [q.unit_price for q in quotes]
        delivery_times = [q.delivery_days for q in quotes]
        
        return {
            'total_quotes': len(quotes),
            'cheapest_price': min(prices),
            'fastest_delivery': min(delivery_times),
            'average_price': sum(prices) / len(prices),
            'price_range': {
                'min': min(prices),
                'max': max(prices),
                'spread_percent': ((max(prices) - min(prices)) / min(prices) * 100)
            },
            'quotes': [self._quote_to_dict(q) for q in quotes],
            'awaiting_quotes': False,
            'timeout_reached': self._check_timeout(task_id)
        }
    
    def _quote_to_dict(self, quote: QuoteResponse) -> Dict:
        """Convert quote to dictionary."""
        supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        return {
            'id': quote.id,
            'supplier_id': quote.supplier_id,
            'supplier_name': supplier.name if supplier else 'Unknown',
            'unit_price': quote.unit_price,
            'total_price': quote.total_price,
            'delivery_days': quote.delivery_days,
            'stock_available': quote.stock_available,
            'notes': quote.notes,
            'responded_at': quote.responded_at.isoformat() if quote.responded_at else None
        }
    
    def _check_timeout(self, task_id: int) -> bool:
        """Check if quote collection has timed out (2 hours)."""
        task = self.db.query(ProcurementTask).get(task_id)
        if not task:
            return False
        
        timeout_threshold = datetime.utcnow() - timedelta(hours=2)
        return task.created_at < timeout_threshold
    
    def should_start_negotiation(self, task_id: int) -> bool:
        """
        Determine if we should start negotiation.
        
        Criteria:
        - Have at least 2 quotes
        - OR timeout reached with at least 1 quote
        """
        quotes = self.get_quotes_for_task(task_id)
        quote_count = len(quotes)
        timeout_reached = self._check_timeout(task_id)
        
        if quote_count >= 2:
            return True
        
        if timeout_reached and quote_count >= 1:
            logger.info(f"Timeout reached for task {task_id} with {quote_count} quote(s)")
            return True
        
        return False
    
    def detect_price_spike(self, task_id: int, medicine_id: int) -> Dict:
        """
        Detect if current quotes show price spikes vs historical average.
        
        Returns:
            {
                'spike_detected': bool,
                'current_avg': float,
                'historical_avg': float,
                'spike_percent': float
            }
        """
        quotes = self.get_quotes_for_task(task_id)
        
        if not quotes:
            return {'spike_detected': False}
        
        current_avg = sum(q.unit_price for q in quotes) / len(quotes)
        
        # Get historical quotes for this medicine (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        historical_quotes = self.db.query(QuoteResponse).join(
            ProcurementTask
        ).filter(
            and_(
                ProcurementTask.medicine_id == medicine_id,
                QuoteResponse.responded_at >= thirty_days_ago,
                QuoteResponse.procurement_task_id != task_id  # Exclude current task
            )
        ).all()
        
        if not historical_quotes:
            # No historical data
            return {
                'spike_detected': False,
                'current_avg': current_avg,
                'historical_avg': None,
                'spike_percent': 0
            }
        
        historical_avg = sum(q.unit_price for q in historical_quotes) / len(historical_quotes)
        spike_percent = ((current_avg - historical_avg) / historical_avg) * 100
        
        # Alert if price is >30% higher than historical
        spike_detected = spike_percent > 30
        
        if spike_detected:
            logger.warning(
                f"Price spike detected for medicine {medicine_id}: "
                f"current ${current_avg:.2f} vs historical ${historical_avg:.2f} "
                f"({spike_percent:.1f}% increase)"
            )
        
        return {
            'spike_detected': spike_detected,
            'current_avg': current_avg,
            'historical_avg': historical_avg,
            'spike_percent': spike_percent
        }
    
    def create_comparison_table(self, task_id: int) -> List[Dict]:
        """Create sortable comparison table data for frontend."""
        quotes = self.get_quotes_for_task(task_id)
        
        if not quotes:
            return []
        
        # Calculate min values for color coding
        min_price = min(q.unit_price for q in quotes)
        max_price = max(q.unit_price for q in quotes)
        min_delivery = min(q.delivery_days for q in quotes)
        max_delivery = max(q.delivery_days for q in quotes)
        
        comparison = []
        
        for quote in quotes:
            supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
            
            # Color coding logic
            if quote.unit_price == min_price:
                price_color = 'green'
            elif quote.unit_price > min_price * 1.2:  # 20% more expensive
                price_color = 'red'
            else:
                price_color = 'yellow'
            
            if quote.delivery_days == min_delivery:
                delivery_color = 'green'
            elif quote.delivery_days > min_delivery * 1.5:
                delivery_color = 'red'
            else:
                delivery_color = 'yellow'
            
            comparison.append({
                'quote_id': quote.id,
                'supplier_id': quote.supplier_id,
                'supplier_name': supplier.name if supplier else 'Unknown',
                'unit_price': quote.unit_price,
                'total_price': quote.total_price,
                'delivery_days': quote.delivery_days,
                'stock_available': quote.stock_available,
                'notes': quote.notes,
                'price_color': price_color,
                'delivery_color': delivery_color,
                'reliability_score': 75,  # TODO: Get from supplier history
                'responded_at': quote.responded_at.isoformat() if quote.responded_at else None
            })
        
        # Sort by total score (price + delivery weighted)
        comparison.sort(key=lambda x: (x['unit_price'] * 0.6 + x['delivery_days'] * 0.4))
        
        return comparison
