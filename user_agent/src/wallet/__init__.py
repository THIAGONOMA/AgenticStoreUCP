"""Modulo de Carteira Virtual do User Agent.

Gerencia saldo e tokens para pagamentos via PSP.
"""
from .wallet import VirtualWallet, get_wallet

__all__ = ["VirtualWallet", "get_wallet"]
