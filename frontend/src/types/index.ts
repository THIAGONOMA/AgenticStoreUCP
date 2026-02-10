// Tipos principais do frontend

export interface Book {
  id: string;
  title: string;
  author: string;
  description: string;
  price: number;
  category: string;
  isbn: string;
  stock: number;
}

export interface CartItem {
  book: Book;
  quantity: number;
}

export interface Cart {
  items: CartItem[];
  total: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agent?: string;
    results_count?: number;
  };
}

export interface ChatSession {
  id: string;
  messages: Message[];
  cart: Cart;
}

export interface CheckoutSession {
  id: string;
  status: 'pending' | 'ready_for_payment' | 'completed' | 'cancelled';
  lineItems: Array<{
    productId: string;
    quantity: number;
    price: number;
  }>;
  totals: Array<{
    type: string;
    amount: number;
  }>;
  currency: string;
}

export interface SearchResult {
  id: string;
  title: string;
  author: string;
  price: number;
  price_formatted: string;
  category: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Wallet types
export interface WalletInfo {
  wallet_id: string;
  balance: number;
  balance_formatted: string;
  credit_limit: number;
  available_credit: number;
  created_at: string;
  last_transaction_at?: string;
}

export interface WalletTransaction {
  id: string;
  wallet_id: string;
  type: 'payment' | 'refund' | 'credit';
  amount: number;
  description?: string;
  reference_id?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'refunded' | 'partially_refunded';
  created_at: string;
  completed_at?: string;
}
