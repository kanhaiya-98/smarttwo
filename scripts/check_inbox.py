"""Check inbox for supplier replies (manual testing)."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.services.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_inbox():
    """Check for new supplier replies."""
    db = SessionLocal()
    
    try:
        logger.info("📬 Checking inbox for supplier replies...")
        
        email_service = EmailService(demo_mode=True)
        new_messages = email_service.check_for_replies(db)
        
        if new_messages:
            logger.info(f"\n✅ Found {len(new_messages)} new replies!")
            for msg in new_messages:
                logger.info(f"\n  From: {msg.display_sender}")
                logger.info(f"  Price: ${msg.quoted_price}/unit" if msg.quoted_price else "  (No price parsed)")
                logger.info(f"  Delivery: {msg.delivery_days} days" if msg.delivery_days else "  (No delivery time parsed)")
        else:
            logger.info("\n📭 No new replies found.")
            logger.info("Make sure you:")
            logger.info("  1. Replied to the demo email from kanhacet@gmail.com")
            logger.info("  2. Kept [DEMO: SupplierName] in the subject")
            logger.info("  3. Included pricing info in the body")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    check_inbox()
