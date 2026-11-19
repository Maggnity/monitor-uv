"""Configuração da aplicação lida de variáveis de ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://uv:uv@localhost:5432/uv"
    uv_provider: Literal["openuv", "simulado"] = "openuv"
    openuv_api_key: str = ""
    openuv_interval_min: int = 120
    openmeteo_interval_min: int = 60
    collect_window_start_hour: int = 6
    collect_window_end_hour: int = 19
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:5173"]

    @property
    def effective_provider(self) -> Literal["openuv", "simulado"]:
        """Provedor realmente usado: sem chave, a OpenUV cai para o simulado."""
        if self.uv_provider == "openuv" and not self.openuv_api_key.strip():
            return "simulado"
        return self.uv_provider


@lru_cache
def get_settings() -> Settings:
    return Settings()
