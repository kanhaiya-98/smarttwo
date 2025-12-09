"""Direct email sending test for discovery."""
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
    logger.info("="*60)
    logger.info("TESTING EMAIL SENDING IN DISCOVERY FLOW")
    logger.info("="*60)
    
    # Get first supplier
    supplier = db.query(DiscoveredSupplier).first()
    medicine = db.query(Medicine).filter_by(name="Paracetamol").first()
    
    if not supplier or not medicine:
        logger.error("No supplier or medicine found!")
        sys.exit(1)
    
    logger.info(f"\nSupplier: {supplier.name}")
    logger.info(f"Display Email: {supplier.display_email}")
    logger.info(f"Actual Email: {supplier.actual_email}")
    logger.info(f"Medicine: {medicine.name}")
    
    # Test email sending
    logger.info("\nSending quote request email...")
    email_service = EmailService(demo_mode=True)
    
    try:
        thread = email_service.send_quote_request(
            db=db,
            supplier=supplier,
            medicine=medicine,
            quantity=5000
        )
        logger.info(f"✅ Email sent successfully!")
        logger.info(f"Thread ID: {thread.id}")
        logger.info(f"Status: {thread.status}")
        logger.info(f"\n📧 Check kanhacet@gmail.com inbox!")
        
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        import traceback
        traceback.print_exc()
    
finally:
    db.close()
