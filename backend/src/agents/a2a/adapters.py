"""
Adapters para compatibilidade entre implementação customizada e SDK oficial do A2A.

Este módulo fornece funções para converter entre os modelos customizados
e os modelos do SDK oficial (a2a-sdk).
"""

from typing import Optional, List, Dict, Any
import uuid
import time

# Modelos customizados (atuais)
from .protocol import (
    A2AMessage,
    A2AMessageType,
    A2AAction,
    AgentProfile,
)

# SDK oficial
try:
    from a2a.types import (
        AgentCard,
        AgentSkill,
        AgentCapabilities,
        Message,
        Task,
        TaskState,
        TaskStatus,
        TextPart,
        Part,
        Role,
        Artifact,
    )
    A2A_SDK_AVAILABLE = True
except ImportError:
    A2A_SDK_AVAILABLE = False
    AgentCard = None
    Message = None
    Task = None


def is_a2a_sdk_available() -> bool:
    """Verifica se o SDK oficial A2A está disponível."""
    return A2A_SDK_AVAILABLE


# =============================================================================
# Conversores: Local -> SDK
# =============================================================================

def local_agent_profile_to_sdk(profile: AgentProfile) -> Optional[Dict[str, Any]]:
    """Converte AgentProfile local para formato AgentCard do SDK."""
    if not A2A_SDK_AVAILABLE:
        return None
    
    # Converter capabilities para skills
    skills = []
    for cap in profile.capabilities:
        if isinstance(cap, str):
            skills.append({
                "id": cap,
                "name": cap,
                "description": f"Capability: {cap}",
            })
        elif isinstance(cap, dict):
            skills.append({
                "id": cap.get("name", cap.get("id", "unknown")),
                "name": cap.get("name", "Unknown"),
                "description": cap.get("description", ""),
            })
    
    return {
        "name": profile.name,
        "version": profile.version,
        "url": f"http://localhost:8000/a2a",  # URL padrão
        "skills": skills,
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
        },
    }


def local_message_to_sdk(message: A2AMessage) -> Optional[Dict[str, Any]]:
    """Converte A2AMessage local para formato Message do SDK."""
    if not A2A_SDK_AVAILABLE:
        return None
    
    # Determinar role baseado no tipo de mensagem
    role = "user" if message.type == A2AMessageType.REQUEST else "agent"
    
    # Criar parte de texto com o conteúdo
    content = message.payload.get("content", message.payload.get("message", ""))
    if not content and message.action:
        content = f"Action: {message.action}"
    
    return {
        "message_id": message.message_id,
        "role": role,
        "parts": [{"kind": "text", "text": content}],
        "metadata": {
            "action": message.action,
            "agent_id": message.agent_id,
            "timestamp": message.timestamp,
            "original_type": message.type.value if hasattr(message.type, 'value') else str(message.type),
        },
    }


def local_message_to_task(message: A2AMessage, task_id: str = None) -> Optional[Dict[str, Any]]:
    """Converte A2AMessage local para formato Task do SDK."""
    if not A2A_SDK_AVAILABLE:
        return None
    
    # Mapear status
    status_map = {
        "success": "completed",
        "error": "failed",
        "pending": "working",
        "connected": "completed",
        "disconnected": "completed",
    }
    
    task_state = status_map.get(message.status, "working") if message.status else "submitted"
    
    return {
        "id": task_id or message.message_id,
        "status": {
            "state": task_state,
            "message": message.error if message.error else None,
        },
        "metadata": {
            "action": message.action,
            "agent_id": message.agent_id,
        },
        "artifacts": [],
        "history": [],
    }


# =============================================================================
# Conversores: SDK -> Local
# =============================================================================

def sdk_agent_card_to_local(card_data: Dict[str, Any]) -> AgentProfile:
    """Converte AgentCard do SDK para AgentProfile local."""
    # Converter skills para capabilities
    capabilities = []
    for skill in card_data.get("skills", []):
        if isinstance(skill, dict):
            capabilities.append(skill.get("name", skill.get("id", "unknown")))
        else:
            capabilities.append(str(skill))
    
    return AgentProfile(
        agent_id=card_data.get("name", "unknown"),
        name=card_data.get("name", "Unknown Agent"),
        version=card_data.get("version", "1.0"),
        capabilities=capabilities,
    )


