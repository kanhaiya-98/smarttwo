from typing import TypedDict, List, Optional, Any

# Mock classes to make the TypedDict valid without full implementation of other files yet
class Quote: pass
class Negotiation: pass
class Offer: pass
class Decision: pass

class ProcurementState(TypedDict):
    medicine_id: str
    medicine_name: str
    required_quantity: int
    urgency_level: str
    quotes: List[Quote]
    negotiations: List[Negotiation]
    final_offers: List[Offer]
    decision: Optional[Decision]
    approval_status: str
    error: Optional[str]
