"""Create test quotes from existing supplier replies."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.quote_response import QuoteResponse
from app.models.email_message import EmailMessage
from app.models.discovered_supplier import DiscoveredSupplier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SessionLocal()

try:
    logger.info("Creating test quotes from supplier replies...")
    
    # Get suppliers who replied
    suppliers = db.query(DiscoveredSupplier).filter(
        DiscoveredSupplier.emails_received > 0
    ).all()
    
    logger.info(f"Found {len(suppliers)} suppliers with replies")
    
    for supplier in suppliers:
        # Check if quote already exists
        existing = db.query(QuoteResponse).filter_by(supplier_id=supplier.id).first()
        if existing:
            logger.info(f"Quote already exists for {supplier.name}")
            continue
        
        # Get their email message
        message = db.query(EmailMessage).filter_by(
            display_sender=supplier.display_email,
            is_from_agent=False
        ).first()
        
        if message and message.quoted_price and message.delivery_days:
            quote = QuoteResponse(
                supplier_id=supplier.id,
                email_message_id=message.id,
                procurement_task_id=1,
                unit_price=message.quoted_price,
                delivery_days=message.delivery_days,
                stock_available=8000,  # Assume good stock
                currency="USD",
                negotiation_round=0
            )
            db.add(quote)
            logger.info(f"Created quote for {supplier.name}: ${message.quoted_price}/unit, {message.delivery_days} days")
    
    db.commit()
    logger.info("Test quotes created!")
    
    # Show summary
    all_quotes = db.query(QuoteResponse).all()
    logger.info(f"\nTotal quotes in database: {len(all_quotes)}")
    for q in all_quotes:
        s = db.query(DiscoveredSupplier).get(q.supplier_id)
        logger.info(f"  - {s.name if s else 'Unknown'}: ${q.unit_price}/unit, {q.delivery_days} days")
    
finally:
    db.close()