def sdk_message_to_local(message_data: Dict[str, Any]) -> A2AMessage:
    """Converte Message do SDK para A2AMessage local."""
    # Determinar tipo baseado no role
    role = message_data.get("role", "user")
    msg_type = A2AMessageType.REQUEST if role == "user" else A2AMessageType.RESPONSE
    
    # Extrair texto das partes
    content = ""
    for part in message_data.get("parts", []):
        if isinstance(part, dict) and part.get("kind") == "text":
            content += part.get("text", "")
        elif hasattr(part, "text"):
            content += part.text
    
    metadata = message_data.get("metadata", {})
    
    return A2AMessage(
        type=msg_type,
        message_id=message_data.get("message_id", str(uuid.uuid4())),
        timestamp=metadata.get("timestamp", int(time.time())),
        agent_id=metadata.get("agent_id"),
        action=metadata.get("action"),
        payload={"content": content, "message": content},
        status="success",
    )


def sdk_task_to_local(task_data: Dict[str, Any]) -> A2AMessage:
    """Converte Task do SDK para A2AMessage local."""
    status_data = task_data.get("status", {})
    state = status_data.get("state", "unknown")
    
    # Mapear estado para status local
    status_map = {
        "submitted": "pending",
        "working": "pending",
        "input-required": "pending",
        "completed": "success",
        "canceled": "error",
        "failed": "error",
        "rejected": "error",
        "auth-required": "error",
        "unknown": "pending",
    }
    
    # Extrair conteúdo do histórico ou artefatos
    content = ""
    for artifact in task_data.get("artifacts", []):
        if isinstance(artifact, dict):
            for part in artifact.get("parts", []):
                if isinstance(part, dict) and part.get("kind") == "text":
                    content += part.get("text", "")
    
    metadata = task_data.get("metadata", {})
    
    return A2AMessage(
        type=A2AMessageType.RESPONSE,
        message_id=task_data.get("id", str(uuid.uuid4())),
        timestamp=int(time.time()),
        agent_id=metadata.get("agent_id"),
        action=metadata.get("action"),
        payload={"content": content, "task_state": state},
        status=status_map.get(state, "pending"),
        error=status_data.get("message") if state in ["failed", "rejected", "canceled"] else None,
    )


# =============================================================================
# Helpers para criar objetos SDK
# =============================================================================

def create_agent_card(
    name: str,
    description: str = "",
    version: str = "1.0.0",
    url: str = "http://localhost:8000/a2a",
    skills: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Cria um AgentCard compatível com o SDK."""
    return {
        "name": name,
        "description": description,
        "version": version,
        "url": url,
        "protocol_version": "0.2.1",
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
        },
        "skills": skills or [],
    }


def create_text_message(
    content: str,
    role: str = "agent",
    message_id: str = None,
    task_id: str = None,
) -> Dict[str, Any]:
    """Cria uma Message de texto compatível com o SDK."""
    return {
        "message_id": message_id or str(uuid.uuid4()),
        "role": role,
        "kind": "message",
        "parts": [{"kind": "text", "text": content}],
        "task_id": task_id,
    }


def create_task_response(
    task_id: str,
    state: str = "completed",
    content: str = None,
    error: str = None,
) -> Dict[str, Any]:
    """Cria uma resposta de Task compatível com o SDK."""
    artifacts = []
    if content:
        artifacts.append({
            "artifact_id": str(uuid.uuid4()),
            "parts": [{"kind": "text", "text": content}],
        })
    
    return {
        "id": task_id,
        "status": {
            "state": state,
            "message": error,
        },
        "artifacts": artifacts,
        "history": [],
    }


# =============================================================================
# Store Agent Card
# =============================================================================

def get_store_agent_card() -> Dict[str, Any]:
    """Retorna o AgentCard da loja para discovery A2A."""
    return create_agent_card(
        name="Livraria Virtual UCP",
        description="Agente de e-commerce para livraria virtual com suporte a UCP e A2A",
        version="1.0.0",
        url="http://localhost:8000/a2a",
        skills=[
            {
                "id": "search",
                "name": "Buscar Livros",
                "description": "Busca livros no catálogo por título, autor ou categoria",
                "input_modes": ["text"],
                "output_modes": ["text"],
            },
            {
                "id": "recommend",
                "name": "Recomendar Livros",
                "description": "Recomenda livros baseado em preferências ou histórico",
                "input_modes": ["text"],
                "output_modes": ["text"],
            },
            {
                "id": "checkout",
                "name": "Processar Compra",
                "description": "Processa compras via UCP com suporte a AP2",
                "input_modes": ["text"],
                "output_modes": ["text"],
            },
            {
                "id": "get_categories",
                "name": "Listar Categorias",
                "description": "Lista todas as categorias de livros disponíveis",
                "input_modes": ["text"],
                "output_modes": ["text"],
            },
        ],
    )
