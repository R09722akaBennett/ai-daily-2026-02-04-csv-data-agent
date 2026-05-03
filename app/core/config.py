from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"

    project_name: str = "Crypto Agent Research"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_path: str = "/api"

    allowed_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    ui_api_url: str = "http://127.0.0.1:8000"

    anthropic_api_key: str = ""

    scout_model: str = "claude-haiku-4-5"
    analyst_model: str = "claude-sonnet-4-6"
    trader_model: str = "claude-opus-4-7"
    risk_model: str = "claude-haiku-4-5"
    reflector_model: str = "claude-opus-4-7"

    data_dir: str = "./data"
    binance_base_url: str = "https://api.binance.com"
    paper_starting_balance_usd: float = 1000.0

    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
