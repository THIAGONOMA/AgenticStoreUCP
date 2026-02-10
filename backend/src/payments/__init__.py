"""Modulo de Pagamentos - PSP Simulado.

Implementa um Payment Service Provider simulado para demonstrar
o fluxo completo de pagamento com AP2.

Nota: PSPSimulator e get_psp_simulator devem ser importados diretamente
de .psp_simulator para evitar importacao circular.
"""
from .models import (
    PaymentStatus,
    PaymentTransaction,
    WalletInfo,
    WalletToken,
    WalletSource,
    ProcessPaymentRequest,
    ProcessPaymentResponse,
    RefundRequest,
    RefundResponse,
)

__all__ = [
    "PaymentStatus",
    "PaymentTransaction",
    "WalletInfo",
    "WalletToken",
    "WalletSource",
    "ProcessPaymentRequest",
    "ProcessPaymentResponse",
    "RefundRequest",
    "RefundResponse",
]


# Funcao para importacao lazy do PSPSimulator (evita ciclo)
def get_psp_simulator():
    """Obter instancia do PSP Simulator (importacao lazy)."""
    from .psp_simulator import get_psp_simulator as _get_psp
    return _get_psp()
