"""Seed database with sample data."""
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models.medicine import Medicine
from app.models.supplier import Supplier, SupplierMedicine
from datetime import datetime
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_medicines(db):
    """Seed sample medicines."""
    logger.info("Seeding medicines...")
    
    medicines_data = [
        # Analgesics
        {"name": "Paracetamol", "dosage": "500mg", "form": "Tablet", "category": "Analgesic"},
        {"name": "Ibuprofen", "dosage": "400mg", "form": "Tablet", "category": "Analgesic"},
        {"name": "Aspirin", "dosage": "75mg", "form": "Tablet", "category": "Analgesic"},
        
        # Antibiotics
        {"name": "Amoxicillin", "dosage": "500mg", "form": "Capsule", "category": "Antibiotic"},
        {"name": "Azithromycin", "dosage": "250mg", "form": "Tablet", "category": "Antibiotic"},
        {"name": "Ciprofloxacin", "dosage": "500mg", "form": "Tablet", "category": "Antibiotic"},
        
        # Antihistamines
        {"name": "Cetirizine", "dosage": "10mg", "form": "Tablet", "category": "Antihistamine"},
        {"name": "Loratadine", "dosage": "10mg", "form": "Tablet", "category": "Antihistamine"},
        
        # Antihypertensives
        {"name": "Amlodipine", "dosage": "5mg", "form": "Tablet", "category": "Antihypertensive"},
        {"name": "Atenolol", "dosage": "50mg", "form": "Tablet", "category": "Antihypertensive"},
        
        # Diabetes
        {"name": "Metformin", "dosage": "500mg", "form": "Tablet", "category": "Antidiabetic"},
        {"name": "Glimepiride", "dosage": "2mg", "form": "Tablet", "category": "Antidiabetic"},
        
        # Others
        {"name": "Omeprazole", "dosage": "20mg", "form": "Capsule", "category": "PPI"},
        {"name": "Vitamin D3", "dosage": "60000 IU", "form": "Capsule", "category": "Vitamin"},
        {"name": "Levothyroxine", "dosage": "100mcg", "form": "Tablet", "category": "Thyroid"},
    ]
    
    medicines = []
    for data in medicines_data:
        # Random stock levels
        current_stock = random.randint(100, 2000)
        avg_daily_sales = random.uniform(20, 150)
        
        medicine = Medicine(
            name=data["name"],
            dosage=data["dosage"],
            form=data["form"],
            category=data["category"],
            current_stock=current_stock,
            average_daily_sales=avg_daily_sales,
            safety_stock=int(avg_daily_sales * 7),  # 7 days
            reorder_point=int(avg_daily_sales * 14),  # 14 days
            last_purchase_price=round(random.uniform(0.10, 0.50), 2),
            average_price=round(random.uniform(0.12, 0.55), 2),
            is_active=True,
            requires_quality_check=data["category"] in ["Antibiotic", "Antidiabetic"],
            min_expiry_months=12
        )
        medicines.append(medicine)
        db.add(medicine)
    
    db.commit()
    logger.info(f"✓ Seeded {len(medicines)} medicines")
    return medicines


