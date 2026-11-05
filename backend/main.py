"""
OptHire FastAPI Application Entry Point.
Configures CORS, standardized exception handling, and API routing.
"""
import logging
import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.router import root_router
from config.settings import settings
from database.db import init_db

# Configure structured application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("opthire.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: initialize database schema on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.error("Database initialization failed on startup: %s", exc)
    yield


def create_app() -> FastAPI:
    """Application factory for OptHire FastAPI backend."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-powered candidate evaluation, ATS matching, interview generation, "
            "and hiring decision support platform powered by Google Gemini."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )


    # Configure CORS securely
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standardized Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred",
                "detail": exc.detail if not isinstance(exc.detail, str) else None,
                "code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Format validation errors without leaking sensitive data
        sanitized_errors = []
        for err in exc.errors():
            sanitized_errors.append({
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check your request parameters.",
                "detail": sanitized_errors,
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception: %s", exc, exc_info=settings.DEBUG)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred. Please try again later.",
                "detail": str(exc) if settings.DEBUG else None,
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

    # Register API routes
    app.include_router(root_router)

    return app


app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
