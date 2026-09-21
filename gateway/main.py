"""
NEXUS Secure Telemetry Gateway Application
Entrypoint for the high-throughput ingestion gateway.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from configs.settings import settings
from gateway.api.routes import router
from streaming.redis.client import redis_manager

logging.basicConfig(
    level=getattr(logging, settings.nexus_log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("nexus.gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NEXUS Secure Telemetry Gateway...")
    await redis_manager.initialize()
    yield
    logger.info("Shutting down NEXUS Gateway...")
    await redis_manager.close()


app = FastAPI(
    title="NEXUS Secure Telemetry Gateway",
    description="High-throughput mTLS ingestion gateway for cyber-physical digital twins.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "gateway.main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=False
    )
