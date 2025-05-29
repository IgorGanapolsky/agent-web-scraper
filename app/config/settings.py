"""Modern configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="agent-web-scraper", description="Application name")
    app_version: str = Field(default="0.2.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=True, description="Enable debug mode")

    # API Keys
    serpapi_key: Optional[str] = Field(
        default=None, description="SerpAPI key for search functionality"
    )
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key for AI features"
    )

    # Google Sheets Configuration
    spreadsheet_name: str = Field(
        default="Reddit Market Research", description="Google Sheets spreadsheet name"
    )
    google_credentials_path: str = Field(
        default="secrets/service_account.json",
        description="Path to Google service account JSON",
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file: str = Field(default="logs/app.log", description="Log file path")

    # Sentry Configuration
    sentry_dsn: Optional[str] = Field(
        default=None, description="Sentry DSN for error tracking"
    )

    # Server Configuration
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Database Configuration
    database_url: str = Field(default="sqlite:///./data.db", description="Database URL")

    # Scraping Configuration
    max_concurrent_requests: int = Field(
        default=10, description="Maximum concurrent HTTP requests"
    )
    request_timeout: int = Field(
        default=30, description="HTTP request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )

    # AI Configuration
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    max_tokens: int = Field(default=1500, description="Maximum tokens for AI responses")
    temperature: float = Field(default=0.3, description="AI response temperature")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def google_credentials_exist(self) -> bool:
        """Check if Google credentials file exists."""
        return Path(self.google_credentials_path).exists()


# Global settings instance
settings = AppSettings()


# Legacy compatibility functions
def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting value with fallback to os.getenv for backward compatibility."""
    value = getattr(settings, key.lower(), None)
    if value is None:
        return os.getenv(key.upper(), default)
    return str(value)


# Backward compatibility exports
SERPAPI_KEY = settings.serpapi_key
OPENAI_API_KEY = settings.openai_api_key
SPREADSHEET_NAME = settings.spreadsheet_name
