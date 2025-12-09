"""Seed supplier data."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/backend')

from app.database import SessionLocal
from app.models.supplier import Supplier, SupplierMedicine
from app.models.medicine import Medicine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_suppliers():
    db = SessionLocal()
    try:
        # Check if suppliers exist
        if db.query(Supplier).count() > 0:
            logger.info("Suppliers already exist. Skipping.")
            return

        suppliers_data = [
            {
                "name": "Budget Pharma",
                "code": "SUP-001",
                "is_budget_supplier": True,
                "is_fast_delivery": False,
                "reliability_score": 85.0,
                "typical_delivery_days": 14,
                "payment_terms": "NET 60"
            },
            {
                "name": "QuickMeds Inc.",
                "code": "SUP-002",
                "is_budget_supplier": False,
                "is_fast_delivery": True,
                "reliability_score": 98.0,
                "typical_delivery_days": 2,
                "payment_terms": "NET 15"
            },
            {
                "name": "BulkHealth Wholesale",
                "code": "SUP-003",
                "is_bulk_supplier": True,
                "reliability_score": 90.0,
                "typical_delivery_days": 7,
                "payment_terms": "NET 30"
            },
            {
                "name": "ReliaMeds Corp",
                "code": "SUP-004",
                "reliability_score": 99.5,
                "typical_delivery_days": 5,
                "payment_terms": "NET 30"
            },
            {
                "name": "LocalStock Emergency",
                "code": "SUP-005",
                "is_fast_delivery": True,
                "reliability_score": 95.0,
                "typical_delivery_days": 1,
                "payment_terms": "IMMEDIATE"
            }
        ]

        created_suppliers = []
        for s_data in suppliers_data:
            supplier = Supplier(**s_data)
            db.add(supplier)
            created_suppliers.append(supplier)
        db.commit()
        
        # Reload to get IDs
        for s in created_suppliers:
            db.refresh(s)
            
        logger.info(f"Created {len(created_suppliers)} suppliers")

        # Link medicines (Assume some medicines exist)
        medicines = db.query(Medicine).all()
        if not medicines:
            logger.warning("No medicines found! Cannot link suppliers.")
            return

        import random
        count = 0
        for medicine in medicines:
            # Each medicine available from 2-4 suppliers
            suppliers_for_med = random.sample(created_suppliers, k=random.randint(2, 4))
            
            for supplier in suppliers_for_med:
                # Price logic
                base_price = (medicine.last_purchase_price or 10.0) * random.uniform(0.9, 1.2)
                if supplier.is_budget_supplier:
                    base_price *= 0.85
                elif supplier.is_fast_delivery:
                    base_price *= 1.25
                
                # Bulk logic
                bulk_threshold = 1000 if supplier.is_bulk_supplier else None
                bulk_price = base_price * 0.9 if bulk_threshold else None
                
                # Lead time
                lead_time = supplier.typical_delivery_days
                if supplier.is_fast_delivery:
                    lead_time = max(1, lead_time - 1)
                
                mapping = SupplierMedicine(
                    supplier_id=supplier.id,
                    medicine_id=medicine.id,
                    is_available=True,
                    current_stock=random.randint(500, 50000),
                    lead_time_days=lead_time,
                    base_price=round(base_price, 2),
                    bulk_discount_threshold=bulk_threshold,
                    bulk_discount_price=round(bulk_price, 2) if bulk_price else None
                )
                db.add(mapping)
                count += 1
        
        db.commit()
        logger.info(f"Created {count} supplier-medicine mappings")

    except Exception as e:
        logger.error(f"Error seeding suppliers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_suppliers()
