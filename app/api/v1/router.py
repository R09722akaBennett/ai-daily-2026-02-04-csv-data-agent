from fastapi import APIRouter

from app.api.v1.routes import demo, extract, health, jobs, tables

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(extract.router, tags=["extract"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(tables.router, tags=["tables"])
api_router.include_router(demo.router, tags=["demo"])
