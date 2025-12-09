# Quick Reference Guide

## 🚀 Quick Start Commands

```bash
# Setup and start everything
chmod +x scripts/setup.sh
./scripts/setup.sh

# Or manually with Docker
docker-compose up -d
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_data.py

# View services
docker-compose ps

# Stop everything
docker-compose down
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Restart a service
docker-compose restart backend

# Execute command in container
docker-compose exec backend python script.py

# Rebuild containers
docker-compose build
docker-compose up -d --build

# Remove all data (WARNING: destructive)
docker-compose down -v
```

## 📊 Database Commands

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U pharmacy_user -d pharmacy_db

# Backup database
docker-compose exec postgres pg_dump -U pharmacy_user pharmacy_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U pharmacy_user -d pharmacy_db

# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_data.py
```

### Useful SQL Queries

```sql
-- Check medicines
SELECT id, name, current_stock, average_daily_sales FROM medicines;

-- Check low stock
SELECT name, current_stock, 
       current_stock / NULLIF(average_daily_sales, 0) as days_supply 
FROM medicines 
WHERE current_stock / NULLIF(average_daily_sales, 0) < 7;

-- Check active tasks
SELECT * FROM procurement_tasks 
WHERE status IN ('QUEUED', 'IN_PROGRESS') 
ORDER BY created_at DESC;

-- Check recent orders
SELECT po_number, status, total_amount, created_at 
FROM purchase_orders 
ORDER BY created_at DESC 
LIMIT 10;

-- Check negotiations
SELECT n.id, s.name as supplier, n.status, n.final_unit_price 
FROM negotiations n 
JOIN suppliers s ON n.supplier_id = s.id 
ORDER BY n.created_at DESC;

-- Supplier performance
SELECT name, reliability_score, on_time_delivery_rate, total_orders_count 
FROM suppliers 
ORDER BY reliability_score DESC;
```

## 🔧 Backend Commands

```bash
# Run backend locally
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Run Celery beat
celery -A app.tasks.celery_app beat --loglevel=info

# Run tests
pytest
pytest --cov=app tests/
pytest tests/test_agents.py -v

# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/
```

## 🌐 API Endpoints Quick Reference

### Health & Status
```bash
# Health check
GET http://localhost:8000/health

# API documentation
GET http://localhost:8000/docs

# OpenAPI schema
GET http://localhost:8000/openapi.json
```

### Inventory Management
```bash
# List all medicines
GET /api/v1/inventory/medicines

# List only low stock items
GET /api/v1/inventory/medicines?low_stock_only=true

# Trigger procurement
POST /api/v1/inventory/trigger-procurement
{
  "medicine_id": 1,
  "quantity": 5000,
  "urgency": "HIGH"
}
```

### Supplier Management
```bash
# List all suppliers
GET /api/v1/suppliers/

# Get supplier details
GET /api/v1/suppliers/{id}

# List active suppliers only
GET /api/v1/suppliers/?active_only=true
```

### Order Management
```bash
# List all orders
GET /api/v1/orders/

# Filter by status
GET /api/v1/orders/?status=PENDING_APPROVAL

# Get order details
GET /api/v1/orders/{id}

# Approve order
POST /api/v1/orders/{id}/approve
{
  "approved": true,
  "notes": "Approved - good price"
}

# Reject order
POST /api/v1/orders/{id}/approve
{
  "approved": false,
  "notes": "Price too high"
}
```

### Negotiations
```bash
# Get negotiations for task
GET /api/v1/negotiations/task/{task_id}

# Get negotiation messages
GET /api/v1/negotiations/{negotiation_id}/messages
```

### Dashboard
```bash
# Get dashboard statistics
GET /api/v1/dashboard/stats

# Get agent status
GET /api/v1/dashboard/agent-status
```

## 📡 cURL Examples

### Trigger Procurement (High Priority)
```bash
curl -X POST http://localhost:8000/api/v1/inventory/trigger-procurement \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_id": 1,
    "quantity": 5000,
    "urgency": "HIGH"
  }'
```

### Get Low Stock Medicines
```bash
curl http://localhost:8000/api/v1/inventory/medicines?low_stock_only=true | jq
```

### Approve an Order
```bash
curl -X POST http://localhost:8000/api/v1/orders/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "notes": "Approved by pharmacist"
  }'
```

### Get Dashboard Stats
```bash
curl http://localhost:8000/api/v1/dashboard/stats | jq
```

## 🔄 Celery Commands

```bash
# View active tasks
celery -A app.tasks.celery_app inspect active

# View scheduled tasks
celery -A app.tasks.celery_app inspect scheduled

