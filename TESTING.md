# Testing Guide

This guide covers how to test all components of the Pharmacy Supply Chain AI system.

## 🧪 Test Scenarios

### 1. Manual Procurement Trigger Test

Test the complete procurement workflow manually:

```bash
# Trigger procurement for Paracetamol (medicine_id: 1)
curl -X POST http://localhost:8000/api/v1/inventory/trigger-procurement \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_id": 1,
    "quantity": 5000,
    "urgency": "HIGH"
  }'

# Expected Response:
# {
#   "task_id": 1,
#   "status": "QUEUED",
#   "message": "Procurement workflow initiated"
# }
```

**What happens:**
1. Procurement task is created
2. Buyer Agent discovers suppliers
3. Quote requests are sent to 3-5 suppliers
4. Quotes are collected (simulated responses)
5. Negotiator Agent negotiates with top suppliers
6. Decision Agent calculates scores and selects best supplier
7. If amount < $1000, order is auto-approved and placed
8. If amount >= $1000, waits for manual approval

**Check progress:**
```bash
# View backend logs
docker-compose logs -f backend

# Check task status
curl http://localhost:8000/api/v1/orders/
```

### 2. Automated Inventory Monitoring Test

Test the scheduled inventory check:

```bash
# Manually trigger inventory check (for testing)
docker-compose exec backend python -c "
from app.tasks.inventory_tasks import check_inventory
from app.database import SessionLocal
db = SessionLocal()
result = check_inventory(db=db)
print('Result:', result)
"

# Or wait for the scheduled run (every 6 hours)
# Check Celery beat logs:
docker-compose logs -f celery_beat
```

**Expected behavior:**
- Scans all 15 medicines
- Identifies medicines with < 7 days of supply
- Creates procurement tasks for low stock items
- Each task triggers the full workflow

### 3. Agent Status Test

Test the agent status dashboard:

```bash
curl http://localhost:8000/api/v1/dashboard/agent-status

# Expected Response:
# {
#   "monitor": "IDLE",
#   "buyer": "ACTIVE",
#   "negotiator": "ACTIVE",
#   "decision": "IDLE"
# }
```

### 4. Negotiation Message Generation Test

Test Gemini AI negotiation message generation:

```python
# Run in Python shell
from app.core.gemini_client import gemini_client
import asyncio

async def test_negotiation():
    message = await gemini_client.generate_negotiation_message(
        supplier_name="QuickMeds",
        medicine_name="Paracetamol 500mg",
        quantity=5000,
        initial_quote={
            "unit_price": 0.22,
            "delivery_days": 1,
            "quantity_available": 5000
        },
        negotiation_context={
            "best_competitor_price": 0.15,
            "urgency": "HIGH",
            "monthly_volume": 3000,
            "relationship": "Regular customer",
            "strategy": "Request price match with best competitor"
        },
        round_number=1
    )
    print(message)

asyncio.run(test_negotiation())
```

### 5. Decision Reasoning Test

Test AI-generated decision reasoning:

```python
from app.core.gemini_client import gemini_client
import asyncio

async def test_decision_reasoning():
    reasoning = await gemini_client.generate_decision_reasoning(
        medicine_name="Paracetamol 500mg",
        all_quotes=[
            {"supplier_name": "Budget Pharma", "unit_price": 0.15, "delivery_days": 7, "total_score": 65.2},
            {"supplier_name": "QuickMeds", "unit_price": 0.22, "delivery_days": 1, "total_score": 72.8},
            {"supplier_name": "ReliaMeds", "unit_price": 0.20, "delivery_days": 3, "total_score": 78.5}
        ],
        selected_supplier={"name": "ReliaMeds", "unit_price": 0.20, "delivery_days": 3, "total_score": 78.5},
        scoring_details={
            "price_score": 75.0,
            "speed_score": 33.3,
            "reliability_score": 92.0,
            "stock_score": 100.0,
            "price_weight": 40,
            "speed_weight": 25,
            "reliability_weight": 20,
            "stock_weight": 15,
            "urgency": "HIGH",
            "budget_status": "Normal"
        }
    )
    print(reasoning)

asyncio.run(test_decision_reasoning())
```

### 6. Low Stock API Test

Test the low stock medicines API:

```bash
curl http://localhost:8000/api/v1/inventory/medicines?low_stock_only=true

# Should return medicines with < 7 days of supply
```

### 7. Supplier Performance Update Test

Test supplier performance calculation:

```bash
docker-compose exec backend python -c "
from app.tasks.inventory_tasks import update_supplier_performance
from app.database import SessionLocal
db = SessionLocal()
result = update_supplier_performance(db=db)
print('Result:', result)
"
```

### 8. Order Approval Test

Test manual order approval:

```bash
# Get pending approvals
curl http://localhost:8000/api/v1/orders/?status=PENDING_APPROVAL

# Approve an order
curl -X POST http://localhost:8000/api/v1/orders/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "notes": "Approved - good price"
  }'

# Reject an order
curl -X POST http://localhost:8000/api/v1/orders/2/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": false,
    "notes": "Price too high, renegotiate"
  }'
```

### 9. Negotiation History Test

Test viewing negotiation messages:

