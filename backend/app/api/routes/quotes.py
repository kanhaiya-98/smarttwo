"""API routes for quote management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.quote_service import QuoteService
from app.models.quote_response import QuoteResponse
from pydantic import BaseModel

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteResponseSchema(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    unit_price: float
    total_price: float
    delivery_days: int
    stock_available: int | None
    notes: str
    responded_at: str | None
    
    class Config:
        from_attributes = True


class QuoteSummarySchema(BaseModel):
    total_quotes: int
    cheapest_price: float | None = None
    fastest_delivery: int | None = None
    average_price: float | None = None
    price_range: dict | None = None
    quotes: List[dict]
    awaiting_quotes: bool
    timeout_reached: bool


class QuoteComparisonSchema(BaseModel):
    quote_id: int
    supplier_id: int
    supplier_name: str
    unit_price: float
    total_price: float
    delivery_days: int
    stock_available: int | None
    notes: str
    price_color: str
    delivery_color: str
    reliability_score: float
    responded_at: str | None


@router.get("/task/{task_id}", response_model=List[QuoteResponseSchema])
def get_quotes_for_task(task_id: int, db: Session = Depends(get_db)):
    """Get all quotes for a procurement task."""
    quote_service = QuoteService(db)
    quotes = quote_service.get_quotes_for_task(task_id)
    
    # Convert to response schema
    result = []
    for quote in quotes:
        from app.models.discovered_supplier import DiscoveredSupplier
        supplier = db.query(DiscoveredSupplier).get(quote.supplier_id)
        
        result.append(QuoteResponseSchema(
            id=quote.id,
            supplier_id=quote.supplier_id,
            supplier_name=supplier.name if supplier else "Unknown",
            unit_price=quote.unit_price,
            total_price=quote.total_price,
            delivery_days=quote.delivery_days,
            stock_available=quote.stock_available,
            notes=quote.notes or "",
            responded_at=quote.responded_at.isoformat() if quote.responded_at else None
        ))
    
    return result


@router.get("/task/{task_id}/summary", response_model=QuoteSummarySchema)
def get_quote_summary(task_id: int, db: Session = Depends(get_db)):
    """Get summary of quotes for a task."""
    quote_service = QuoteService(db)
    summary = quote_service.get_quote_summary(task_id)
    return summary


@router.get("/task/{task_id}/comparison", response_model=List[QuoteComparisonSchema])
def get_quote_comparison(task_id: int, db: Session = Depends(get_db)):
    """Get color-coded comparison table for quotes."""
    quote_service = QuoteService(db)
    comparison = quote_service.create_comparison_table(task_id)
    return comparison


@router.get("/task/{task_id}/price-spike")
def check_price_spike(task_id: int, medicine_id: int, db: Session = Depends(get_db)):
    """Check if current quotes show price spike vs historical data."""
    quote_service = QuoteService(db)
    spike_data = quote_service.detect_price_spike(task_id, medicine_id)
    return spike_data


@router.get("/{quote_id}")
def get_quote_details(quote_id: int, db: Session = Depends(get_db)):
    """Get details of a specific quote."""
    quote = db.query(QuoteResponse).get(quote_id)
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    from app.models.discovered_supplier import DiscoveredSupplier
    supplier = db.query(DiscoveredSupplier).get(quote.supplier_id)
    
    return {
        "id": quote.id,
        "procurement_task_id": quote.procurement_task_id,
        "supplier_id": quote.supplier_id,
        "supplier_name": supplier.name if supplier else "Unknown",
        "unit_price": quote.unit_price,
        "total_price": quote.total_price,
        "delivery_days": quote.delivery_days,
        "stock_available": quote.stock_available,
        "notes": quote.notes,
        "source": quote.source,
        "responded_at": quote.responded_at.isoformat() if quote.responded_at else None,
        "created_at": quote.created_at.isoformat() if quote.created_at else None
    }
