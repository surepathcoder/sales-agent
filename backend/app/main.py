"""
Kijani AI — FastAPI application entry point.

Architecture:
- Async lifespan for DB init and Redis connection
- CORS for Next.js frontend
- Tenant context middleware on all /api/v1 routes
- Structured JSON logging with request IDs
"""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1 import api_router
from app.config import get_settings
from app.database import init_db
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit_http import RateLimitHTTPMiddleware
from app.middleware.tenant_context import TenantContextMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kijani")


@asynccontextmanager
async def lifespan(app: FastAPI):
  settings = get_settings()
  logger.info("Starting %s [%s]", settings.app_name, settings.app_env)

  if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

  await init_db()

  try:
    app.state.redis = aioredis.from_url(settings.redis_url_str, decode_responses=True)
    await app.state.redis.ping()
    logger.info("Redis connected")
  except Exception as e:
    logger.warning("Redis unavailable: %s", e)
    app.state.redis = None

  yield

  if app.state.redis:
    await app.state.redis.aclose()
  logger.info("Shutdown complete")


def create_app() -> FastAPI:
  settings = get_settings()

  app = FastAPI(
    title=settings.app_name,
    description="Agentic AI sales platform for Tanzanian B2B businesses",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
  )

  app.add_middleware(RateLimitHTTPMiddleware)
  app.add_middleware(RequestLoggingMiddleware)
  app.add_middleware(TenantContextMiddleware)
  app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  app.include_router(api_router)

  @app.get("/health")
  async def health_check():
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}

  # Prometheus metrics
  metrics_app = make_asgi_app()
  app.mount("/metrics", metrics_app)

  return app


app = create_app()
