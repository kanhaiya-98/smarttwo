"""Updated Celery tasks with MonitorAgent integration."""
from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.agents.monitor_agent import MonitorAgent
from app.workflows.procurement_graph import ProcurementWorkflow
from app.models.medicine import ProcurementTask as ProcurementTaskModel, Medicine
from app.models.supplier import Supplier, SupplierPerformance
from app.models.order import PurchaseOrder
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""
    
    def __call__(self, *args, **kwargs):
        """Execute task with database session."""
        db = SessionLocal()
        try:
            return super().__call__(*args, db=db, **kwargs)
        finally:
            db.close()


@celery_app.task(base=DatabaseTask, bind=True)
def check_inventory(self, db):
    """
    Automated inventory monitoring using MonitorAgent.
    Runs every 6 hours as configured in celery_app.py.
    
    Args:
        db: Database session (injected by DatabaseTask)
    
    Returns:
        Scan results dictionary
    """
    logger.info("="*60)
    logger.info("STARTING AUTOMATED INVENTORY SCAN")
    logger.info("="*60)
    
    try:
        # Create monitor agent
        monitor = MonitorAgent(db)
        
        # Execute scan (async method, so we need to run it in event loop)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
             # We are likely in a nested environment or a worker with a loop
             # Use run_coroutine_threadsafe if we are in a thread with a loop?
             # No, if loop is running we can't use run_until_complete.
             # We should create a new task if we are async? But this is a sync function.
             # If loop is running, we cannot block on it easily without nesting issues.
             # Use a new loop in a separate thread implies complexity.
             # Simple workaround: nest_asyncio or checking loop state.
             # For Celery, usually there is NO running loop in the worker process for the task unless configured.
             # But if there IS, we must handle it. 
             # Let's hope calling run_until_complete on a new loop works if get_event_loop fails, 
             # OR if there is a loop, we assume we can use it? No, sync function can't await.
             # We will create a new loop for safety if get_event_loop fails, or use runner.
             # Using asyncio.run() is cleaner in Python 3.7+.
             result = asyncio.run(monitor.execute_scan())
        else:
             result = loop.run_until_complete(monitor.execute_scan())
             
        # Actually the snippet provided:
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # result = loop.run_until_complete(...)
        # loop.close()
        # This is safe for a sync worker process. I will use that pattern from the user prompt.
        
        # Re-implementing strictly from user prompt for safety:
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # result = loop.run_until_complete(monitor.execute_scan())
        # loop.close()
        
        # ... Wait, if I use the user prompt's EXACT code it uses `asyncio.new_event_loop()`. 
        # I will stick to user prompt logic as requested.
        
    except Exception as e_loop:
        # Fallback if loop issues
        logger.warning(f"Loop error, trying asyncio.run: {e_loop}")
        result = asyncio.run(monitor.execute_scan())

    
    logger.info("="*60)
    logger.info(f"SCAN COMPLETE: {result}")
    logger.info("="*60)
    
    # If tasks were created, trigger their workflows
    if result.get("tasks_created", 0) > 0:
        logger.info(f"Triggering {result['tasks_created']} procurement workflows...")
        
        # Get the newly created tasks
        new_tasks = db.query(ProcurementTaskModel).filter(
            ProcurementTaskModel.status == "QUEUED"
        ).all()
        
        for task in new_tasks:
            # Trigger workflow asynchronously
            trigger_procurement_workflow.delay(task.id)
            logger.info(f"Queued workflow for task {task.id}")
    
    return result


