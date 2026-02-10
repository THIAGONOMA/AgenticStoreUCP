"""
Discovery endpoint UCP - /.well-known/ucp

O endpoint de discovery permite que agentes descubram as capacidades
da loja, servicos disponiveis e metodos de pagamento suportados.

Este modulo usa as definicoes organizadas em:
- capabilities/ : Capabilities UCP (checkout, discount, fulfillment)
- services/     : Services UCP (shopping) e Payment Handlers
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from .capabilities import get_all_capabilities, UcpCapabilitySpec
from .services import get_all_services, get_payment_profile, UcpService, PaymentProfile


class Ap2Profile(BaseModel):
    """Perfil AP2 - Agent Payments Protocol."""
    version: str = "2025.0"
    sdk_source: str = "google-agentic-commerce/AP2"
    supported_mandates: List[str] = ["IntentMandate", "CartMandate", "PaymentMandate"]
    supported_rails: List[str] = ["mock", "x402"]
    sdk_available: bool = False


class UcpProfile(BaseModel):
    """Perfil UCP principal."""
    version: str = "2026-01-11"
    services: Dict[str, UcpService] = {}
    capabilities: List[UcpCapabilitySpec] = []


class UcpDiscoveryProfile(BaseModel):
    """Perfil completo de discovery UCP."""
    ucp: UcpProfile
    payment: PaymentProfile
    ap2: Optional[Ap2Profile] = None


def get_discovery_profile(base_url: str = "http://localhost:8182") -> UcpDiscoveryProfile:
    """
    Gerar perfil de discovery da livraria.
    
    Este perfil e retornado no endpoint /.well-known/ucp
    e permite que agentes descubram:
    - Versao do protocolo UCP
    - Services disponiveis (shopping)
    - Capabilities (checkout, discount, fulfillment)
    - Payment handlers (mock, ap2)
    - Suporte AP2 (Agent Payments Protocol)
    
    Args:
        base_url: URL base do servidor UCP
        
    Returns:
        UcpDiscoveryProfile com todas as informacoes
    """
    # Buscar services e capabilities organizados
    services = get_all_services(base_url)
    capabilities = get_all_capabilities()
    payment = get_payment_profile()
    
    # Verificar disponibilidade do SDK AP2
    try:
        from ..security import is_ap2_sdk_available
        sdk_available = is_ap2_sdk_available()
    except ImportError:
        sdk_available = False
    
    # Perfil AP2
    ap2 = Ap2Profile(
        version="2025.0",
        sdk_source="google-agentic-commerce/AP2",
        supported_mandates=["IntentMandate", "CartMandate", "PaymentMandate"],
        supported_rails=["mock", "x402"],
        sdk_available=sdk_available
    )
    
    return UcpDiscoveryProfile(
        ucp=UcpProfile(
            version="2026-01-11",
            services=services,
            capabilities=capabilities
        ),
        payment=payment,
        ap2=ap2
    )


# Manter compatibilidade com codigo existente
PaymentHandlerConfig = Dict[str, Any]


def get_store_info() -> Dict[str, Any]:
    """Retorna informacoes basicas da loja."""
    return {
        "name": "Livraria Virtual UCP",
        "description": "Demonstracao do Universal Commerce Protocol",
        "version": "1.0.0",
        "contact": {
            "email": "contato@livraria-ucp.demo",
            "website": "https://livraria-ucp.demo"
        }
    }


# =============================================================================
# A2A Discovery - /.well-known/agent.json
# =============================================================================

def get_a2a_agent_card(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Gerar AgentCard para discovery A2A.
    
    Este perfil e retornado no endpoint /.well-known/agent.json
    e permite que outros agentes descubram as capacidades deste agente.
    
    Segue o formato do SDK oficial A2A.
    """
    from ..agents.a2a.adapters import get_store_agent_card
    
    card = get_store_agent_card()
    card["url"] = f"{base_url}/a2a"
    
    return card


__all__ = [
    "UcpProfile",
    "UcpDiscoveryProfile",
    "Ap2Profile",
    "get_discovery_profile",
    "get_store_info",
    "get_a2a_agent_card",
]
