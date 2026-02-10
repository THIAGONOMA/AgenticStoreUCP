"""
MCP Server - Model Context Protocol para a Livraria.

Este servidor expoe ferramentas MCP que permitem a agentes de IA
interagir com o catalogo da livraria de forma estruturada.

Ferramentas disponiveis:
- search_books: Buscar livros por termo
- get_book_details: Detalhes de um livro
- list_categories: Listar categorias
- get_books_by_category: Livros por categoria
- check_discount_code: Verificar cupom
- calculate_cart: Calcular carrinho
- get_recommendations: Recomendacoes
"""
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import structlog
import json

from .tools import get_all_tools, call_tool_handler

logger = structlog.get_logger()

# Criar instancia do servidor MCP
mcp_server = Server("livraria-mcp")


@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """
    Listar ferramentas disponiveis.
    
    Retorna todas as ferramentas MCP registradas,
    organizadas em modulos:
    - search: Busca de livros
    - catalog: Categorias
    - cart: Carrinho e descontos
    - recommendations: Recomendacoes
    """
    return get_all_tools()


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Executar uma ferramenta MCP.
    
    Args:
        name: Nome da ferramenta
        arguments: Argumentos para a ferramenta
        
    Returns:
        Lista com TextContent contendo o resultado em JSON
    """
    logger.info("MCP tool called", tool=name, arguments=arguments)
    
    try:
        result = await call_tool_handler(name, arguments)
        
        return [TextContent(
            type="text", 
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        logger.error("MCP tool error", tool=name, error=str(e))
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Exportar para uso externo
__all__ = ["mcp_server", "list_tools", "call_tool"]
