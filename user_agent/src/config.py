"""Configuracoes do User Agent."""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Configuracoes do User Agent."""
    
    # LLM - Gemini (prioritario)
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"
    
    # LLM - Fallback (OpenAI/Anthropic)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4-turbo-preview"
    
    # HTTP
    http_timeout: float = 30.0
    
    # A2A
    a2a_reconnect_interval: float = 5.0
    a2a_ping_interval: float = 30.0
    
    # Default stores
    default_stores: List[str] = ["http://localhost:8182"]
    api_gateway_url: str = "http://localhost:8000"
    ucp_server_url: str = "http://localhost:8182"
    
    # Security
    jwt_expiry_seconds: int = 3600
    user_key_id: str = "user-agent-key-001"
    
    # Debug
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
