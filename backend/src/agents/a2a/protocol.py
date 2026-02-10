"""A2A Protocol - Comunicacao entre agentes."""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import structlog

logger = structlog.get_logger()


class A2AMessageType(str, Enum):
    """Tipos de mensagem A2A."""
    CONNECT = "a2a.connect"
    DISCONNECT = "a2a.disconnect"
    REQUEST = "a2a.request"
    RESPONSE = "a2a.response"
    EVENT = "a2a.event"
    ERROR = "a2a.error"


class A2AAction(str, Enum):
    """Acoes A2A suportadas."""
    # Discovery
    SEARCH = "search"
    GET_PRODUCTS = "get_products"
    GET_CATEGORIES = "list_categories"
    
    # Shopping
    CREATE_ORDER = "create_order"
    GET_CHECKOUT = "get_checkout"
    COMPLETE_CHECKOUT = "complete_checkout"
    
    # Recommendations
    RECOMMEND = "recommend"
    
    # Info
    GET_PROFILE = "get_profile"
    PING = "ping"


@dataclass
class A2AMessage:
    """Mensagem A2A."""
    type: A2AMessageType
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = field(default_factory=lambda: int(time.time()))
    agent_id: Optional[str] = None
    action: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    status: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionario."""
        return {
            "type": self.type.value if isinstance(self.type, A2AMessageType) else self.type,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "action": self.action,
            "payload": self.payload,
            "status": self.status,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Criar de dicionario."""
        msg_type = data.get("type", "")
        
        # Converter string para enum
        try:
            msg_type = A2AMessageType(msg_type)
        except ValueError:
            msg_type = A2AMessageType.ERROR
        
        return cls(
            type=msg_type,
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", int(time.time())),
            agent_id=data.get("agent_id"),
            action=data.get("action"),
            payload=data.get("payload", {}),
            status=data.get("status"),
            error=data.get("error")
        )


@dataclass
class AgentProfile:
    """Perfil de um agente externo."""
    agent_id: str
    name: str
    version: str = "1.0"
    capabilities: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities
        }


class A2AProtocol:
    """
    Protocolo A2A para comunicacao entre agentes.
    
    Gerencia conexoes, roteamento e processamento de mensagens.
    """
    
    def __init__(self):
        self.connected_agents: Dict[str, AgentProfile] = {}
    
    def register_agent(self, profile: AgentProfile):
        """Registrar agente conectado."""
        self.connected_agents[profile.agent_id] = profile
        logger.info("Agent connected", agent_id=profile.agent_id, name=profile.name)
    
    def unregister_agent(self, agent_id: str):
        """Remover agente."""
        if agent_id in self.connected_agents:
            del self.connected_agents[agent_id]
            logger.info("Agent disconnected", agent_id=agent_id)
    
    def is_connected(self, agent_id: str) -> bool:
        """Verificar se agente esta conectado."""
        return agent_id in self.connected_agents
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Obter perfil do agente."""
        return self.connected_agents.get(agent_id)
    
    def list_agents(self) -> list:
        """Listar agentes conectados."""
        return [p.to_dict() for p in self.connected_agents.values()]
    
    def create_response(
        self,
        request: A2AMessage,
        status: str,
        payload: Dict[str, Any],
        error: Optional[str] = None
    ) -> A2AMessage:
        """Criar resposta para uma requisicao."""
        return A2AMessage(
            type=A2AMessageType.RESPONSE,
            message_id=request.message_id,
            agent_id="store-agent",
            action=request.action,
            payload=payload,
            status=status,
            error=error
        )
    
    def create_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> A2AMessage:
        """Criar evento para broadcast."""
        return A2AMessage(
            type=A2AMessageType.EVENT,
            agent_id="store-agent",
            action=event_type,
            payload=payload
        )
    
    def create_error(
        self,
        request: A2AMessage,
        error: str
    ) -> A2AMessage:
        """Criar mensagem de erro."""
        return A2AMessage(
            type=A2AMessageType.ERROR,
            message_id=request.message_id,
            agent_id="store-agent",
            action=request.action,
            status="error",
            error=error
        )


# Instancia global
a2a_protocol = A2AProtocol()
