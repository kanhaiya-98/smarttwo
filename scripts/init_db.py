"""Initialize database with tables."""
import sys
sys.path.append('.')

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
