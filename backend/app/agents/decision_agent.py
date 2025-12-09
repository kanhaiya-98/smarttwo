"""Decision Agent - Weighted scoring algorithm + Gemini explanation."""
import google.generativeai as genai
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models.quote_response import QuoteResponse
from app.models.supplier_score import SupplierScore
from app.models.discovered_supplier import DiscoveredSupplier

logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GOOGLE_API_KEY)


class DecisionAgent:
    """AI agent for intelligent procurement decisions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def get_scenario_weights(self, urgency: str = "MEDIUM", budget_mode: bool = False) -> Dict[str, float]:
        """Get scoring weights based on scenario."""
        if urgency == "CRITICAL":
            return {"price": 0.30, "speed": 0.50, "reliability": 0.10, "stock": 0.10}
        elif budget_mode:
            return {"price": 0.60, "speed": 0.15, "reliability": 0.125, "stock": 0.125}
        else:
            return {"price": 0.40, "speed": 0.25, "reliability": 0.20, "stock": 0.15}
    
    def calculate_scores(
        self,
        quotes: List[QuoteResponse],
        required_quantity: int = 5000,
        urgency: str = "MEDIUM",
        budget_mode: bool = False
    ) -> List[SupplierScore]:
        """Calculate weighted scores."""
        if not quotes:
            return []
        
        weights = self.get_scenario_weights(urgency, budget_mode)
        scores = []
        
        cheapest_price = min(q.unit_price for q in quotes)
        fastest_delivery = min(q.delivery_days for q in quotes)
        
        for quote in quotes:
            price_score = (cheapest_price / quote.unit_price) * 100
            speed_score = (fastest_delivery / quote.delivery_days) * 100
            reliability_score = 75.0  # Default for now
            stock_score = min((quote.stock_available or 5000) / required_quantity * 100, 100)
            
            total_score = (
                price_score * weights['price'] +
                speed_score * weights['speed'] +
                reliability_score * weights['reliability'] +
                stock_score * weights['stock']
            )
            
            score_record = SupplierScore(
                supplier_id=quote.supplier_id,
                quote_id=quote.id,
                procurement_task_id=quote.procurement_task_id,
                price_score=round(price_score, 2),
                speed_score=round(speed_score, 2),
                reliability_score=round(reliability_score, 2),
                stock_score=round(stock_score, 2),
                total_score=round(total_score, 2),
                urgency_level=urgency,
                budget_mode=str(budget_mode)
            )
            scores.append(score_record)
        
        scores.sort(key=lambda x: x.total_score, reverse=True)
        for rank, score in enumerate(scores, 1):
            score.rank = rank
        
        return scores
    
    def generate_decision_explanation(
        self, selected_score: SupplierScore, all_scores: List[SupplierScore], quotes: List[QuoteResponse]
    ) -> str:
        """Use Gemini to explain decision."""
        supplier = self.db.query(DiscoveredSupplier).get(selected_score.supplier_id)
        quote = next((q for q in quotes if q.id == selected_score.quote_id), None)
        
        prompt = f"""Explain procurement decision professionally.

Selected: {supplier.name if supplier else 'Unknown'}
Price: ${quote.unit_price:.2f}/unit, Delivery: {quote.delivery_days} days
Score: {selected_score.total_score:.1f}/100

Explain in 3 paragraphs why this supplier was chosen over alternatives."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"Selected {supplier.name if supplier else 'supplier'} with score {selected_score.total_score:.1f} based on balanced pricing and delivery."
    
    def make_decision(
        self, quotes: List[QuoteResponse], required_quantity: int = 5000, urgency: str = "MEDIUM"
    ) -> Tuple[SupplierScore, str]:
        """Complete decision process."""
        scores = self.calculate_scores(quotes, required_quantity, urgency)
        if not scores:
            return None, "No quotes available."
        
        best_score = scores[0]
        explanation = self.generate_decision_explanation(best_score, scores, quotes)
        best_score.reasoning = explanation
        
        for score in scores:
            self.db.add(score)
        self.db.commit()
        
        return best_score, explanation
