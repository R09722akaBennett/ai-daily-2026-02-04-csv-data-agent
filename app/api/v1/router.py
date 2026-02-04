from fastapi import APIRouter

from app.api.v1.routes import health, csv_agent

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(csv_agent.router, tags=["csv"])
