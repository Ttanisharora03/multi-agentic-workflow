# pyright: ignore [reportMissingImports]
from fastapi import FastAPI, Request
# pyright: ignore [reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware
# pyright: ignore [reportMissingImports]
from fastapi.responses import JSONResponse
# pyright: ignore [reportMissingImports]
from pydantic import ValidationError
# pyright: ignore [reportMissingImports]
import structlog
from dotenv import load_dotenv

load_dotenv()

# pyright: ignore [reportMissingImports]
from src.api.routes import router as api_router

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Dubai AI Travel Planner",
    description="Agentic pipeline for generating personalized Dubai travel itineraries",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# pyright: ignore [reportMissingImports]
from fastapi.staticfiles import StaticFiles
import os

# Include routes
app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Mount frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Global Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error("validation_error", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": "Input validation error", "errors": exc.errors()},
    )

@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
    logger.error("timeout_error", error=str(exc))
    return JSONResponse(
        status_code=504,
        content={"detail": "Request processing timed out"},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
