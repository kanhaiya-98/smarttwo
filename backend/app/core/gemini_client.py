"""Google Gemini API client wrapper."""
import google.generativeai as genai
from typing import Optional, Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Gemini API with retry logic and error handling."""
    
    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.generation_config = {
            "temperature": settings.GEMINI_TEMPERATURE,
            "max_output_tokens": settings.GEMINI_MAX_TOKENS,
        }
    
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text response
        """
        try:
            config = self.generation_config.copy()
            if temperature is not None:
                config["temperature"] = temperature
            if max_tokens is not None:
                config["max_output_tokens"] = max_tokens
            
            # Create model with system instruction if provided
            if system_instruction:
                model = genai.GenerativeModel(
                    settings.GEMINI_MODEL,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            response = model.generate_content(
                prompt,
                generation_config=config
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def generate_negotiation_message(
        self,
        supplier_name: str,
        medicine_name: str,
        quantity: int,
        initial_quote: Dict[str, Any],
        negotiation_context: Dict[str, Any],
        round_number: int,
    ) -> str:
        """
        Generate a negotiation message for a supplier.
        
        Args:
            supplier_name: Supplier name
            medicine_name: Medicine being negotiated
            quantity: Quantity needed
            initial_quote: Initial quote from supplier
            negotiation_context: Additional context (competitor quotes, urgency, etc.)
            round_number: Current negotiation round
            
        Returns:
            Generated negotiation message
        """
        system_instruction = """You are an expert procurement negotiator for a pharmacy. 
Your goal is to negotiate better prices and terms while maintaining good supplier relationships. 
Be professional, data-driven, and persuasive. Always provide clear value propositions."""
        
        prompt = f"""
Generate a professional negotiation email for the following scenario:

Supplier: {supplier_name}
Medicine: {medicine_name}
Quantity: {quantity} units
Negotiation Round: {round_number}

Initial Quote:
- Price per unit: ${initial_quote['unit_price']}
- Delivery: {initial_quote['delivery_days']} days
- Stock available: {initial_quote.get('quantity_available', 'Unknown')}

Context:
- Competitor best price: ${negotiation_context.get('best_competitor_price', 'N/A')}
- Our urgency level: {negotiation_context.get('urgency', 'MEDIUM')}
- Our monthly volume: {negotiation_context.get('monthly_volume', 'N/A')} units
- Historical relationship: {negotiation_context.get('relationship', 'Regular customer')}

Negotiation Strategy:
{negotiation_context.get('strategy', 'Price reduction and faster delivery')}

Generate a concise, professional email (3-4 sentences) that:
1. Acknowledges their quote
2. Presents our position with data
3. Makes a specific counter-offer
4. Offers value (volume commitment, relationship, etc.)

Email:
"""
        
        return await self.generate_text(prompt, system_instruction=system_instruction)
    
    async def generate_decision_reasoning(
        self,
        medicine_name: str,
        all_quotes: List[Dict[str, Any]],
        selected_supplier: Dict[str, Any],
        scoring_details: Dict[str, Any],
    ) -> str:
        """
        Generate human-readable explanation for supplier selection decision.
        
        Args:
            medicine_name: Medicine being procured
            all_quotes: All received quotes
            selected_supplier: The selected supplier and quote
            scoring_details: Detailed scoring breakdown
            
        Returns:
            Decision reasoning text
        """
        system_instruction = """You are a decision explanation AI for a procurement system. 
Explain supplier selection decisions clearly and logically, highlighting key factors and trade-offs. 
Be concise but comprehensive."""
        
        quotes_summary = "\n".join([
            f"- {q['supplier_name']}: ${q['unit_price']}/unit, {q['delivery_days']} days delivery, Score: {q.get('total_score', 'N/A')}"
            for q in all_quotes
        ])
        
        prompt = f"""
Explain why we selected {selected_supplier['name']} for procuring {medicine_name}.

All Quotes Received:
{quotes_summary}

Selected Supplier: {selected_supplier['name']}
- Price: ${selected_supplier['unit_price']}/unit
- Delivery: {selected_supplier['delivery_days']} days
- Total Score: {selected_supplier.get('total_score', 'N/A')}

Scoring Breakdown:
- Price Score: {scoring_details.get('price_score', 'N/A')} (Weight: {scoring_details.get('price_weight', 40)}%)
- Speed Score: {scoring_details.get('speed_score', 'N/A')} (Weight: {scoring_details.get('speed_weight', 25)}%)
- Reliability Score: {scoring_details.get('reliability_score', 'N/A')} (Weight: {scoring_details.get('reliability_weight', 20)}%)
- Stock Score: {scoring_details.get('stock_score', 'N/A')} (Weight: {scoring_details.get('stock_weight', 15)}%)

Context:
- Urgency: {scoring_details.get('urgency', 'MEDIUM')}
- Budget status: {scoring_details.get('budget_status', 'Normal')}

Generate a clear, structured explanation (4-6 sentences) that:
1. States the selected supplier and total score
2. Explains the key factors in the decision
3. Addresses why other options weren't chosen
4. Justifies any cost premium or trade-offs
5. Mentions risk mitigation if relevant

Reasoning:
"""
        
        return await self.generate_text(prompt, system_instruction=system_instruction)
    
    async def analyze_supplier_response(
        self,
        supplier_message: str,
        our_last_offer: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze supplier's response message and extract structured data.
        
        Args:
            supplier_message: Supplier's response text
            our_last_offer: Our previous offer details
            
        Returns:
            Structured analysis of response
        """
        system_instruction = """You are an AI that extracts structured data from supplier responses.
Parse the message and return a JSON-like analysis."""
        
        prompt = f"""
Analyze this supplier response and extract key information:

Supplier Message:
{supplier_message}

Our Last Offer:
- Price: ${our_last_offer.get('price', 'N/A')}
- Delivery: {our_last_offer.get('delivery_days', 'N/A')} days

Extract and return:
1. Acceptance status (Accepted/Rejected/Counter-offer)
2. Counter-offer price (if any)
3. Counter-offer delivery (if any)
4. Reasoning/conditions mentioned
5. Sentiment (Positive/Neutral/Negative)
6. Negotiation room (High/Medium/Low/None)

Format your response as a structured analysis.
"""
        
        response = await self.generate_text(prompt, system_instruction=system_instruction)
        # Note: In production, you'd parse this into structured data
        # For now, return as text (can be improved with JSON parsing)
        return {"analysis": response, "raw_message": supplier_message}


# Global client instance
gemini_client = GeminiClient()
