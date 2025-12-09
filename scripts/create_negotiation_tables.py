"""Create tables for negotiation and decision system."""
import sys
sys.path.append('.')

from app.database import Base, engine
from app.models.quote_response import QuoteResponse
from app.models.negotiation_round import NegotiationRound
from app.models.supplier_score import SupplierScore

print("Creating negotiation & decision tables...")

try:
    Base.metadata.create_all(bind=engine, tables=[
        QuoteResponse.__table__,
        NegotiationRound.__table__,
        SupplierScore.__table__
    ])
    print("Tables created successfully!")
except Exception as e:
    print(f"Error creating tables: {e}")
