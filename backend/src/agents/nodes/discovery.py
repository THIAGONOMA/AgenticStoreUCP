"""Discovery Node - Busca de livros e informacoes."""
from typing import Dict, Any, List, Optional
import structlog
import json

from ..state import StoreAgentState, Message
from ..llm import generate_response_with_llm, is_llm_enabled, get_llm
from ...db.products import products_repo

logger = structlog.get_logger()


# Prompt para extracao inteligente de termos de busca
SEARCH_EXTRACTION_PROMPT = """Voce e um assistente de busca de uma livraria.
Analise a mensagem do usuario e extraia os termos de busca relevantes.

IMPORTANTE:
- Extraia palavras-chave para buscar livros (titulos, autores, temas, generos)
- Normalize a escrita (ex: "Python" ou "python" sao equivalentes)
- Remova stopwords e termos irrelevantes
- Se o usuario errou a escrita, tente corrigir (ex: "pithon" -> "python", "testes" -> "test")
- Retorne multiplas variantes quando houver duvida

Mensagem: {message}

Responda APENAS em JSON no formato:
{{"search_terms": ["termo1", "termo2", ...], "possible_categories": ["cat1", ...]}}"""


SEMANTIC_MATCH_PROMPT = """Voce e um assistente de uma livraria virtual.
O usuario buscou: "{query}"

Aqui estao os livros disponiveis no catalogo:
{books_list}

Selecione os livros que MELHOR correspondem a busca do usuario.
Considere:
- Correspondencia de titulo (mesmo parcial ou com erros de digitacao)
- Correspondencia de autor
- Correspondencia de tema/categoria
- Sinonimos e termos relacionados

Responda APENAS em JSON no formato:
{{"matched_ids": ["id1", "id2", ...]}}

Se nenhum livro corresponder, retorne: {{"matched_ids": []}}"""


async def discovery_node(state: StoreAgentState) -> Dict[str, Any]:
    """
    Discovery Node - Busca livros e fornece informacoes.
    
    Responsavel por:
    - Buscar livros por termo
    - Listar categorias
    - Fornecer detalhes de livros
    - Responder perguntas sobre a loja
    """
    logger.info("Discovery node processing", session=state["session_id"])
    
    intent = state.get("current_intent", "help")
    messages = []
    search_results = []
    
    # Verificar se e requisicao A2A
    if state.get("a2a_request"):
        return await _handle_a2a_request(state)
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["type"] == "user"]
    last_message = user_messages[-1]["content"] if user_messages else ""
    
    if intent == "help":
        fallback = _get_help_message()
        response = await generate_response_with_llm(
            context="Usuario chegou na loja ou pediu ajuda",
            data={"message": "Saudar e explicar o que a loja oferece"},
            fallback_response=fallback
        )
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "discovery", "llm_used": is_llm_enabled()}
        ))
    
    elif intent == "search":
        # Busca inteligente com LLM
        books = await _smart_search(last_message)
        
        if books:
            search_results = [
                {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "price": b.price,
                    "price_formatted": f"R$ {b.price / 100:.2f}",
                    "category": b.category
                }
                for b in books[:5]
            ]
            
            fallback = _format_search_results(search_results)
            response = await generate_response_with_llm(
                context=f"Usuario buscou livros com '{last_message}'",
                data={"books": search_results},
                fallback_response=fallback
            )
        else:
            # Sem resultados - listar categorias como alternativa
            all_books = await products_repo.get_all()
            categories = list(set(b.category for b in all_books))
            
            fallback = f"Nao encontrei livros correspondentes. Temos estas categorias: {', '.join(sorted(categories))}. Quer ver alguma delas?"
            response = await generate_response_with_llm(
                context=f"Busca por '{last_message}' nao retornou resultados",
                data={"message": "Sugerir categorias disponiveis", "categories": sorted(categories)},
                fallback_response=fallback
            )
        
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "discovery", "results_count": len(search_results), "llm_used": is_llm_enabled()}
        ))
    
    return {
        "messages": messages,
        "search_results": search_results,
        "search_query": _extract_search_term_simple(last_message) if intent == "search" else None,
        "next_agent": None  # Fim do fluxo
    }


