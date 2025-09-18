from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import logging
from routes import contract, compare, policy, clause

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Contract Manager API",
    version="2.0.0",
    description="Enhanced API for contract analysis and comparison with clause detection"
)

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # Add the server's own origin
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static files
static_path = Path(__file__).parent / "static"
policies_path = Path(__file__).parent / "policies"
static_path.mkdir(exist_ok=True)
policies_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
app.mount("/policies", StaticFiles(directory=str(policies_path)), name="policies")

# Include routers
app.include_router(contract.router, prefix="/api", tags=["contracts"])
app.include_router(compare.router, prefix="/api", tags=["comparisons"])
app.include_router(policy.router, prefix="/api", tags=["policies"])
app.include_router(clause.router, prefix="/api", tags=["clauses"])

@app.get("/")
async def root():
    return {"message": "Contract Manager API v2.0.0 is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "text_normalization",
            "llm_circuit_breaker", 
            "enhanced_provenance",
            "structured_logging"
        ]
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Contract Manager API v2.0.0...")
    
    # Initialize services
    try:
        # Check if embedding model can be loaded
        from services.clause_analyzer import embedding_model
        if embedding_model is not None:
            logger.info("✅ Sentence transformer model loaded successfully")
        else:
            logger.warning("⚠️ Sentence transformer model not available, using rule-based fallback")
    except Exception as e:
        logger.warning(f"⚠️ Error checking embedding model: {str(e)}")
    
    # Check database connection
    try:
        from database.db import client
        # Ping the database
        client.admin.command('ping')
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {str(e)} - running without persistence")
    
    logger.info(f"🚀 Contract Manager API started successfully on http://127.0.0.1:{port if 'port' in locals() else 8001}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Allow port override from command line
    port = 8001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number provided")
            sys.exit(1)
    
    try:
        logger.info(f"Starting server on http://127.0.0.1:{port}")
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=port, 
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        sys.exit(1)
