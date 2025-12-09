from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supplier import Supplier, SupplierPerformance
from pydantic import BaseModel

router = APIRouter()


class SupplierResponse(BaseModel):
    id: int
    name: str
    code: str
    email: str
    phone: str
    reliability_score: float
    on_time_delivery_rate: float
    quality_rating: float
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[SupplierResponse])
async def get_suppliers(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of suppliers."""
    query = db.query(Supplier)
    
    if active_only:
        query = query.filter(Supplier.is_active == True, Supplier.is_blacklisted == False)
    
    suppliers = query.all()
    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get supplier details."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return supplier
