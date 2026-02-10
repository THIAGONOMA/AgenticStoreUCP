"""Configuracoes do backend."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuracoes da aplicacao."""
    
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ucp_host: str = "0.0.0.0"
    ucp_port: int = 8182
    mcp_port: int = 8183
    
    # Database
    products_db_path: str = "./data/products.db"
    transactions_db_path: str = "./data/transactions.db"
    
    # LLM - Gemini (Principal)
    google_api_key: str = ""
    llm_model: str = "gemini-2.0-flash-lite"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    
    # LLM - Alternativos
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Security
    jwt_expiry_seconds: int = 3600
    ap2_key_id: str = "livraria-key-001"
    
    # HTTP
    http_timeout: float = 30.0
    
    # Sandbox
    sandbox_globals: List[str] = ["json", "asyncio", "re", "datetime"]
    
    # Debug
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
