# backend/app/main.py
"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles  # <-- Comment this out
from .core.config import settings
from .api import auth, chat, websocket, analytics

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="Real-time Chat Application with AI-powered Sentiment Analysis"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

# Serve static files (frontend)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Realtime Chat AI - Backend with Sentiment Analysis",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "JWT Authentication",
            "Real-time WebSocket Chat",
            "AI Sentiment Analysis (LightGBM - 88.4% accuracy)",
            "Admin Analytics Dashboard",
            "One-to-One & Group Chat"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .ml.inference import ml_inference_service
    
    return {
        "status": "healthy",
        "ml_model_loaded": ml_inference_service.is_model_loaded()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)