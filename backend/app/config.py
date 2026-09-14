"""Application configuration loaded from environment variables."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — accepts either LLM_API_KEY or the standard OPENAI_API_KEY alias.
    # Priority: LLM_API_KEY (if non-empty) → OPENAI_API_KEY → "" (mock mode).
    llm_api_key: str = ""
    openai_api_key: str = ""          # alias: OPENAI_API_KEY in .env

    llm_base_url: str = "https://api.openai.com/v1"

    # Model — accepts either LLM_MODEL or OPENAI_MODEL alias.
    llm_model: str = "gpt-4o-mini"
    openai_model: str = ""            # alias: OPENAI_MODEL in .env

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Uploads
    upload_dir: str = "data/uploads"
    max_upload_size_mb: int = 20

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Chroma
    chroma_path: str = "data/chroma"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def effective_api_key(self) -> str:
        """Return the first non-empty key: LLM_API_KEY → OPENAI_API_KEY."""
        if self.llm_api_key and self.llm_api_key.strip():
            return self.llm_api_key.strip()
        if self.openai_api_key and self.openai_api_key.strip():
            return self.openai_api_key.strip()
        return ""

    @property
    def effective_model(self) -> str:
        """Return the first non-empty model: LLM_MODEL → OPENAI_MODEL → default."""
        if self.openai_model and self.openai_model.strip():
            return self.openai_model.strip()
        return self.llm_model.strip() or "gpt-4o-mini"

    @property
    def has_llm_key(self) -> bool:
        return bool(self.effective_api_key)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_dirs(self):
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
