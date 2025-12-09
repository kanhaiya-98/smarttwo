"""Check and fix thread status."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.email_thread import EmailThread
from app.models.discovered_supplier import DiscoveredSupplier

db = SessionLocal()

try:
    # Find the "Top" supplier
    supplier = db.query(DiscoveredSupplier).filter_by(demo_identifier="Top").first()
    
    if supplier:
        print(f"Supplier: {supplier.name}")
        print(f"Demo ID: {supplier.demo_identifier}")
        
        # Get all threads for this supplier
        threads = db.query(EmailThread).filter_by(supplier_id=supplier.id).all()
        print(f"\nThreads for this supplier: {len(threads)}")
        
        for t in threads:
            print(f"  Thread {t.id}: Status={t.status}, Subject={t.subject[:60]}...")
            
            # If thread is not AWAITING_REPLY, update it
            if t.status != "AWAITING_REPLY":
                print(f"    Updating status to AWAITING_REPLY")
                t.status = "AWAITING_REPLY"
        
        db.commit()
        print("\n✅ Thread status updated!")
    else:
        print("❌ No supplier found with demo_identifier='Top'")
        
finally:
    db.close()
