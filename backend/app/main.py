"""
FastAPI main application module for BlackStack Cybersecurity AI Platform.
"""

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

from app.routes import siem, ai
from app.core.orchestrator import SecurityOrchestrator

# Load environment variables
load_dotenv()

# FastAPI app configuration
app = FastAPI(
    title="BlackStack Cybersecurity AI Platform",
    description="Production-ready API for cybersecurity analysis with AI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = SecurityOrchestrator()

# Dependency to get orchestrator
async def get_orchestrator() -> SecurityOrchestrator:
    return orchestrator

# Include routers
app.include_router(
    siem.router,
    prefix="/api/v1/siem",
    tags=["SIEM"],
    dependencies=[Depends(get_orchestrator)]
)

app.include_router(
    ai.router,
    prefix="/api/v1/ai",
    tags=["AI"],
    dependencies=[Depends(get_orchestrator)]
)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "BlackStack Cybersecurity AI Platform API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": orchestrator.get_current_timestamp(),
        "services": await orchestrator.check_service_health()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        workers=int(os.getenv("WORKERS", 1))
    )