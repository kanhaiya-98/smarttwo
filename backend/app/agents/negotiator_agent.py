"""Negotiator agent for price negotiation with suppliers."""
from typing import Dict, Any, List
from datetime import datetime
from app.agents.base_agent import BaseAgent
from app.workflows.state import Quote, Negotiation, NegotiationRound
from app.core.gemini_client import gemini_client
from app.models.negotiation import Negotiation as NegotiationModel, NegotiationMessage
from sqlalchemy.orm import Session
import logging
import asyncio

logger = logging.getLogger(__name__)


class NegotiatorAgent(BaseAgent):
    """Agent responsible for negotiating with suppliers."""
    
    def __init__(self, db: Session, max_rounds: int = 3):
        self.db = db
        self.max_rounds = max_rounds
        super().__init__(
            name="Negotiator Agent",
            description="Negotiates prices and terms with suppliers"
        )
    
    def _create_tools(self) -> list:
        """Negotiator uses Gemini directly, no specific tools needed."""
        return []
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for negotiator agent."""
        return """You are an expert Negotiator Agent for pharmacy procurement.
Your goals:
1. Achieve better prices and terms than initial quotes
2. Maintain professional supplier relationships
3. Use data and competitor information strategically
4. Know when to accept an offer vs. push for better terms
5. Balance cost savings with delivery speed and reliability

