from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import os

from .routes import router as api_router
from .config import settings

app = FastAPI(
    title="AI DevOps Assistant - Natural Language Interface Service",
    description="Natural Language Interface Service for the AI DevOps Assistant",
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
app.include_router(api_router, prefix="/api/v1/nlp")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "natural-language"}

# Prometheus metrics in text/plain for Prometheus scraping
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return "# HELP natural_language_up 1 if the service is up\n# TYPE natural_language_up gauge\nnatural_language_up 1\n"


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI DevOps Assistant Natural Language Interface Service"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)