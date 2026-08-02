import sys
import os
from contextlib import asynccontextmanager

# Add src/ to sys.path so services and models import seamlessly
sys_path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(sys_path_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.database import init_db

from api.routers import auth, clients, documents, working_papers, dashboard, audit_projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to initialize database on app startup."""
    init_db()
    yield


app = FastAPI(
    title="FinAuditPro Enterprise API",
    description="Multi-User Client-Server REST API Backend for FinAuditPro Enterprise Statutory Audit Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0", "service": "FinAuditPro API"}


# Include v1 API Routers
api_v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(clients.router, prefix=api_v1_prefix)
app.include_router(documents.router, prefix=api_v1_prefix)
app.include_router(working_papers.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(audit_projects.router, prefix=api_v1_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
