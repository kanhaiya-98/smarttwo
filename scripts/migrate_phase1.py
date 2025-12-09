"""Phase 1 Database Migration Script."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/backend')

from sqlalchemy import inspect, text, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import engine, SessionLocal
from app.models.agent_activity import AgentActivity
from app.models.demand_forecast import DemandForecast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def table_exists(table_name):
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    if not table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_agent_activities():
    """Create agent_activities table if it doesn't exist."""
    if table_exists('agent_activities'):
        logger.info("✓ agent_activities table already exists")
        return
    
    logger.info("Creating agent_activities table...")
    
    AgentActivity.__table__.create(engine)
    
    logger.info("✓ agent_activities table created successfully")


def migrate_demand_forecasts():
    """Create demand_forecasts table if it doesn't exist."""
    if table_exists('demand_forecasts'):
        logger.info("✓ demand_forecasts table already exists")
        return
    
    logger.info("Creating demand_forecasts table...")
    
    DemandForecast.__table__.create(engine)
    
    logger.info("✓ demand_forecasts table created successfully")


def migrate_medicine_columns():
    """Add new columns to medicines table."""
    columns_to_add = {
        'seasonality_index': 'FLOAT DEFAULT 1.0',
        'peak_season_months': 'JSON',
        'last_forecast_update': 'TIMESTAMP WITH TIME ZONE',
        'stockout_count': 'INTEGER DEFAULT 0',
        'last_stockout_date': 'TIMESTAMP WITH TIME ZONE',
        'custom_reorder_days': 'INTEGER',
        'is_critical': 'BOOLEAN DEFAULT FALSE'
    }
    
    db = SessionLocal()
    
    for col_name, col_type in columns_to_add.items():
        if column_exists('medicines', col_name):
            logger.info(f"✓ medicines.{col_name} already exists")
            continue
        
        logger.info(f"Adding medicines.{col_name}...")
        
        try:
            sql = f"ALTER TABLE medicines ADD COLUMN {col_name} {col_type}"
            db.execute(text(sql))
            db.commit()
            logger.info(f"✓ medicines.{col_name} added successfully")
        except Exception as e:
            logger.error(f"✗ Failed to add medicines.{col_name}: {str(e)}")
            db.rollback()
    
    db.close()


def seed_initial_forecasts():
    """Generate initial demand forecasts for all medicines."""
    from app.services.forecast_service import ForecastingService
    
    logger.info("Generating initial demand forecasts...")
    
    db = SessionLocal()
    try:
        forecasting_service = ForecastingService(db)
        # Note: update_forecasts might not return a count in current implementation
        # Checking implementation from Step 31/68:
        # update_forecasts(self, medicine_id: int = None) -> None or count?
        # In Step 68 summary: "Generates or updates... Logs forecast generation..."
        # It iterates. If I need a count, I assume the user code knows it returns it, OR I'll handle if it returns None.
        count = forecasting_service.update_forecasts()
        if count is None:
             count = "unknown"
        logger.info(f"✓ Generated {count} initial demand forecasts")
    except Exception as e:
        logger.error(f"✗ Failed to generate forecasts: {str(e)}")
    finally:
        db.close()


def verify_migration():
    """Verify that all migrations were successful."""
    logger.info("\n" + "="*60)
    logger.info("VERIFYING MIGRATION")
    logger.info("="*60)
    
    checks = []
    
    # Check tables
    if table_exists('agent_activities'):
        checks.append("✓ agent_activities table exists")
    else:
        checks.append("✗ agent_activities table MISSING")
    
    if table_exists('demand_forecasts'):
        checks.append("✓ demand_forecasts table exists")
    else:
        checks.append("✗ demand_forecasts table MISSING")
    
    # Check medicine columns
    medicine_cols = [
        'seasonality_index',
        'peak_season_months',
        'last_forecast_update',
        'stockout_count',
        'last_stockout_date',
        'custom_reorder_days',
        'is_critical'
    ]
    
    for col in medicine_cols:
        if column_exists('medicines', col):
            checks.append(f"✓ medicines.{col} exists")
        else:
            checks.append(f"✗ medicines.{col} MISSING")
    
    # Print results
    for check in checks:
        logger.info(check)
    
    # Check if all passed
    failed = [c for c in checks if c.startswith('✗')]
    
    logger.info("="*60)
    if failed:
        logger.error(f"MIGRATION INCOMPLETE: {len(failed)} checks failed")
        return False
    else:
        logger.info("✅ MIGRATION SUCCESSFUL - All checks passed!")
        return True


def main():
    """Run all migrations."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 1 DATABASE MIGRATION")
    logger.info("="*60 + "\n")
    
    try:
        # Step 1: Create new tables
        logger.info("Step 1: Creating new tables...")
        migrate_agent_activities()
        migrate_demand_forecasts()
        
        # Step 2: Add new columns to existing tables
        logger.info("\nStep 2: Adding new columns to existing tables...")
        migrate_medicine_columns()
        
        # Step 3: Seed initial data
        logger.info("\nStep 3: Seeding initial data...")
        seed_initial_forecasts()
        
        # Step 4: Verify
        logger.info("\nStep 4: Verifying migration...")
        success = verify_migration()
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("🎉 MIGRATION COMPLETE!")
            logger.info("="*60)
            logger.info("\nNext steps:")
            logger.info("1. Restart your application")
            logger.info("2. Check the agent activity dashboard")
            logger.info("3. Trigger a manual inventory scan to test")
            logger.info("\nCommand to test:")
            logger.info("  docker-compose exec backend python -c \"from app.agents.monitor_agent import MonitorAgent; from app.database import SessionLocal; import asyncio; db = SessionLocal(); agent = MonitorAgent(db); asyncio.run(agent.execute_scan())\"")
        else:
            logger.error("\n⚠️  Migration completed with errors. Please review logs.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ Migration failed with error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
