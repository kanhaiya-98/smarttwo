# Agentic AI Supply Chain Negotiator for Pharmacy

A production-grade autonomous AI system that handles medicine procurement through intelligent agents that monitor inventory, negotiate with suppliers, and make data-driven purchasing decisions.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│           LangGraph Agent Orchestration                 │
│  ┌──────────────┐ → ┌──────────────┐ → ┌─────────────┐│
│  │   Monitor    │   │    Buyer     │   │ Negotiator  ││
│  │    Agent     │   │    Agent     │   │   Agent     ││
│  └──────────────┘   └──────────────┘   └─────────────┘│
│                                             ↓          │
│                                      ┌─────────────┐   │
│                                      │  Decision   │   │
│                                      │   Agent     │   │
│                                      └─────────────┘   │
└─────────────────────────────────────────────────────────┘
        ↓                    ↓                    ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  PostgreSQL  │   │    Redis     │   │   Gemini     │
│   Database   │   │ Cache/Queue  │   │  AI Model    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)
- Google Gemini API Key

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd pharmacy-supply-chain-ai

# 2. Create .env file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_data.py

# 5. Access the application
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Set up PostgreSQL database
createdb pharmacy_db

# 4. Configure environment
cp ../.env.example ../.env
# Edit .env with your configuration

# 5. Initialize database
python scripts/init_db.py
python scripts/seed_data.py

# 6. Start Redis (in separate terminal)
redis-server

# 7. Start Celery worker (in separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# 8. Start Celery beat (in separate terminal)
celery -A app.tasks.celery_app beat --loglevel=info

# 9. Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 Environment Variables

Create a `.env` file in the project root:

```bash
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# Database
DATABASE_URL=postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# Inventory Settings
INVENTORY_CHECK_INTERVAL_HOURS=6
REORDER_THRESHOLD_DAYS=7
CRITICAL_THRESHOLD_DAYS=2

# Negotiation Settings
MAX_NEGOTIATION_ROUNDS=3
AUTO_APPROVE_THRESHOLD=1000
```

## 🔄 Workflow Process

### 1. **Inventory Monitoring (Every 6 Hours)**
- Automated stock level checks
- Days of supply calculation
- Low stock alert generation

### 2. **Buyer Agent Activation**
- Supplier discovery
- Parallel quote requests
- Response collection

### 3. **Negotiation Agent**
- AI-powered message generation
- Multi-round negotiations
- Counter-offer handling

### 4. **Decision Agent**
- Weighted scoring (Price, Speed, Reliability, Stock)
- Scenario-based logic
- AI-generated reasoning

### 5. **Approval & Execution**
- Auto-approval for orders < $1,000
- Manual review for larger orders
- Purchase order creation

### 6. **Tracking & Follow-up**
- Delivery monitoring
- Performance tracking
- Financial processing

## 📊 API Endpoints

### Inventory
- `GET /api/v1/inventory/medicines` - List all medicines
- `GET /api/v1/inventory/medicines?low_stock_only=true` - Low stock items
- `POST /api/v1/inventory/trigger-procurement` - Trigger procurement

### Suppliers
- `GET /api/v1/suppliers/` - List suppliers
- `GET /api/v1/suppliers/{id}` - Supplier details

### Orders
- `GET /api/v1/orders/` - List orders
- `GET /api/v1/orders/{id}` - Order details
- `POST /api/v1/orders/{id}/approve` - Approve/reject order

### Negotiations
- `GET /api/v1/negotiations/task/{task_id}` - Get negotiations
- `GET /api/v1/negotiations/{id}/messages` - Negotiation messages

### Dashboard
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/agent-status` - Agent status

## 🧪 Testing

```bash
# Run tests
cd backend
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_agents.py -v
```

## 🔧 Key Features

### ✅ Implemented
- **LangGraph Workflow** - State machine for procurement process
- **Multi-Agent System** - Buyer, Negotiator, Decision agents
- **Gemini AI Integration** - For negotiation and decision reasoning
- **Automated Inventory Monitoring** - Celery scheduled tasks
- **Supplier Management** - Performance tracking
- **Negotiation System** - Multi-round AI-powered negotiations
- **Weighted Decision Making** - Scenario-based scoring
- **Human-in-the-Loop Approval** - For high-value orders
- **RESTful API** - FastAPI with OpenAPI docs
- **Database Models** - Complete ORM with relationships

### 🔄 Workflow States

```python
QUEUED → IN_PROGRESS → NEGOTIATING → PENDING_APPROVAL → APPROVED → COMPLETED
                                                    ↓
                                                 REJECTED
         ↓
       FAILED (with error handling)
```

## 📁 Project Structure

```
pharmacy-supply-chain-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   ├── api/             # API routes
│   │   ├── core/            # Core utilities
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   ├── workflows/       # LangGraph workflows
│   │   └── main.py          # FastAPI app
│   ├── scripts/             # Utility scripts
│   └── tests/               # Test files
├── docker/                  # Docker configurations
├── .env.example            # Environment template
└── docker-compose.yml      # Docker Compose config
```

## 🎯 Agent Responsibilities

### Monitor Agent
- Runs every 6 hours
- Checks inventory levels
- Creates procurement tasks

### Buyer Agent
- Discovers eligible suppliers
- Sends parallel quote requests
- Collects responses with timeout

### Negotiator Agent
- Analyzes initial quotes
- Generates negotiation messages with Gemini
- Conducts up to 3 rounds of negotiation
- Tracks conversation history

### Decision Agent
- Calculates weighted scores
- Applies scenario-based weights
- Uses Gemini to explain reasoning
- Selects best supplier

## 🔐 Security Considerations

- API key management via environment variables
- Database connection pooling
- CORS configuration for frontend
- Input validation with Pydantic
- SQL injection prevention with ORM

## 📈 Monitoring & Logging

```bash
# View backend logs
docker-compose logs -f backend

# View Celery worker logs
docker-compose logs -f celery_worker

# View Celery beat logs
docker-compose logs -f celery_beat

# View all logs
docker-compose logs -f
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python scripts/init_db.py
```

### Celery Not Processing Tasks
```bash
# Restart Celery worker
docker-compose restart celery_worker celery_beat

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Gemini API Errors
- Verify API key in `.env`
- Check API quota limits
- Review error logs for rate limiting

## 📝 Manual Procurement Trigger

```bash
# Trigger procurement for a specific medicine
curl -X POST "http://localhost:8000/api/v1/inventory/trigger-procurement" \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_id": 1,
    "quantity": 5000,
    "urgency": "HIGH"
  }'
```

## 🔄 Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🚀 Production Deployment

1. **Set strong passwords** in production `.env`
2. **Configure proper CORS** origins
3. **Use environment-specific settings**
4. **Set up SSL/TLS** for HTTPS
5. **Configure backup** for PostgreSQL
6. **Set up monitoring** (Prometheus, Grafana)
7. **Use proper logging** aggregation
8. **Scale Celery workers** as needed

## 📄 License

[Your License Here]

## 👥 Contributing

We welcome contributions to the Pharmacy Supply Chain AI project! Whether you're fixing a bug, improving documentation, or adding a new feature, your help is appreciated.

### How to Contribute

1.  **Fork the Project**: Click the "Fork" button at the top right of this page.
2.  **Clone your Fork**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/smarttwo.git
    cd smarttwo
    ```
3.  **Create a Feature Branch**:
    ```bash
    git checkout -b feature/AmazingFeature
    ```
4.  **Make your Changes**: Implement your feature or fix.
5.  **Commit your Changes**:
    ```bash
    git commit -m 'Add some AmazingFeature'
    ```
6.  **Push to the Branch**:
    ```bash
    git push origin feature/AmazingFeature
    ```
7.  **Open a Pull Request**: Go to the original repository and click "New Pull Request".

### Coding Standards

-   **Python**: Follow PEP 8 style guide.
-   **Frontend**: Use functional components and hooks. Ensure responsive design.
-   **Commits**: Write clear, descriptive commit messages.

### Reporting Issues

If you find a bug or have a feature request, please open an issue in the issue tracker.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

## 🎓 Learning Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)

---
