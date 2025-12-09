"""Create quotes from detected email replies."""
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
    logger.info("Creating QuoteResponse records from email replies...")
    
    # Get email messages that are supplier replies
    supplier_messages = db.query(EmailMessage).filter(
        EmailMessage.is_from_agent == False,
        EmailMessage.quoted_price.isnot(None)
    ).all()
    
    logger.info(f"Found {len(supplier_messages)} supplier reply messages")
    
    for msg in supplier_messages:
        # Check if quote already exists
        existing = db.query(QuoteResponse).filter_by(email_message_id=msg.id).first()
        if existing:
            logger.info(f"  Quote already exists for message {msg.id}")
            continue
        
        # Find supplier by email
        supplier = db.query(DiscoveredSupplier).filter_by(display_email=msg.display_sender).first()
        
        if not supplier:
            logger.warning(f"  No supplier found for {msg.display_sender}")
            continue
        
        # Create quote
        quote = QuoteResponse(
            supplier_id=supplier.id,
            email_message_id=msg.id,
            procurement_task_id=1,
            unit_price=msg.quoted_price,
            delivery_days=msg.delivery_days,
            stock_available=8000,
            currency="USD",
            negotiation_round=0
        )
        db.add(quote)
        logger.info(f"  ✅ Created quote for {supplier.name}: ${msg.quoted_price}/unit, {msg.delivery_days} days")
    
    db.commit()
    
    # Show summary
    all_quotes = db.query(QuoteResponse).all()
    logger.info(f"\n📊 Total quotes in database: {len(all_quotes)}")
    for q in all_quotes:
        s = db.query(DiscoveredSupplier).get(q.supplier_id)
        logger.info(f"  - {s.name if s else 'Unknown'}: ${q.unit_price}/unit, {q.delivery_days} days")
    
finally:
    db.close()
