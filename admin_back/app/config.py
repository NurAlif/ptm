from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings loaded from the .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

# Create a single instance of the settings to be used throughout the app
settings = Settings()

