from fastapi import APIRouter

from app.api.v1.routes import cycles, health, memory

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cycles.router, tags=["cycles"])
api_router.include_router(memory.router, tags=["memory"])
