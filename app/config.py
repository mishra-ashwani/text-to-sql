from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite+aiosqlite:///./text_to_sql.db"
    default_sql_dialect: str = "postgresql"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0
    llm_timeout: int = 30
    allowed_origins: str = "*"
    log_level: str = "INFO"
    rate_limit: str = "20/minute"

    class Config:
        env_file = ".env"


settings = Settings()
