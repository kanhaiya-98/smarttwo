"""Supplier selection and discovery service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Dict, Optional
from app.models.supplier import Supplier, SupplierMedicine
from app.models.medicine import UrgencyLevel
import logging

logger = logging.getLogger(__name__)

class SupplierService:
    """Service for finding and ranking suppliers."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def find_best_suppliers(
        self, 
        medicine_id: int, 
        quantity: int,
        urgency: str = UrgencyLevel.MEDIUM
    ) -> List[Dict]:
        """
        Find and rank suppliers based on urgency and constraints.
        
        Ranking Logic:
        - CRITICAL: Prioritize lead_time (Fastest first), then reliability.
        - HIGH: Balanced approach (Score = 0.6*Speed + 0.4*Price).
        - MEDIUM/LOW: Prioritize price (Cheapest first).
        """
        # Find all suppliers with this medicine in stock
        candidates = self.db.query(Supplier, SupplierMedicine).join(
            SupplierMedicine, Supplier.id == SupplierMedicine.supplier_id
        ).filter(
            SupplierMedicine.medicine_id == medicine_id,
            SupplierMedicine.is_available == True,
            Supplier.is_active == True,
            Supplier.is_blacklisted == False,
            # Filter out suppliers with past quality issues (Requirement)
            # Assuming quality_rating is 0-5
            Supplier.quality_rating >= 3.0 
        ).all()
        
        results = []
        
        for supplier, supply in candidates:
            # check relationship status (contract terms, credit limits)
            # Simulation: If Total Cost > Credit Limit, skip or flag (soft check for MVP)
            # In Phase 2: We just log/consider it in scoring or filtering.
            
            # Calculate effective price (check bulk discounts)
            price = supply.base_price
            if supply.bulk_discount_threshold and quantity >= supply.bulk_discount_threshold:
                price = supply.bulk_discount_price
                
            # Score the supplier
            score = self._calculate_score(supplier, supply, urgency, price)
            
            results.append({
                "supplier": supplier,
                "supply_info": supply,
                "price": price,
                "total_cost": price * quantity,
                "lead_time": supply.lead_time_days,
                "score": score,
                "reason": self._get_selection_reason(supplier, urgency)
            })
            
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results

    def _calculate_score(self, supplier: Supplier, supply: SupplierMedicine, urgency: str, price: float) -> float:
        """Calculate weighted score based on urgency."""
        # Normalize metrics (0-1 scale approx)
        reliability = (supplier.reliability_score or 50) / 100
        speed_inv = 1 / (supply.lead_time_days or 7) # Higher is faster
        price_inv = 1 / (price or 100) # Higher is cheaper
        
        if urgency == UrgencyLevel.CRITICAL:
            # 70% Speed, 30% Reliability, Price ignored
            return (0.7 * speed_inv * 100) + (0.3 * reliability)
            
        elif urgency == UrgencyLevel.HIGH:
            # 50% Speed, 30% Reliability, 20% Price
            return (0.5 * speed_inv * 100) + (0.3 * reliability) + (0.2 * price_inv * 1000)
            
        else: # MEDIUM / LOW
            # 70% Price, 30% Reliability, Speed less important
            return (0.7 * price_inv * 1000) + (0.3 * reliability) + (0.1 * speed_inv * 10)

    def _get_selection_reason(self, supplier: Supplier, urgency: str) -> str:
        if urgency == "CRITICAL" and supplier.is_fast_delivery:
            return "Selected for fastest delivery time during critical shortage."
        if supplier.is_budget_supplier:
            return "Best price offered for non-critical stock replenishment."
        if supplier.is_bulk_supplier:
            return "Volume discount applied for large order."
        if supplier.reliability_score > 90:
            return "High reliability score preferred."
        return "Balanced choice of price and speed."
