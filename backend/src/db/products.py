"""Repository de produtos (livros)."""
from typing import Optional, List
from datetime import datetime
import uuid

from .database import products_db
from ..ucp_server.models.book import Book, BookCreate


class ProductsRepository:
    """Repository para operacoes com livros."""
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Book]:
        """Listar todos os livros."""
        rows = await products_db.fetch_all(
            "SELECT * FROM books ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [Book(**dict(row)) for row in rows]
    
    async def get_by_id(self, book_id: str) -> Optional[Book]:
        """Buscar livro por ID."""
        row = await products_db.fetch_one(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        )
        return Book(**dict(row)) if row else None
    
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Book]:
        """Buscar livros por termo (case-insensitive)."""
        # Normalizar query para lowercase
        query_lower = query.lower().strip()
        
        # Busca case-insensitive usando LOWER()
        sql = """
            SELECT * FROM books
            WHERE (
                LOWER(title) LIKE LOWER(?) OR 
                LOWER(author) LIKE LOWER(?) OR 
                LOWER(description) LIKE LOWER(?) OR
                LOWER(category) LIKE LOWER(?)
            )
        """
        params = [f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%"]
        
        if category:
            sql += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        
        sql += " ORDER BY title LIMIT ?"
        params.append(limit)
        
        rows = await products_db.fetch_all(sql, tuple(params))
        return [Book(**dict(row)) for row in rows]
    
    async def fuzzy_search(self, query: str, limit: int = 20) -> List[Book]:
        """
        Busca fuzzy - busca por palavras individuais e retorna matches parciais.
        Util quando a busca exata nao encontra resultados.
        """
        # Separar palavras da query
        words = [w.lower().strip() for w in query.split() if len(w) > 2]
        
        if not words:
            return []
        
        # Construir SQL com OR para cada palavra
        conditions = []
        params = []
        
        for word in words:
            conditions.append("""
                (LOWER(title) LIKE ? OR 
                 LOWER(author) LIKE ? OR 
                 LOWER(description) LIKE ? OR
                 LOWER(category) LIKE ?)
            """)
            params.extend([f"%{word}%"] * 4)
        
        sql = f"""
            SELECT *, (
                {' + '.join([f"(CASE WHEN LOWER(title) LIKE '%{w}%' THEN 2 ELSE 0 END)" for w in words])}
            ) as relevance
            FROM books
            WHERE {' OR '.join(conditions)}
            ORDER BY relevance DESC, title
            LIMIT ?
        """
        params.append(limit)
        
        rows = await products_db.fetch_all(sql, tuple(params))
        return [Book(**{k: v for k, v in dict(row).items() if k != 'relevance'}) for row in rows]
    
    async def get_by_category(self, category: str, limit: int = 50) -> List[Book]:
        """Listar livros por categoria."""
        rows = await products_db.fetch_all(
            "SELECT * FROM books WHERE category = ? ORDER BY title LIMIT ?",
            (category, limit)
        )
        return [Book(**dict(row)) for row in rows]
    
    async def create(self, book: BookCreate) -> Book:
        """Criar novo livro."""
        book_id = f"book_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        
        await products_db.execute(
            """
            INSERT INTO books (id, title, author, description, price, category, isbn, stock, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_id,
                book.title,
                book.author,
                book.description,
                book.price,
                book.category,
                book.isbn,
                book.stock,
                now,
                now,
            )
        )
        
        return await self.get_by_id(book_id)
    
    async def update_stock(self, book_id: str, quantity: int) -> bool:
        """Atualizar estoque do livro."""
        await products_db.execute(
            "UPDATE books SET stock = stock + ?, updated_at = ? WHERE id = ?",
            (quantity, datetime.utcnow(), book_id)
        )
        return True
    
    async def count(self) -> int:
        """Contar total de livros."""
        row = await products_db.fetch_one("SELECT COUNT(*) as count FROM books")
        return row["count"] if row else 0


# Instancia global
products_repo = ProductsRepository()