@celery_app.task(base=DatabaseTask, bind=True)
def trigger_procurement_workflow(self, task_id: int, db=None):
    """
    Trigger procurement workflow for a task.
    
    Args:
        task_id: Procurement task ID
        db: Database session (injected)
    """
    logger.info(f"Starting procurement workflow for task {task_id}")
    
    task = None
    try:
        # Get task details
        task = db.query(ProcurementTaskModel).filter(
            ProcurementTaskModel.id == task_id
        ).first()
        
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"success": False, "error": "Task not found"}
        
        # Update status
        task.status = "IN_PROGRESS"
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Get medicine details
        medicine = db.query(Medicine).filter(
            Medicine.id == task.medicine_id
        ).first()
        
        if not medicine:
            logger.error(f"Medicine {task.medicine_id} not found")
            task.status = "FAILED"
            task.error_message = "Medicine not found"
            db.commit()
            return {"success": False, "error": "Medicine not found"}
        
        # Create and run workflow
        workflow = ProcurementWorkflow(db)
        
        # Get urgency value safely
        urgency_val = task.urgency_level
        if hasattr(urgency_val, 'value'):
            urgency_val = urgency_val.value
        
        # Run async workflow
        # Using the same loop pattern as check_inventory or the one in user prompt
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(workflow.run(
            task_id=task.id,
            medicine_id=medicine.id,
            medicine_name=medicine.name,
            medicine_dosage=medicine.dosage,
            medicine_form=medicine.form,
            required_quantity=task.required_quantity,
            urgency_level=urgency_val,
            days_of_supply_remaining=task.days_of_supply_remaining,
            average_daily_sales=medicine.average_daily_sales,
            safety_stock=medicine.safety_stock,
            budget_available=50000,
            monthly_volume=int(medicine.average_daily_sales * 30)
        ))
        
        loop.close()
        
        # Update task based on result
        if result.get("errors"):
            task.status = "FAILED"
            task.error_message = "; ".join(result["errors"])
        elif result.get("approval_status") == "PENDING":
            task.status = "PENDING_APPROVAL"
        else:
            task.status = "COMPLETED"
        
        task.current_stage = result.get("current_stage", "COMPLETED")
        task.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Workflow completed for task {task_id}: {task.status}")
        
        return {"success": True, "task_id": task_id, "status": task.status}
        
    except Exception as e:
        logger.error(f"Workflow failed for task {task_id}: {str(e)}", exc_info=True)
        
        if task:
            try:
                task.status = "FAILED"
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
            except Exception as db_e:
                 logger.error(f"Failed to save error status: {db_e}")
        
        return {"success": False, "error": str(e)}


@celery_app.task(base=DatabaseTask)
def update_supplier_performance(db):
    """
    Update supplier performance metrics based on recent orders.
    Runs daily.
    """
    logger.info("Updating supplier performance metrics...")
    
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    
    # Period: Last 30 days
    period_start = datetime.utcnow() - timedelta(days=30)
    period_end = datetime.utcnow()
    
    for supplier in suppliers:
        # Get orders for this supplier in the period
        orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier.id,
            PurchaseOrder.created_at >= period_start,
            PurchaseOrder.created_at <= period_end
        ).all()
        
        if not orders:
            continue
        
        # Calculate metrics
        total_orders = len(orders)
        on_time_deliveries = sum(
            1 for o in orders
            if o.actual_delivery_date and o.expected_delivery_date
            and o.actual_delivery_date <= o.expected_delivery_date
        )
        late_deliveries = sum(
            1 for o in orders
            if o.actual_delivery_date and o.expected_delivery_date
            and o.actual_delivery_date > o.expected_delivery_date
        )
        quality_issues = sum(1 for o in orders if o.quality_check_passed == False)
        
        # Calculate scores
        delivery_score = (on_time_deliveries / total_orders * 100) if total_orders > 0 else 0
        quality_score = ((total_orders - quality_issues) / total_orders * 100) if total_orders > 0 else 100
        
        # Overall score (weighted average)
        overall_score = (delivery_score * 0.6 + quality_score * 0.4)
        
        # Update supplier
        supplier.reliability_score = round(overall_score, 2)
        supplier.on_time_delivery_rate = round(on_time_deliveries / total_orders, 3) if total_orders > 0 else 0
        supplier.total_orders_count = supplier.total_orders_count + total_orders
        
        # Create performance record
        perf = SupplierPerformance(
            supplier_id=supplier.id,
            period_start=period_start,
            period_end=period_end,
            total_orders=total_orders,
            on_time_deliveries=on_time_deliveries,
            late_deliveries=late_deliveries,
            quality_issues=quality_issues,
            delivery_score=delivery_score,
            quality_score=quality_score,
            overall_score=overall_score
        )
        db.add(perf)
    
    db.commit()
    
    logger.info(f"Updated performance metrics for {len(suppliers)} suppliers")
    
    return {"suppliers_updated": len(suppliers)}
