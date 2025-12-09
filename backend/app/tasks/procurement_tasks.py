from celery import shared_task
from app.database import SessionLocal
from app.agents.buyer_agent import BuyerAgent
from app.models.medicine import ProcurementTask
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.procurement.run_buyer_agent")
def run_buyer_agent():
    """Execute Buyer Agent cycle to process queued tasks."""
    logger.info("Starting Buyer Agent cycle...")
    db = SessionLocal()
    try:
        agent = BuyerAgent(db)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(agent.run_cycle())
        loop.close()
        
        logger.info("Buyer Agent cycle completed.")
    except Exception as e:
        logger.error(f"Error in Buyer Agent task: {e}")
    finally:
        db.close()

@shared_task(name="app.tasks.procurement.run_negotiator_agent")
def run_negotiator_agent():
    """Execute Negotiator Agent cycle."""
    logger.info("Starting Negotiator Agent cycle...")
    db = SessionLocal()
    try:
        # Import here to avoid circular dependencies
        from app.agents.negotiator_agent import NegotiatorAgent
        agent = NegotiatorAgent(db)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agent.run_cycle())
        loop.close()
        logger.info("Negotiator Agent cycle completed.")
    except Exception as e:
        logger.error(f"Error in Negotiator Agent task: {e}")
    finally:
        db.close()

@shared_task(name="app.tasks.procurement.run_decision_agent")
def run_decision_agent():
    """Execute Decision Agent cycle."""
    logger.info("Starting Decision Agent cycle...")
    db = SessionLocal()
    try:
        from app.agents.decision_agent import DecisionAgent
        agent = DecisionAgent(db)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agent.run_cycle())
        loop.close()
        logger.info("Decision Agent cycle completed.")
    except Exception as e:
        logger.error(f"Error in Decision Agent task: {e}")
    finally:
        db.close()


@shared_task(name="make_procurement_decision")
def make_procurement_decision(task_id: int):
    """
    Make procurement decision for a task after negotiations.
    
    This task:
    1. Runs decision agent to score all quotes
    2. Creates approval request or auto-approves
    3. Sends PO if auto-approved
    """
    logger.info(f"📊 Making procurement decision for task {task_id}")
    db = SessionLocal()
    
    try:
        from app.agents.decision_agent import DecisionAgent
        from app.services.approval_service import ApprovalService
        from app.services.po_service import POService
        from app.services.quote_service import QuoteService
        from app.models.medicine import ProcurementTask
        
        # Get task
        task = db.query(ProcurementTask).get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Get all quotes
        quote_service = QuoteService(db)
        quotes = quote_service.get_quotes_for_task(task_id)
        
        if not quotes:
            logger.warning(f"No quotes available for task {task_id}")
            task.status = 'FAILED'
            task.error_message = "No quotes received"
            db.commit()
            return {"status": "failed", "error": "No quotes"}
        
        logger.info(f"Running decision agent with {len(quotes)} quotes")
        
        # Run decision agent
        decision_agent = DecisionAgent(db)
        best_score, reasoning = decision_agent.make_decision(
            quotes=quotes,
            required_quantity=task.quantity_needed or 5000,
            urgency=task.urgency or "MEDIUM"
        )
        
        if not best_score:
            logger.error("Decision agent failed to select a supplier")
            task.status = 'FAILED'
            task.error_message = "Decision agent failed"
            db.commit()
            return {"status": "failed", "error": "No decision"}
        
        logger.info(
            f"Decision: Supplier {best_score.supplier_id}, "
            f"Score: {best_score.total_score:.2f}"
        )
        
        # Create approval request
        approval_service = ApprovalService(db)
        approval_result = approval_service.create_approval_request(
            task_id=task_id,
            selected_score=best_score,
            decision_reasoning=reasoning
        )
        
        if approval_result['auto_approved']:
            # Auto-approved, send PO
            logger.info(f"Order auto-approved: {approval_result['order'].po_number}")
            
            # Send PO to supplier
            po_service = POService(db)
            po_service.send_po_to_supplier(approval_result['order'].id)
            
            return {
                "status": "auto_approved",
                "order_id": approval_result['order'].id,
                "po_number": approval_result['order'].po_number
            }
        else:
            # Manual approval required
            logger.info(f"Task {task_id} requires manual approval")
            
            return {
                "status": "pending_approval",
                "task_id": task_id,
                "total_price": approval_result['total_price']
            }
    
    except Exception as e:
        logger.error(f"Error making procurement decision: {e}")
        task = db.query(ProcurementTask).get(task_id)
        if task:
            task.status = 'FAILED'
            task.error_message = f"Decision error: {str(e)}"
            db.commit()
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()

