// Componente de Carteira Virtual
import { useState, useEffect } from 'react';
import { Wallet as WalletIcon, CreditCard, Plus, RefreshCw, X, TrendingDown, TrendingUp, CheckCircle, XCircle, Clock } from 'lucide-react';
import clsx from 'clsx';
import type { WalletInfo, WalletTransaction } from '../types';

interface WalletProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Wallet({ isOpen, onClose }: WalletProps) {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [addFundsAmount, setAddFundsAmount] = useState('');
  const [showAddFunds, setShowAddFunds] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWallet = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/payments/wallet`);
      if (response.ok) {
        const data = await response.json();
        setWallet(data);
      }
    } catch (err) {
      console.error('Error fetching wallet:', err);
      setError('Erro ao carregar carteira');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const response = await fetch(`/api/payments/transactions`);
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.transactions || []);
      }
    } catch (err) {
      console.error('Error fetching transactions:', err);
    }
  };

  const handleAddFunds = async () => {
    const amount = parseInt(addFundsAmount) * 100; // Convert to cents
    if (isNaN(amount) || amount <= 0) {
      setError('Valor invalido');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/payments/wallet/add-funds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
      });

      if (response.ok) {
        setAddFundsAmount('');
        setShowAddFunds(false);
        await fetchWallet();
      } else {
        const data = await response.json();
        setError(data.detail || 'Erro ao adicionar fundos');
      }
    } catch (err) {
      setError('Erro ao adicionar fundos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchWallet();
      fetchTransactions();
    }
  }, [isOpen]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={16} />;
      case 'failed':
        return <XCircle className="text-red-500" size={16} />;
      case 'refunded':
      case 'partially_refunded':
        return <RefreshCw className="text-blue-500" size={16} />;
      default:
        return <Clock className="text-yellow-500" size={16} />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'Pendente',
      processing: 'Processando',
      completed: 'Concluido',
      failed: 'Falhou',
      refunded: 'Reembolsado',
      partially_refunded: 'Parcial',
    };
    return labels[status] || status;
  };

  const formatCurrency = (amount: number) => {
    return `R$ ${(amount / 100).toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <WalletIcon size={24} />
                Carteira Virtual
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Balance Card */}
            {wallet && (
              <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                <p className="text-sm text-white/80 mb-1">Saldo disponivel</p>
                <p className="text-3xl font-bold">
                  {wallet.balance_formatted}
                </p>
                {wallet.credit_limit > 0 && (
                  <p className="text-sm text-white/70 mt-2">
                    <CreditCard size={14} className="inline mr-1" />
                    Limite: {formatCurrency(wallet.credit_limit)}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-4 max-h-[50vh] overflow-y-auto">
            {/* Error */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg flex justify-between items-center">
                <span>{error}</span>
                <button onClick={() => setError(null)}>
                  <X size={16} />
                </button>
              </div>
            )}

            {/* Add Funds */}
            {showAddFunds ? (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium mb-2">Adicionar fundos</p>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                      R$
                    </span>
                    <input
                      type="number"
                      value={addFundsAmount}
                      onChange={(e) => setAddFundsAmount(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0,00"
                      min="1"
                    />
                  </div>
                  <button
                    onClick={handleAddFunds}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? <RefreshCw className="animate-spin" size={20} /> : 'Adicionar'}
                  </button>
                  <button
                    onClick={() => setShowAddFunds(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddFunds(true)}
                className="w-full mb-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors flex items-center justify-center gap-2"
              >
                <Plus size={20} />
                Adicionar fundos (simulado)
              </button>
            )}

            {/* Transactions */}
            <div>
              <h3 className="font-semibold text-gray-700 mb-3 flex items-center justify-between">
                <span>Transacoes recentes</span>
                <button
                  onClick={() => {
                    fetchWallet();
                    fetchTransactions();
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                  title="Atualizar"
                >
                  <RefreshCw size={16} className={clsx(loading && 'animate-spin')} />
                </button>
              </h3>

              {transactions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CreditCard size={32} className="mx-auto mb-2 opacity-50" />
                  <p>Nenhuma transacao ainda</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {transactions.slice(0, 10).map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <div
                        className={clsx(
                          'p-2 rounded-full',
                          tx.type === 'payment'
                            ? 'bg-red-100'
                            : tx.type === 'refund'
                            ? 'bg-blue-100'
                            : 'bg-green-100'
                        )}
                      >
                        {tx.type === 'payment' ? (
                          <TrendingDown className="text-red-600" size={16} />
                        ) : tx.type === 'refund' ? (
                          <RefreshCw className="text-blue-600" size={16} />
                        ) : (
                          <TrendingUp className="text-green-600" size={16} />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {tx.description || (tx.type === 'payment' ? 'Pagamento' : tx.type === 'refund' ? 'Reembolso' : 'Credito')}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(tx.created_at)}
                        </p>
                      </div>

                      <div className="text-right">
                        <p
                          className={clsx(
                            'font-semibold',
                            tx.type === 'payment' ? 'text-red-600' : 'text-green-600'
                          )}
                        >
                          {tx.type === 'payment' ? '-' : '+'}{formatCurrency(tx.amount)}
                        </p>
                        <div className="flex items-center gap-1 justify-end">
                          {getStatusIcon(tx.status)}
                          <span className="text-xs text-gray-500">
                            {getStatusLabel(tx.status)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t bg-gray-50">
            <p className="text-xs text-gray-500 text-center">
              Carteira simulada para demonstracao do protocolo UCP + AP2
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
