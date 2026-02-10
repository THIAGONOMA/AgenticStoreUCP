"""Modelo de Livro."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Book(BaseModel):
    """Livro no catalogo."""
    id: str
    title: str
    author: str
    description: Optional[str] = None
    price: int  # em centavos
    category: Optional[str] = None
    isbn: Optional[str] = None
    stock: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookCreate(BaseModel):
    """Dados para criar um livro."""
    title: str
    author: str
    description: Optional[str] = None
    price: int
    category: Optional[str] = None
    isbn: Optional[str] = None
    stock: int = 0


class BookSearch(BaseModel):
    """Resultado de busca de livros."""
    books: list[Book]
    total: int
    page: int = 1
    per_page: int = 20
