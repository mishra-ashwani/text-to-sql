from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite+aiosqlite:///./text_to_sql.db"
    default_sql_dialect: str = "postgresql"

    class Config:
        env_file = ".env"


settings = Settings()
