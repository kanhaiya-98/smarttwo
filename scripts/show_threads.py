"""Check email threads in database."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.email_thread import EmailThread
from app.models.discovered_supplier import DiscoveredSupplier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SessionLocal()

try:
    # Get all threads awaiting reply
    threads = db.query(EmailThread).filter_by(status='AWAITING_REPLY').all()
    
    logger.info(f"\n📧 Email Threads Awaiting Reply: {len(threads)}")
    logger.info("=" * 60)
    
    for i, thread in enumerate(threads[:5], 1):
        supplier = db.query(DiscoveredSupplier).get(thread.supplier_id)
        
        logger.info(f"\n[{i}] {supplier.name}")
        logger.info(f"   Demo ID: {supplier.demo_identifier}")
        logger.info(f"   Display Email: {thread.display_recipient}")
        logger.info(f"   Actual Email: {thread.actual_recipient}")
        logger.info(f"   Subject: {thread.subject}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"\n✅ {len(threads)} threads ready to receive replies!")
    logger.info("\n📧 Check kanhacet@gmail.com for NEW emails")
    logger.info("   Subject format: [DEMO: SupplierName] Bulk Procurement...")
    
finally:
    db.close()
