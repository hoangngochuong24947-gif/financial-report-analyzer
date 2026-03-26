"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import routes_analysis, routes_report, routes_stock, routes_v2
from src.config.settings import settings
from src.utils.logger import logger, setup_logger

setup_logger(log_level=settings.log_level)

app = FastAPI(
    title="Financial Report Analyzer",
    description="A-share financial report analysis service",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_stock.router)
app.include_router(routes_analysis.router)
app.include_router(routes_report.router)
app.include_router(routes_v2.router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("=" * 60)
    logger.info("Financial Report Analyzer Starting...")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Financial Provider: {settings.financial_provider}")
    logger.info(f"Archive Root: {settings.archive_root}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Financial Report Analyzer Shutting Down...")


@app.get("/")
async def root():
    return {
        "message": "Financial Report Analyzer API",
        "version": "0.2.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "financial-report-analyzer",
    }
