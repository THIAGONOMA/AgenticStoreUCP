// Modal de checkout
import { useState } from 'react';
import { X, CreditCard, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useCheckout } from '../hooks/useCheckout';

interface CheckoutProps {
  isOpen: boolean;
  onClose: () => void;
}

type CheckoutStep = 'review' | 'processing' | 'success' | 'error';

export function Checkout({ isOpen, onClose }: CheckoutProps) {
  const [step, setStep] = useState<CheckoutStep>('review');
  const [orderId, setOrderId] = useState<string>('');

  const { cartItems, cartTotal } = useStore();
  const { createCheckout, loading } = useCheckout();

  const handleCheckout = async () => {
    setStep('processing');

    const result = await createCheckout();

    if (result.success) {
      setOrderId(result.orderId || '');
      setStep('success');
    } else {
      setStep('error');
    }
  };

  const handleClose = () => {
    setStep('review');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <CreditCard size={24} />
            Checkout UCP
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 'review' && (
            <div>
              <h3 className="font-semibold mb-4">Resumo do Pedido</h3>

              <div className="space-y-3 mb-6">
                {cartItems.map((item) => (
                  <div
                    key={item.book.id}
                    className="flex justify-between text-sm"
                  >
                    <span className="text-gray-600">
                      {item.quantity}x {item.book.title.slice(0, 30)}...
                    </span>
                    <span className="font-medium">
                      R$ {((item.book.price * item.quantity) / 100).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between text-lg font-bold">
                  <span>Total</span>
                  <span className="text-green-600">
                    R$ {(cartTotal / 100).toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>UCP Checkout:</strong> Este checkout utiliza o
                  Universal Commerce Protocol para processamento seguro.
                </p>
              </div>

              <button
                onClick={handleCheckout}
                disabled={loading}
                className="w-full mt-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                Confirmar Pagamento
              </button>
            </div>
          )}

          {step === 'processing' && (
            <div className="text-center py-8">
              <Loader2 size={48} className="mx-auto text-blue-600 animate-spin" />
              <p className="mt-4 text-gray-600">Processando pagamento...</p>
              <p className="text-sm text-gray-400 mt-2">
                Comunicando com UCP Server
              </p>
            </div>
          )}

          {step === 'success' && (
            <div className="text-center py-8">
              <CheckCircle size={64} className="mx-auto text-green-500" />
              <h3 className="mt-4 text-xl font-semibold text-green-700">
                Compra Realizada!
              </h3>
              <p className="mt-2 text-gray-600">
                Seu pedido foi processado com sucesso.
              </p>
              {orderId && (
                <p className="mt-4 text-sm">
                  <span className="text-gray-500">Pedido:</span>{' '}
                  <code className="bg-gray-100 px-2 py-1 rounded">
                    #{orderId.slice(0, 8)}
                  </code>
                </p>
              )}
              <button
                onClick={handleClose}
                className="mt-6 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Continuar Comprando
              </button>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center py-8">
              <AlertCircle size={64} className="mx-auto text-red-500" />
              <h3 className="mt-4 text-xl font-semibold text-red-700">
                Erro no Pagamento
              </h3>
              <p className="mt-2 text-gray-600">
                Nao foi possivel processar seu pagamento.
              </p>
              <button
                onClick={() => setStep('review')}
                className="mt-6 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Tentar Novamente
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
