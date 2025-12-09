"""State management for procurement workflow using LangGraph."""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from operator import add
from datetime import datetime


class Quote(TypedDict):
    """Quote from a supplier."""
    supplier_id: int
    supplier_name: str
    unit_price: float
    delivery_days: int
    quantity_available: int
    stock_availability: str
    response_time_seconds: int
    bulk_discount_available: bool
    bulk_discount_price: Optional[float]
    bulk_discount_quantity: Optional[int]


class NegotiationRound(TypedDict):
    """Single round of negotiation."""
    round_number: int
    our_message: str
    supplier_response: Optional[str]
    our_offer_price: Optional[float]
    supplier_counter_price: Optional[float]
    status: str  # SENT, RECEIVED, ACCEPTED, REJECTED


class Negotiation(TypedDict):
    """Complete negotiation with a supplier."""
    supplier_id: int
    supplier_name: str
    initial_quote: Quote
    rounds: List[NegotiationRound]
    final_price: Optional[float]
    final_delivery_days: Optional[int]
    status: str  # IN_PROGRESS, SUCCESSFUL, FAILED, TIMEOUT
    savings: Optional[float]


class ScoringDetails(TypedDict):
    """Detailed scoring for a supplier."""
    supplier_id: int
    supplier_name: str
    price_score: float
    speed_score: float
    reliability_score: float
    stock_score: float
    total_score: float
    weights: Dict[str, float]


class Decision(TypedDict):
    """Final procurement decision."""
    selected_supplier_id: int
    selected_supplier_name: str
    final_unit_price: float
    final_delivery_days: int
    total_amount: float
    reasoning: str
    all_scores: List[ScoringDetails]
    decision_factors: Dict[str, Any]


class ProcurementState(TypedDict):
    """
    State for the procurement workflow.
    This state is passed between all agents in the LangGraph.
    """
    
    # Task identification
    task_id: int
    medicine_id: int
    medicine_name: str
    medicine_dosage: str
    medicine_form: str
    
    # Requirements
    required_quantity: int
    urgency_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    days_of_supply_remaining: float
    
    # Context
    average_daily_sales: float
    safety_stock: int
    budget_available: float
    monthly_volume: int
    
    # Supplier discovery
    eligible_suppliers: Annotated[List[Dict[str, Any]], add]
    
    # Quote collection
    quotes: Annotated[List[Quote], add]
    quote_request_sent_at: Optional[datetime]
    quote_timeout_reached: bool
    
    # Negotiations
    negotiations: Annotated[List[Negotiation], add]
    negotiation_complete: bool
    
    # Decision
    decision: Optional[Decision]
    decision_reasoning: Optional[str]
    
    # Approval
    requires_approval: bool
    approval_status: str  # PENDING, APPROVED, REJECTED
    approval_notes: Optional[str]
    
    # Order placement
    po_number: Optional[str]
    order_placed: bool
    order_confirmed: bool
    
    # Error handling
    errors: Annotated[List[str], add]
    current_stage: str
    
    # Metadata
    workflow_started_at: datetime
    workflow_completed_at: Optional[datetime]


def create_initial_state(
    task_id: int,
    medicine_id: int,
    medicine_name: str,
    medicine_dosage: str,
    medicine_form: str,
    required_quantity: int,
    urgency_level: str,
    days_of_supply_remaining: float,
    average_daily_sales: float,
    safety_stock: int,
    budget_available: float,
    monthly_volume: int,
) -> ProcurementState:
    """
    Create initial state for procurement workflow.
    
    Args:
        All required task parameters
        
    Returns:
        Initial ProcurementState
    """
    return ProcurementState(
        task_id=task_id,
        medicine_id=medicine_id,
        medicine_name=medicine_name,
        medicine_dosage=medicine_dosage,
        medicine_form=medicine_form,
        required_quantity=required_quantity,
        urgency_level=urgency_level,
        days_of_supply_remaining=days_of_supply_remaining,
        average_daily_sales=average_daily_sales,
        safety_stock=safety_stock,
        budget_available=budget_available,
        monthly_volume=monthly_volume,
        eligible_suppliers=[],
        quotes=[],
        quote_request_sent_at=None,
        quote_timeout_reached=False,
        negotiations=[],
        negotiation_complete=False,
        decision=None,
        decision_reasoning=None,
        requires_approval=False,
        approval_status="PENDING",
        approval_notes=None,
        po_number=None,
        order_placed=False,
        order_confirmed=False,
        errors=[],
        current_stage="INITIALIZED",
        workflow_started_at=datetime.utcnow(),
        workflow_completed_at=None,
    )
