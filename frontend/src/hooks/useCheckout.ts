// Hook para checkout integrado com UCP
import { useState } from 'react';
import { useStore } from '../store/useStore';

interface CheckoutResult {
  success: boolean;
  orderId?: string;
  error?: string;
}

export function useCheckout() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { cartItems, cartTotal, clearCart, triggerRefresh } = useStore();

  const createCheckout = async (): Promise<CheckoutResult> => {
    if (cartItems.length === 0) {
      return { success: false, error: 'Carrinho vazio' };
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Criar checkout session via UCP
      const lineItems = cartItems.map((item) => ({
        product_id: item.book.id,
        quantity: item.quantity,
      }));

      const createResponse = await fetch('/api/ucp/checkout-sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'UCP-Agent': 'frontend/1.0',
        },
        body: JSON.stringify({
          line_items: lineItems,
          buyer: {
            email: 'cliente@exemplo.com',
            name: 'Cliente Web',
          },
        }),
      });

      if (!createResponse.ok) {
        throw new Error('Falha ao criar checkout');
      }

      const session = await createResponse.json();
      console.log('Checkout session created:', session.id);

      // 2. Gerar wallet token da carteira da loja
      const tokenResponse = await fetch('/api/payments/wallet/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet_id: 'default_wallet',
        }),
      });

      if (!tokenResponse.ok) {
        throw new Error('Falha ao gerar token de pagamento');
      }

      const { token: walletToken } = await tokenResponse.json();
      console.log('Wallet token generated');

      // 3. Completar checkout com token valido
      const completeResponse = await fetch(
        `/api/ucp/checkout-sessions/${session.id}/complete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'UCP-Agent': 'frontend/1.0',
          },
          body: JSON.stringify({
            payment: {
              token: walletToken,
              wallet_token: walletToken,
            },
          }),
        }
      );

      if (!completeResponse.ok) {
        const errorData = await completeResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Falha no pagamento');
      }

      const result = await completeResponse.json();

      // Limpar carrinho
      clearCart();

      // Forcar atualizacao dos livros para refletir novo estoque
      triggerRefresh();

      return {
        success: true,
        orderId: result.id || result.order_id,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  return {
    createCheckout,
    loading,
    error,
    cartTotal,
    itemCount: cartItems.length,
  };
}
