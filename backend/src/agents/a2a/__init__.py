"""A2A Protocol - Agent-to-Agent Communication."""
from .protocol import (
    A2AMessage,
    A2AMessageType,
    A2AAction,
    A2AProtocol,
    AgentProfile,
    a2a_protocol
)
from .handler import A2AHandler, a2a_handler

# Adapters para SDK oficial
from .adapters import (
    is_a2a_sdk_available,
    local_agent_profile_to_sdk,
    local_message_to_sdk,
    local_message_to_task,
    sdk_agent_card_to_local,
    sdk_message_to_local,
    sdk_task_to_local,
    create_agent_card,
    create_text_message,
    create_task_response,
    get_store_agent_card,
)

# Tipos do SDK oficial (se disponível)
try:
    from a2a.types import (
        AgentCard,
        Message as SdkMessage,
        Task as SdkTask,
        TaskState,
        TaskStatus,
        TextPart,
        Role,
    )
    A2A_SDK_AVAILABLE = True
except ImportError:
    AgentCard = None
    SdkMessage = None
    SdkTask = None
    TaskState = None
    TaskStatus = None
    TextPart = None
    Role = None
    A2A_SDK_AVAILABLE = False

__all__ = [
    # Tipos locais
    "A2AMessage",
    "A2AMessageType",
    "A2AAction",
    "A2AProtocol",
    "AgentProfile",
    "a2a_protocol",
    "A2AHandler",
    "a2a_handler",
    # Adapters
    "is_a2a_sdk_available",
    "local_agent_profile_to_sdk",
    "local_message_to_sdk",
    "sdk_agent_card_to_local",
    "sdk_message_to_local",
    "create_agent_card",
    "create_text_message",
    "create_task_response",
    "get_store_agent_card",
    # SDK (se disponível)
    "AgentCard",
    "SdkMessage",
    "SdkTask",
    "TaskState",
    "TaskStatus",
    "A2A_SDK_AVAILABLE",
]
