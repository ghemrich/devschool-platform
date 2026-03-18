import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    secret_key: str = "change-me-in-production"
    base_url: str = "http://localhost"
    environment: str = "development"
    allowed_origins: str = "http://localhost,http://localhost:4321"
    github_org: str = ""
    github_org_admin_token: str = ""
    github_webhook_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    webhook_skip_verify: bool = False
    discord_webhook_url: str = ""

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment in ("production", "staging"):
            if self.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production/staging")
            if not self.github_client_secret:
                raise ValueError("GITHUB_CLIENT_SECRET is required in production/staging")
            if not self.github_webhook_secret:
                logger.warning("GITHUB_WEBHOOK_SECRET is not set — webhook verification disabled")
            if "*" in self.allowed_origins:
                raise ValueError("ALLOWED_ORIGINS must not contain '*' — credentials are enabled")
        elif self.secret_key == "change-me-in-production":
            logger.warning("SECRET_KEY is using the default value — do not use in any shared environment")
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
