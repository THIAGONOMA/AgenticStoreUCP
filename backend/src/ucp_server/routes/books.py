"""Routes para livros."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ...db.products import products_repo
from ..models.book import Book

router = APIRouter()


@router.get("", response_model=List[Book])
async def list_books(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Listar todos os livros."""
    return await products_repo.get_all(limit=limit, offset=offset)


@router.get("/search", response_model=List[Book])
async def search_books(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    limit: int = Query(default=20, le=50),
):
    """Buscar livros por termo."""
    return await products_repo.search(query=q, category=category, limit=limit)


@router.get("/categories")
async def list_categories():
    """Listar categorias disponiveis."""
    books = await products_repo.get_all(limit=1000)
    categories = list(set(b.category for b in books if b.category))
    return {"categories": sorted(categories)}


@router.get("/{book_id}", response_model=Book)
async def get_book(book_id: str):
    """Obter livro por ID."""
    book = await products_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