def seed_suppliers(db):
    """Seed sample suppliers."""
    logger.info("Seeding suppliers...")
    
    suppliers_data = [
        {
            "name": "Budget Pharma",
            "code": "SUP001",
            "email": "orders@budgetpharma.com",
            "phone": "+1-555-0101",
            "typical_delivery_days": 7,
            "is_bulk_supplier": False,
            "is_fast_delivery": False,
            "is_budget_supplier": True,
            "reliability_score": 82.0,
            "on_time_delivery_rate": 0.78,
            "quality_rating": 4.1,
        },
        {
            "name": "QuickMeds",
            "code": "SUP002",
            "email": "sales@quickmeds.com",
            "phone": "+1-555-0102",
            "typical_delivery_days": 1,
            "is_bulk_supplier": False,
            "is_fast_delivery": True,
            "is_budget_supplier": False,
            "reliability_score": 95.0,
            "on_time_delivery_rate": 0.95,
            "quality_rating": 4.7,
        },
        {
            "name": "BulkHealth",
            "code": "SUP003",
            "email": "bulk@bulkhealth.com",
            "phone": "+1-555-0103",
            "typical_delivery_days": 5,
            "is_bulk_supplier": True,
            "is_fast_delivery": False,
            "is_budget_supplier": False,
            "reliability_score": 88.0,
            "on_time_delivery_rate": 0.85,
            "quality_rating": 4.4,
        },
        {
            "name": "ReliaMeds",
            "code": "SUP004",
            "email": "info@reliameds.com",
            "phone": "+1-555-0104",
            "typical_delivery_days": 3,
            "is_bulk_supplier": False,
            "is_fast_delivery": False,
            "is_budget_supplier": False,
            "reliability_score": 92.0,
            "on_time_delivery_rate": 0.92,
            "quality_rating": 4.6,
        },
        {
            "name": "LocalStock",
            "code": "SUP005",
            "email": "orders@localstock.com",
            "phone": "+1-555-0105",
            "typical_delivery_days": 1,
            "is_bulk_supplier": False,
            "is_fast_delivery": True,
            "is_budget_supplier": False,
            "reliability_score": 85.0,
            "on_time_delivery_rate": 0.88,
            "quality_rating": 4.3,
        },
    ]
    
    suppliers = []
    for data in suppliers_data:
        supplier = Supplier(
            name=data["name"],
            code=data["code"],
            email=data["email"],
            phone=data["phone"],
            address=f"123 Medical Street, City, State 12345",
            has_api_integration=random.choice([True, False]),
            payment_terms="NET 30",
            credit_limit=100000.0,
            minimum_order_value=500.0,
            typical_delivery_days=data["typical_delivery_days"],
            is_bulk_supplier=data["is_bulk_supplier"],
            is_fast_delivery=data["is_fast_delivery"],
            is_budget_supplier=data["is_budget_supplier"],
            reliability_score=data["reliability_score"],
            on_time_delivery_rate=data["on_time_delivery_rate"],
            quality_rating=data["quality_rating"],
            average_response_time_hours=random.uniform(0.5, 3.0),
            total_orders_count=random.randint(50, 500),
            is_active=True,
            is_blacklisted=False
        )
        suppliers.append(supplier)
        db.add(supplier)
    
    db.commit()
    logger.info(f"✓ Seeded {len(suppliers)} suppliers")
    return suppliers


def seed_supplier_medicines(db, medicines, suppliers):
    """Create medicine-supplier mappings."""
    logger.info("Creating supplier-medicine mappings...")
    
    count = 0
    for medicine in medicines:
        # Each medicine available from 3-5 suppliers
        num_suppliers = random.randint(3, 5)
        selected_suppliers = random.sample(suppliers, num_suppliers)
        
        for supplier in selected_suppliers:
            base_price = medicine.average_price + random.uniform(-0.05, 0.05)
            
            supplier_medicine = SupplierMedicine(
                supplier_id=supplier.id,
                medicine_id=medicine.id,
                is_available=True,
                current_stock=random.randint(5000, 20000),
                lead_time_days=supplier.typical_delivery_days,
                base_price=round(base_price, 2),
                bulk_discount_threshold=10000 if supplier.is_bulk_supplier else None,
                bulk_discount_price=round(base_price * 0.9, 2) if supplier.is_bulk_supplier else None,
            )
            db.add(supplier_medicine)
            count += 1
    
    db.commit()
    logger.info(f"✓ Created {count} supplier-medicine mappings")


def main():
    """Seed all data."""
    db = SessionLocal()
    
    try:
        logger.info("Starting database seeding...")
        
        # Check if already seeded
        existing_medicines = db.query(Medicine).count()
        if existing_medicines > 0:
            logger.warning(f"Database already has {existing_medicines} medicines. Skipping seed.")
            return
        
        medicines = seed_medicines(db)
        suppliers = seed_suppliers(db)
        seed_supplier_medicines(db, medicines, suppliers)
        
        logger.info("✓ Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Error seeding database: {str(e)}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
