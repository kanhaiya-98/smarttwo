from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.medicine import Medicine, ProcurementTask, UrgencyLevel
from app.workflows.procurement_graph import ProcurementWorkflow
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MedicineResponse(BaseModel):
    id: int
    name: str
    dosage: str
    form: str
    current_stock: int
    days_of_supply: float
    urgency_level: str
    
    class Config:
        from_attributes = True


class TriggerProcurementRequest(BaseModel):
    medicine_id: int
    quantity: int
    urgency: str = "MEDIUM"


@router.get("/medicines", response_model=List[MedicineResponse])
async def get_medicines(
    skip: int = 0,
    limit: int = 100,
    low_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get list of medicines with stock levels."""
    query = db.query(Medicine).filter(Medicine.is_active == True)
    
    if low_stock_only:
        # Filter medicines approaching reorder point
        medicines = []
        for med in query.all():
            if med.average_daily_sales > 0:
                days_supply = med.current_stock / med.average_daily_sales
                if days_supply < 7:
                    medicines.append(med)
    else:
        medicines = query.offset(skip).limit(limit).all()
    
    # Calculate days of supply and urgency for each
    results = []
    for med in medicines:
        days_supply = med.current_stock / med.average_daily_sales if med.average_daily_sales > 0 else 999
        
        if days_supply < 2:
            urgency = "CRITICAL"
        elif days_supply < 5:
            urgency = "HIGH"
        elif days_supply < 7:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"
        
        results.append(MedicineResponse(
            id=med.id,
            name=med.name,
            dosage=med.dosage,
            form=med.form,
            current_stock=med.current_stock,
            days_of_supply=round(days_supply, 1),
            urgency_level=urgency
        ))
    
    return results


@router.post("/trigger-procurement")
async def trigger_procurement(
    request: TriggerProcurementRequest,
    db: Session = Depends(get_db)
):
    """Manually trigger procurement for a medicine."""
    medicine = db.query(Medicine).filter(Medicine.id == request.medicine_id).first()
    
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Create procurement task
    task = ProcurementTask(
        medicine_id=medicine.id,
        required_quantity=request.quantity,
        urgency_level=UrgencyLevel(request.urgency),
        days_of_supply_remaining=medicine.current_stock / medicine.average_daily_sales if medicine.average_daily_sales > 0 else 0,
        status="QUEUED"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Start workflow asynchronously
    workflow = ProcurementWorkflow(db)
    # In production, this would be a background task
    # For now, return task ID
    
    return {
        "task_id": task.id,
        "status": "QUEUED",
        "message": "Procurement workflow initiated"
    }