async def _handle_a2a_request(state: StoreAgentState) -> Dict[str, Any]:
    """Processar requisicao A2A."""
    request = state["a2a_request"]
    action = request.get("action", "")
    payload = request.get("payload", {})
    
    logger.info("A2A Discovery request", action=action)
    
    if action == "search":
        query = payload.get("query", "")
        books = await products_repo.search(query) if query else await products_repo.get_all()
        
        return {
            "search_results": [
                {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "price": b.price,
                    "category": b.category,
                    "stock": b.stock
                }
                for b in books[:20]
            ],
            "next_agent": None
        }
    
    elif action == "get_products":
        category = payload.get("category")
        if category:
            books = await products_repo.get_by_category(category)
        else:
            books = await products_repo.get_all()
        
        return {
            "search_results": [
                {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "price": b.price,
                    "category": b.category
                }
                for b in books
            ],
            "next_agent": None
        }
    
    return {"next_agent": None}


async def _smart_search(message: str) -> List:
    """
    Busca inteligente usando LLM para interpretar a intencao do usuario.
    
    Estrategia:
    1. Tentar extrair termos de busca com LLM
    2. Buscar com cada termo variante
    3. Tentar busca fuzzy por palavras
    4. Se nao encontrar, fazer matching semantico com todos os livros
    """
    logger.info("Smart search starting", message=message)
    
    # Passo 1: Extrair termos de busca inteligentemente
    search_terms = await _extract_search_terms_with_llm(message)
    
    # Adicionar correcoes comuns de erros de digitacao
    corrected_terms = _apply_common_corrections(search_terms)
    all_terms = list(set(search_terms + corrected_terms))
    logger.debug("Search terms with corrections", terms=all_terms)
    
    # Passo 2: Buscar com cada termo
    found_books = []
    seen_ids = set()
    
    for term in all_terms:
        books = await products_repo.search(term)
        for book in books:
            if book.id not in seen_ids:
                found_books.append(book)
                seen_ids.add(book.id)
    
    if found_books:
        logger.info("Smart search found books via terms", count=len(found_books))
        return found_books
    
    # Passo 3: Tentar busca fuzzy por palavras individuais
    logger.debug("No exact results, trying fuzzy search")
    fuzzy_books = await products_repo.fuzzy_search(message)
    if fuzzy_books:
        logger.info("Smart search found books via fuzzy search", count=len(fuzzy_books))
        return fuzzy_books
    
    # Passo 4: Se nao encontrou, fazer matching semantico
    logger.debug("No fuzzy results, trying semantic matching")
    all_books = await products_repo.get_all()
    matched_books = await _semantic_match(message, all_books)
    
    if matched_books:
        logger.info("Smart search found books via semantic matching", count=len(matched_books))
        return matched_books
    
    # Passo 5: Fallback - busca simples com termo original
    simple_term = _extract_search_term_simple(message)
    if simple_term:
        books = await products_repo.search(simple_term)
        if books:
            return books
    
    return []


def _apply_common_corrections(terms: List[str]) -> List[str]:
    """Aplicar correcoes comuns de erros de digitacao."""
    corrections = {
        # Erros comuns de digitacao em portugues
        "atumatizado": "automatizado",
        "atumatizados": "automatizados",
        "automatisado": "automatizado",
        "automatisados": "automatizados",
        "testes": "test",
        "teste": "test",
        "pithon": "python",
        "piton": "python",
        "pytho": "python",
        "javascrip": "javascript",
        "javascritp": "javascript",
        "javasript": "javascript",
        "programacao": "programação",
        "programaçao": "programação",
        "codigo": "código",
        "codgo": "código",
        "limpo": "clean",
        "clena": "clean",
        "clen": "clean",
        "desing": "design",
        "desin": "design",
        "paterns": "patterns",
        "patern": "pattern",
        "padrao": "pattern",
        "padroes": "patterns",
        "arquitetura": "architecture",
        "arquiterura": "architecture",
        "refatoracao": "refactoring",
        "refatoraçao": "refactoring",
        "algoritmo": "algorithm",
        "algorítmo": "algorithm",
        "algoritimos": "algorithms",
        "estrutura": "structure",
        "estruturas": "structures",
        "dados": "data",
        "banco": "database",
        "agil": "agile",
        "ágil": "agile",
        "devops": "devops",
        "dev ops": "devops",
    }
    
    corrected = []
    for term in terms:
        term_lower = term.lower()
        # Verificar se o termo tem correcao
        if term_lower in corrections:
            corrected.append(corrections[term_lower])
        # Verificar palavras individuais
        words = term_lower.split()
        for word in words:
            if word in corrections:
                corrected.append(corrections[word])
    
    return list(set(corrected))