Be persuasive but respectful. Use concrete numbers and value propositions."""
    
    async def _execute_logic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute negotiator agent logic."""
        state["current_stage"] = "NEGOTIATOR_AGENT"
        
        quotes = state.get("quotes", [])
        if not quotes:
            state["errors"].append("No quotes available for negotiation")
            return state
        
        # Identify negotiation opportunities
        negotiation_targets = self._identify_negotiation_targets(quotes, state)
        
        if not negotiation_targets:
            logger.info("No negotiation opportunities identified")
            state["negotiation_complete"] = True
            return state
        
        # Conduct negotiations with selected suppliers
        negotiations = []
        for target in negotiation_targets:
            negotiation = await self._negotiate_with_supplier(
                supplier_id=target["supplier_id"],
                supplier_name=target["supplier_name"],
                initial_quote=target["quote"],
                state=state
            )
            negotiations.append(negotiation)
        
        state["negotiations"] = negotiations
        state["negotiation_complete"] = True
        
        logger.info(f"Completed {len(negotiations)} negotiations")
        return state
    
    def _identify_negotiation_targets(
        self,
        quotes: List[Quote],
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify which suppliers are worth negotiating with.
        
        Args:
            quotes: All received quotes
            state: Current workflow state
            
        Returns:
            List of suppliers to negotiate with
        """
        if not quotes:
            return []
        
        # Sort quotes by price
        sorted_quotes = sorted(quotes, key=lambda q: q["unit_price"])
        cheapest_price = sorted_quotes[0]["unit_price"]
        
        targets = []
        
        for quote in quotes:
            reasons = []
            
            # Target 1: Fast delivery but expensive
            if quote.get("delivery_days", 999) <= 2 and quote["unit_price"] > cheapest_price * 1.15:
                reasons.append("Fast delivery with premium price")
            
            # Target 2: Good delivery but not cheapest
            if 2 < quote.get("delivery_days", 999) <= 4 and quote["unit_price"] > cheapest_price:
                reasons.append("Moderate delivery speed with negotiable price")
            
            # Target 3: Bulk discount available
            if quote.get("bulk_discount_available"):
                reasons.append("Bulk discount opportunity")
            
            # Target 4: High reliability but higher price (for critical items)
            # Would need supplier reliability data from state
            
            if reasons:
                targets.append({
                    "supplier_id": quote["supplier_id"],
                    "supplier_name": quote["supplier_name"],
                    "quote": quote,
                    "negotiation_reasons": reasons
                })
        
        # Limit to top 3-4 negotiation targets
        return targets[:4]
    
    async def _negotiate_with_supplier(
        self,
        supplier_id: int,
        supplier_name: str,
        initial_quote: Quote,
        state: Dict[str, Any]
    ) -> Negotiation:
        """
        Conduct multi-round negotiation with a supplier.
        
        Args:
            supplier_id: Supplier ID
            supplier_name: Supplier name
            initial_quote: Initial quote from supplier
            state: Workflow state
            
        Returns:
            Negotiation results
        """
        # Create negotiation record
        db_negotiation = NegotiationModel(
            procurement_task_id=state["task_id"],
            supplier_id=supplier_id,
            status="IN_PROGRESS",
            max_rounds=self.max_rounds
        )
        self.db.add(db_negotiation)
        self.db.commit()
        self.db.refresh(db_negotiation)
        
        negotiation = {
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "initial_quote": initial_quote,
            "rounds": [],
            "final_price": initial_quote["unit_price"],
            "final_delivery_days": initial_quote["delivery_days"],
            "status": "IN_PROGRESS",
            "savings": 0.0
        }
        
        # Prepare negotiation context
        all_quotes = state.get("quotes", [])
        best_price = min(q["unit_price"] for q in all_quotes)
        
        context = {
            "best_competitor_price": best_price,
            "urgency": state["urgency_level"],
            "monthly_volume": state.get("monthly_volume", 3000),
            "relationship": "Regular customer",
        }
        
        # Conduct negotiation rounds
        current_price = initial_quote["unit_price"]
        current_delivery = initial_quote["delivery_days"]
        
        for round_num in range(1, self.max_rounds + 1):
            # Determine negotiation strategy for this round
            if round_num == 1:
                context["strategy"] = "Request price match with best competitor and faster delivery"
                target_price = best_price + 0.02  # Slightly above best price
            elif round_num == 2:
                context["strategy"] = "Offer volume commitment for better terms"
                target_price = (current_price + best_price) / 2
            else:
                context["strategy"] = "Final offer with multi-month commitment"
                target_price = best_price + 0.01
            
            # Generate negotiation message using Gemini
            our_message = await gemini_client.generate_negotiation_message(
                supplier_name=supplier_name,
                medicine_name=state["medicine_name"],
                quantity=state["required_quantity"],
                initial_quote=initial_quote,
                negotiation_context=context,
                round_number=round_num
            )
            
            # Simulate supplier response (in production, this would be actual response)
            supplier_response = await self._simulate_supplier_response(
                our_message=our_message,
                target_price=target_price,
                current_price=current_price,
                round_num=round_num
            )
            
            # Save round to database
            db_message = NegotiationMessage(
                negotiation_id=db_negotiation.id,
                round_number=round_num,
                sender="BUYER_AGENT",
                message_content=our_message,
                offer_price=target_price,
                generated_by_ai=True
            )
            self.db.add(db_message)
            
            round_data = {
                "round_number": round_num,
                "our_message": our_message,
                "supplier_response": supplier_response["message"],
                "our_offer_price": target_price,
                "supplier_counter_price": supplier_response.get("counter_price"),
                "status": supplier_response["status"]
            }
            
            negotiation["rounds"].append(round_data)
            
            # Check if supplier accepted
            if supplier_response["status"] == "ACCEPTED":
                negotiation["final_price"] = supplier_response.get("counter_price", target_price)
                negotiation["final_delivery_days"] = supplier_response.get("delivery_days", current_delivery)
                negotiation["status"] = "SUCCESSFUL"
                break
            elif supplier_response["status"] == "REJECTED":
                negotiation["status"] = "FAILED"
                break
            else:  # COUNTER_OFFER
                current_price = supplier_response.get("counter_price", current_price)
        
        # Calculate savings
        negotiation["savings"] = (initial_quote["unit_price"] - negotiation["final_price"]) * state["required_quantity"]
        
        # Update database
        db_negotiation.status = negotiation["status"]
        db_negotiation.final_unit_price = negotiation["final_price"]
        db_negotiation.final_delivery_days = negotiation["final_delivery_days"]
        db_negotiation.savings_amount = negotiation["savings"]
        db_negotiation.completed_at = datetime.utcnow()
        self.db.commit()
        
        return negotiation
    
    async def _simulate_supplier_response(
        self,
        our_message: str,
        target_price: float,
        current_price: float,
        round_num: int
    ) -> Dict[str, Any]:
        """
        Simulate supplier response to negotiation.
        In production, this would parse actual supplier emails/messages.
        
        Args:
            our_message: Our negotiation message
            target_price: Our target price
            current_price: Current offer price
            round_num: Current round number
            
        Returns:
            Simulated supplier response
        """
        import random
        
        # Simulate decision making
        price_gap = current_price - target_price
        acceptance_probability = max(0.2, 1.0 - (price_gap / current_price) * 5)
        
        # Increase acceptance probability in later rounds
        acceptance_probability += round_num * 0.15
        
        if random.random() < acceptance_probability:
            # Accept with slight adjustment
            final_price = target_price + random.uniform(0, 0.02)
            return {
                "status": "ACCEPTED",
                "message": f"We can accept ${final_price:.2f}/unit for this order. Let's proceed.",
                "counter_price": round(final_price, 2),
                "delivery_days": None
            }
        
        elif round_num >= 3:  # Last round
            return {
                "status": "REJECTED",
                "message": f"We appreciate your offer but cannot go below ${current_price:.2f}/unit.",
                "counter_price": current_price
            }
        
        else:
            # Counter offer
            counter_price = (current_price + target_price) / 2 + random.uniform(-0.01, 0.01)
            return {
                "status": "COUNTER_OFFER",
                "message": f"We can offer ${counter_price:.2f}/unit if you commit to 6 months.",
                "counter_price": round(counter_price, 2)
            }
