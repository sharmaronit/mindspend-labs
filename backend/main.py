"""
FastAPI Main Application
- Initializes FastAPI app
- Configures middleware (CORS, rate limiting)
- Registers route modules
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from database import init_db, engine
from auth.routes import router as auth_router
from routes.user import router as user_router

# Load environment variables
load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Personal Behavioral Analyst API",
    description="Backend API for financial analytics and behavioral insights",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================
# Middleware Configuration
# ============================================

# CORS Middleware
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions"""
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": "Internal server error"
        }
    )


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        print("🚀 Starting Personal Behavioral Analyst API...")
        print("📊 Initializing database...")
        init_db()
        print("✅ Database ready")
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        print("👋 Shutting down API...")
        engine.dispose()
    except Exception as e:
        print(f"Error during shutdown: {e}")


# ============================================
# Route Registration
# ============================================

# Health check
@app.get("/health")
async def health_check(request: Request):
    """API health check endpoint"""
    return {
        "status": "healthy",
        "message": "Personal Behavioral Analyst API is running"
    }


# Root endpoint
@app.get("/")
async def root(request: Request):
    """Root endpoint with API information"""
    return {
        "message": "Personal Behavioral Analyst API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Register routers
app.include_router(auth_router)
app.include_router(user_router)


# ============================================
# Development Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "127.0.0.1")  # Changed from 0.0.0.0 to 127.0.0.1
    port = int(os.getenv("API_PORT", "8001"))
    reload = False  # Always disable reload to prevent issues
    
    print(f"🔧 Starting development server on {host}:{port}")
    print(f"📚 API docs available at http://{host}:{port}/docs")
    
    uvicorn.run(
        app,  # Changed from "main:app" string to app object
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
