from app.config import Settings


def test_effective_provider_falls_back_to_simulado_without_key():
    settings = Settings(database_url="x", uv_provider="openuv", openuv_api_key="")
    assert settings.effective_provider == "simulado"


def test_effective_provider_keeps_openuv_with_key():
    settings = Settings(database_url="x", uv_provider="openuv", openuv_api_key="k")
    assert settings.effective_provider == "openuv"
