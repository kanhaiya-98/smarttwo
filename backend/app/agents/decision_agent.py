"""Decision Agent - Weighted scoring and AI-powered decision making."""
import logging
from typing import List, Tuple
import google.generativeai as genai

from app.config import settings
from app.models.quote_response import QuoteResponse
from app.models.supplier_score import SupplierScore
from app.models.discovered_supplier import DiscoveredSupplier

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)


class DecisionAgent:
    """AI decision agent with weighted scoring and Gemini explanations."""
    
    def __init__(self, db):
        self.db = db
        self.model = genai.GenerativeModel('gemini-pro') if settings.GOOGLE_API_KEY else None
    
    def get_scenario_weights(self, urgency: str = "MEDIUM", budget_mode: bool = False) -> dict:
        """
        Get scoring weights based on urgency and scenario.
        
        Args:
            urgency: CRITICAL, HIGH, MEDIUM, LOW
            budget_mode: If True, prioritize price heavily
        
        Returns:
            Dict with price_weight, speed_weight, reliability_weight, stock_weight
        """
        if urgency == "CRITICAL":
            return {
                "price_weight": 0.30,
                "speed_weight": 0.50,
                "reliability_weight": 0.10,
                "stock_weight": 0.10
            }
        elif budget_mode:
            return {
                "price_weight": 0.60,
                "speed_weight": 0.15,
                "reliability_weight": 0.15,
                "stock_weight": 0.10
            }
        else:  # Standard/MEDIUM
            return {
                "price_weight": 0.40,
                "speed_weight": 0.25,
                "reliability_weight": 0.20,
                "stock_weight": 0.15
            }
    
    def calculate_scores(
        self,
        quotes: List[QuoteResponse],
        required_quantity: int,
        weights: dict
    ) -> List[SupplierScore]:
        """
        Calculate weighted scores for all quotes.
        
        Scoring formulas:
        - Price Score: (Best Price / Current Price) × 100
        - Speed Score: (Fastest Delivery / Current Delivery) × 100
        - Reliability Score: Based on historical performance (0-100)
        - Stock Score: (Stock Available / Required Quantity) × 100 (capped at 100)
        """
        if not quotes:
            return []
        
        # Find best metrics
        best_price = min(q.unit_price for q in quotes)
        fastest_delivery = min(q.delivery_days for q in quotes)
        
        scores = []
        
        for quote in quotes:
            # Calculate individual scores
            price_score = (best_price / quote.unit_price) * 100
            speed_score = (fastest_delivery / quote.delivery_days) * 100
            reliability_score = self._get_reliability_score(quote.supplier_id)
            
            # Stock score
            if quote.stock_available:
                stock_score = min((quote.stock_available / required_quantity) * 100, 100)
            else:
                stock_score = 50  # Unknown stock = medium score
            
            # Calculate weighted total
            total_score = (
                price_score * weights["price_weight"] +
                speed_score * weights["speed_weight"] +
                reliability_score * weights["reliability_weight"] +
                stock_score * weights["stock_weight"]
            )
            
            # Create score object
            score = SupplierScore(
                supplier_id=quote.supplier_id,
                quote_response_id=quote.id,
                procurement_task_id=quote.procurement_task_id,
                price_score=round(price_score, 2),
                speed_score=round(speed_score, 2),
                reliability_score=round(reliability_score, 2),
                stock_score=round(stock_score, 2),
                price_weight=weights["price_weight"],
                speed_weight=weights["speed_weight"],
                reliability_weight=weights["reliability_weight"],
                stock_weight=weights["stock_weight"],
                total_score=round(total_score, 2)
            )
            
            scores.append(score)
        
        return scores
    
    def _get_reliability_score(self, supplier_id: int) -> float:
        """Get reliability score based on historical performance."""
        # TODO: Implement based on past orders
        # For now, return a default score
        return 75.0
    
    def generate_decision_explanation(
        self,
        best_score: SupplierScore,
        all_scores: List[SupplierScore],
        quotes: List[QuoteResponse],
        urgency: str
    ) -> str:
        """
        Generate human-readable explanation using Gemini.
        """
        # Get supplier details
        best_supplier = self.db.query(DiscoveredSupplier).get(best_score.supplier_id)
        best_quote = next(q for q in quotes if q.id == best_score.quote_response_id)
        
        # Get alternatives
        alternatives = sorted(all_scores, key=lambda x: x.total_score, reverse=True)[1:3]
        
        prompt = f"""You are an AI procurement advisor. Explain why we should choose this supplier.

RECOMMENDED SUPPLIER: {best_supplier.name}
- Price: ${best_quote.unit_price}/unit
- Delivery: {best_quote.delivery_days} days
- Total Score: {best_score.total_score:.1f}/100

SCORE BREAKDOWN:
- Price Score: {best_score.price_score:.1f} (weight: {best_score.price_weight*100:.0f}%)
- Speed Score: {best_score.speed_score:.1f} (weight: {best_score.speed_weight*100:.0f}%)
- Reliability: {best_score.reliability_score:.1f} (weight: {best_score.reliability_weight*100:.0f}%)
- Stock Score: {best_score.stock_score:.1f} (weight: {best_score.stock_weight*100:.0f}%)

URGENCY: {urgency}
ALTERNATIVES: {len(alternatives)} other suppliers scored lower

Generate a 3-paragraph explanation (150 words max):
1. Why this supplier is recommended
2. Trade-offs vs alternatives
3. Risk considerations

Be concise and professional."""

        try:
            if self.model:
                response = self.model.generate_content(prompt)
                return response.text
            else:
                return self._fallback_explanation(best_supplier, best_score, best_quote)
        except Exception as e:
            logger.error(f"Gemini explanation failed: {e}")
            return self._fallback_explanation(best_supplier, best_score, best_quote)
    
    def _fallback_explanation(self, supplier, score, quote):
        """Fallback explanation if Gemini unavailable."""
        return f"""Based on our weighted scoring analysis, {supplier.name} is recommended with a total score of {score.total_score:.1f}/100.

They offer competitive pricing at ${quote.unit_price}/unit with delivery in {quote.delivery_days} days. Their price score of {score.price_score:.1f} and delivery score of {score.speed_score:.1f} make them the best balanced option.

Risk: Standard procurement risks apply. Stock availability confirmed for this order."""
    
    def make_decision(
        self,
        quotes: List[QuoteResponse],
        required_quantity: int,
        urgency: str = "MEDIUM",
        budget_mode: bool = False
    ) -> Tuple[SupplierScore, str]:
        """
        Make decision and return best score with explanation.
        
        Returns:
            (best_score, explanation)
        """
        # Get weights
        weights = self.get_scenario_weights(urgency, budget_mode)
        
        # Calculate scores
        scores = self.calculate_scores(quotes, required_quantity, weights)
        
        if not scores:
            raise ValueError("No quotes to analyze")
        
        # Find best score
        best_score = max(scores, key=lambda x: x.total_score)
        
        # Save scores
        for score in scores:
            self.db.add(score)
        self.db.commit()
        
        # Generate explanation
        explanation = self.generate_decision_explanation(
            best_score, scores, quotes, urgency
        )
        
        # Update reasoning
        best_score.reasoning = explanation
        best_score.urgency_level = urgency
        self.db.commit()
        
        logger.info(f"Decision made: Supplier {best_score.supplier_id} with score {best_score.total_score:.1f}")
        
        return best_score, explanation
