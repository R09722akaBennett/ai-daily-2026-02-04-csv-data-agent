from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment
    env: str = "dev"
    log_level: str = "INFO"

    # API
    project_name: str = "Daily Service"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_path: str = "/api"

    allowed_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    # UI
    ui_api_url: str = "http://127.0.0.1:8000"

    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
