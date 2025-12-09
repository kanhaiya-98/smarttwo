"""Test negotiation and decision system end-to-end."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.quote_response import QuoteResponse
from app.models.discovered_supplier import DiscoveredSupplier
from app.agents.negotiator_agent_v2 import NegotiatorAgent
from app.agents.decision_agent import DecisionAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SessionLocal()

try:
    logger.info("="*60)
    logger.info("TESTING NEGOTIATION & DECISION SYSTEM")
    logger.info("="*60)
    
    # Step 1: Create some test quotes manually
    logger.info("\n[STEP 1] Creating test quotes...")
    
    suppliers = db.query(DiscoveredSupplier).limit(4).all()
    quotes = []
    
    test_data = [
        {"price": 0.15, "days": 7},  # Cheap but slow
        {"price": 0.22, "days": 1},  # Expensive but fast
        {"price": 0.20, "days": 3},  # Balanced
        {"price": 0.18, "days": 5},  # Good value
    ]
    
    for supplier, data in zip(suppliers, test_data):
        quote = QuoteResponse(
            supplier_id=supplier.id,
            unit_price=data["price"],
            delivery_days=data["days"],
            stock_available=8000,
            procurement_task_id=1,
            negotiation_round=0
        )
        db.add(quote)
        quotes.append(quote)
        logger.info(f"  {supplier.name}: ${data['price']}/unit, {data['days']} days")
    
    db.commit()
    logger.info(f"Created {len(quotes)} test quotes")
    
    # Step 2: Test Negotiation
    logger.info("\n[STEP 2] Testing Negotiation Agent...")
    negotiator = NegotiatorAgent(db)
    
    strategies = negotiator.analyze_quotes(quotes)
    logger.info(f"Negotiation strategies: {strategies}")
    
    # Generate a sample negotiation message
    if quotes:
        message = negotiator.generate_negotiation_message(
            supplier=suppliers[1],  # The expensive but fast one
            current_quote=quotes[1],
            all_quotes=quotes,
            strategy="price_match",
            round_number=1
        )
        logger.info(f"\nGenerated negotiation message:\n{message[:200]}...")
    
    # Step 3: Test Decision Agent
    logger.info("\n[STEP 3] Testing Decision Agent...")
    decision_agent = DecisionAgent(db)
    
    best_score, explanation = decision_agent.make_decision(
        quotes=quotes,
        required_quantity=5000,
        urgency="MEDIUM"
    )
    
    logger.info(f"\nDecision Result:")
    logger.info(f"Recommended Supplier ID: {best_score.supplier_id}")
    logger.info(f"Total Score: {best_score.total_score:.1f}")
    logger.info(f"  - Price Score:  {best_score.price_score:.1f}")
    logger.info(f"  - Speed Score:  {best_score.speed_score:.1f}")
    logger.info(f"  - Reliability:  {best_score.reliability_score:.1f}")
    logger.info(f"  - Stock Score:  {best_score.stock_score:.1f}")
    
    logger.info(f"\nGemini Explanation:\n{explanation[:300]}...")
    
    logger.info("\n" + "="*60)
    logger.info("ALL TESTS PASSED!")
    logger.info("="*60)
    
finally:
    db.close()
