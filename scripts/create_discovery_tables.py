"""Simple script to create discovery tables directly."""
from app.database import engine
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.email_thread import EmailThread
from app.models.email_message import EmailMessage
from app.database import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create supplier discovery tables."""
    logger.info("Creating supplier discovery tables...")
    
    # Import models to ensure they're registered
    from app.models import discovered_supplier, email_thread, email_message
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("✓ Tables created successfully!")

if __name__ == "__main__":
    create_tables()
