from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import get_anthropic, get_binance, get_memory, get_settings
from app.services.orchestrator import report_to_dict, run_cycle

router = APIRouter()


class RunCycleRequest(BaseModel):
    reflect: bool = False


@router.post("/cycles/run")
def cycles_run(req: RunCycleRequest | None = None) -> dict:
    settings = get_settings()
    memory = get_memory()
    client = get_anthropic()
    reflect = bool(req.reflect) if req is not None else False
    with get_binance() as binance:
        try:
            report = run_cycle(
                settings=settings,
                binance=binance,
                memory=memory,
                client=client,
                reflect=reflect,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"cycle failed: {exc}") from exc
    return report_to_dict(report)
