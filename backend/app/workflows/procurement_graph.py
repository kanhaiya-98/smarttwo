"""LangGraph workflow for procurement process."""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.workflows.state import ProcurementState, create_initial_state
from app.agents.buyer_agent import BuyerAgent
from app.agents.negotiator_agent import NegotiatorAgent
from app.agents.decision_agent import DecisionAgent
from app.database import get_db
from app.models.order import PurchaseOrder, OrderStatus
from app.config import settings
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ProcurementWorkflow:
    """Workflow for automated procurement using LangGraph."""
    
    def __init__(self, db: Session):
        """
        Initialize procurement workflow.
        
        Args:
            db: Database session
        """
        self.db = db
        self.buyer_agent = BuyerAgent(db)
        self.negotiator_agent = NegotiatorAgent(db, max_rounds=settings.MAX_NEGOTIATION_ROUNDS)
        self.decision_agent = DecisionAgent(db)
        
        # Build the workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            StateGraph workflow
        """
        workflow = StateGraph(ProcurementState)
        
        # Add nodes (each node is an agent or decision point)
        workflow.add_node("buyer", self._buyer_node)
        workflow.add_node("negotiator", self._negotiator_node)
        workflow.add_node("decision", self._decision_node)
        workflow.add_node("approval_check", self._approval_check_node)
        workflow.add_node("place_order", self._place_order_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("buyer")
        
        # From buyer to negotiator or error
        workflow.add_conditional_edges(
            "buyer",
            self._should_continue_after_buyer,
            {
                "continue": "negotiator",
                "error": "handle_error"
            }
        )
        
        # From negotiator to decision
        workflow.add_conditional_edges(
            "negotiator",
            self._should_continue_after_negotiator,
            {
                "continue": "decision",
                "error": "handle_error"
            }
        )
        
        # From decision to approval check
        workflow.add_edge("decision", "approval_check")
        
        # From approval check to place order or end (wait for approval)
        workflow.add_conditional_edges(
            "approval_check",
            self._should_place_order,
            {
                "place_order": "place_order",
                "wait_approval": END,
                "error": "handle_error"
            }
        )
        
        # From place order to end
        workflow.add_edge("place_order", END)
        
        # From error handling to end
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    # ==================== Node Functions ====================
    
    async def _buyer_node(self, state: ProcurementState) -> ProcurementState:
        """Execute buyer agent."""
        return await self.buyer_agent.execute(state)
    
    async def _negotiator_node(self, state: ProcurementState) -> ProcurementState:
        """Execute negotiator agent."""
        return await self.negotiator_agent.execute(state)
    
    async def _decision_node(self, state: ProcurementState) -> ProcurementState:
        """Execute decision agent."""
        return await self.decision_agent.execute(state)
    
    async def _approval_check_node(self, state: ProcurementState) -> ProcurementState:
        """Check if approval is needed."""
        state["current_stage"] = "APPROVAL_CHECK"
        
        decision = state.get("decision")
        if not decision:
            state["errors"].append("No decision available")
            return state
        
        # Check if auto-approval threshold is met
        total_amount = decision["total_amount"]
        
        if total_amount < settings.AUTO_APPROVE_THRESHOLD:
            state["approval_status"] = "APPROVED"
            logger.info(f"Auto-approved: ${total_amount:.2f} < ${settings.AUTO_APPROVE_THRESHOLD}")
        else:
            state["approval_status"] = "PENDING"
            logger.info(f"Awaiting approval: ${total_amount:.2f} >= ${settings.AUTO_APPROVE_THRESHOLD}")
        
        return state
    
    async def _place_order_node(self, state: ProcurementState) -> ProcurementState:
        """Place the purchase order."""
        state["current_stage"] = "PLACING_ORDER"
        
        decision = state.get("decision")
        if not decision:
            state["errors"].append("Cannot place order without decision")
            return state
        
        # Generate PO number
        po_number = f"AUTO-{datetime.utcnow().strftime('%Y%m%d')}-{state['task_id']:06d}"
        
        # Calculate expected delivery date
        expected_delivery_date = datetime.utcnow() + timedelta(days=decision["final_delivery_days"])
        
        # Create purchase order in database
        po = PurchaseOrder(
            po_number=po_number,
            procurement_task_id=state["task_id"],
            supplier_id=decision["selected_supplier_id"],
            medicine_id=state["medicine_id"],
            quantity=state["required_quantity"],
            unit_price=decision["final_unit_price"],
            total_amount=decision["total_amount"],
            expected_delivery_days=decision["final_delivery_days"],
            expected_delivery_date=expected_delivery_date,
            status=OrderStatus.APPROVED,
            decision_score=decision["all_scores"][0]["total_score"],  # Winner's score
            decision_reasoning=decision["reasoning"],
            selected_by_agent=True,
            placed_at=datetime.utcnow()
        )
        
        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)
        
        state["po_number"] = po_number
        state["order_placed"] = True
        
        # In production, send order to supplier via API/email
        # await self._send_order_to_supplier(po)
        
        logger.info(f"Order placed: PO {po_number} to {decision['selected_supplier_name']}")
        
        return state
    
    async def _handle_error_node(self, state: ProcurementState) -> ProcurementState:
        """Handle errors in the workflow."""
        state["current_stage"] = "ERROR"
        errors = state.get("errors", [])
        
        logger.error(f"Workflow errors for task {state['task_id']}: {errors}")
        
        # In production, send alerts to administrators
        # await self._send_error_alert(state)
        
        return state
    
    # ==================== Conditional Edge Functions ====================
    
    def _should_continue_after_buyer(self, state: ProcurementState) -> str:
        """Determine next step after buyer agent."""
        if state.get("errors"):
            return "error"
        if not state.get("quotes"):
            return "error"
        return "continue"
    
    def _should_continue_after_negotiator(self, state: ProcurementState) -> str:
        """Determine next step after negotiator agent."""
        if state.get("errors"):
            return "error"
        return "continue"
    
    def _should_place_order(self, state: ProcurementState) -> str:
        """Determine if order should be placed."""
        if state.get("errors"):
            return "error"
        
        approval_status = state.get("approval_status", "PENDING")
        
        if approval_status == "APPROVED":
            return "place_order"
        else:
            return "wait_approval"
    
    # ==================== Public Methods ====================
    
    async def run(
        self,
        task_id: int,
        medicine_id: int,
        medicine_name: str,
        medicine_dosage: str,
        medicine_form: str,
        required_quantity: int,
        urgency_level: str,
        days_of_supply_remaining: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the complete procurement workflow.
        
        Args:
            task_id: Procurement task ID
            medicine_id: Medicine ID
            medicine_name: Medicine name
            medicine_dosage: Medicine dosage
            medicine_form: Medicine form
            required_quantity: Quantity needed
            urgency_level: Urgency level
            days_of_supply_remaining: Days of supply remaining
            **kwargs: Additional parameters
            
        Returns:
            Final workflow state
        """
        # Create initial state
        initial_state = create_initial_state(
            task_id=task_id,
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            medicine_dosage=medicine_dosage,
            medicine_form=medicine_form,
            required_quantity=required_quantity,
            urgency_level=urgency_level,
            days_of_supply_remaining=days_of_supply_remaining,
            average_daily_sales=kwargs.get("average_daily_sales", 100),
            safety_stock=kwargs.get("safety_stock", 500),
            budget_available=kwargs.get("budget_available", 50000),
            monthly_volume=kwargs.get("monthly_volume", 3000),
        )
        
        logger.info(f"Starting procurement workflow for task {task_id}")
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        final_state["workflow_completed_at"] = datetime.utcnow()
        
        logger.info(f"Procurement workflow completed for task {task_id}")
        
        return final_state
    
    async def approve_decision(self, task_id: int, approved: bool, notes: str = "") -> bool:
        """
        Approve or reject a pending decision.
        
        Args:
            task_id: Task ID
            approved: Whether decision is approved
            notes: Approval notes
            
        Returns:
            Success status
        """
        from app.models.order import Decision as DecisionModel
        
        decision = self.db.query(DecisionModel).filter(
            DecisionModel.procurement_task_id == task_id
        ).first()
        
        if not decision:
            logger.error(f"Decision not found for task {task_id}")
            return False
        
        decision.is_approved = approved
        decision.approval_notes = notes
        decision.approved_at = datetime.utcnow()
        self.db.commit()
        
        if approved:
            # Continue workflow - place order
            # In production, you'd resume the workflow from approval_check
            logger.info(f"Decision approved for task {task_id}")
            # TODO: Resume workflow and place order
        else:
            logger.info(f"Decision rejected for task {task_id}")
        
        return True
