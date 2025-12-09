"""Negotiator Agent - Gemini-powered negotiation message generation."""
import logging
from typing import List, Dict
import google.generativeai as genai

from app.config import settings
from app.models.quote_response import QuoteResponse
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.negotiation_round import NegotiationRound, NegotiationStatus
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)


class NegotiatorAgent:
    """AI negotiation agent using Gemini for message generation."""
    
    def __init__(self, db):
        self.db = db
        self.model = genai.GenerativeModel('gemini-pro') if settings.GOOGLE_API_KEY else None
    
    def analyze_quotes(self, quotes: List[QuoteResponse]) -> Dict[int, str]:
        """
        Analyze quotes and determine negotiation strategy for each supplier.
        
        Returns:
            Dict mapping supplier_id to strategy (price_match, bulk_discount, expedite, skip)
        """
        if len(quotes) < 2:
            return {}
        
        # Find best price and delivery
        best_price = min(q.unit_price for q in quotes)
        best_delivery = min(q.delivery_days for q in quotes)
        
        strategies = {}
        
        for quote in quotes:
            supplier_id = quote.supplier_id
            
            # Skip if already best on both metrics
            if quote.unit_price == best_price and quote.delivery_days == best_delivery:
                strategies[supplier_id] = "skip"
                continue
            
            # Determine strategy
            price_diff = ((quote.unit_price - best_price) / best_price) * 100
            delivery_diff = quote.delivery_days - best_delivery
            
            if price_diff > 5:  # More than 5% higher
                strategies[supplier_id] = "price_match"
            elif delivery_diff > 2:  # More than 2 days slower
                strategies[supplier_id] = "expedite"
            elif quote.stock_available and quote.stock_available > 10000:
                strategies[supplier_id] = "bulk_discount"
            else:
                strategies[supplier_id] = "skip"
        
        return strategies
    
    def generate_negotiation_message(
        self,
        supplier: DiscoveredSupplier,
        current_quote: QuoteResponse,
        all_quotes: List[QuoteResponse],
        strategy: str,
        round_number: int = 1
    ) -> str:
        """
        Generate negotiation email using Gemini.
        
        Args:
            supplier: The supplier to negotiate with
            current_quote: Their current quote
            all_quotes: All quotes for comparison context
            strategy: Negotiation strategy (price_match, bulk_discount, expedite)
            round_number: Which negotiation round (1-3)
        
        Returns:
            Negotiation email message
        """
        # Get market context
        best_price = min(q.unit_price for q in all_quotes)
        avg_delivery = sum(q.delivery_days for q in all_quotes) / len(all_quotes)
        
        # Build Gemini prompt
        prompt = f"""You are a professional procurement negotiator for a pharmacy. Generate a polite but firm negotiation email.

SUPPLIER: {supplier.name}
CURRENT QUOTE: ${current_quote.unit_price}/unit, {current_quote.delivery_days} days delivery
MARKET CONTEXT: Best price in market is ${best_price}/unit, average delivery {avg_delivery:.1f} days
NEGOTIATION ROUND: {round_number} of 3
STRATEGY: {strategy}

Generate a professional negotiation email that:
1. Thanks them for their quote
2. Mentions we're a regular customer (3,000-5,000 units monthly)
3. References competitive market pricing WITHOUT naming other suppliers
4. Makes a specific counter-offer based on strategy:
   - price_match: Ask to match best price (${best_price}/unit)
   - expedite: Ask for faster delivery ({int(avg_delivery)-1} days)
   - bulk_discount: Request volume discount for 5,000+ unit order
5. Keeps it under 150 words
6. Ends with looking forward to their response

Write ONLY the email body, no subject line."""

        try:
            if self.model:
                response = self.model.generate_content(prompt)
                return response.text
            else:
                # Fallback template if Gemini not available
                return self._fallback_template(supplier, current_quote, best_price, strategy)
                
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return self._fallback_template(supplier, current_quote, best_price, strategy)
    
    def _fallback_template(self, supplier, current_quote, best_price, strategy):
        """Fallback template if Gemini unavailable."""
        return f"""Hi {supplier.name},

Thank you for your quote of ${current_quote.unit_price}/unit with {current_quote.delivery_days} days delivery.

As a regular customer ordering 3,000-5,000 units monthly, we've received competitive offers from multiple suppliers. The current market rate is around ${best_price}/unit.

Given our consistent order volume, could you consider matching ${best_price + 0.02:.2f}/unit? This would allow us to proceed with a long-term partnership.

Looking forward to your response.

Best regards"""
    
    def start_negotiation(self, quote_id: int) -> NegotiationRound:
        """Start negotiation for a quote."""
        quote = self.db.query(QuoteResponse).get(quote_id)
        supplier = self.db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        # Get all quotes for context
        all_quotes = self.db.query(QuoteResponse).filter_by(
            procurement_task_id=quote.procurement_task_id
        ).all()
        
        # Analyze strategy
        strategies = self.analyze_quotes(all_quotes)
        strategy = strategies.get(supplier.id, "price_match")
        
        if strategy == "skip":
            logger.info(f"Skipping negotiation with {supplier.name} - already competitive")
            return None
        
        # Generate message
        message = self.generate_negotiation_message(
            supplier, quote, all_quotes, strategy, round_number=1
        )
        
        # Create negotiation round
        neg_round = NegotiationRound(
            supplier_id=supplier.id,
            quote_response_id=quote.id,
            round_number=1,
            our_message=message,
            our_counter_price=min(q.unit_price for q in all_quotes),
            status=NegotiationStatus.SENT
        )
        
        self.db.add(neg_round)
        self.db.commit()
        
        # Send email
        email_service = EmailService(demo_mode=True)
        # TODO: Implement send_negotiation_email method
        
        logger.info(f"Started negotiation with {supplier.name}")
        return neg_round
