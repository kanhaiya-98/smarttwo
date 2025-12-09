"""Main FastAPI application."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.api.routes import (
    inventory, suppliers, orders, negotiations, dashboard, agents,
    negotiation, discovery, negotiation_decision, quotes, approvals, tracking
)
import logging

from app.core.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Pharmacy Supply Chain AI System")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI Supply Chain Negotiator for Pharmacy",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Include routers
app.include_router(
    inventory.router,
    prefix=f"{settings.API_V1_PREFIX}/inventory",
    tags=["Inventory"]
)
app.include_router(
    suppliers.router,
    prefix=f"{settings.API_V1_PREFIX}/suppliers",
    tags=["Suppliers"]
)
app.include_router(
    orders.router,
    prefix=f"{settings.API_V1_PREFIX}/orders",
    tags=["Orders"]
)
app.include_router(
    negotiations.router,
    prefix=f"{settings.API_V1_PREFIX}/negotiations",
    tags=["Negotiations"]
)
app.include_router(
    negotiation.router,
    prefix=f"{settings.API_V1_PREFIX}/negotiation",
    tags=["Start Negotiation"]
)
app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_PREFIX}/dashboard",
    tags=["Dashboard"]
)
app.include_router(
    agents.router,
    prefix=f"{settings.API_V1_PREFIX}/agents",
    tags=["Agents"]
)
app.include_router(
    discovery.router,
    prefix=f"{settings.API_V1_PREFIX}/discovery",
    tags=["Discovery"]
)
app.include_router(
    negotiation_decision.router,
    prefix=f"{settings.API_V1_PREFIX}/negotiation-decision",
    tags=["Negotiation & Decision"]
)
app.include_router(
    quotes.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Quotes"]
)
app.include_router(
    approvals.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Approvals"]
)
app.include_router(
    tracking.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Tracking"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pharmacy Supply Chain AI System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-01-15T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
