from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RFQ Application"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Rate Limiting
    RATE_LIMIT_GENERAL: int = 60
    RATE_LIMIT_AUTH: int = 10
    RATE_LIMIT_QUOTE: int = 10
    RATE_LIMIT_CLARIFICATION: int = 20
    
    # Security
    JWT_SECRET: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        origins = []
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",") if i.strip() != "*"]
        elif isinstance(v, list):
            origins = [i for i in v if i != "*"]
            
        # Hardcode the Render frontend URLs to guarantee it works for the demo
        guaranteed_origins = [
            "http://localhost:3000",
            "https://procura-frontend-0jz6.onrender.com",
            "https://procura-frontend.onrender.com"
        ]
        for url in guaranteed_origins:
            if url not in origins:
                origins.append(url)
                
        return origins
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
