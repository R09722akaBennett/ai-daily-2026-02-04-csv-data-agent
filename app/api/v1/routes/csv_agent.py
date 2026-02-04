from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.csv_agent import profile_csv

router = APIRouter()


class ProfileRequest(BaseModel):
    csv_text: str


@router.post('/csv/profile')
def csv_profile(req: ProfileRequest):
    prof = profile_csv(req.csv_text)
    return {'columns': [p.__dict__ for p in prof]}
