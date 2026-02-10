// Componente de chat com agente
import { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User, Wifi, WifiOff } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';

export function Chat() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, isChatOpen, toggleChat, isConnected } = useStore();
  const { sendMessage } = useWebSocket();

  // Auto-scroll para ultima mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Overlay */}
      {isChatOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleChat}
        />
      )}

      {/* Chat Window */}
      <div
        className={clsx(
          'fixed z-50 bg-white shadow-2xl flex flex-col transition-all duration-300',
          // Mobile: full screen
          'inset-0 lg:inset-auto',
          // Desktop: floating window
          'lg:bottom-4 lg:right-4 lg:w-96 lg:h-[600px] lg:rounded-lg lg:overflow-hidden',
          isChatOpen ? 'opacity-100 visible' : 'opacity-0 invisible lg:translate-y-4'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Bot size={24} />
            </div>
            <div>
              <h3 className="font-semibold">Assistente da Livraria</h3>
              <div className="flex items-center gap-1 text-sm opacity-80">
                {isConnected ? (
                  <>
                    <Wifi size={14} />
                    <span>Conectado</span>
                  </>
                ) : (
                  <>
                    <WifiOff size={14} />
                    <span>Desconectado</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={toggleChat}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Bot size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">
                Ola! Como posso ajudar voce hoje?
              </p>
              <p className="text-gray-400 text-sm mt-2">
                Pergunte sobre livros, recomendacoes ou ajuda com seu pedido.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-white" />
                  </div>
                )}

                <div
                  className={clsx(
                    'max-w-[80%] p-3 rounded-lg',
                    message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-white shadow rounded-bl-none'
                  )}
                >
                  {message.role === 'assistant' ? (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                  <span
                    className={clsx(
                      'text-xs mt-1 block',
                      message.role === 'user'
                        ? 'text-blue-100'
                        : 'text-gray-400'
                    )}
                  >
                    {new Date(message.timestamp).toLocaleTimeString('pt-BR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <User size={18} className="text-gray-600" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              disabled={!isConnected}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            />
            <button
              onClick={handleSend}
              disabled={!isConnected || !input.trim()}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                isConnected && input.trim()
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              )}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* FAB para abrir chat */}
      {!isChatOpen && (
        <button
          onClick={toggleChat}
          className="fixed bottom-4 right-4 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center z-40"
        >
          <Bot size={28} />
        </button>
      )}
    </>
  );
}
