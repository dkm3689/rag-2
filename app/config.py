from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    llm_model: str
    jwt_secret_key: str
    jwt_alogorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
