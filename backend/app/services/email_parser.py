"""Email parsing service to extract structured data from supplier emails."""
import re
import json
import logging
from typing import Dict, List, Optional
from app.core.gemini_client import gemini_client

logger = logging.getLogger(__name__)


class EmailParser:
    """Extract price, delivery, and terms from supplier email responses."""
    
    def parse_supplier_email(self, email_body: str) -> Dict:
        """
        Extract structured data from supplier email.
        
        Returns:
            {
                "price": float or None,
                "delivery_days": int or None,
                "conditions": List[str],
                "raw_text": str
            }
        """
        parsed = {
            "price": None,
            "delivery_days": None,
            "conditions": [],
            "raw_text": email_body
        }
        
        # Extract price
        parsed["price"] = self._extract_price(email_body)
        
        # Extract delivery time
        parsed["delivery_days"] = self._extract_delivery_days(email_body)
        
        # Extract conditions
        parsed["conditions"] = self._extract_conditions(email_body)
        
        return parsed
    
    def _extract_price(self, text: str) -> float:
        """Extract unit price from email text."""
        
        price_patterns = [
            # Rs. 12 per unit, Rs 12/unit, Rs.12 per tablet
            r'(?:Rs\.?|INR|₹)\s*(\d+(?:\.\d{1,2})?)\s*(?:per|/)\s*(?:unit|tablet|piece|pc)',
            # $0.18 per unit, $0.18/unit
            r'\$\s*(\d+(?:\.\d{1,2})?)\s*(?:per|/)\s*(?:unit|tablet|piece|pc)',
            # price: Rs 12, quote: $0.18, cost: 12
            r'(?:price|quote|cost|rate)[:=\s]+(?:Rs\.?|INR|₹|\$)?\s*(\d+(?:\.\d{1,2})?)',
            # We can offer at Rs 12
            r'(?:offer|provide|supply).*?(?:Rs\.?|INR|₹|\$)\s*(\d+(?:\.\d{1,2})?)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = float(match.group(1))
                # Convert Rs to $ if needed (approximate: Rs 75 = $1)
                if 'Rs' in match.group(0) or '₹' in match.group(0) or 'INR' in match.group(0):
                    price = price / 75.0  # Rough conversion
                return round(price, 2)
        
        return None
    
    def _extract_delivery_days(self, text: str) -> int:
        """Extract delivery timeframe in days."""
        
        delivery_patterns = [
            # 5 days, 3 business days
            r'(\d+)\s*(?:business\s+)?days?',
            # within 5 days, in 3 days
            r'(?:within|in)\s+(\d+)\s*(?:business\s+)?days?',
            # delivery: 5 days, delivery in 3 days
            r'(?:delivery|ship|dispatch).*?(\d+)\s*(?:business\s+)?days?',
            # 2 weeks
            r'(\d+)\s*weeks?',
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                days = int(match.group(1))
                # Convert weeks to days
                if 'week' in match.group(0).lower():
                    days *= 7
                return days
        
        return None
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract special conditions or terms."""
        
        conditions = []
        
        condition_keywords = [
            'minimum order',
            'MOQ',
            'advance payment',
            'payment terms',
            'bulk discount',
            'commitment',
            'contract'
        ]
        
        sentences = text.split('.')
        
        for keyword in condition_keywords:
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    conditions.append(sentence.strip())
                    break
        
        return conditions
    
    def parse_quote_from_email(
        self, 
        subject: str, 
        body: str, 
        sender: str
    ) -> Optional[Dict]:
        """
        Parse quote response from supplier email using AI.
        
        Args:
            subject: Email subject line
            body: Email body text
            sender: Sender email address
            
        Returns:
            {
                'unit_price': float,
                'total_price': float,
                'delivery_days': int,
                'stock_available': int or None,
                'notes': str
            }
        """
        try:
            # Try rule-based parsing first (faster)
            parsed = self.parse_supplier_email(body)
            
            if parsed['price'] and parsed['delivery_days']:
                # Successfully parsed with rules
                return {
                    'unit_price': parsed['price'],
                    'total_price': parsed['price'] * 5000,  # Assume 5000 units
                    'delivery_days': parsed['delivery_days'],
                    'stock_available': None,
                    'notes': ', '.join(parsed['conditions']) if parsed['conditions'] else ''
                }
            
            # Fall back to AI parsing
            logger.info("Rule-based parsing incomplete, using Gemini AI")
            return self._parse_with_ai(subject, body)
            
        except Exception as e:
            logger.error(f"Error parsing quote: {e}")
            return None
    
    def _parse_with_ai(self, subject: str, body: str) -> Optional[Dict]:
        """Use Gemini AI to extract quote data from email."""
        
        prompt = f"""Extract quote details from this supplier email response.

Subject: {subject}
Body: {body}

Extract and return ONLY a JSON object with these fields:
{{
    "unit_price": <price per unit in USD, as float>,
    "total_price": <total order price in USD, as float>,
    "delivery_days": <delivery time in days, as integer>,
    "stock_available": <available stock quantity, as integer or null>,
    "notes": "<any special conditions or notes as string>"
}}

If the email is a rejection or "out of stock", return null for numeric fields.
Return ONLY valid JSON, no explanation or markdown formatting."""

        try:
            response = gemini_client.generate_text(prompt, max_tokens=500)
            
            # Clean up response
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = re.sub(r'```(?:json)?\n?', '', response_text)
                response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate required fields
            if not data.get('unit_price') or not data.get('delivery_days'):
                logger.warning("AI parsing returned incomplete data")
                return None
            
            # Ensure correct types
            return {
                'unit_price': float(data['unit_price']),
                'total_price': float(data.get('total_price', data['unit_price'] * 5000)),
                'delivery_days': int(data['delivery_days']),
                'stock_available': int(data['stock_available']) if data.get('stock_available') else None,
                'notes': str(data.get('notes', ''))
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {response}")
            return None
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return None

