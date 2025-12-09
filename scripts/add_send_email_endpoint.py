"""API endpoint to send email to individual supplier."""
import sys
sys.path.insert(0, '.')

# Add the new endpoint code
new_endpoint = """

@router.post("/send-email/{supplier_id}")
async def send_email_to_supplier(
    supplier_id: int,
    quantity: int = 5000,
    db: Session = Depends(get_db)
):
    \"\"\"
    Manually send quote request email to a specific supplier.
    User clicks 'Send Email' button to trigger this.
    \"\"\"
    supplier = db.query(DiscoveredSupplier).filter_by(id=supplier_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get medicine
    medicine = db.query(Medicine).first()
    
    if not medicine:
        raise HTTPException(status_code=404, detail="No medicine found")
    
    # Send email
    email_service = EmailService(demo_mode=True)
    
    try:
        thread = email_service.send_quote_request(
            db=db,
            supplier=supplier,
            medicine=medicine,
            quantity=quantity
        )
        
        logger.info(f"📧 Email sent to {supplier.display_email} (supplier_id: {supplier_id})")
        
        # Update supplier status
        supplier.emails_sent += 1
        supplier.last_email_sent_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Email sent to {supplier.name}",
            "thread_id": thread.id,
            "supplier_id": supplier_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {supplier.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
"""

# Read current file
with open('d:/smartcluade/pharmacy-supply-chain-ai/backend/app/api/routes/discovery.py', 'r') as f:
    content = f.read()

# Append endpoint if not already there
if '@router.post("/send-email/{supplier_id}")' not in content:
    with open('d:/smartcluade/pharmacy-supply-chain-ai/backend/app/api/routes/discovery.py', 'a') as f:
        f.write(new_endpoint)
    print("✅ Added send-email endpoint")
else:
    print("Endpoint already exists")
