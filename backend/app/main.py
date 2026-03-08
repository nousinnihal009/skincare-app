"""
SkinCare AI — FastAPI Backend
Production-grade API for AI skin analysis, dermatology assistant, and skincare recommendations.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from app.routes.analysis import router as analysis_router
from app.routes.chat import router as chat_router
from app.routes.recommendations import router as recommendations_router
from app.routes.doctors import router as doctors_router
from app.routes.environment import router as environment_router
from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Startup: preload model
    print("🚀 Starting SkinCare AI Backend...")
    try:
        from app.models.prediction import load_model
        load_model()
        print("✅ ML Model loaded successfully")
    except Exception as e:
        print(f"⚠️ Model loading failed: {e}")
        print("   Backend will start but /api/analyze will not work until model is available.")
    yield
    # Shutdown
    print("👋 Shutting down SkinCare AI Backend...")


app = FastAPI(
    title="SkinCare AI",
    description="AI-Powered Dermatology Assistant Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(recommendations_router)
app.include_router(doctors_router)
app.include_router(environment_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "name": "SkinCare AI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "chat": "POST /api/chat",
            "skincare_routine": "POST /api/skincare-routine",
            "medicines": "GET /api/medicines/{condition}",
            "ingredient_check": "POST /api/ingredient-check",
            "doctors": "GET /api/doctors/search",
            "environment": "GET /api/environment/risks",
            "health": "GET /health",
        }
    }