# View registered tasks
celery -A app.tasks.celery_app inspect registered

# Purge all tasks
celery -A app.tasks.celery_app purge

# Manually trigger inventory check
docker-compose exec backend python -c "
from app.tasks.inventory_tasks import check_inventory
from app.database import SessionLocal
db = SessionLocal()
result = check_inventory(db=db)
print(result)
"
```

## 🧪 Testing Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/

# Run integration tests
bash tests/integration_test.sh

# Load test
bash tests/load_test.sh
```

## 🔍 Debugging Commands

```bash
# Check Python path
docker-compose exec backend python -c "import sys; print('\n'.join(sys.path))"

# Test Gemini connection
docker-compose exec backend python -c "
import google.generativeai as genai
from app.config import settings
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')
response = model.generate_content('Test message')
print(response.text)
"

# Test database connection
docker-compose exec backend python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connected:', result.fetchone())
"

# Check Redis connection
docker-compose exec redis redis-cli ping

# Monitor Redis keys
docker-compose exec redis redis-cli MONITOR

# Check environment variables
docker-compose exec backend python -c "
from app.config import settings
print('GOOGLE_API_KEY:', settings.GOOGLE_API_KEY[:10] + '...')
print('DATABASE_URL:', settings.DATABASE_URL)
"
```

## 📝 Logs & Monitoring

```bash
# Tail all logs
docker-compose logs -f

# Tail specific service with timestamp
docker-compose logs -f --timestamps backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Save logs to file
docker-compose logs backend > backend.log

# Search logs for errors
docker-compose logs backend | grep ERROR

# Real-time error monitoring
docker-compose logs -f backend | grep -E "ERROR|CRITICAL"
```

## 🔐 Security Commands

```bash
# Generate new SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Check for security issues
docker-compose exec backend pip-audit

# Update dependencies
docker-compose exec backend pip install --upgrade pip
docker-compose exec backend pip install -r requirements.txt --upgrade
```

## 📦 Maintenance Commands

```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Backup everything
mkdir backup_$(date +%Y%m%d)
docker-compose exec postgres pg_dump -U pharmacy_user pharmacy_db > backup_$(date +%Y%m%d)/db.sql
cp -r backend/ backup_$(date +%Y%m%d)/

# Update packages
cd backend
pip list --outdated
pip install -U package_name

# Restart all services
docker-compose restart

# Check disk usage
docker-compose exec backend df -h
docker system df
```

## 🎯 Common Workflows

### Daily Operations

```bash
# Morning check
docker-compose ps                                    # Verify all running
curl http://localhost:8000/health                    # Check API health
curl http://localhost:8000/api/v1/dashboard/stats    # View stats

# Monitor throughout day
docker-compose logs -f backend                       # Watch activity

# End of day
docker-compose logs backend | grep ERROR             # Check for errors
```

### Weekly Maintenance

```bash
# Backup database
docker-compose exec postgres pg_dump -U pharmacy_user pharmacy_db > backup_weekly.sql

# Review supplier performance
docker-compose exec backend python -c "
from app.tasks.inventory_tasks import update_supplier_performance
from app.database import SessionLocal
db = SessionLocal()
update_supplier_performance(db=db)
"

# Check logs for issues
docker-compose logs --since=7d backend | grep -E "ERROR|WARNING" > weekly_issues.log
```

### Monthly Review

```bash
# Generate performance report
curl http://localhost:8000/api/v1/dashboard/stats | jq > monthly_report.json

# Backup database
docker-compose exec postgres pg_dump -U pharmacy_user pharmacy_db > backup_monthly.sql

# Update dependencies
docker-compose exec backend pip list --outdated

# Review and update suppliers
# Access PostgreSQL and review supplier_performance table
```

## 🆘 Emergency Procedures

### System Down

```bash
# Quick restart
docker-compose down
docker-compose up -d

# If that fails, rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Corruption

```bash
# Restore from backup
docker-compose down
docker volume rm pharmacy-supply-chain-ai_postgres_data
docker-compose up -d postgres
cat backup.sql | docker-compose exec -T postgres psql -U pharmacy_user -d pharmacy_db
docker-compose up -d
```

### Out of Memory

```bash
# Clear Docker cache
docker system prune -a

# Restart services
docker-compose restart

# Check memory usage
docker stats
```

## 📞 Support Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LangChain**: https://python.langchain.com/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Gemini API**: https://ai.google.dev/docs
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Celery**: https://docs.celeryq.dev/

---

**Pro Tip**: Save this file locally and use `Ctrl+F` to quickly find commands you need!
