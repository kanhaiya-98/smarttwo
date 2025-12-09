"""Create negotiation system database tables."""
import sys
sys.path.append('.')

from app.database import engine, Base
from app.models.quote_response import QuoteResponse
from app.models.negotiation_round import NegotiationRound
from app.models.supplier_score import SupplierScore

print("Creating negotiation system tables...")

# Create tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully:")
print("   - quote_responses")
print("   - negotiation_rounds")
print("   - supplier_scores")
