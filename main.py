import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from controllers.chat_controller import router as chat_router
from controllers.ingest_controller import router as ingest_router
from core.config import get_settings
from core.exceptions import AppError
from services.system_service import get_system_health, log_startup_health

logging.basicConfig(level=logging.INFO)

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"


@asynccontextmanager
async def lifespan(_: FastAPI):
    log_startup_health()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)
app.include_router(ingest_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": error["loc"][-1], "message": error["msg"]} for error in exc.errors()]
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request", "details": errors},
    )


@app.get("/")
def home():
    return FileResponse(UI_DIR / "index.html")


@app.get("/health")
def health_check():
    health = get_system_health()
    status_code = 200 if health["status"] == "ok" else 503
    return JSONResponse(status_code=status_code, content=health)


@app.get("/about")
def about():
    return {
        "project": settings.app_name,
        "version": settings.app_version,
        "developer": settings.developer_display_name,
        "description": settings.app_description,
    }


@app.get("/api/info")
def api_info():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "developer": settings.developer_display_name,
    }
