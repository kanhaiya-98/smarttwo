"""Negotiator Agent - AI-powered supplier negotiation using Gemini."""
import google.generativeai as genai
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.config import settings
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.quote_response import QuoteResponse
from app.models.negotiation_round import NegotiationRound
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)


class NegotiatorAgent:
    """AI agent that negotiates with suppliers using Gemini."""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.email_service = EmailService(demo_mode=True)
        self.max_rounds = 3
    
    def analyze_quotes(self, quotes: List[QuoteResponse]) -> Dict[int, str]:
        """Identify negotiation strategies for each supplier."""
        if not quotes or len(quotes) < 2:
            return {}
        
        strategies = {}
        cheapest_price = min(q.unit_price for q in quotes)
        fastest_delivery = min(q.delivery_days for q in quotes)
        
        for quote in quotes:
            supplier_id = quote.supplier_id
            
            if quote.unit_price == cheapest_price and quote.delivery_days == fastest_delivery:
                strategies[supplier_id] = "skip"
            elif quote.delivery_days <= fastest_delivery + 1 and quote.unit_price > cheapest_price * 1.1:
                strategies[supplier_id] = "price_match"
            elif quote.unit_price <= cheapest_price * 1.1 and quote.delivery_days > fastest_delivery + 2:
                strategies[supplier_id] = "expedite"
            else:
                strategies[supplier_id] = "price_match"
        
        return strategies
    
    def generate_negotiation_message(
        self,
        supplier: DiscoveredSupplier,
        current_quote: QuoteResponse,
        all_quotes: List[QuoteResponse],
        strategy: str,
        round_number: int = 1
    ) -> str:
        """Use Gemini to generate negotiation email."""
        cheapest_price = min(q.unit_price for q in all_quotes)
        fastest_delivery = min(q.delivery_days for q in all_quotes)
        
        prompt = f"""Professional procurement negotiation email.

Supplier: {supplier.name}
Their Quote: ${current_quote.unit_price:.2f}/unit, {current_quote.delivery_days} days
Best Price Available: ${cheapest_price:.2f}/unit
Fastest Delivery: {fastest_delivery} days
Strategy: {strategy}
Round: {round_number}

Write a respectful negotiation email requesting better terms. Mention we're regular customers (3,000-5,000 units monthly). Be specific with counter-offer. 3-4 paragraphs. Professional tone.

Email body only (no subject):"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini failed: {e}")
            return f"Dear {supplier.name} Team,\n\nThank you for your quote of ${current_quote.unit_price:.2f}/unit. We've received competitive offers at ${cheapest_price:.2f}/unit. As a regular customer, could you match this pricing?\n\nBest regards,\nProcurement Team"
    
    def start_negotiation(
        self,
        supplier_id: int,
        quote_id: int,
        all_quotes: List[QuoteResponse],
        strategy: str
    ) -> NegotiationRound:
        """Initiate negotiation with supplier."""
        supplier = self.db.query(DiscoveredSupplier).get(supplier_id)
        quote = self.db.query(QuoteResponse).get(quote_id)
        
        message = self.generate_negotiation_message(
            supplier, quote, all_quotes, strategy, 1
        )
        
        cheapest = min(q.unit_price for q in all_quotes)
        our_offer = round(cheapest * 1.05, 2)
        
        round_record = NegotiationRound(
            supplier_id=supplier_id,
            procurement_task_id=quote.procurement_task_id,
            round_number=1,
            our_message=message,
            our_offer_price=our_offer,
            status="SENT"
        )
        self.db.add(round_record)
        self.db.commit()
        
        try:
            self.email_service._send_via_smtp(
                to=supplier.actual_email,
                subject=f"Quote Follow-up - {supplier.name}",
                body=message
            )
            logger.info(f"Negotiation sent to {supplier.name}")
        except Exception as e:
            logger.error(f"Email failed: {e}")
            round_record.status = "FAILED"
            self.db.commit()
        
        return round_record
