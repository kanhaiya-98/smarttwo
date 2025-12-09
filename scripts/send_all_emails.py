"""Send quote request emails to all discovered suppliers."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.medicine import Medicine
from app.services.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SessionLocal()

try:
    # Get all suppliers
    suppliers = db.query(DiscoveredSupplier).all()
    logger.info(f"Found {len(suppliers)} suppliers in database")
    
    # Get Paracetamol
    medicine = db.query(Medicine).filter_by(name="Paracetamol").first()
    if not medicine:
        logger.error("Paracetamol not found!")
        sys.exit(1)
    
    # Initialize email service
    email_service = EmailService(demo_mode=True)
    
    # Send emails to all suppliers that don't have threads yet
    sent_count = 0
    for supplier in suppliers:
        # Check if thread already exists
        from app.models.email_thread import EmailThread
        existing_thread = db.query(EmailThread).filter_by(supplier_id=supplier.id).first()
        
        if existing_thread:
            logger.info(f"⏭️  Skipping {supplier.name} (thread already exists)")
            continue
        
        try:
            logger.info(f"📧 Sending to {supplier.name} ({supplier.display_email})...")
            thread = email_service.send_quote_request(
                db=db,
                supplier=supplier,
                medicine=medicine,
                quantity=5000
            )
            logger.info(f"   ✅ Sent! Thread ID: {thread.id}")
            sent_count += 1
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Sent {sent_count} quote request emails")
    logger.info(f"📧 Check kanhacet@gmail.com inbox!")
    logger.info(f"{'='*60}")
    
finally:
    db.close()
