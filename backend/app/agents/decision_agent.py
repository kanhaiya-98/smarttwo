"""Decision agent for final supplier selection."""
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.workflows.state import Quote, Negotiation, Decision as DecisionState, ScoringDetails
from app.core.gemini_client import gemini_client
from app.models.negotiation import Decision as DecisionModel
from sqlalchemy.orm import Session
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DecisionAgent(BaseAgent):
    """Agent responsible for making final supplier selection decision."""
    
    def __init__(self, db: Session):
        self.db = db
        super().__init__(
            name="Decision Agent",
            description="Makes final supplier selection with weighted scoring"
        )
    
    def _create_tools(self) -> list:
        """Decision agent uses calculation logic, no specific tools needed."""
        return []
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for decision agent."""
        return """You are a Decision Agent for pharmacy procurement.
Your role:
1. Analyze all quotes and negotiation outcomes
2. Calculate weighted scores based on multiple criteria
3. Apply scenario-based logic (urgency, budget, quality)
4. Explain decisions clearly with data-driven reasoning
5. Balance cost optimization with risk mitigation

Make logical, defensible decisions that optimize for the pharmacy's needs."""
    
    async def _execute_logic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute decision agent logic."""
        state["current_stage"] = "DECISION_AGENT"
        
        # Collect all final offers
        final_offers = self._collect_final_offers(state)
        
        if not final_offers:
            state["errors"].append("No valid offers available for decision")
            return state
        
        # Calculate scores for all offers
        scores = self._calculate_scores(final_offers, state)
        
        # Select best supplier
        best_supplier = self._select_best_supplier(scores, state)
        
        # Generate decision reasoning using Gemini
        reasoning = await self._generate_reasoning(
            medicine_name=state["medicine_name"],
            all_scores=scores,
            selected=best_supplier,
            state=state
        )
        
        # Create decision object
        decision = {
            "selected_supplier_id": best_supplier["supplier_id"],
            "selected_supplier_name": best_supplier["supplier_name"],
            "final_unit_price": best_supplier["final_price"],
            "final_delivery_days": best_supplier["final_delivery_days"],
            "total_amount": best_supplier["final_price"] * state["required_quantity"],
            "reasoning": reasoning,
            "all_scores": scores,
            "decision_factors": {
                "urgency_level": state["urgency_level"],
                "budget_available": state.get("budget_available"),
                "weights_applied": best_supplier.get("weights", {}),
            }
        }
        
        state["decision"] = decision
        state["decision_reasoning"] = reasoning
        
        # Determine if approval needed
        total_amount = decision["total_amount"]
        state["requires_approval"] = total_amount >= settings.AUTO_APPROVE_THRESHOLD
        
        # Save decision to database
        db_decision = DecisionModel(
            procurement_task_id=state["task_id"],
            selected_supplier_id=decision["selected_supplier_id"],
            all_scores={"scores": [s for s in scores]},
            winning_score=best_supplier["total_score"],
            reasoning_text=reasoning,
            decision_factors=decision["decision_factors"],
            urgency_level=state["urgency_level"],
            budget_constraint=state.get("budget_available"),
            requires_approval=state["requires_approval"]
        )
        self.db.add(db_decision)
        self.db.commit()
        
        logger.info(f"Decision: Selected {best_supplier['supplier_name']} with score {best_supplier['total_score']:.2f}")
        return state
    
    def _collect_final_offers(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect final offers from quotes and negotiations.
        
        Args:
            state: Workflow state
            
        Returns:
            List of final offers with best prices
        """
        quotes = state.get("quotes", [])
        negotiations = state.get("negotiations", [])
        
        # Create a map of supplier_id to best offer
        offers_map = {}
        
        # Start with initial quotes
        for quote in quotes:
            offers_map[quote["supplier_id"]] = {
                "supplier_id": quote["supplier_id"],
                "supplier_name": quote["supplier_name"],
                "final_price": quote["unit_price"],
                "final_delivery_days": quote["delivery_days"],
                "quantity_available": quote["quantity_available"],
                "source": "INITIAL_QUOTE"
            }
        
        # Update with negotiation results (if better)
        for negotiation in negotiations:
            supplier_id = negotiation["supplier_id"]
            if negotiation["status"] == "SUCCESSFUL":
                # Use negotiated price if better
                if supplier_id not in offers_map or negotiation["final_price"] < offers_map[supplier_id]["final_price"]:
                    offers_map[supplier_id].update({
                        "final_price": negotiation["final_price"],
                        "final_delivery_days": negotiation["final_delivery_days"],
                        "source": "NEGOTIATED"
                    })
        
        return list(offers_map.values())
    
    def _calculate_scores(
        self,
        offers: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> List[ScoringDetails]:
        """
        Calculate weighted scores for all offers.
        
        Args:
            offers: List of final offers
            state: Workflow state
            
        Returns:
            List of scoring details
        """
        # Determine weights based on scenario
        weights = self._get_scenario_weights(state)
        
        # Find best values for normalization
        prices = [o["final_price"] for o in offers]
        delivery_times = [o["final_delivery_days"] for o in offers]
        
        cheapest_price = min(prices)
        fastest_delivery = min(delivery_times)
        
        scores = []
        
        for offer in offers:
            # Calculate individual scores (0-100)
            price_score = (cheapest_price / offer["final_price"]) * 100
            speed_score = (fastest_delivery / offer["final_delivery_days"]) * 100
            
            # Reliability score - would come from supplier history
            # For now, use a placeholder (in production, query from DB)
            reliability_score = 85.0  # Default
            
            # Stock availability score
            stock_score = min(
                (offer.get("quantity_available", state["required_quantity"]) / state["required_quantity"]) * 100,
                100
            )
            
            # Calculate weighted total
            total_score = (
                price_score * weights["price"] +
                speed_score * weights["speed"] +
                reliability_score * weights["reliability"] +
                stock_score * weights["stock"]
            )
            
            scores.append({
                "supplier_id": offer["supplier_id"],
                "supplier_name": offer["supplier_name"],
                "price_score": round(price_score, 2),
                "speed_score": round(speed_score, 2),
                "reliability_score": round(reliability_score, 2),
                "stock_score": round(stock_score, 2),
                "total_score": round(total_score, 2),
                "weights": weights,
                "final_price": offer["final_price"],
                "final_delivery_days": offer["final_delivery_days"]
            })
        
        return scores
    
    def _get_scenario_weights(self, state: Dict[str, Any]) -> Dict[str, float]:
        """
        Determine scoring weights based on scenario.
        
        Args:
            state: Workflow state
            
        Returns:
            Weight dictionary
        """
        urgency = state.get("urgency_level", "MEDIUM")
        budget_available = state.get("budget_available", float('inf'))
        
        # Default weights
        weights = {
            "price": 0.40,
            "speed": 0.25,
            "reliability": 0.20,
            "stock": 0.15
        }
        
        # Adjust based on urgency
        if urgency == "CRITICAL":
            weights = {
                "price": 0.20,
                "speed": 0.50,
                "reliability": 0.20,
                "stock": 0.10
            }
        elif urgency == "HIGH":
            weights = {
                "price": 0.30,
                "speed": 0.35,
                "reliability": 0.20,
                "stock": 0.15
            }
        
        # Adjust if budget constrained
        required_amount = state["required_quantity"] * 0.20  # Estimated average
        if budget_available < required_amount * 1.2:
            weights["price"] = 0.60
            weights["speed"] = 0.15
            weights["reliability"] = 0.15
            weights["stock"] = 0.10
        
        return weights
    
    def _select_best_supplier(
        self,
        scores: List[ScoringDetails],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select the best supplier based on scores.
        
        Args:
            scores: List of all scores
            state: Workflow state
            
        Returns:
            Best supplier details
        """
        # Sort by total score
        sorted_scores = sorted(scores, key=lambda s: s["total_score"], reverse=True)
        best = sorted_scores[0]
        
        return best
    
    async def _generate_reasoning(
        self,
        medicine_name: str,
        all_scores: List[ScoringDetails],
        selected: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable decision reasoning using Gemini.
        
        Args:
            medicine_name: Medicine name
            all_scores: All supplier scores
            selected: Selected supplier
            state: Workflow state
            
        Returns:
            Decision reasoning text
        """
        # Prepare data for Gemini
        all_quotes = []
        for score in all_scores:
            all_quotes.append({
                "supplier_name": score["supplier_name"],
                "unit_price": score["final_price"],
                "delivery_days": score["final_delivery_days"],
                "total_score": score["total_score"]
            })
        
        selected_supplier = {
            "name": selected["supplier_name"],
            "unit_price": selected["final_price"],
            "delivery_days": selected["final_delivery_days"],
            "total_score": selected["total_score"]
        }
        
        scoring_details = {
            "price_score": selected["price_score"],
            "speed_score": selected["speed_score"],
            "reliability_score": selected["reliability_score"],
            "stock_score": selected["stock_score"],
            "price_weight": selected["weights"]["price"] * 100,
            "speed_weight": selected["weights"]["speed"] * 100,
            "reliability_weight": selected["weights"]["reliability"] * 100,
            "stock_weight": selected["weights"]["stock"] * 100,
            "urgency": state["urgency_level"],
            "budget_status": "Tight" if state.get("budget_available", float('inf')) < 10000 else "Normal"
        }
        
        reasoning = await gemini_client.generate_decision_reasoning(
            medicine_name=medicine_name,
            all_quotes=all_quotes,
            selected_supplier=selected_supplier,
            scoring_details=scoring_details
        )
        
        return reasoning
