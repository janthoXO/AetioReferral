from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmSettings(BaseSettings):
    # Real environment variables win over .env (read from the working directory); other keys in .env are ignored.
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra="ignore")

    provider: str | None = None  # pydantic-ai provider name: openai, anthropic, google, ollama, ...
    model: str | None = None
    url: str | None = None
    api_key: SecretStr | None = None


def load_llm_settings() -> LlmSettings | None:
    """None when no LLM_* variable is set: the generate path is then not exposed at all."""
    settings = LlmSettings()
    if settings.provider and settings.model:
        return settings
    present = [f"LLM_{name.upper()}" for name in LlmSettings.model_fields if getattr(settings, name)]
    if not present:
        return None
    missing = [f"LLM_{name.upper()}" for name in ("provider", "model") if not getattr(settings, name)]
    raise ValueError(f"{', '.join(present)} set but {', '.join(missing)} missing")
