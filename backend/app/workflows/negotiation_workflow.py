"""Negotiation workflow orchestration."""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from celery import shared_task

from app.core.database import SessionLocal
from app.services.quote_service import QuoteService
from app.agents.negotiator_agent import NegotiatorAgent
from app.agents.decision_agent import DecisionAgent
from app.models.medicine import ProcurementTask
from app.models.quote_response import QuoteResponse

logger = logging.getLogger(__name__)


@shared_task(name="trigger_negotiation_workflow")
def trigger_negotiation_workflow(task_id: int):
    """
    Trigger negotiation workflow for a procurement task.
    
    Flow:
    1. Check if we have enough quotes
    2. Analyze quotes and identify negotiation targets
    3. Run negotiation rounds with suppliers
    4. Trigger decision process
    """
    logger.info(f"🤝 Starting negotiation workflow for task {task_id}")
    db = SessionLocal()
    
    try:
        quote_service = QuoteService(db)
        
        # Check if we should start negotiation
        if not quote_service.should_start_negotiation(task_id):
            logger.info(f"Not enough quotes yet for task {task_id}, waiting...")
            return {"status": "waiting", "message": "Waiting for more quotes"}
        
        # Get task
        task = db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update task status
        task.status = 'NEGOTIATING'
        db.commit()
        
        # Get all quotes
        quotes = quote_service.get_quotes_for_task(task_id)
        logger.info(f"Found {len(quotes)} quotes for task {task_id}")
        
        # Initialize negotiator agent
        negotiator = NegotiatorAgent(db)
        
        # Run negotiation workflow
        negotiation_results = negotiator.negotiate_with_suppliers(
            task_id=task_id,
            quotes=quotes
        )
        
        logger.info(f"Negotiation complete: {len(negotiation_results)} suppliers negotiated")
        
        # Trigger decision process
        from app.tasks.procurement_tasks import make_procurement_decision
        make_procurement_decision.delay(task_id)
        
        return {
            "status": "success",
            "negotiations_completed": len(negotiation_results)
        }
        
    except Exception as e:
        logger.error(f"Error in negotiation workflow: {e}")
        task = db.query(ProcurementTask).get(task_id)
        if task:
            task.status = 'FAILED'
            task.error_message = f"Negotiation error: {str(e)}"
            db.commit()
        return {"status": "error", "error": str(e)}
        
finally:
        db.close()


def run_negotiation_sync(db: Session, task_id: int) -> Dict:
    """
    Run negotiation synchronously (for testing or direct calls).
    """
    quote_service = QuoteService(db)
    negotiator = NegotiatorAgent(db)
    
    quotes = quote_service.get_quotes_for_task(task_id)
    
    if not quotes:
        return {"status": "no_quotes"}
    
    results = negotiator.negotiate_with_suppliers(task_id, quotes)
    
    return {
        "status": "success",
        "results": results
    }
