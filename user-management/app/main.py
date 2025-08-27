from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from .database import engine, get_db
from . import models, schemas, crud, auth
from .routes import router as api_router

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Optionally seed a default admin user on startup (controlled by env SEED_ADMIN=true)
SEED_ADMIN = os.getenv("SEED_ADMIN", "true").lower() == "true"
if SEED_ADMIN:
    try:
        from .seed_admin import seed_admin
        seed_admin()
    except Exception as e:
        print(f"[seed_admin] Skipped or failed seeding default admin: {e}")

app = FastAPI(
    title="AI DevOps Assistant - User Management Service",
    description="User Management Service for the AI DevOps Assistant",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-management"}

# Prometheus metrics in text/plain for Prometheus scraping
from fastapi.responses import PlainTextResponse
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return "# HELP user_management_up 1 if the service is up\n# TYPE user_management_up gauge\nuser_management_up 1\n"


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI DevOps Assistant User Management Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)