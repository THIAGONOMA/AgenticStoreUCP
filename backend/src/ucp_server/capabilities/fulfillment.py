"""
UCP Capability: dev.ucp.shopping.fulfillment

Capability de fulfillment que estende checkout para suportar
entrega, rastreamento e atualizacoes de status.

Spec: https://ucp.dev/specs/shopping/fulfillment
"""
from pydantic import BaseModel
from typing import Optional


class FulfillmentCapability(BaseModel):
    """Especificacao da capability de fulfillment."""
    name: str = "dev.ucp.shopping.fulfillment"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/shopping/fulfillment"
    schema_url: str = "https://ucp.dev/schemas/shopping/fulfillment.json"
    extends: str = "dev.ucp.shopping.checkout"
    
    class Config:
        frozen = True


# Status de fulfillment
FULFILLMENT_STATUS = {
    "pending": "Aguardando processamento",
    "processing": "Em processamento",
    "shipped": "Enviado",
    "in_transit": "Em transito",
    "out_for_delivery": "Saiu para entrega",
    "delivered": "Entregue",
    "cancelled": "Cancelado",
    "returned": "Devolvido"
}


# Operacoes de fulfillment
FULFILLMENT_OPERATIONS = [
    {
        "name": "get_fulfillment_status",
        "description": "Obter status de fulfillment de um pedido",
        "endpoint": "GET /orders/{order_id}/fulfillment",
        "response_schema": "FulfillmentStatus"
    },
    {
        "name": "update_shipping_address",
        "description": "Atualizar endereco de entrega (se permitido)",
        "endpoint": "PUT /orders/{order_id}/shipping",
        "request_schema": "UpdateShippingRequest",
        "response_schema": "FulfillmentStatus"
    },
    {
        "name": "track_shipment",
        "description": "Obter informacoes de rastreamento",
        "endpoint": "GET /orders/{order_id}/tracking",
        "response_schema": "TrackingInfo"
    },
]


def get_fulfillment_capability() -> FulfillmentCapability:
    """Retorna a capability de fulfillment."""
    return FulfillmentCapability()


def get_operations():
    """Retorna operacoes da capability."""
    return FULFILLMENT_OPERATIONS
