"""
Centralized application configuration using Pydantic BaseSettings.
All environment variables are loaded and validated here.
"""
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version prefix")
    PROJECT_NAME: str = Field(default="User Profile API", description="Project name")
    API_VERSION: str = Field(default="1.0.0", description="API version")

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")
    DATABASE_POOL_MIN_SIZE: int = Field(default=10, description="Min database pool size")
    DATABASE_POOL_MAX_SIZE: int = Field(default=20, description="Max database pool size")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_CACHE_DB: int = Field(default=0, description="Redis cache database number")
    REDIS_RATE_LIMIT_DB: int = Field(default=1, description="Redis rate limit database number")

    # JWT Authentication (matches auth-api configuration)
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key for token validation")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")

    # Service-to-Service API Keys
    ACTIVITIES_API_KEY: str = Field(..., description="Activities service API key")
    PARTICIPATION_API_KEY: str = Field(..., description="Participation service API key")
    MODERATION_API_KEY: str = Field(..., description="Moderation service API key")
    PAYMENT_API_KEY: str = Field(..., description="Payment processor API key")

    # External Services
    IMAGE_API_URL: str = Field(..., description="Image API base URL")
    IMAGE_API_CDN_DOMAIN: str = Field(..., description="CDN domain for image validation")
    EMAIL_API_URL: str = Field(..., description="Email API base URL")
    AUTH_API_URL: str = Field(..., description="Auth API base URL")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")

    # Caching
    CACHE_ENABLED: bool = Field(default=True, description="Enable Redis caching")
    CACHE_DEFAULT_TTL: int = Field(default=300, description="Default cache TTL in seconds")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or console")

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")

    # Cache TTL Configuration (in seconds)
    CACHE_TTL_USER_PROFILE: int = Field(default=300, description="User profile cache TTL (5 minutes)")
    CACHE_TTL_USER_SETTINGS: int = Field(default=1800, description="User settings cache TTL (30 minutes)")
    CACHE_TTL_USER_INTERESTS: int = Field(default=3600, description="User interests cache TTL (1 hour)")

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("LOG_FORMAT")
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "console"]
        if v.lower() not in valid_formats:
            raise ValueError(f"LOG_FORMAT must be one of {valid_formats}")
        return v.lower()

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
