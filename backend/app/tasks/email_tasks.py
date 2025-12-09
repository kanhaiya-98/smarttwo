"""Email checking tasks for Celery."""
import logging
from typing import List
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.email_service import EmailService
from app.services.email_parser import EmailParser
from app.models.email_message import EmailMessage
from app.models.email_thread import EmailThread
from app.models.quote_response import QuoteResponse
from app.models.medicine import ProcurementTask
from app.workflows.negotiation_workflow import trigger_negotiation_workflow

logger = logging.getLogger(__name__)


@shared_task(name="check_email_replies")
def check_email_replies():
    """
    Periodic task to check for supplier email replies.
    Runs every 5 minutes.
    """
    logger.info("📧 Starting email reply check...")
    db = SessionLocal()
    
    try:
        email_service = EmailService(demo_mode=True)
        parser = EmailParser()
        
        # Check for new replies
        new_messages = email_service.check_for_replies(db)
        
        if not new_messages:
            logger.info("No new email replies found")
            return {"status": "success", "new_messages": 0}
        
        logger.info(f"Found {len(new_messages)} new email replies")
        
        # Process each reply
        quotes_created = 0
        for message in new_messages:
            try:
                # Parse quote from email
                quote_data = parser.parse_quote_from_email(
                    subject=message.subject,
                    body=message.body,
                    sender=message.sender
                )
                
                if quote_data:
                    # Get the email thread
                    thread = db.query(EmailThread).filter(
                        EmailThread.id == message.thread_id
                    ).first()
                    
                    if thread:
                        # Create quote response
                        quote = QuoteResponse(
                            procurement_task_id=thread.procurement_task_id,
                            supplier_id=thread.supplier_id,
                            unit_price=quote_data['unit_price'],
                            total_price=quote_data['total_price'],
                            delivery_days=quote_data['delivery_days'],
                            stock_available=quote_data.get('stock_available'),
                            notes=quote_data.get('notes', ''),
                            source='email',
                            email_message_id=message.id
                        )
                        db.add(quote)
                        db.commit()
                        db.refresh(quote)
                        
                        quotes_created += 1
                        logger.info(f"✓ Created quote from {message.sender}: ${quote_data['unit_price']}/unit")
                        
                        # Check if we should trigger negotiation
                        task = db.query(ProcurementTask).get(thread.procurement_task_id)
                        if task and task.status == 'IN_PROGRESS':
                            # Trigger negotiation workflow
                            trigger_negotiation_workflow.delay(thread.procurement_task_id)
                
            except Exception as e:
                logger.error(f"Error processing message {message.id}: {e}")
                continue
        
        logger.info(f"✓ Email check complete: {quotes_created} quotes created")
        return {
            "status": "success",
            "new_messages": len(new_messages),
            "quotes_created": quotes_created
        }
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}")
        return {"status": "error", "error": str(e)}
        
    finally:
        db.close()


@shared_task(name="check_quote_timeouts")
def check_quote_timeouts():
    """
    Check for quote collection timeouts (2 hours).
    Trigger decision process if timeout reached.
    """
    logger.info("⏰ Checking for quote timeouts...")
    db = SessionLocal()
    
    try:
        from datetime import timedelta
        timeout_threshold = datetime.utcnow() - timedelta(hours=2)
        
        # Find tasks that are waiting for quotes and have timed out
        tasks = db.query(ProcurementTask).filter(
            ProcurementTask.status == 'IN_PROGRESS',
            ProcurementTask.created_at < timeout_threshold
        ).all()
        
        timed_out = 0
        for task in tasks:
            # Check if we have any quotes
            quote_count = db.query(QuoteResponse).filter(
                QuoteResponse.procurement_task_id == task.id
            ).count()
            
            if quote_count > 0:
                # We have quotes, trigger decision
                logger.info(f"Task {task.id} timed out with {quote_count} quotes, triggering decision")
                from app.tasks.procurement_tasks import make_procurement_decision
                make_procurement_decision.delay(task.id)
                timed_out += 1
            else:
                # No quotes at all, escalate
                logger.warning(f"Task {task.id} timed out with no quotes, escalating")
                task.status = 'FAILED'
                task.error_message = "No quotes received within timeout period"
                db.commit()
                
                # TODO: Send alert to pharmacist
        
        return {
            "status": "success",
            "timeouts_processed": timed_out
        }
        
    except Exception as e:
        logger.error(f"Error checking timeouts: {e}")
        return {"status": "error", "error": str(e)}
        
    finally:
        db.close()
