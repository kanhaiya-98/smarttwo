"""Quick test script for supplier discovery hackathon demo."""
import asyncio
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.medicine import Medicine
from app.services.supplier_discovery_service import SupplierDiscoveryService
from app.services.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_discovery():
    """Test the complete supplier discovery flow."""
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        logger.info("🎬 HACKATHON DEMO TEST - Supplier Discovery")
        logger.info("=" * 60)
        
        # Get Paracetamol
        medicine = db.query(Medicine).filter_by(name="Paracetamol").first()
        if not medicine:
            logger.error("❌ Paracetamol not found in database")
            return
        
        logger.info(f"\n✓ Medicine: {medicine.name} {medicine.dosage}")
        logger.info(f"  Quantity needed: 5000 units")
        
        # Step 1: Discover suppliers
        logger.info("\n[STEP 1] 🔍 Discovering suppliers...")
        discovery_service = SupplierDiscoveryService(db, demo_mode=True)
        suppliers = discovery_service.discover_suppliers(
            medicine=medicine,
            quantity=5000
        )
        
        logger.info(f"\n✓ Found {len(suppliers)} suppliers:")
        for s in suppliers:
            logger.info(f"  - {s.name}")
            logger.info(f"    Display: {s.display_email}")
            logger.info(f"    Actually sends to: {s.actual_email}")
        
        # Step 2: Send emails
        logger.info("\n[STEP 2] 📧 Sending quote request emails...")
        email_service = EmailService(demo_mode=True)
        
        for supplier in suppliers[:2]:  # Send to first 2 for demo
            thread = email_service.send_quote_request(
                db=db,
                supplier=supplier,
                medicine=medicine,
                quantity=5000
            )
            logger.info(f"✓ Email sent to {supplier.display_email}")
            logger.info(f"  (Actually: {supplier.actual_email})")
        
        # Step 3: Instructions for manual testing
        logger.info("\n[STEP 3] 📱 MANUAL TEST INSTRUCTIONS")
        logger.info("=" * 60)
        logger.info("Check your email: kanhacet@gmail.com")
        logger.info("")
        logger.info("You should see emails with subjects like:")
        logger.info(f"  '[DEMO: MedPharma] Bulk Procurement Inquiry - Paracetamol 5000 units'")
        logger.info("")
        logger.info("To test reply detection:")
        logger.info("1. Reply to one of the emails from kanhacet@gmail.com")
        logger.info("2. In your reply, include pricing info like:")
        logger.info("   'We can offer at Rs 12 per unit, delivery in 5 days'")
        logger.info("3. Run: python scripts/check_inbox.py")
        logger.info("")
        logger.info("=" * 60)
        logger.info("\n🎉 TEST COMPLETE!")
        logger.info("Your system is ready for the hackathon demo!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_discovery())
