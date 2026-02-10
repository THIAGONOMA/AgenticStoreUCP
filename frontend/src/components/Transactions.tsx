// Componente de Historico de Transacoes PSP
import { useState, useEffect } from 'react';
import { Receipt, RefreshCw, X, CheckCircle, XCircle, Clock, Undo2, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';
import type { WalletTransaction } from '../types';

interface TransactionsProps {
  isOpen: boolean;
  onClose: () => void;
}

interface PSPTransaction {
  id: string;
  checkout_session_id?: string;
  wallet_id: string;
  amount: number;
  currency: string;
  status: string;
  mandate_id?: string;
  description?: string;
  created_at: string;
  completed_at?: string;
  refund_amount?: number;
  refunded_at?: string;
  metadata?: Record<string, unknown>;
}

export function Transactions({ isOpen, onClose }: TransactionsProps) {
  const [transactions, setTransactions] = useState<PSPTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedTx, setExpandedTx] = useState<string | null>(null);
  const [refunding, setRefunding] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const url = filter === 'all' 
        ? `/api/payments/transactions`
        : `/api/payments/transactions?status=${filter}`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.transactions || []);
      }
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError('Erro ao carregar transacoes');
    } finally {
      setLoading(false);
    }
  };

  const handleRefund = async (transactionId: string, amount?: number) => {
    try {
      setRefunding(transactionId);
      const body: Record<string, unknown> = {};
      if (amount) {
        body.amount = amount;
      }

      const response = await fetch(`/api/payments/transactions/${transactionId}/refund`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        await fetchTransactions();
      } else {
        const data = await response.json();
        setError(data.detail || 'Erro ao processar reembolso');
      }
    } catch (err) {
      setError('Erro ao processar reembolso');
    } finally {
      setRefunding(null);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTransactions();
    }
  }, [isOpen, filter]);

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { icon: typeof CheckCircle; color: string; bg: string; label: string }> = {
      completed: {
        icon: CheckCircle,
        color: 'text-green-600',
        bg: 'bg-green-100',
        label: 'Concluido',
      },
      failed: {
        icon: XCircle,
        color: 'text-red-600',
        bg: 'bg-red-100',
        label: 'Falhou',
      },
      pending: {
        icon: Clock,
        color: 'text-yellow-600',
        bg: 'bg-yellow-100',
        label: 'Pendente',
      },
      processing: {
        icon: RefreshCw,
        color: 'text-blue-600',
        bg: 'bg-blue-100',
        label: 'Processando',
      },
      refunded: {
        icon: Undo2,
        color: 'text-purple-600',
        bg: 'bg-purple-100',
        label: 'Reembolsado',
      },
      partially_refunded: {
        icon: Undo2,
        color: 'text-orange-600',
        bg: 'bg-orange-100',
        label: 'Parcial',
      },
    };
    return configs[status] || configs.pending;
  };

  const formatCurrency = (amount: number, currency = 'BRL') => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency,
    }).format(amount / 100);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
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
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-gray-50">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Receipt size={24} className="text-blue-600" />
              Transacoes PSP
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={fetchTransactions}
                disabled={loading}
                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                title="Atualizar"
              >
                <RefreshCw size={20} className={clsx(loading && 'animate-spin')} />
              </button>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="p-4 border-b bg-white">
            <div className="flex gap-2 flex-wrap">
              {['all', 'completed', 'pending', 'failed', 'refunded'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm transition-colors',
                    filter === f
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  )}
                >
                  {f === 'all' ? 'Todas' : getStatusConfig(f).label}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mx-4 mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex justify-between items-center">
              <span>{error}</span>
              <button onClick={() => setError(null)}>
                <X size={16} />
              </button>
            </div>
          )}

          {/* Transactions List */}
          <div className="p-4 max-h-[60vh] overflow-y-auto">
            {loading && transactions.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="animate-spin text-gray-400" size={32} />
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Receipt size={48} className="mx-auto mb-4 opacity-50" />
                <p>Nenhuma transacao encontrada</p>
              </div>
            ) : (
              <div className="space-y-3">
                {transactions.map((tx) => {
                  const statusConfig = getStatusConfig(tx.status);
                  const StatusIcon = statusConfig.icon;
                  const isExpanded = expandedTx === tx.id;
                  const canRefund = tx.status === 'completed' && (!tx.refund_amount || tx.refund_amount < tx.amount);

                  return (
                    <div
                      key={tx.id}
                      className="border rounded-lg overflow-hidden"
                    >
                      {/* Main row */}
                      <div
                        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => setExpandedTx(isExpanded ? null : tx.id)}
                      >
                        <div className={clsx('p-2 rounded-full', statusConfig.bg)}>
                          <StatusIcon className={statusConfig.color} size={20} />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">
                              {tx.description || 'Pagamento'}
                            </span>
                            <span className={clsx('text-xs px-2 py-0.5 rounded-full', statusConfig.bg, statusConfig.color)}>
                              {statusConfig.label}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 truncate">
                            ID: {tx.id.slice(0, 8)}... • {formatDate(tx.created_at)}
                          </p>
                        </div>

                        <div className="text-right">
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(tx.amount, tx.currency)}
                          </p>
                          {tx.refund_amount && tx.refund_amount > 0 && (
                            <p className="text-xs text-purple-600">
                              -{formatCurrency(tx.refund_amount)} reemb.
                            </p>
                          )}
                        </div>

                        <button className="p-1 text-gray-400">
                          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                      </div>

                      {/* Expanded details */}
                      {isExpanded && (
                        <div className="px-4 pb-4 pt-2 bg-gray-50 border-t">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500">ID da Transacao</p>
                              <p className="font-mono text-xs break-all">{tx.id}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">Carteira</p>
                              <p className="font-mono text-xs">{tx.wallet_id}</p>
                            </div>
                            {tx.checkout_session_id && (
                              <div>
                                <p className="text-gray-500">Sessao Checkout</p>
                                <p className="font-mono text-xs break-all">{tx.checkout_session_id}</p>
                              </div>
                            )}
                            {tx.mandate_id && (
                              <div>
                                <p className="text-gray-500">Mandato AP2</p>
                                <p className="font-mono text-xs">{tx.mandate_id.slice(0, 20)}...</p>
                              </div>
                            )}
                            <div>
                              <p className="text-gray-500">Criado em</p>
                              <p>{formatDate(tx.created_at)}</p>
                            </div>
                            {tx.completed_at && (
                              <div>
                                <p className="text-gray-500">Concluido em</p>
                                <p>{formatDate(tx.completed_at)}</p>
                              </div>
                            )}
                          </div>

                          {/* Refund button */}
                          {canRefund && (
                            <div className="mt-4 pt-4 border-t">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRefund(tx.id);
                                }}
                                disabled={refunding === tx.id}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 disabled:opacity-50 transition-colors"
                              >
                                {refunding === tx.id ? (
                                  <RefreshCw className="animate-spin" size={16} />
                                ) : (
                                  <Undo2 size={16} />
                                )}
                                Reembolsar
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t bg-gray-50">
            <p className="text-xs text-gray-500 text-center">
              Mostrando {transactions.length} transacao(oes) do PSP simulado
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
