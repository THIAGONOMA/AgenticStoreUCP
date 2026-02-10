"""Script para importar catalogo de livros e cupons."""
import csv
import asyncio
from pathlib import Path

from .database import init_databases, products_db
from .products import products_repo
from .discounts import discounts_repo, DiscountCode
from ..ucp_server.models.book import BookCreate


async def import_books():
    """Importar livros do CSV."""
    csv_path = Path(__file__).parent.parent.parent / "data" / "books_catalog.csv"
    
    if not csv_path.exists():
        print(f"Arquivo nao encontrado: {csv_path}")
        return
    
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Verificar se ja existe
            existing = await products_repo.get_by_id(row["id"])
            if existing:
                continue
            
            # Inserir diretamente com ID especifico
            await products_db.execute(
                """
                INSERT INTO books (id, title, author, description, price, category, isbn, stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["title"],
                    row["author"],
                    row["description"],
                    int(row["price"]),
                    row["category"],
                    row["isbn"],
                    int(row["stock"]),
                )
            )
            count += 1
            print(f"  + {row['title']}")
    
    print(f"\nImportados {count} livros")


async def import_discounts():
    """Importar cupons do CSV."""
    csv_path = Path(__file__).parent.parent.parent / "data" / "discount_codes.csv"
    
    if not csv_path.exists():
        print(f"Arquivo nao encontrado: {csv_path}")
        return
    
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Verificar se ja existe
            existing = await discounts_repo.get_by_code(row["code"])
            if existing:
                continue
            
            discount = DiscountCode(
                code=row["code"],
                title=row["title"],
                type=row["type"],
                value=int(row["value"]),
                min_purchase=int(row["min_purchase"]) if row["min_purchase"] else 0,
                max_uses=int(row["max_uses"]) if row["max_uses"] else None,
            )
            await discounts_repo.create(discount)
            count += 1
            print(f"  + {row['code']}: {row['title']}")
    
    print(f"\nImportados {count} cupons")


async def main():
    """Executar importacao completa."""
    print("=== Inicializando bancos de dados ===\n")
    await init_databases()
    
    print("\n=== Importando livros ===\n")
    await products_db.connect()
    await import_books()
    await products_db.disconnect()
    
    print("\n=== Importando cupons ===\n")
    await products_db.connect()
    await import_discounts()
    await products_db.disconnect()
    
    print("\n=== Importacao completa! ===")


if __name__ == "__main__":
    asyncio.run(main())
