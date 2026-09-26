import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401  (ensures every model is registered on Base.metadata)

from app.routes import (
    auth, customers, connections, meters, readings, tariffs,
    bills, payments, complaints, technicians, service_requests,
    analytics, dashboard,
)
from app.utils.exceptions import AppException
from app.utils.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("electricity_ums")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "A FastAPI-based Electricity Utility Management System covering customers, "
        "connections, smart meters, readings, tariffs, billing, payments, complaints, "
        "technicians, service requests, analytics and reporting."
    ),
)

# --- Middleware --------------------------------------------------------
cors_origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [
    o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


# --- Global exception handling (Level 16) -------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Validation error.", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# --- Startup -------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    # Dev/demo convenience: creates any missing tables. In a real deployment,
    # schema changes should flow through Alembic migrations (see /alembic).
    Base.metadata.create_all(bind=engine)


# --- Health / root ---------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    return {"service": settings.APP_NAME, "status": "running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# --- Routers (Level 17: API versioning bonus, all under /api/v1) --------
for router in (
    auth.router, customers.router, connections.router, meters.router, readings.router,
    tariffs.router, bills.router, payments.router, complaints.router, technicians.router,
    service_requests.router, analytics.router, dashboard.router,
):
    app.include_router(router, prefix=settings.API_V1_PREFIX)
