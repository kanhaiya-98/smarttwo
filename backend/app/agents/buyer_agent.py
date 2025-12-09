"""Buyer agent for quote requests and collection."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain.tools import BaseTool, tool
from app.agents.base_agent import BaseAgent
from app.workflows.state import Quote
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supplier import Supplier, SupplierMedicine
from app.models.negotiation import Quote as QuoteModel
import logging
import asyncio

logger = logging.getLogger(__name__)


class BuyerAgent(BaseAgent):
    """Agent responsible for discovering suppliers and requesting quotes."""
    
    def __init__(self, db: Session):
        self.db = db
        super().__init__(
            name="Buyer Agent",
            description="Discovers eligible suppliers and requests quotes"
        )
    
    def _create_tools(self) -> list[BaseTool]:
        """Create tools for buyer agent."""
        return [
            # Tools would be defined here using @tool decorator
            # For simplicity, we'll handle logic directly in _execute_logic
        ]
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for buyer agent."""
        return """You are a Buyer Agent for a pharmacy supply chain system.
Your responsibilities:
1. Identify eligible suppliers for medicines
2. Filter out unreliable or blacklisted suppliers
3. Send quote requests to suppliers
4. Collect and validate quote responses
5. Handle timeouts and non-responsive suppliers

Be thorough and ensure all data is accurate."""
    
    async def _execute_logic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute buyer agent logic."""
        state["current_stage"] = "BUYER_AGENT"
        
        # Step 1: Discover eligible suppliers
        suppliers = await self._discover_suppliers(
            medicine_id=state["medicine_id"],
            urgency=state["urgency_level"]
        )
        state["eligible_suppliers"] = suppliers
        
        if not suppliers:
            state["errors"].append("No eligible suppliers found")
            return state
        
        # Step 2: Send quote requests to all suppliers
        state["quote_request_sent_at"] = datetime.utcnow()
        quotes = await self._request_quotes(
            suppliers=suppliers,
            medicine_name=state["medicine_name"],
            quantity=state["required_quantity"],
            urgency=state["urgency_level"],
            task_id=state["task_id"]
        )
        
        state["quotes"] = quotes
        
        if not quotes:
            state["errors"].append("No quotes received from suppliers")
            return state
        
        logger.info(f"Received {len(quotes)} quotes from suppliers")
        return state
    
    async def _discover_suppliers(
        self,
        medicine_id: int,
        urgency: str
    ) -> List[Dict[str, Any]]:
        """
        Discover eligible suppliers for a medicine.
        
        Args:
            medicine_id: Medicine ID
            urgency: Urgency level
            
        Returns:
            List of eligible supplier details
        """
        # Query suppliers who have this medicine
        supplier_medicines = self.db.query(SupplierMedicine).filter(
            SupplierMedicine.medicine_id == medicine_id,
            SupplierMedicine.is_available == True
        ).all()
        
        supplier_ids = [sm.supplier_id for sm in supplier_medicines]
        
        # Get supplier details
        suppliers = self.db.query(Supplier).filter(
            Supplier.id.in_(supplier_ids),
            Supplier.is_active == True,
            Supplier.is_blacklisted == False
        ).all()
        
        # Sort by reliability if urgent
        if urgency in ["CRITICAL", "HIGH"]:
            suppliers = sorted(suppliers, key=lambda s: s.reliability_score, reverse=True)
        
        return [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "email": s.email,
                "has_api": s.has_api_integration,
                "api_endpoint": s.api_endpoint,
                "typical_delivery_days": s.typical_delivery_days,
                "reliability_score": s.reliability_score,
                "is_fast_delivery": s.is_fast_delivery,
                "is_bulk_supplier": s.is_bulk_supplier,
            }
            for s in suppliers
        ]
    
    async def _request_quotes(
        self,
        suppliers: List[Dict[str, Any]],
        medicine_name: str,
        quantity: int,
        urgency: str,
        task_id: int
    ) -> List[Quote]:
        """
        Send quote requests to all suppliers in parallel.
        
        Args:
            suppliers: List of supplier details
            medicine_name: Medicine name
            quantity: Required quantity
            urgency: Urgency level
            task_id: Procurement task ID
            
        Returns:
            List of quotes received
        """
        # In a real system, this would send actual API requests or emails
        # For this implementation, we'll simulate quote responses
        
        tasks = []
        for supplier in suppliers:
            tasks.append(
                self._send_quote_request(
                    supplier=supplier,
                    medicine_name=medicine_name,
                    quantity=quantity,
                    urgency=urgency,
                    task_id=task_id
                )
            )
        
        # Wait for all quote requests with timeout
        timeout_hours = 2  # From settings
        try:
            quotes = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_hours * 3600
            )
            
            # Filter out exceptions
            valid_quotes = [q for q in quotes if isinstance(q, dict) and not isinstance(q, Exception)]
            return valid_quotes
        
        except asyncio.TimeoutError:
            logger.warning("Quote request timeout reached")
            return []
    
    async def _send_quote_request(
        self,
        supplier: Dict[str, Any],
        medicine_name: str,
        quantity: int,
        urgency: str,
        task_id: int
    ) -> Quote:
        """
        Send quote request to a single supplier.
        
        Args:
            supplier: Supplier details
            medicine_name: Medicine name
            quantity: Required quantity
            urgency: Urgency level
            task_id: Task ID
            
        Returns:
            Quote from supplier
        """
        # Simulate API call or email sending
        # In production, this would make actual HTTP requests to supplier APIs
        
        logger.info(f"Sending quote request to {supplier['name']}")
        
        # Simulate response time
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # For demonstration, generate simulated quotes
        # In production, parse actual supplier responses
        import random
        
        base_price = 0.15 + random.uniform(0, 0.10)
        delivery_days = supplier["typical_delivery_days"] + random.randint(-1, 2)
        
        quote_data = {
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "unit_price": round(base_price, 2),
            "delivery_days": max(1, delivery_days),
            "quantity_available": quantity + random.randint(0, 5000),
            "stock_availability": "IN_STOCK",
            "response_time_seconds": random.randint(30, 300),
            "bulk_discount_available": supplier["is_bulk_supplier"],
            "bulk_discount_price": round(base_price * 0.9, 2) if supplier["is_bulk_supplier"] else None,
            "bulk_discount_quantity": 10000 if supplier["is_bulk_supplier"] else None,
        }
        
        # Save quote to database
        db_quote = QuoteModel(
            procurement_task_id=task_id,
            supplier_id=supplier["id"],
            unit_price=quote_data["unit_price"],
            quantity_available=quote_data["quantity_available"],
            delivery_days=quote_data["delivery_days"],
            bulk_discount_available=quote_data["bulk_discount_available"],
            bulk_discount_price=quote_data["bulk_discount_price"],
            bulk_discount_quantity=quote_data["bulk_discount_quantity"],
            response_time_seconds=quote_data["response_time_seconds"],
        )
        self.db.add(db_quote)
        self.db.commit()
        
        return quote_data
