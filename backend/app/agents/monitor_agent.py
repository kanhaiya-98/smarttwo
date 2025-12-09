"""Enhanced Monitor Agent with real-time activity logging."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.medicine import Medicine, ProcurementTask, UrgencyLevel
from app.models.agent_activity import AgentActivity
from app.services.forecast_service import ForecastingService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MonitorAgent:
    """Agent responsible for continuous inventory monitoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.forecasting_service = ForecastingService(db)
        self.name = "MONITOR"
    
    def _log_activity(
        self,
        action_type: str,
        message: str,
        status: str = "INFO",
        metadata: Dict[str, Any] = None
    ):
        """
        Log agent activity to database for real-time display.
        
        Args:
            action_type: Type of action (SCAN, DETECT, ALERT, etc.)
            message: Human-readable message
            status: INFO, SUCCESS, WARNING, ERROR
            metadata: Additional context data
        """
        try:
            activity = AgentActivity(
                agent_name=self.name,
                action_type=action_type,
                message=message,
                status=status,
                context_data=metadata or {}
            )
            self.db.add(activity)
            self.db.commit()
            
            logger.info(f"[{self.name}] {action_type}: {message}")
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
    
    async def execute_scan(self) -> Dict[str, Any]:
        """
        Execute complete inventory scan with real-time logging.
        
        Returns:
            Scan results with statistics
        """
        scan_start = datetime.utcnow()
        
        # Log scan start
        self._log_activity(
            action_type="SCAN",
            message="🔍 Starting automated inventory scan...",
            status="INFO"
        )
        
        try:
            # Step 1: Update forecasts first
            self._log_activity(
                action_type="FORECAST",
                message="📊 Updating demand forecasts for intelligent analysis...",
                status="INFO"
            )
            
            forecast_count = self.forecasting_service.update_forecasts()
            
            self._log_activity(
                action_type="FORECAST",
                message=f"✓ Generated {forecast_count} demand forecasts",
                status="SUCCESS",
                metadata={"forecast_count": forecast_count}
            )
            
            # Step 2: Get all active medicines
            medicines = self.db.query(Medicine).filter(
                Medicine.is_active == True
            ).all()
            
            self._log_activity(
                action_type="SCAN",
                message=f"📦 Scanning {len(medicines)} active medicines...",
                status="INFO",
                metadata={"total_medicines": len(medicines)}
            )
            
            # Step 3: Check each medicine
            low_stock_items = []
            tasks_created = 0
            
            for medicine in medicines:
                # Calculate days of supply using forecasts
                days_supply = self.forecasting_service.calculate_days_supply(medicine)
                
                # Log check for each medicine (only in verbose mode or for low stock)
                if days_supply < settings.REORDER_THRESHOLD_DAYS:
                    self._log_activity(
                        action_type="DETECT",
                        message=f"⚠️  Low stock: {medicine.name} ({days_supply:.1f} days remaining)",
                        status="WARNING",
                        metadata={
                            "medicine_id": medicine.id,
                            "medicine_name": medicine.name,
                            "current_stock": medicine.current_stock,
                            "days_supply": round(days_supply, 1)
                        }
                    )
                    
                    low_stock_items.append({
                        "medicine": medicine,
                        "days_supply": days_supply
                    })
            
            # Step 4: Create procurement tasks for low stock items
            if low_stock_items:
                self._log_activity(
                    action_type="ALERT",
                    message=f"🚨 Found {len(low_stock_items)} items below reorder threshold",
                    status="WARNING",
                    metadata={"low_stock_count": len(low_stock_items)}
                )
                
                for item in low_stock_items:
                    medicine = item["medicine"]
                    days_supply = item["days_supply"]
                    
                    # Check if task already exists
                    existing_task = self.db.query(ProcurementTask).filter(
                        ProcurementTask.medicine_id == medicine.id,
                        ProcurementTask.status.in_([
                            "QUEUED", "IN_PROGRESS", "NEGOTIATING", "PENDING_APPROVAL"
                        ])
                    ).first()
                    
                    if existing_task:
                        self._log_activity(
                            action_type="SKIP",
                            message=f"⏭️  Skipping {medicine.name} - Active task exists (ID: {existing_task.id})",
                            status="INFO",
                            metadata={
                                "medicine_id": medicine.id,
                                "existing_task_id": existing_task.id
                            }
                        )
                        continue
                    
                    # Determine urgency
                    if days_supply < settings.CRITICAL_THRESHOLD_DAYS:
                        urgency = UrgencyLevel.CRITICAL
                        urgency_emoji = "🔴"
                    elif days_supply < settings.HIGH_THRESHOLD_DAYS:
                        urgency = UrgencyLevel.HIGH
                        urgency_emoji = "🟠"
                    else:
                        urgency = UrgencyLevel.MEDIUM
                        urgency_emoji = "🟡"
                    
                    # Calculate required quantity using forecast
                    forecast_30_days = self.forecasting_service._get_forecast_demand(
                        medicine.id, 30
                    )
                    
                    if forecast_30_days > 0:
                        required_quantity = int(forecast_30_days + medicine.safety_stock)
                    else:
                        required_quantity = max(
                            medicine.reorder_point - medicine.current_stock + medicine.safety_stock,
                            int(medicine.average_daily_sales * 14)
                        )
                    
                    # Create procurement task
                    task = ProcurementTask(
                        medicine_id=medicine.id,
                        required_quantity=required_quantity,
                        urgency_level=urgency,
                        days_of_supply_remaining=days_supply,
                        status="QUEUED"
                    )
                    
                    self.db.add(task)
                    self.db.commit()
                    self.db.refresh(task)
                    
                    tasks_created += 1
                    
                    self._log_activity(
                        action_type="CREATE_TASK",
                        message=f"{urgency_emoji} Created procurement task #{task.id} for {medicine.name} - {urgency.value} priority (qty: {required_quantity:,})",
                        status="SUCCESS",
                        metadata={
                            "task_id": task.id,
                            "medicine_id": medicine.id,
                            "medicine_name": medicine.name,
                            "urgency": urgency.value,
                            "required_quantity": required_quantity,
                            "days_supply": round(days_supply, 1)
                        }
                    )
                    
                    # Log to standard logger too
                    logger.info(
                        f"Created procurement task {task.id} for {medicine.name} "
                        f"({urgency.value}, {days_supply:.1f} days supply, qty: {required_quantity})"
                    )
            else:
                self._log_activity(
                    action_type="SCAN",
                    message="✓ All medicines have adequate stock levels",
                    status="SUCCESS"
                )
            
            # Step 5: Scan complete summary
            scan_duration = (datetime.utcnow() - scan_start).total_seconds()
            
            self._log_activity(
                action_type="SCAN",
                message=f"✅ Scan complete in {scan_duration:.1f}s - Created {tasks_created} tasks for {len(low_stock_items)} low stock items",
                status="SUCCESS",
                metadata={
                    "scan_duration_seconds": round(scan_duration, 1),
                    "medicines_scanned": len(medicines),
                    "low_stock_found": len(low_stock_items),
                    "tasks_created": tasks_created
                }
            )
            
            return {
                "success": True,
                "medicines_scanned": len(medicines),
                "low_stock_items": len(low_stock_items),
                "tasks_created": tasks_created,
                "scan_duration_seconds": round(scan_duration, 1)
            }
            
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            
            self._log_activity(
                action_type="ERROR",
                message=f"❌ {error_msg}",
                status="ERROR",
                metadata={"error": str(e)}
            )
            
            logger.error(f"Monitor Agent scan failed: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e),
                "medicines_scanned": 0,
                "low_stock_items": 0,
                "tasks_created": 0
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitor agent status.
        
        Returns:
            Status information
        """
        # Check if there's been activity in last 2 minutes
        two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
        
        recent_activity = self.db.query(AgentActivity).filter(
            AgentActivity.agent_name == self.name,
            AgentActivity.created_at >= two_minutes_ago
        ).first()
        
        status = "ACTIVE" if recent_activity else "IDLE"
        
        # Get last activity
        last_activity = self.db.query(AgentActivity).filter(
            AgentActivity.agent_name == self.name
        ).order_by(AgentActivity.created_at.desc()).first()
        
        return {
            "agent": self.name,
            "status": status,
            "last_activity": last_activity.message if last_activity else None,
            "last_activity_time": last_activity.created_at if last_activity else None
        }
