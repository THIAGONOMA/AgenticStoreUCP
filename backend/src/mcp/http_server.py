"""Servidor HTTP para MCP (alternativa ao SSE/stdio)."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import structlog

from .server import mcp_server, list_tools, call_tool
from .progressive_disclosure import get_progressive_disclosure

router = APIRouter(prefix="/mcp", tags=["MCP"])
logger = structlog.get_logger()


@router.get("/tools")
async def get_tools(session_id: Optional[str] = Query(None)):
    """
    Listar ferramentas MCP disponiveis.
    
    Se session_id fornecido, aplica progressive disclosure.
    """
    if session_id:
        disclosure = get_progressive_disclosure()
        tools = disclosure.get_available_tools(session_id)
    else:
        tools_list = await list_tools()
        tools = [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema
            }
            for t in tools_list
        ]
    
    return {"tools": tools, "count": len(tools)}


@router.post("/tools/{tool_name}/call")
async def call_mcp_tool(
    tool_name: str,
    request: Dict[str, Any],
    session_id: Optional[str] = Query(None)
):
    """
    Chamar uma ferramenta MCP.
    
    Args:
        tool_name: Nome da ferramenta
        request: {"arguments": {...}}
        session_id: ID da sessao para progressive disclosure
    """
    arguments = request.get("arguments", {})
    
    # Verificar acesso se session_id fornecido
    if session_id:
        disclosure = get_progressive_disclosure()
        context = disclosure.get_context(session_id)
        if not context.can_access(tool_name):
            raise HTTPException(
                status_code=403,
                detail=f"Tool '{tool_name}' not available at current disclosure level"
            )
        disclosure.record_interaction(session_id, tool_name)
    
    try:
        result = await call_tool(tool_name, arguments)
        
        # Resultado vem como lista de TextContent
        if result and len(result) > 0:
            import json
            text = result[0].text
            try:
                data = json.loads(text)
                return {"success": True, "data": data}
            except:
                return {"success": True, "data": text}
        
        return {"success": True, "data": None}
        
    except Exception as e:
        logger.error("MCP tool call failed", tool=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/upgrade")
async def upgrade_disclosure_level(
    session_id: str,
    request: Dict[str, Any]
):
    """
    Fazer upgrade do nivel de disclosure.
    
    Args:
        request: {"level": "shopping" | "advanced"}
    """
    level = request.get("level", "shopping")
    
    disclosure = get_progressive_disclosure()
    new_tools = disclosure.upgrade_level(session_id, level)
    
    return {
        "session_id": session_id,
        "new_level": level,
        "new_tools": new_tools
    }


@router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str):
    """Obter contexto de disclosure de uma sessao."""
    disclosure = get_progressive_disclosure()
    context = disclosure.get_context(session_id)
    
    return {
        "session_id": session_id,
        "current_level": context.current_level,
        "unlocked_tools": list(context.unlocked_tools),
        "interaction_count": context.interaction_count
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Limpar contexto de sessao."""
    disclosure = get_progressive_disclosure()
    disclosure.clear_context(session_id)
    
    return {"message": "Session cleared"}
