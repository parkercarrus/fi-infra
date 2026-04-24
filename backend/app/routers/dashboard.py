from __future__ import annotations

from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.models import HealthResponse, PlatformResponse
from backend.app.services.dashboard import get_platform_data


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", database_path=str(settings.database_path))


@router.get("/api/v1/dashboard", response_model=PlatformResponse)
@router.get("/api/v1/platform", response_model=PlatformResponse)
def dashboard() -> PlatformResponse:
    return get_platform_data()