async def _extract_search_terms_with_llm(message: str) -> List[str]:
    """Extrair termos de busca usando LLM."""
    llm = get_llm()
    
    # Sempre gerar variantes basicas primeiro
    basic_terms = _generate_search_variants(message)
    
    if not llm:
        return basic_terms
    
    try:
        prompt = SEARCH_EXTRACTION_PROMPT.format(message=message)
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # Extrair JSON da resposta
        if "{" in content:
            json_str = content[content.find("{"):content.rfind("}")+1]
            data = json.loads(json_str)
            llm_terms = data.get("search_terms", [])
            categories = data.get("possible_categories", [])
            
            # Combinar com termos basicos
            all_terms = list(set(basic_terms + llm_terms + categories))
            return all_terms[:10]  # Limitar a 10 termos
    
    except Exception as e:
        logger.warning("LLM term extraction failed", error=str(e))
    
    return basic_terms


async def _semantic_match(query: str, books: List) -> List:
    """Usar LLM para encontrar livros semanticamente relevantes."""
    llm = get_llm()
    
    if not llm or not books:
        return []
    
    try:
        # Formatar lista de livros para o prompt
        books_list = "\n".join([
            f"- ID: {b.id} | Titulo: {b.title} | Autor: {b.author} | Categoria: {b.category}"
            for b in books[:30]  # Limitar para nao exceder contexto
        ])
        
        prompt = SEMANTIC_MATCH_PROMPT.format(query=query, books_list=books_list)
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # Extrair JSON
        if "{" in content:
            json_str = content[content.find("{"):content.rfind("}")+1]
            data = json.loads(json_str)
            matched_ids = data.get("matched_ids", [])
            
            # Retornar livros correspondentes
            id_to_book = {b.id: b for b in books}
            return [id_to_book[bid] for bid in matched_ids if bid in id_to_book]
    
    except Exception as e:
        logger.warning("Semantic matching failed", error=str(e))
    
    return []


def _generate_search_variants(message: str) -> List[str]:
    """Gerar variantes de busca a partir da mensagem."""
    # Limpar a mensagem
    clean = message.lower().strip()
    
    # Stop words expandidas
    stop_words = {
        "buscar", "procurar", "encontrar", "quero", "preciso", "gostaria",
        "livro", "livros", "de", "sobre", "um", "uma", "o", "a", "os", "as",
        "me", "mostre", "mostra", "tem", "voce", "algum", "alguns", "alguma",
        "por", "para", "com", "em", "no", "na", "nos", "nas", "do", "da",
        "favor", "poderia", "pode", "consegue", "quer", "queria"
    }
    
    words = clean.split()
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    
    variants = []
    
    # Adicionar palavras individuais
    variants.extend(filtered)
    
    # Adicionar combinacao de todas as palavras filtradas
    if len(filtered) > 1:
        variants.append(" ".join(filtered))
    
    # Adicionar variantes com capitalizacao diferente
    for word in filtered:
        variants.append(word.capitalize())
        variants.append(word.upper())
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique = []
    for v in variants:
        if v.lower() not in seen:
            seen.add(v.lower())
            unique.append(v)
    
    return unique


def _extract_search_term_simple(message: str) -> str:
    """Extrair termo de busca simples (fallback)."""
    stop_words = {
        "buscar", "procurar", "encontrar", "quero", "preciso",
        "livro", "livros", "de", "sobre", "um", "uma", "o", "a",
        "me", "mostre", "mostra", "tem", "voce"
    }
    
    words = message.lower().split()
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    
    return " ".join(filtered) if filtered else ""


def _get_help_message() -> str:
    """Mensagem de ajuda."""
    return """Ola! Bem-vindo a Livraria Virtual! 📚

Posso te ajudar com:
• Buscar livros - Ex: "Buscar livros de Python"
• Ver categorias - Ex: "Quais categorias voces tem?"
• Recomendacoes - Ex: "Me recomende livros de ficcao"
• Carrinho - Ex: "Adicionar ao carrinho" ou "Ver meu carrinho"
• Finalizar compra - Ex: "Quero finalizar minha compra"

O que voce gostaria de fazer?"""


def _format_search_results(results: list) -> str:
    """Formatar resultados de busca."""
    if not results:
        return "Nenhum livro encontrado."
    
    lines = ["Encontrei estes livros para voce:\n"]
    
    for i, book in enumerate(results, 1):
        lines.append(
            f"**{i}. {book['title']}**\n"
            f"   Autor: {book['author']}\n"
            f"   Preco: {book['price_formatted']}\n"
        )
    
    lines.append("\nPara adicionar ao carrinho, digite: **adicionar 1** (ou o numero do livro desejado)")
    
    return "\n".join(lines)


def _format_categories(categories: list) -> str:
    """Formatar lista de categorias."""
    lines = ["Temos livros nestas categorias:\n"]
    
    for cat in sorted(categories):
        lines.append(f"• {cat}")
    
    lines.append("\nQual categoria te interessa?")
    
    return "\n".join(lines)
