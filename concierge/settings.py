from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    google_cloud_project: str = Field(default="tools-cashtimepay-com")
    google_cloud_location: str = Field(default="europe-west6")
    google_genai_use_vertexai: str = Field(default="TRUE")

    concierge_planner_model: str = Field(default="gemini-3.1-pro-preview")
    concierge_worker_model: str = Field(default="gemini-3.5-flash")

    # --- Gemini Enterprise Search grounding (research sub-agent RAG) ---
    # When ``gemini_search_datastore`` is set, ``ground_taxonomy`` queries the
    # Gemini Enterprise Search data store. Otherwise it falls back to the bundled
    # canonical-taxonomy corpus (deterministic, offline, demo-safe).
    gemini_search_datastore: str = Field(default="")
    gemini_search_location: str = Field(default="global")

    mcp_base_url: str = Field(default="https://mcp.cashtimepay.com")
    mcp_bearer_token: str = Field(default="")

    aibmr_base_url: str = Field(default="")
    aibmo_base_url: str = Field(default="")
    aimm_base_url: str = Field(default="")
    cren_base_url: str = Field(default="")
    aicrops_base_url: str = Field(default="")

    cf_access_client_id: str = Field(default="")
    cf_access_client_secret: str = Field(default="")

    twenty_base_url: str = Field(default="https://crm.cashtimepay.com")
    twenty_api_key: str = Field(default="")

    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")
    demo_mode: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
