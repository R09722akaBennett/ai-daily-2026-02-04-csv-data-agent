from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"

    project_name: str = "KDoc IDP"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_path: str = "/api"

    allowed_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8501,http://127.0.0.1:8501"
    )
    ui_api_url: str = "http://127.0.0.1:8000"

    data_dir: str = "./data"
    max_upload_mb: int = 50

    demo_mode: bool = True

    # Docling knobs (only consumed when docling is importable).
    docling_do_table_structure: bool = True
    docling_do_ocr: bool = True
    docling_max_pages: int = 200

    # RAG chunker.
    chunk_target_tokens: int = 500
    chunk_overlap_tokens: int = 60

    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
