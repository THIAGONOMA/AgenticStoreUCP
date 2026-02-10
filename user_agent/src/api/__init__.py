"""API REST do User Agent."""
from .wallet_routes import router as wallet_router

__all__ = ["wallet_router"]
