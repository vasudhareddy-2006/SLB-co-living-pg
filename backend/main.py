from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import db_service
from backend.routers import auth, leads, stats

ROOT_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db_service.connect()
    except Exception as e:
        print(f"Warning: Database connect in lifespan: {e}")
    yield
    try:
        await db_service.disconnect()
    except Exception:
        pass

app = FastAPI(
    title="SLB Coliving PG API",
    description="Backend API with Supabase & Prisma support, JWT authentication, and Call-back Lead management.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.CORS_ORIGINS else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(stats.router)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health status and database mode."""
    return {
        "status": "healthy",
        "databaseMode": "supabase_prisma" if db_service.use_prisma else "local_sqlite_fallback",
        "service": "SLB Coliving PG Backend",
    }

# Serve Admin portal
@app.get("/admin", include_in_schema=False)
async def serve_admin_page():
    admin_path = ROOT_DIR / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    return {"message": "Admin portal file not found"}

# Serve Root Index page
@app.get("/", include_in_schema=False)
async def serve_index_page():
    index_path = ROOT_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "SLB Coliving PG API is running. Visit /docs for Swagger UI."}

# Mount static files (style.css, script.js, assets)
app.mount("/assets", StaticFiles(directory=ROOT_DIR / "assets", check_dir=False), name="assets")

@app.get("/style.css", include_in_schema=False)
async def serve_style():
    return FileResponse(ROOT_DIR / "style.css", media_type="text/css")

@app.get("/script.js", include_in_schema=False)
async def serve_script():
    return FileResponse(ROOT_DIR / "script.js", media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
