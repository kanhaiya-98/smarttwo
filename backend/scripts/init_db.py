"""Initialize database with tables."""
import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, init_db
from app.models import medicine, supplier, order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database."""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"✗ Error creating tables: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
