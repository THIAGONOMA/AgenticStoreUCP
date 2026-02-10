// Header da aplicacao
import { useState, useEffect } from 'react';
import { ShoppingCart, BookOpen, Menu, Wallet as WalletIcon, Receipt } from 'lucide-react';
import { useStore } from '../store/useStore';
import { Wallet } from './Wallet';
import { Transactions } from './Transactions';
import type { WalletInfo } from '../types';

export function Header() {
  const { cartItems, toggleCart, refreshTrigger } = useStore();
  const [walletInfo, setWalletInfo] = useState<WalletInfo | null>(null);
  const [isWalletOpen, setWalletOpen] = useState(false);
  const [isTransactionsOpen, setTransactionsOpen] = useState(false);

  const itemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const fetchWallet = async () => {
    try {
      const response = await fetch(`/api/payments/wallet`);
      if (response.ok) {
        const data = await response.json();
        setWalletInfo(data);
      }
    } catch (err) {
      console.error('Error fetching wallet:', err);
    }
  };

  useEffect(() => {
    fetchWallet();
  }, [refreshTrigger]);

  // Refresh wallet periodically
  useEffect(() => {
    const interval = setInterval(fetchWallet, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="bg-white shadow-sm sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <BookOpen className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Livraria UCP</h1>
                <p className="text-xs text-gray-500 hidden sm:block">
                  Comercio Universal por Agentes
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a
                href="#catalogo"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Catalogo
              </a>
              <a
                href="#categorias"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Categorias
              </a>
              <a
                href="#sobre"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Sobre UCP
              </a>
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Wallet balance */}
              {walletInfo && (
                <button
                  onClick={() => setWalletOpen(true)}
                  className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-full hover:from-blue-100 hover:to-purple-100 transition-colors"
                >
                  <WalletIcon size={18} className="text-blue-600" />
                  <span className="text-sm font-semibold text-gray-700">
                    {walletInfo.balance_formatted}
                  </span>
                </button>
              )}

              {/* Wallet button (mobile) */}
              <button
                onClick={() => setWalletOpen(true)}
                className="sm:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
                title="Carteira Virtual"
              >
                <WalletIcon size={24} />
              </button>

              {/* Transactions button */}
              <button
                onClick={() => setTransactionsOpen(true)}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
                title="Transacoes"
              >
                <Receipt size={24} />
              </button>

              {/* Cart button */}
              <button
                onClick={toggleCart}
                className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ShoppingCart size={24} />
                {itemCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                    {itemCount > 9 ? '9+' : itemCount}
                  </span>
                )}
              </button>

              {/* Mobile menu */}
              <button className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                <Menu size={24} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Modals */}
      <Wallet isOpen={isWalletOpen} onClose={() => setWalletOpen(false)} />
      <Transactions isOpen={isTransactionsOpen} onClose={() => setTransactionsOpen(false)} />
    </>
  );
}
