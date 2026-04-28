from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.database import init_db
import os

app = FastAPI(
    title="NirvanaX API",
    description="Verified Financial Intelligence OS — Multi-Agent AI Financial Governance Platform",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Initialize database
@app.on_event("startup")
def startup_event():
    init_db()

# Include routes
app.include_router(router, prefix="/api/v1", tags=["NirvanaX"])

@app.get("/")
def root():
    return {
        "message": "NirvanaX API — Verified Financial Intelligence OS",
        "tagline": "Trust-first, explainable, multi-agent governed financial intelligence",
        "version": "2.0.0",
        "status": "active",
        "architecture": "Council of Three Multi-Agent Governance"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "platform": "NirvanaX"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
