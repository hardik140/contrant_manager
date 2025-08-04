from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import contract, compare

app = FastAPI(title="Contract Manager API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contract.router, prefix="/api", tags=["contracts"])
app.include_router(compare.router, prefix="/api", tags=["comparisons"])

@app.get("/")
async def root():
    return {"message": "Contract Manager API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
