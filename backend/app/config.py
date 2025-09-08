"""
Application configuration management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API Configuration
    api_host: str = "localhost"
    api_port: int = 8000
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"

    # Database Configuration
    database_url: str = "sqlite:///./quiz_generator.db"

    # Google Gemini API Configuration
    gemini_api_key: str | None = None

    # Frontend Configuration
    frontend_url: str = "http://localhost:3000"

    # Quiz Generation Settings
    default_questions_per_quiz: int = 5
    default_options_per_question: int = 4
    max_topic_length: int = 100

    # AI Model Configuration
    gemini_model: str = "gemini-2.5-flash"
    gemini_thinking_budget: int = 1024


# Global settings instance
settings = Settings()
