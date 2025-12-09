"""Buyer Agent for autonomous procurement."""
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.models.medicine import ProcurementTask
from app.models.order import PurchaseOrder, OrderStatus
from app.services.supplier_service import SupplierService
# from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
# from langchain.tools import BaseTool 
from app.agents.base_agent import BaseAgent, BaseTool # Use fallback from base_agent
import random

logger = logging.getLogger(__name__)

class BuyerAgent(BaseAgent):
    """
    Autonomous Buyer Agent.
    
    Responsibilities:
    1. Monitor QUEUED procurement tasks.
    2. Analyze requirements (Budget, Urgency).
    3. Find and select best suppliers.
    4. Create Purchase Orders (Draft/Placed).
    """
    
    def __init__(self, db: Session):
        super().__init__(
            name="BUYER",
            description="Procurement Manager responsible for selecting suppliers and creating orders."
        )
        self.db = db
        self.supplier_service = SupplierService(db)
        # self.notification_service = NotificationService(db) # Optional

    def _create_tools(self) -> list[BaseTool]:
        """Tools for the buyer agent."""
        return [] # No LLM tools needed for Phase 2 deterministic logic

    def _get_system_prompt(self) -> str:
        return "You are an autonomous Buyer Agent responsible for pharmacy procurement."

    async def _execute_logic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logic flow (LangGraph integration)."""
        # For Phase 2, we are using deterministic run_cycle, but this method is required by BaseAgent.
        await self.run_cycle()
        return state

    async def run_cycle(self):
        """Execute one cycle of the buyer agent."""
        self.log_activity("IDLE", "Checking for new procurement tasks...", "INFO")
        
        # 1. Find pending tasks
        tasks = self.check_new_tasks()
        
        if not tasks:
            return
            
        self.log_activity("SCAN", f"Found {len(tasks)} pending procurement tasks", "INFO")
        
        for task in tasks:
            await self.process_task(task)
            
    def check_new_tasks(self):
        """Find QUEUED tasks."""
        return self.db.query(ProcurementTask).filter(
            ProcurementTask.status == "QUEUED"
        ).all()

    async def process_task(self, task: ProcurementTask):
        """Process a single procurement task."""
        try:
            self.log_activity(
                "DETECT", 
                f"Processing task for {task.medicine_id} (Urgency: {task.urgency_level})", 
                "INFO",
                {"task_id": task.id, "medicine_id": task.medicine_id}
            )
            
            # Update task status
            task.current_stage = "SUPPLIER_DISCOVERY"
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # 2. Gather Context (Requirement Step 4)
            self.log_activity("SCAN", "Gathering Procurement Context...", "INFO")
            await asyncio.sleep(0.5)
            
            # Simulate Context Checks
            budget_status = "HEALTHY" # In real app, check Finance Service
            preferred_suppliers = "Budget Pharma, QuickMeds" # Based on history
            
            self.log_activity(
                "DETECT",
                f"Context Analyzed: Budget status is {budget_status}. Priority: {task.urgency_level}",
                "INFO",
                {
                    "budget": "OK", 
                    "forecast_qty": task.required_quantity,
                    "cash_flow": "POSITIVE"
                }
            )

            # 3. Find Suppliers (Requirement Step 5) & Collect Quotes (Phase 3)
            self.log_activity("SCAN", f"Searching for eligible suppliers for Medicine ID {task.medicine_id}...", "INFO")
            await asyncio.sleep(1) 
            
            # SIMULATION LOGIC FOR DEMO (Paracetamol)
            if task.medicine_id == 1 or "Paracetamol" in str(task.medicine_id): # Assuming ID 1 or check logic
                candidates = await self._simulate_quotes(task)
            else:
                candidates = self.supplier_service.find_best_suppliers(
                    task.medicine_id, 
                    task.required_quantity, 
                    task.urgency_level
                )
            
            if not candidates:
                self.log_activity("ERROR", "No suitable suppliers found!", "ERROR")
                task.status = "FAILED"
                task.error_message = "No suppliers with stock found"
                self.db.commit()
                return

            # Log candidates found
            self.log_activity(
                "DETECT", 
                f"Received quotes from {len(candidates)} suppliers", 
                "INFO",
                {"candidates": [c['supplier'].name for c in candidates[:3]]}
            )

            # 3. Select Best Candidate (Initial logic, Decision agent does final)
            # Logic is already sorted in find_best_suppliers or simulation
            best_match = candidates[0]
            supplier = best_match['supplier']
            supply_info = best_match['supply_info']
            
            await asyncio.sleep(1) # Simulate decision time
            
            selection_reason = best_match['reason']
            self.log_activity(
                "DECISION", 
                f"Initial Selection: {supplier.name} - {selection_reason}", 
                "SUCCESS",
                {
                    "supplier": supplier.name, 
                    "price": best_match['price'],
                    "score": round(best_match['score'], 2)
                }
            )
            
            # 4. Create Order
            po = self._create_purchase_order(task, best_match)
            
            # Update Task
            task.status = "COMPLETED"
            task.current_stage = "ORDER_CREATED"
            task.completed_at = datetime.utcnow()
            self.db.commit()
            
            self.log_activity(
                "CREATE_TASK", 
                f"Created Purchase Order {po.po_number}", 
                "SUCCESS",
                {"po_number": po.po_number, "amount": po.total_amount}
            )
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            self.log_activity("ERROR", f"Failed to process task: {str(e)}", "ERROR")
            task.status = "ERROR"
            task.error_message = str(e)
            self.db.commit()

    def _create_purchase_order(self, task: ProcurementTask, match: Dict) -> PurchaseOrder:
        """Create a database PurchaseOrder."""
        import uuid
        supplier = match['supplier']
        supply = match['supply_info']
        
        po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        po = PurchaseOrder(
            po_number=po_number,
            procurement_task_id=task.id,
            supplier_id=supplier.id,
            medicine_id=task.medicine_id,
            quantity=task.required_quantity,
            unit_price=match['price'],
            total_amount=match['total_cost'],
            status=OrderStatus.PENDING_APPROVAL, # Or PLACED if auto-approving
            expected_delivery_days=supply.lead_time_days,
            decision_score=match['score'],
            decision_reasoning=match['reason'],
            selected_by_agent=True
        )
        
        self.db.add(po)
        self.db.commit()
        return po
    
    def log_activity(self, action_type: str, message: str, status: str = "INFO", metadata: Dict = None):
        """Log activity to database."""
        # Note: BaseAgent in Step 300 does NOT have log_activity method. 
        # I need to implement it or use a service. MonitorAgent used internal helper.
        # I will check MonitorAgent implementation or just import AgentActivity model and write to DB.
        from app.models.agent_activity import AgentActivity
        
        activity = AgentActivity(
            agent_name=self.name,
            action_type=action_type,
            message=message,
            status=status,
            context_data=metadata or {}
        )
        self.db.add(activity)
        self.db.commit()

    async def _simulate_quotes(self, task: ProcurementTask) -> List[Dict[str, Any]]:
        """
        Generate specific simulation quotes as requested by user.
        Ensures suppliers exist before creating quotes.
        """
        # Phase 3: Quote Request Process (Step 6 & 7)
        self.log_activity("CREATE_TASK", f"Sent parallel quote requests to 5 suppliers for {task.required_quantity} units", "INFO")
        await asyncio.sleep(1.5)

        from app.models.negotiation import Quote
        from app.models.supplier import Supplier
        
        # Hardcoded scenarios mapped to seed suppliers
        scenarios = [
            # Supplier A: Budget Pharma (lowest prices, slower)
            {"code": "SUP-001", "price": 0.15, "del": 7, "qty": 10000, "name": "Budget Pharma", "msg": "Quote received: $0.15/unit - 7 days delivery"},
            # Supplier B: QuickMeds (premium pricing, fast)
            {"code": "SUP-002", "price": 0.22, "del": 1, "qty": 5000, "name": "QuickMeds Inc.", "msg": "Quote received: $0.22/unit - 1 day delivery"},
            # Supplier C: BulkHealth (bulk discount)
            {"code": "SUP-003", "price": 0.18, "del": 5, "qty": 10000, "name": "BulkHealth Wholesale", "msg": "Quote received: $0.18/unit (Bulk: 10k units applied)"},
            # Supplier D: ReliaMeds (consistent)
            {"code": "SUP-004", "price": 0.20, "del": 3, "qty": 8000, "name": "ReliaMeds Corp", "msg": "Quote received: $0.20/unit - 3 days delivery"},
            # Supplier E: LocalStock (Out of stock)
             {"code": "SUP-005", "price": 0.0, "del": 0, "qty": 0, "name": "LocalStock Emergency", "msg": "LocalStock unavailable (Out of Stock)"},
        ]
        
        candidates = []
        
        for scenario in scenarios:
            # 1. Ensure Supplier Exists (Fix for "No suppliers found")
            supplier = self.db.query(Supplier).filter(Supplier.code == scenario["code"]).first()
            if not supplier:
                self.log_activity("INFO", f"Seeding missing supplier: {scenario['name']}", "INFO")
                supplier = Supplier(
                    name=scenario["name"],
                    contact_person="Sales Rep",
                    email=f"sales@{scenario['name'].lower().replace(' ', '')}.com",
                    phone="555-0100",
                    code=scenario["code"],
                    reliability_score=4.5 if "Relia" in scenario["name"] else 4.0
                )
                self.db.add(supplier)
                self.db.commit()
                self.db.refresh(supplier)

            # Simulate Supplier E: Out of stock - Logs rejection
            if scenario["code"] == "SUP-005":
                self.log_activity("WARNING", f"LocalStock Emergency rejected request: Out of Stock", "WARNING")
                continue

            # Check if quote already exists for this task
            existing_quote = self.db.query(Quote).filter(
                Quote.procurement_task_id == task.id, 
                Quote.supplier_id == supplier.id
            ).first()
            
            if existing_quote:
                 # Skip if already quoted (idempotency)
                 continue

            # Create Quote in DB
            new_quote = Quote(
                procurement_task_id=task.id,
                supplier_id=supplier.id,
                unit_price=scenario["price"],
                quantity_available=scenario["qty"],
                delivery_days=scenario["del"],
                response_time_seconds=random.randint(60, 300),
                quote_valid_until=datetime.utcnow() + timedelta(hours=24)
            )
            self.db.add(new_quote)
            
            # Log receipt
            self.log_activity("SCAN", scenario["msg"], "INFO")
            await asyncio.sleep(0.3)
            
            # Calculate score for candidate list
            # Simplified scoring for demo
            score = 100 - (scenario["price"] * 100) - (scenario["del"] * 2) 
            
            candidates.append({
                "supplier": supplier,
                "supply_info": None, # Not needed for demo flow
                "price": scenario["price"],
                "score": score,
                "reason": f"Simulated Match: ${scenario['price']} / {scenario['del']} days"
            })
        
        self.db.commit()
        
        # Sort candidates by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates
