# Complete Implementation Guide

This guide will help you implement the entire Pharmacy Supply Chain AI project from scratch.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher
- [ ] Docker and Docker Compose
- [ ] Git
- [ ] Google Gemini API Key ([Get it here](https://makersuite.google.com/app/apikey))
- [ ] PostgreSQL 15+ (if not using Docker)
- [ ] Redis 7+ (if not using Docker)
- [ ] Node.js 18+ (for frontend)
- [ ] Text editor (VS Code recommended)

## 🚀 Step-by-Step Implementation

### Step 1: Create Project Structure

```bash
# Create main project directory
mkdir pharmacy-supply-chain-ai
cd pharmacy-supply-chain-ai

# Create all required directories
mkdir -p backend/app/{agents/tools,api/routes,core,models,schemas,services,tasks,workflows,utils}
mkdir -p backend/tests
mkdir -p backend/alembic/versions
mkdir -p scripts
mkdir -p frontend/src/{components/{Dashboard,Inventory,Orders,Suppliers},services,hooks,types}
mkdir -p docker

# Initialize git
git init
echo "__pycache__" > .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "node_modules/" >> .gitignore
echo ".DS_Store" >> .gitignore
```

### Step 2: Set Up Backend Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt (copy from artifact)
# Then install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
cd ..  # Back to project root

# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your Google Gemini API key
nano .env  # or use your preferred editor
```

**Required changes in .env:**
```bash
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

### Step 4: Copy All Python Files

Create each Python file by copying from the artifacts:

**Backend Core Files:**
1. `backend/app/config.py` - Configuration management
2. `backend/app/database.py` - Database setup
3. `backend/app/main.py` - FastAPI application

**Database Models:**
4. `backend/app/models/__init__.py` - (empty file, just `touch` it)
5. `backend/app/models/medicine.py` - Medicine models
6. `backend/app/models/supplier.py` - Supplier models
7. `backend/app/models/order.py` - Order and negotiation models

**Agents:**
8. `backend/app/agents/__init__.py` - (empty)
9. `backend/app/agents/base_agent.py` - Base agent class
10. `backend/app/agents/buyer_agent.py` - Buyer agent
11. `backend/app/agents/negotiator_agent.py` - Negotiator agent
12. `backend/app/agents/decision_agent.py` - Decision agent

**Workflows:**
13. `backend/app/workflows/__init__.py` - (empty)
14. `backend/app/workflows/state.py` - LangGraph state
15. `backend/app/workflows/procurement_graph.py` - LangGraph workflow

**Core Utilities:**
16. `backend/app/core/__init__.py` - (empty)
17. `backend/app/core/gemini_client.py` - Gemini API client

**API Routes:**
18. `backend/app/api/__init__.py` - (empty)
19. `backend/app/api/routes/__init__.py` - (empty)
20. `backend/app/api/routes/inventory.py` - From combined routes artifact
21. `backend/app/api/routes/suppliers.py` - From combined routes artifact
22. `backend/app/api/routes/orders.py` - From combined routes artifact
23. `backend/app/api/routes/negotiations.py` - From combined routes artifact
24. `backend/app/api/routes/dashboard.py` - From combined routes artifact

**Tasks:**
25. `backend/app/tasks/__init__.py` - (empty)
26. `backend/app/tasks/celery_app.py` - Celery configuration
27. `backend/app/tasks/inventory_tasks.py` - Celery tasks

**Scripts:**
28. `scripts/init_db.py` - Database initialization
29. `scripts/seed_data.py` - Seed sample data
30. `scripts/setup.sh` - Setup script

### Step 5: Set Up Docker

Copy Docker configuration files:

31. `docker-compose.yml` - Docker Compose configuration
32. `docker/Dockerfile.backend` - Backend Dockerfile
33. `docker/Dockerfile.frontend` - Frontend Dockerfile

### Step 6: Initialize Database

```bash
# Option A: Using Docker (Recommended)
docker-compose up -d postgres redis
sleep 10  # Wait for PostgreSQL to be ready
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_data.py

# Option B: Local PostgreSQL
createdb pharmacy_db
python scripts/init_db.py
python scripts/seed_data.py
```

### Step 7: Start Backend Services

```bash
# Using Docker (Recommended)
docker-compose up -d

# Or manually:
# Terminal 1 - Backend API
uvicorn app.main:app --reload

# Terminal 2 - Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3 - Celery Beat
celery -A app.tasks.celery_app beat --loglevel=info
```

### Step 8: Verify Backend

```bash
# Check health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Get medicines list
curl http://localhost:8000/api/v1/inventory/medicines

# Check dashboard stats
curl http://localhost:8000/api/v1/dashboard/stats
```

### Step 9: Set Up Frontend (Optional)

```bash
cd frontend

# Copy package.json
# Then install dependencies
npm install

# Copy src files
# - src/App.tsx
# - src/main.tsx (create basic entry point)
# - src/index.css (Tailwind config)

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### Step 10: Test the System

```bash
# Trigger a test procurement
curl -X POST http://localhost:8000/api/v1/inventory/trigger-procurement \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_id": 1,
    "quantity": 5000,
    "urgency": "HIGH"
  }'

# Watch the logs
docker-compose logs -f backend

# Check created orders
curl http://localhost:8000/api/v1/orders/
```

## 🎯 Verification Checklist

After implementation, verify:

- [ ] Backend API responds at http://localhost:8000
- [ ] API docs available at http://localhost:8000/docs
- [ ] Database has 15 medicines and 5 suppliers
- [ ] Celery worker is running
- [ ] Can trigger procurement manually
- [ ] Procurement workflow completes successfully
- [ ] Orders are created in database
- [ ] Gemini AI generates negotiation messages
- [ ] Decision reasoning is generated
- [ ] Dashboard shows statistics
- [ ] Frontend loads (if implemented)

## 🐛 Common Issues and Solutions

### Issue 1: Gemini API Key Not Working

**Solution:**
```bash
# Verify API key is set
docker-compose exec backend python -c "from app.config import settings; print(settings.GOOGLE_API_KEY)"

# Test Gemini directly
docker-compose exec backend python -c "
import google.generativeai as genai
from app.config import settings
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')
response = model.generate_content('Hello')
print(response.text)
"
```

### Issue 2: Database Connection Error

**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify connection string
docker-compose exec backend python -c "from app.config import settings; print(settings.DATABASE_URL)"

# Restart PostgreSQL
docker-compose restart postgres
```

### Issue 3: Celery Not Processing Tasks

**Solution:**
```bash
# Check Celery worker logs
docker-compose logs celery_worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery
docker-compose restart celery_worker celery_beat
```

### Issue 4: Import Errors

**Solution:**
```bash
# Verify all __init__.py files exist
find backend/app -type d -exec touch {}/__init__.py \;

# Reinstall dependencies
docker-compose exec backend pip install -r requirements.txt
```

## 📦 File Organization Tips

### Create Empty __init__.py Files

```bash
# Run this to create all __init__.py files
cd backend
find app -type d -exec touch {}/__init__.py \;
```

### Verify File Structure

```bash
# Check your structure matches
tree -L 3 backend/app
```

Should look like:
```
backend/app
├── __init__.py
├── agents
│   ├── __init__.py
│   ├── base_agent.py
│   ├── buyer_agent.py
│   ├── decision_agent.py
│   └── negotiator_agent.py
├── api
│   ├── __init__.py
│   └── routes
│       ├── __init__.py
│       ├── dashboard.py
│       ├── inventory.py
│       ├── negotiations.py
│       ├── orders.py
│       └── suppliers.py
├── config.py
├── core
│   ├── __init__.py
│   └── gemini_client.py
├── database.py
├── main.py
├── models
│   ├── __init__.py
│   ├── medicine.py
│   ├── order.py
│   └── supplier.py
├── tasks
│   ├── __init__.py
│   ├── celery_app.py
│   └── inventory_tasks.py
└── workflows
    ├── __init__.py
    ├── procurement_graph.py
    └── state.py
```

## 🎨 Frontend Setup Details

### Create frontend/src/main.tsx

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### Create frontend/src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Create frontend/vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
  },
})
```

### Create frontend/tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

## 🚢 Production Deployment

### 1. Security Hardening

```bash
# Generate strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with production values
# - Change all passwords
# - Use production database URL
# - Set DEBUG=False
```

### 2. Build for Production

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Set Up SSL/TLS

Use Nginx reverse proxy with Let's Encrypt:
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## 📚 Additional Resources

- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Tutorial**: https://langchain-ai.github.io/langgraph/tutorials/
- **Gemini API**: https://ai.google.dev/docs
- **FastAPI Guide**: https://fastapi.tiangolo.com/tutorial/
- **Celery Best Practices**: https://docs.celeryq.dev/en/stable/userguide/

## ✅ Final Checklist

- [ ] All Python files created
- [ ] All __init__.py files exist
- [ ] .env file configured with Gemini API key
- [ ] Docker Compose running
- [ ] Database initialized and seeded
- [ ] Backend API responding
- [ ] Celery workers running
- [ ] Test procurement successful
- [ ] Orders created in database
- [ ] Frontend displaying (if implemented)
- [ ] Logs showing AI-generated messages
- [ ] Documentation reviewed

## 🎉 Success!

If all checks pass, your Pharmacy Supply Chain AI system is fully operational!

**Next Steps:**
1. Customize medicine and supplier data
2. Integrate with real supplier APIs
3. Add email notifications
4. Implement WebSocket for real-time updates
5. Add more sophisticated forecasting
6. Deploy to production

**Questions or issues?** Review logs first, then check the TESTING.md guide.