```bash
# Get negotiations for a task
curl http://localhost:8000/api/v1/negotiations/task/1

# Get messages for a negotiation
curl http://localhost:8000/api/v1/negotiations/1/messages

# Expected: See full conversation history with AI-generated messages
```

### 10. Dashboard Stats Test

Test the dashboard statistics API:

```bash
curl http://localhost:8000/api/v1/dashboard/stats

# Expected Response includes:
# - active_tasks count
# - pending_approvals count
# - low_stock_items count
# - recent_orders list
```

## 🔍 Integration Tests

### Full Workflow Integration Test

```bash
#!/bin/bash
# integration_test.sh

echo "Starting integration test..."

# 1. Create low stock situation
echo "1. Setting low stock for Paracetamol..."
docker-compose exec -T postgres psql -U pharmacy_user -d pharmacy_db <<SQL
UPDATE medicines SET current_stock = 100 WHERE id = 1;
SQL

# 2. Trigger inventory check
echo "2. Running inventory check..."
docker-compose exec backend python -c "
from app.tasks.inventory_tasks import check_inventory
from app.database import SessionLocal
db = SessionLocal()
check_inventory(db=db)
"

# 3. Wait for workflow to complete
echo "3. Waiting for workflow (60 seconds)..."
sleep 60

# 4. Check if order was created
echo "4. Checking for created order..."
curl http://localhost:8000/api/v1/orders/ | grep "AUTO-"

echo "Integration test complete!"
```

### Load Test

Test multiple concurrent procurements:

```bash
#!/bin/bash
# load_test.sh

echo "Running load test - 10 concurrent procurement requests..."

for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/inventory/trigger-procurement \
    -H "Content-Type: application/json" \
    -d "{\"medicine_id\": $i, \"quantity\": 5000, \"urgency\": \"MEDIUM\"}" &
done

wait
echo "All requests completed!"
```

## 🧩 Unit Tests

Run pytest unit tests:

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app tests/

# Run specific test file
docker-compose exec backend pytest tests/test_agents.py -v

# Run specific test
docker-compose exec backend pytest tests/test_agents.py::test_buyer_agent -v
```

### Sample Unit Test

```python
# tests/test_agents.py
import pytest
from app.agents.buyer_agent import BuyerAgent
from app.database import SessionLocal

@pytest.mark.asyncio
async def test_buyer_agent_discovers_suppliers():
    """Test buyer agent can discover eligible suppliers."""
    db = SessionLocal()
    buyer = BuyerAgent(db)
    
    suppliers = await buyer._discover_suppliers(
        medicine_id=1,
        urgency="HIGH"
    )
    
    assert len(suppliers) > 0
    assert all('id' in s for s in suppliers)
    assert all('reliability_score' in s for s in suppliers)
    
    db.close()
```

## 📊 Performance Tests

### Response Time Test

```bash
# Test API response times
ab -n 1000 -c 10 http://localhost:8000/api/v1/inventory/medicines

# Results should show:
# - Mean response time < 100ms
# - No failed requests
```

### Database Query Performance

```sql
-- Check slow queries
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE medicines;
ANALYZE suppliers;
ANALYZE purchase_orders;
```

## 🐛 Debugging Tips

### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U pharmacy_user -d pharmacy_db

# Useful queries:
SELECT * FROM medicines WHERE current_stock < 500;
SELECT * FROM procurement_tasks ORDER BY created_at DESC LIMIT 5;
SELECT * FROM negotiations WHERE status = 'SUCCESSFUL';
SELECT * FROM purchase_orders ORDER BY created_at DESC LIMIT 10;
```

### Redis Inspection

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check Celery tasks
KEYS celery-task-meta-*
GET celery-task-meta-<task-id>

# Check active tasks
LLEN celery
```

## ✅ Test Checklist

- [ ] Backend API is responding
- [ ] Database is initialized with tables
- [ ] Sample data is seeded
- [ ] Celery worker is running
- [ ] Celery beat is scheduling tasks
- [ ] Manual procurement trigger works
- [ ] Buyer agent discovers suppliers
- [ ] Quotes are collected successfully
- [ ] Negotiation messages are generated by Gemini
- [ ] Decision agent selects best supplier
- [ ] Decision reasoning is generated by Gemini
- [ ] Orders are created in database
- [ ] Auto-approval works for < $1000 orders
- [ ] Manual approval works for >= $1000 orders
- [ ] Dashboard stats API returns data
- [ ] Agent status API returns data
- [ ] Low stock API filters correctly
- [ ] Negotiation history is viewable
- [ ] Supplier performance updates
- [ ] Frontend displays correctly
- [ ] WebSocket updates work (if implemented)

## 🎯 Expected Outcomes

After running all tests, you should see:

1. **Database**: 15 medicines, 5 suppliers, multiple purchase orders
2. **Logs**: AI-generated negotiation messages
3. **Orders**: Successfully placed orders with PO numbers
4. **Negotiations**: Saved conversation history
5. **Decisions**: Detailed reasoning for supplier selection
6. **Performance**: Updated supplier reliability scores

## 📝 Test Reports

Generate test reports:

```bash
# Coverage report
docker-compose exec backend pytest --cov=app --cov-report=html tests/

# View in browser
open backend/htmlcov/index.html
```

---

**Need help?** Check logs first, then review error messages in the dashboard.
