"""Test complete negotiation and decision workflow with real quotes."""
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
    logger.info("="*70)
    logger.info("TESTING AI NEGOTIATION & DECISION AGENTS")
    logger.info("="*70)
    
    # Step 1: Get all quotes
    quotes = db.query(QuoteResponse).all()
    logger.info(f"\n[1] Found {len(quotes)} quotes in database:")
    for q in quotes:
        supplier = db.query(DiscoveredSupplier).get(q.supplier_id)
        logger.info(f"  - {supplier.name if supplier else 'Unknown'}: ${q.unit_price}/unit, {q.delivery_days} days")
    
    if len(quotes) < 2:
        logger.error("\n❌ Need at least 2 quotes to test negotiation/decision")
        logger.info("Reply to supplier emails first!")
        sys.exit(1)
    
    # Step 2: Test Negotiation Agent
    logger.info("\n[2] Testing Negotiation Agent (Gemini)...")
    negotiator = NegotiatorAgent(db)
    
    strategies = negotiator.analyze_quotes(quotes)
    logger.info(f"Identified {len(strategies)} negotiation strategies:")
    for supplier_id, strategy in strategies.items():
        supplier = db.query(DiscoveredSupplier).get(supplier_id)
        logger.info(f"  - {supplier.name if supplier else 'Unknown'}: {strategy}")
    
    # Generate sample negotiation message
    if len(quotes) >= 2:
        quote = quotes[0]
        supplier = db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        logger.info(f"\nGenerating negotiation message for {supplier.name}...")
        message = negotiator.generate_negotiation_message(
            supplier=supplier,
            current_quote=quote,
            all_quotes=quotes,
            strategy="price_match",
            round_number=1
        )
        
        logger.info("\n" + "="*70)
        logger.info("GEMINI-GENERATED NEGOTIATION MESSAGE:")
        logger.info("="*70)
        logger.info(message)
        logger.info("="*70)
    
    # Step 3: Test Decision Agent
    logger.info("\n[3] Testing Decision Agent (Weighted Scoring + Gemini)...")
    decision_agent = DecisionAgent(db)
    
    best_score, explanation = decision_agent.make_decision(
        quotes=quotes,
        required_quantity=5000,
        urgency="MEDIUM"
    )
    
    supplier =db.query(DiscoveredSupplier).get(best_score.supplier_id)
    
    logger.info("\n" + "="*70)
    logger.info("DECISION RESULTS:")
    logger.info("="*70)
    logger.info(f"Recommended Supplier: {supplier.name if supplier else 'Unknown'}")
    logger.info(f"Total Score: {best_score.total_score:.1f}/100")
    logger.info(f"\nScore Breakdown:")
    logger.info(f"  - Price Score:      {best_score.price_score:.1f} (weight: {best_score.price_weight*100:.0f}%)")
    logger.info(f"  - Speed Score:      {best_score.speed_score:.1f} (weight: {best_score.speed_weight*100:.0f}%)")
    logger.info(f"  - Reliability:      {best_score.reliability_score:.1f} (weight: {best_score.reliability_weight*100:.0f}%)")
    logger.info(f"  - Stock Score:      {best_score.stock_score:.1f} (weight: {best_score.stock_weight*100:.0f}%)")
    
    logger.info("\n" + "="*70)
    logger.info("GEMINI DECISION EXPLANATION:")
    logger.info("="*70)
    logger.info(explanation)
    logger.info("="*70)
    
    logger.info("\n✅ ALL AI AGENTS WORKING SUCCESSFULLY!")
    
finally:
    db.close()
