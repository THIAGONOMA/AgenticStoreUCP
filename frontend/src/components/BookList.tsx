// Lista de livros com busca e filtro
import { useState, useEffect, useCallback } from 'react';
import { Search, Filter } from 'lucide-react';
import { BookCard } from './BookCard';
import { useStore } from '../store/useStore';
import type { Book } from '../types';

export function BookList() {
  const [books, setBooks] = useState<Book[]>([]);
  const [filteredBooks, setFilteredBooks] = useState<Book[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  // Observar trigger de refresh (atualiza apos checkout)
  const refreshTrigger = useStore((state) => state.refreshTrigger);

  // Funcao para buscar livros
  const fetchBooks = useCallback(async () => {
    try {
      const response = await fetch('/api/books');
      const data = await response.json();
      setBooks(data.books || []);
      setFilteredBooks(data.books || []);

      // Extrair categorias unicas
      const cats = [...new Set(data.books?.map((b: Book) => b.category) || [])];
      setCategories(cats as string[]);
    } catch (err) {
      console.error('Failed to fetch books:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Carregar livros na montagem e quando refreshTrigger mudar
  useEffect(() => {
    fetchBooks();
  }, [fetchBooks, refreshTrigger]);

  // Filtrar livros
  useEffect(() => {
    let result = books;

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (book) =>
          book.title.toLowerCase().includes(term) ||
          book.author.toLowerCase().includes(term) ||
          book.description.toLowerCase().includes(term)
      );
    }

    if (selectedCategory) {
      result = result.filter((book) => book.category === selectedCategory);
    }

    setFilteredBooks(result);
  }, [books, searchTerm, selectedCategory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Barra de busca e filtros */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        {/* Busca */}
        <div className="relative flex-1">
          <Search
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            size={20}
          />
          <input
            type="text"
            placeholder="Buscar livros..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filtro por categoria */}
        <div className="relative">
          <Filter
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            size={20}
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
          >
            <option value="">Todas as categorias</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Contador */}
      <p className="text-gray-600 mb-4">
        {filteredBooks.length} livro{filteredBooks.length !== 1 ? 's' : ''}{' '}
        encontrado{filteredBooks.length !== 1 ? 's' : ''}
      </p>

      {/* Grid de livros */}
      {filteredBooks.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredBooks.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">
            Nenhum livro encontrado com os filtros selecionados.
          </p>
        </div>
      )}
    </div>
  );
}
