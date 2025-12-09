from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.medicine import Medicine, ProcurementTask, UrgencyLevel
from app.models.supplier import Supplier, SupplierPerformance
from app.models.order import PurchaseOrder
from app.workflows.procurement_graph import ProcurementWorkflow
from app.config import settings
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

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
    Check inventory levels and trigger procurement for low stock items.
    Runs every 6 hours as configured.
    """
    logger.info("Starting inventory check...")
    
    # Get all active medicines
    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    
    tasks_created = 0
    
    for medicine in medicines:
        # Skip if average daily sales is 0 (can't calculate)
        if medicine.average_daily_sales <= 0:
            continue
        
        # Calculate days of supply
        days_of_supply = medicine.current_stock / medicine.average_daily_sales
        
        # Check if below reorder threshold
        if days_of_supply < settings.REORDER_THRESHOLD_DAYS:
            # Determine urgency
            if days_of_supply < settings.CRITICAL_THRESHOLD_DAYS:
                urgency = UrgencyLevel.CRITICAL
            elif days_of_supply < settings.HIGH_THRESHOLD_DAYS:
                urgency = UrgencyLevel.HIGH
            else:
                urgency = UrgencyLevel.MEDIUM
            
            # Check if already have active task for this medicine
            existing_task = db.query(ProcurementTask).filter(
                ProcurementTask.medicine_id == medicine.id,
                ProcurementTask.status.in_(["QUEUED", "IN_PROGRESS", "NEGOTIATING", "PENDING_APPROVAL"])
            ).first()
            
            if existing_task:
                logger.info(f"Skipping {medicine.name} - active task exists")
                continue
            
            # Calculate required quantity
            # Formula: (Reorder point - Current stock) + Safety stock
            required_quantity = max(
                medicine.reorder_point - medicine.current_stock + medicine.safety_stock,
                int(medicine.average_daily_sales * 14)  # At least 2 weeks supply
            )
            
            # Create procurement task
            task = ProcurementTask(
                medicine_id=medicine.id,
                required_quantity=required_quantity,
                urgency_level=urgency,
                days_of_supply_remaining=days_of_supply,
                status="QUEUED"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            logger.info(f"Created procurement task for {medicine.name} (Task ID: {task.id})")
            tasks_created += 1
            
            # Trigger procurement workflow asynchronously
            trigger_procurement_workflow.delay(
                task_id=task.id,
                medicine_id=medicine.id,
                medicine_name=medicine.name,
                medicine_dosage=medicine.dosage,
                medicine_form=medicine.form,
                required_quantity=required_quantity,
                urgency_level=urgency.value,
                days_of_supply_remaining=days_of_supply,
                average_daily_sales=medicine.average_daily_sales,
                safety_stock=medicine.safety_stock
            )
    
    logger.info(f"Inventory check complete. Created {tasks_created} procurement tasks.")
    
    return {
        "tasks_created": tasks_created,
        "checked_medicines": len(medicines)
    }


@celery_app.task(base=DatabaseTask)
def trigger_procurement_workflow(
    task_id: int,
    medicine_id: int,
    medicine_name: str,
    medicine_dosage: str,
    medicine_form: str,
    required_quantity: int,
    urgency_level: str,
    days_of_supply_remaining: float,
    average_daily_sales: float,
    safety_stock: int,
    db=None
):
    """
    Execute the procurement workflow for a task.
    
    Args:
        All parameters needed for procurement workflow
        db: Database session (injected by DatabaseTask)
    """
    logger.info(f"Starting procurement workflow for task {task_id}")
    
    # Update task status
    task = db.query(ProcurementTask).filter(ProcurementTask.id == task_id).first()
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    task.status = "IN_PROGRESS"
    task.started_at = datetime.utcnow()
    db.commit()
    
    try:
        # Create workflow
        workflow = ProcurementWorkflow(db)
        
        # Run workflow
        result = workflow.run(
            task_id=task_id,
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            medicine_dosage=medicine_dosage,
            medicine_form=medicine_form,
            required_quantity=required_quantity,
            urgency_level=urgency_level,
            days_of_supply_remaining=days_of_supply_remaining,
            average_daily_sales=average_daily_sales,
            safety_stock=safety_stock,
            budget_available=50000,  # This should come from actual budget system
            monthly_volume=int(average_daily_sales * 30)
        )
        
        # Update task status based on result
        if result.get("errors"):
            task.status = "FAILED"
            task.error_message = "; ".join(result["errors"])
        elif result.get("approval_status") == "PENDING":
            task.status = "PENDING_APPROVAL"
        elif result.get("order_placed"):
            task.status = "COMPLETED"
        else:
            task.status = "COMPLETED"
        
        task.current_stage = result.get("current_stage", "COMPLETED")
        task.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Procurement workflow completed for task {task_id}: {task.status}")
        
    except Exception as e:
        logger.error(f"Error in procurement workflow for task {task_id}: {str(e)}")
        task.status = "FAILED"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()
        raise


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
