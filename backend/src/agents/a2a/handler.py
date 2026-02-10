"""A2A Handler - Processa requisicoes A2A."""
from typing import Dict, Any
import structlog

from .protocol import (
    A2AMessage, A2AMessageType, A2AAction, A2AProtocol, AgentProfile,
    a2a_protocol
)
from ..graph import store_agent_runner
from ...ucp_server.discovery import get_discovery_profile

logger = structlog.get_logger()


class A2AHandler:
    """
    Handler para requisicoes A2A.
    
    Processa mensagens de agentes externos e roteia para os Store Agents.
    """
    
    def __init__(self, protocol: A2AProtocol = None):
        self.protocol = protocol or a2a_protocol
    
    async def handle_message(
        self,
        message: A2AMessage,
        session_id: str
    ) -> A2AMessage:
        """
        Processar mensagem A2A.
        
        Args:
            message: Mensagem A2A recebida
            session_id: ID da sessao WebSocket
            
        Returns:
            Mensagem de resposta
        """
        logger.info(
            "A2A message received",
            type=message.type.value,
            action=message.action,
            agent=message.agent_id
        )
        
        try:
            if message.type == A2AMessageType.CONNECT:
                return await self._handle_connect(message)
            
            elif message.type == A2AMessageType.DISCONNECT:
                return await self._handle_disconnect(message)
            
            elif message.type == A2AMessageType.REQUEST:
                return await self._handle_request(message, session_id)
            
            else:
                return self.protocol.create_error(
                    message,
                    f"Unknown message type: {message.type}"
                )
                
        except Exception as e:
            logger.error("A2A handler error", error=str(e))
            return self.protocol.create_error(message, str(e))
    
    async def _handle_connect(self, message: A2AMessage) -> A2AMessage:
        """Processar conexao de agente."""
        profile_data = message.payload.get("agent_profile", {})
        
        profile = AgentProfile(
            agent_id=message.agent_id or profile_data.get("agent_id", "unknown"),
            name=profile_data.get("name", "Unknown Agent"),
            version=profile_data.get("version", "1.0"),
            capabilities=profile_data.get("capabilities", [])
        )
        
        self.protocol.register_agent(profile)
        
        # Retornar perfil da loja
        store_profile = get_discovery_profile("http://localhost:8182")
        
        return self.protocol.create_response(
            message,
            status="connected",
            payload={
                "store_profile": {
                    "name": "Livraria Virtual UCP",
                    "version": store_profile.ucp.version,
                    "capabilities": [cap.name for cap in store_profile.ucp.capabilities]
                },
                "supported_actions": [a.value for a in A2AAction]
            }
        )
    
    async def _handle_disconnect(self, message: A2AMessage) -> A2AMessage:
        """Processar desconexao de agente."""
        if message.agent_id:
            self.protocol.unregister_agent(message.agent_id)
        
        return self.protocol.create_response(
            message,
            status="disconnected",
            payload={}
        )
    
    async def _handle_request(
        self,
        message: A2AMessage,
        session_id: str
    ) -> A2AMessage:
        """Processar requisicao de agente."""
        action = message.action
        payload = message.payload
        
        if action == A2AAction.PING.value:
            return self.protocol.create_response(
                message,
                status="success",
                payload={"pong": True, "timestamp": message.timestamp}
            )
        
        elif action == A2AAction.GET_PROFILE.value:
            store_profile = get_discovery_profile("http://localhost:8182")
            return self.protocol.create_response(
                message,
                status="success",
                payload=store_profile.model_dump(by_alias=True, exclude_none=True)
            )
        
        elif action in [
            A2AAction.SEARCH.value,
            A2AAction.GET_PRODUCTS.value,
            A2AAction.CREATE_ORDER.value,
            A2AAction.RECOMMEND.value
        ]:
            # Delegar para Store Agents
            result = await store_agent_runner.process_a2a_request(
                session_id=session_id,
                agent_id=message.agent_id or "unknown",
                action=action,
                payload=payload
            )
            
            return self.protocol.create_response(
                message,
                status=result.get("status", "success"),
                payload=result.get("data", {})
            )
        
        elif action == A2AAction.GET_CATEGORIES.value:
            from ...db.products import products_repo
            books = await products_repo.get_all()
            categories = list(set(b.category for b in books))
            
            return self.protocol.create_response(
                message,
                status="success",
                payload={"categories": sorted(categories)}
            )
        
        else:
            return self.protocol.create_error(
                message,
                f"Unknown action: {action}"
            )


# Handler global
a2a_handler = A2AHandler()
