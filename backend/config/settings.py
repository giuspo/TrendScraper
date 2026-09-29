from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys & Gateway
    SCRAPE_OPS_API_KEY: Optional[str] = None
    SCRAPER_API_KEY: Optional[str] = None
    
    # Execution Mode
    MOCK_MODE: bool = True  # Se True, usa file locali offline anzichè colpire le API esterne
    
    # Database
    DATABASE_URL: str = "sqlite:///trendradar.db"
    
    # Paths
    RULES_PATH: str = "config/rules.yaml"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
