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

# Configure CORS with explicit allowed origins (never wildcard * when allow_credentials=True)
cors_env = os.environ.get("FINAUDIT_CORS_ORIGINS") or os.environ.get("CORS_ORIGINS")
if cors_env:
    allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

# Never combine wildcard '*' with allow_credentials=True
allow_creds = True
if "*" in allowed_origins:
    if len(allowed_origins) == 1:
        allow_creds = False
    else:
        allowed_origins = [o for o in allowed_origins if o != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
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
    dev_reload = os.environ.get("FINAUDIT_DEV_RELOAD", "false").lower() == "true"
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=dev_reload)
