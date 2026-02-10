// Zustand store para estado global
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Book, CartItem, Message } from '../types';

interface AppState {
  // Cart
  cartItems: CartItem[];
  cartTotal: number;
  addToCart: (book: Book) => void;
  removeFromCart: (bookId: string) => void;
  updateQuantity: (bookId: string, quantity: number) => void;
  clearCart: () => void;

  // Chat
  messages: Message[];
  sessionId: string | null;
  isConnected: boolean;
  addMessage: (message: Message) => void;
  setSessionId: (id: string) => void;
  setConnected: (connected: boolean) => void;
  clearMessages: () => void;

  // Search
  searchQuery: string;
  searchResults: Book[];
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: Book[]) => void;

  // UI
  isChatOpen: boolean;
  isCartOpen: boolean;
  toggleChat: () => void;
  toggleCart: () => void;

  // Refresh trigger para atualizar dados apos checkout
  refreshTrigger: number;
  triggerRefresh: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Cart state
      cartItems: [],
      cartTotal: 0,

      addToCart: (book: Book) => {
        const items = get().cartItems;
        const existing = items.find((item) => item.book.id === book.id);

        if (existing) {
          set({
            cartItems: items.map((item) =>
              item.book.id === book.id
                ? { ...item, quantity: item.quantity + 1 }
                : item
            ),
          });
        } else {
          set({ cartItems: [...items, { book, quantity: 1 }] });
        }

        // Recalcular total
        const newItems = get().cartItems;
        const total = newItems.reduce(
          (sum, item) => sum + item.book.price * item.quantity,
          0
        );
        set({ cartTotal: total });
      },

      removeFromCart: (bookId: string) => {
        const items = get().cartItems.filter((item) => item.book.id !== bookId);
        const total = items.reduce(
          (sum, item) => sum + item.book.price * item.quantity,
          0
        );
        set({ cartItems: items, cartTotal: total });
      },

      updateQuantity: (bookId: string, quantity: number) => {
        if (quantity <= 0) {
          get().removeFromCart(bookId);
          return;
        }

        const items = get().cartItems.map((item) =>
          item.book.id === bookId ? { ...item, quantity } : item
        );
        const total = items.reduce(
          (sum, item) => sum + item.book.price * item.quantity,
          0
        );
        set({ cartItems: items, cartTotal: total });
      },

      clearCart: () => set({ cartItems: [], cartTotal: 0 }),

      // Chat state
      messages: [],
      sessionId: null,
      isConnected: false,

      addMessage: (message: Message) =>
        set({ messages: [...get().messages, message] }),

      setSessionId: (id: string) => set({ sessionId: id }),

      setConnected: (connected: boolean) => set({ isConnected: connected }),

      clearMessages: () => set({ messages: [] }),

      // Search state
      searchQuery: '',
      searchResults: [],

      setSearchQuery: (query: string) => set({ searchQuery: query }),

      setSearchResults: (results: Book[]) => set({ searchResults: results }),

      // UI state
      isChatOpen: false,
      isCartOpen: false,

      toggleChat: () => set({ isChatOpen: !get().isChatOpen }),

      toggleCart: () => set({ isCartOpen: !get().isCartOpen }),

      // Refresh trigger para forcar atualizacao de dados
      refreshTrigger: 0,
      triggerRefresh: () => set({ refreshTrigger: get().refreshTrigger + 1 }),
    }),
    {
      name: 'livraria-storage',
      partialize: (state) => ({
        cartItems: state.cartItems,
        cartTotal: state.cartTotal,
      }),
    }
  )
);
