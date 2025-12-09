#!/bin/bash

# Pharmacy Supply Chain AI - Complete Setup Script
# This script will set up the entire project from scratch

set -e  # Exit on error

echo "========================================="
echo "Pharmacy Supply Chain AI - Setup Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        echo "Please install $1 and try again."
        exit 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
    fi
}

check_command docker
check_command docker-compose
check_command python3

echo ""
echo "All prerequisites are installed!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your GOOGLE_API_KEY${NC}"
    echo "Press Enter after you've added your API key..."
    read
fi

# Create necessary directories
echo "Creating project structure..."
mkdir -p backend/app/{agents,api/routes,core,models,schemas,services,tasks,workflows,utils}
mkdir -p backend/tests
mkdir -p backend/alembic/versions
mkdir -p scripts
mkdir -p frontend/src/{components,services,hooks,types}
mkdir -p docker

echo -e "${GREEN}✓ Project structure created${NC}"

# Build and start Docker containers
echo ""
echo "Building and starting Docker containers..."
docker-compose down -v  # Clean start
docker-compose build
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker containers are running${NC}"
else
    echo -e "${RED}✗ Some containers failed to start${NC}"
    docker-compose logs
    exit 1
fi

# Initialize database
echo ""
echo "Initializing database..."
docker-compose exec -T backend python scripts/init_db.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo -e "${RED}✗ Database initialization failed${NC}"
    exit 1
fi

# Seed database with sample data
echo ""
echo "Seeding database with sample data..."
docker-compose exec -T backend python scripts/seed_data.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database seeded${NC}"
else
    echo -e "${RED}✗ Database seeding failed${NC}"
    exit 1
fi

# Test backend API
echo ""
echo "Testing backend API..."
sleep 5  # Wait for backend to fully start

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓ Backend API is responding${NC}"
else
    echo -e "${RED}✗ Backend API is not responding (HTTP $response)${NC}"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Services are running:"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Frontend:       http://localhost:3000"
echo "  • PostgreSQL:     localhost:5432"
echo "  • Redis:          localhost:6379"
echo ""
echo "Celery workers are running in the background."
echo ""
echo "To view logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f celery_worker"
echo ""
echo "To trigger a test procurement:"
echo "  curl -X POST http://localhost:8000/api/v1/inventory/trigger-procurement \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"medicine_id\": 1, \"quantity\": 5000, \"urgency\": \"HIGH\"}'"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""
echo -e "${GREEN}Happy automating! 🚀${NC}"
