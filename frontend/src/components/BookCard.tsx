// Card de livro no catalogo
import { ShoppingCart, Eye } from 'lucide-react';
import type { Book } from '../types';
import { useStore } from '../store/useStore';
import clsx from 'clsx';

interface BookCardProps {
  book: Book;
  onViewDetails?: (book: Book) => void;
}

export function BookCard({ book, onViewDetails }: BookCardProps) {
  const { addToCart } = useStore();

  const priceFormatted = `R$ ${(book.price / 100).toFixed(2)}`;
  const inStock = book.stock > 0;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      {/* Imagem placeholder */}
      <div className="h-48 bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
        <span className="text-6xl">📚</span>
      </div>

      {/* Conteudo */}
      <div className="p-4">
        {/* Categoria */}
        <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full mb-2">
          {book.category}
        </span>

        {/* Titulo */}
        <h3 className="font-semibold text-gray-900 text-lg mb-1 line-clamp-2">
          {book.title}
        </h3>

        {/* Autor */}
        <p className="text-gray-600 text-sm mb-2">{book.author}</p>

        {/* Descricao */}
        <p className="text-gray-500 text-sm mb-4 line-clamp-2">
          {book.description}
        </p>

        {/* Preco e acoes */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xl font-bold text-green-600">
              {priceFormatted}
            </span>
            <p
              className={clsx(
                'text-xs',
                inStock ? 'text-green-500' : 'text-red-500'
              )}
            >
              {inStock ? `${book.stock} em estoque` : 'Indisponivel'}
            </p>
          </div>

          <div className="flex gap-2">
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(book)}
                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                title="Ver detalhes"
              >
                <Eye size={20} />
              </button>
            )}

            <button
              onClick={() => addToCart(book)}
              disabled={!inStock}
              className={clsx(
                'p-2 rounded-full transition-colors',
                inStock
                  ? 'text-white bg-blue-600 hover:bg-blue-700'
                  : 'text-gray-400 bg-gray-200 cursor-not-allowed'
              )}
              title={inStock ? 'Adicionar ao carrinho' : 'Indisponivel'}
            >
              <ShoppingCart size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
