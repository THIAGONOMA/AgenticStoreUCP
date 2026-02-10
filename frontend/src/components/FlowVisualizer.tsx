// Visualizador de fluxo em tela cheia com diagrama em arvore e venda real
import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  X, Play, Pause, RotateCcw, Zap, User, Store, Server, 
  CreditCard, CheckCircle, ArrowDown, Package, Database,
  MessageSquare, ShoppingCart, Key, Wallet, Receipt
} from 'lucide-react';
import clsx from 'clsx';

interface FlowVisualizerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FlowMessage {
  id: number;
  from: string;
  to: string;
  protocol: string;
  action: string;
  data?: string;
  response?: string;
  status: 'pending' | 'active' | 'success' | 'error';
}

// Configuracao dos nos do diagrama - posicoes em porcentagem (compacto 20%)
const nodes: Record<string, { label: string; icon: typeof User; color: string; x: number; y: number }> = {
  userAgent: { label: 'User Agent', icon: User, color: 'blue', x: 50, y: 12 },
  wallet: { label: 'Wallet', icon: Wallet, color: 'pink', x: 26, y: 12 },
  a2a: { label: 'A2A', icon: MessageSquare, color: 'purple', x: 26, y: 30 },
  storeAgent: { label: 'Store Agent', icon: Store, color: 'indigo', x: 50, y: 30 },
  ap2: { label: 'AP2', icon: Key, color: 'green', x: 74, y: 30 },
  ucp: { label: 'UCP', icon: Server, color: 'cyan', x: 50, y: 48 },
  database: { label: 'Database', icon: Database, color: 'amber', x: 74, y: 48 },
  psp: { label: 'PSP', icon: Receipt, color: 'rose', x: 26, y: 66 },
  checkout: { label: 'Checkout', icon: ShoppingCart, color: 'emerald', x: 50, y: 66 },
};

// Conexoes entre nos
const connections = [
  { from: 'userAgent', to: 'wallet', id: 'userAgent-wallet' },
  { from: 'userAgent', to: 'a2a', id: 'userAgent-a2a' },
  { from: 'userAgent', to: 'storeAgent', id: 'userAgent-storeAgent' },
  { from: 'userAgent', to: 'ap2', id: 'userAgent-ap2' },
  { from: 'a2a', to: 'storeAgent', id: 'a2a-storeAgent' },
  { from: 'storeAgent', to: 'ucp', id: 'storeAgent-ucp' },
  { from: 'ap2', to: 'ucp', id: 'ap2-ucp' },
  { from: 'ucp', to: 'database', id: 'ucp-database' },
  { from: 'ucp', to: 'psp', id: 'ucp-psp' },
  { from: 'ucp', to: 'checkout', id: 'ucp-checkout' },
  { from: 'psp', to: 'checkout', id: 'psp-checkout' },
  { from: 'wallet', to: 'psp', id: 'wallet-psp' },
];

// CSS para animacoes
const styles = `
  @keyframes vibrate {
    0%, 100% { transform: translate(-50%, -50%) scale(1.15); }
    10% { transform: translate(-50%, -50%) scale(1.15) translateX(-2px); }
    20% { transform: translate(-50%, -50%) scale(1.15) translateX(2px); }
    30% { transform: translate(-50%, -50%) scale(1.15) translateX(-2px); }
    40% { transform: translate(-50%, -50%) scale(1.15) translateX(2px); }
    50% { transform: translate(-50%, -50%) scale(1.15) translateX(-1px); }
    60% { transform: translate(-50%, -50%) scale(1.15) translateX(1px); }
    70% { transform: translate(-50%, -50%) scale(1.15); }
  }
  
  @keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 20px 5px currentColor, 0 0 40px 10px currentColor; }
    50% { box-shadow: 0 0 30px 10px currentColor, 0 0 60px 20px currentColor; }
  }
  
  @keyframes dash-flow {
    from { stroke-dashoffset: 24; }
    to { stroke-dashoffset: 0; }
  }
  
  @keyframes message-travel {
    0% { offset-distance: 0%; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { offset-distance: 100%; opacity: 0; }
  }
  
  .node-vibrating {
    animation: vibrate 0.5s ease-in-out;
  }
  
  .node-glowing {
    animation: glow-pulse 1s ease-in-out infinite;
  }
  
  .line-active {
    stroke-dasharray: 8 4;
    animation: dash-flow 0.5s linear infinite;
  }
  
  .message-particle {
    animation: message-travel 1s ease-in-out forwards;
  }
`;

export function FlowVisualizer({ isOpen, onClose }: FlowVisualizerProps) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [messages, setMessages] = useState<FlowMessage[]>([]);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [sourceNode, setSourceNode] = useState<string | null>(null);
  const [targetNode, setTargetNode] = useState<string | null>(null);
  const [activeConnection, setActiveConnection] = useState<string | null>(null);
  const [selectedBook, setSelectedBook] = useState<any>(null);
  const [checkoutResult, setCheckoutResult] = useState<any>(null);
  const [stockBefore, setStockBefore] = useState<number | null>(null);
  const [stockAfter, setStockAfter] = useState<number | null>(null);
  const [travelingMessage, setTravelingMessage] = useState<{ from: string; to: string } | null>(null);
  const [walletBalanceBefore, setWalletBalanceBefore] = useState<number | null>(null);
  const [walletBalanceAfter, setWalletBalanceAfter] = useState<number | null>(null);
  const [transactionId, setTransactionId] = useState<string | null>(null);
  const [mandateStatus, setMandateStatus] = useState<{ intent: boolean; payment: boolean }>({ intent: false, payment: false });
  const [animationProgress, setAnimationProgress] = useState(0);
  const [walletToken, setWalletToken] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para o final quando novas mensagens chegam
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  // Gerar mensagens com valores dinamicos
  const getFlowMessages = useCallback((): Omit<FlowMessage, 'status'>[] => {
    const balance = walletBalanceBefore ?? 50000;
    const balanceAfter = walletBalanceAfter ?? (balance - (selectedBook?.price ?? 4990));
    const token = walletToken ?? 'wtk_xxx';
    const tokenShort = token.substring(0, 12) + '...';
    const session = sessionId ?? 'sess_xxx';
    const bookTitle = selectedBook?.title ?? 'Livro';
    const bookPrice = selectedBook?.price ?? 4990;
    const stock = stockBefore ?? 50;
    const txnId = transactionId ?? 'txn_xxx';

    return [
      { id: 1, from: 'userAgent', to: 'a2a', protocol: 'A2A', action: 'Conectar ao Store Agent', data: 'ws://localhost:8000/ws/a2a' },
      { id: 2, from: 'a2a', to: 'storeAgent', protocol: 'A2A', action: 'Handshake', data: '{"type": "connect"}' },
      { id: 3, from: 'storeAgent', to: 'ucp', protocol: 'UCP', action: 'Discovery', data: 'GET /.well-known/ucp' },
      { id: 4, from: 'ucp', to: 'storeAgent', protocol: 'UCP', action: 'Capabilities', response: '{"version": "1.0", "psp": true}' },
      { id: 5, from: 'userAgent', to: 'storeAgent', protocol: 'A2A', action: 'Buscar Produto', data: `"Quero ${bookTitle}"` },
      { id: 6, from: 'storeAgent', to: 'ucp', protocol: 'UCP', action: 'Search Products', data: 'GET /books/search' },
      { id: 7, from: 'ucp', to: 'storeAgent', protocol: 'UCP', action: 'Product List', response: `[{"title": "${bookTitle}"}]` },
      { id: 8, from: 'userAgent', to: 'storeAgent', protocol: 'A2A', action: 'Selecionar Item', data: `"Comprar ${bookTitle}"` },
      { id: 9, from: 'userAgent', to: 'wallet', protocol: 'Wallet', action: 'Check Balance', data: 'GET /wallet' },
      { id: 10, from: 'wallet', to: 'userAgent', protocol: 'Wallet', action: 'Balance OK', response: `{"balance": ${balance}}` },
      { id: 11, from: 'userAgent', to: 'wallet', protocol: 'Wallet', action: 'Generate Token', data: 'POST /wallet/token' },
      { id: 12, from: 'wallet', to: 'userAgent', protocol: 'Wallet', action: 'Token Created', response: `{"token": "${tokenShort}"}` },
      { id: 13, from: 'userAgent', to: 'ap2', protocol: 'AP2', action: 'Intent Mandate', data: `sign(amount=${bookPrice})` },
      { id: 14, from: 'userAgent', to: 'ap2', protocol: 'AP2', action: 'Payment Mandate', data: `jwt(${tokenShort})` },
      { id: 15, from: 'storeAgent', to: 'ucp', protocol: 'UCP', action: 'Create Checkout', data: `POST /checkout {price: ${bookPrice}}` },
      { id: 16, from: 'ucp', to: 'storeAgent', protocol: 'UCP', action: 'Session Created', response: `{"id": "${session}"}` },
      { id: 17, from: 'ap2', to: 'ucp', protocol: 'UCP+AP2', action: 'Complete Checkout', data: `${session} + ${tokenShort}` },
      { id: 18, from: 'ucp', to: 'psp', protocol: 'PSP', action: 'Process Payment', data: `{"token": "${tokenShort}", "amt": ${bookPrice}}` },
      { id: 19, from: 'psp', to: 'wallet', protocol: 'PSP', action: 'Validate Token', data: `validate(${tokenShort})` },
      { id: 20, from: 'wallet', to: 'psp', protocol: 'PSP', action: 'Token Valid', response: `{"valid": true, "bal": ${balance}}` },
      { id: 21, from: 'psp', to: 'wallet', protocol: 'PSP', action: 'Debit Wallet', data: `debit(${bookPrice})` },
      { id: 22, from: 'wallet', to: 'psp', protocol: 'PSP', action: 'Debit Success', response: `{"new_balance": ${balanceAfter}}` },
      { id: 23, from: 'psp', to: 'ucp', protocol: 'PSP', action: 'Payment Complete', response: `{"txn": "${txnId}", "ok": true}` },
      { id: 24, from: 'ucp', to: 'database', protocol: 'SQL', action: 'Debitar Estoque', data: `UPDATE stock=${stock}-1` },
      { id: 25, from: 'database', to: 'ucp', protocol: 'SQL', action: 'Stock Updated', response: `{"stock": ${stock - 1}}` },
      { id: 26, from: 'ucp', to: 'checkout', protocol: 'UCP', action: 'Checkout Complete', response: `{"status": "completed"}` },
      { id: 27, from: 'userAgent', to: 'wallet', protocol: 'Wallet', action: 'Record Transaction', data: `record(${bookPrice}, "${txnId}")` },
    ];
  }, [walletBalanceBefore, walletBalanceAfter, walletToken, sessionId, selectedBook, stockBefore, transactionId]);

  // Memoizar mensagens do fluxo
  const flowMessages = getFlowMessages();

  // Buscar saldo da carteira pessoal do User Agent
  const fetchWalletBalance = useCallback(async () => {
    try {
      const res = await fetch('/api/user-agent/wallet');
      if (res.ok) {
        const data = await res.json();
        return data.balance;
      }
      console.warn('User Agent API nao disponivel. Execute: make up-ua-api');
    } catch (error) {
      console.warn('User Agent API nao disponivel. Execute: make up-ua-api');
    }
    return 50000; // fallback se API nao estiver rodando
  }, []);

  // Gerar token da carteira pessoal do User Agent
  const generateWalletToken = useCallback(async () => {
    try {
      const res = await fetch('/api/user-agent/wallet/token', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        return data.token;
      }
      console.error('User Agent API nao disponivel. Execute: make up-ua-api');
    } catch (error) {
      console.error('User Agent API nao disponivel. Execute: make up-ua-api');
    }
    return null;
  }, []);

  // Avancar para proximo passo
  const advanceStep = useCallback(async () => {
    const nextStep = currentStep + 1;
    
    if (nextStep >= flowMessages.length) {
      setIsPlaying(false);
      setActiveNodes(new Set());
      setSourceNode(null);
      setTargetNode(null);
      setActiveConnection(null);
      setTravelingMessage(null);
      setAnimationProgress(0);
      return;
    }
    
    const msg = flowMessages[nextStep];
    
    // Iniciar animacao
    setSourceNode(msg.from);
    setTravelingMessage({ from: msg.from, to: msg.to });
    setActiveConnection(`${msg.from}-${msg.to}`);
    setAnimationProgress(0);
    
    // Animar o progresso da bolinha
    const animationDuration = 800;
    const animationSteps = 20;
    const stepDuration = animationDuration / animationSteps;
    
    for (let i = 1; i <= animationSteps; i++) {
      setTimeout(() => {
        setAnimationProgress((i / animationSteps) * 100);
      }, i * stepDuration);
    }
    
    // Apos delay, ativar destino
    setTimeout(() => {
      setTargetNode(msg.to);
      setActiveNodes(prev => new Set([...prev, msg.from, msg.to]));
    }, 500);
    
    // Atualizar mensagens
    setMessages(prev => [...prev, { ...msg, status: 'active' }]);
    
    // Atualizar estados baseado no passo
    // Generate Token (passo 11) - gerar token real
    if (nextStep === 10) {
      const token = await generateWalletToken();
      if (token) setWalletToken(token);
    }
    // Intent Mandate (passo 13)
    if (nextStep === 12) {
      setMandateStatus(prev => ({ ...prev, intent: true }));
    }
    // Payment Mandate (passo 14)
    if (nextStep === 13) {
      setMandateStatus(prev => ({ ...prev, payment: true }));
    }
    // Create Checkout (passo 15) - criar sessao real
    if (nextStep === 14 && selectedBook && walletToken) {
      try {
        const checkoutRes = await fetch('/api/ucp/checkout-sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            line_items: [{ product_id: selectedBook.id, quantity: 1 }],
            buyer: { email: 'demo@flow.com', name: 'Demo Flow' }
          })
        });
        const session = await checkoutRes.json();
        setSessionId(session.id);
      } catch (error) {
        console.error('Error creating checkout session:', error);
      }
    }
    // Process Payment (passo 18)
    if (nextStep === 17) {
      setTransactionId(`txn_${Date.now().toString(36)}`);
    }
    // Complete Checkout (passo 17) - completar venda real
    if (nextStep === 16 && sessionId && walletToken) {
      try {
        const completeRes = await fetch(`/api/ucp/checkout-sessions/${sessionId}/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            payment: { token: walletToken, wallet_token: walletToken }
          })
        });
        const result = await completeRes.json();
        setCheckoutResult(result);
      } catch (error) {
        console.error('Error completing checkout:', error);
      }
    }
    // Debit Success (passo 22) - buscar saldo atualizado
    if (nextStep === 21) {
      const balance = await fetchWalletBalance();
      setWalletBalanceAfter(balance);
    }
    // Stock Updated (passo 25) - buscar estoque atualizado
    if (nextStep === 24 && selectedBook) {
      try {
        const updatedRes = await fetch(`/api/books/${selectedBook.id}`);
        const updatedBook = await updatedRes.json();
        setStockAfter(updatedBook.stock);
      } catch (error) {
        console.error('Error fetching updated stock:', error);
      }
    }
    
    // Marcar como sucesso e limpar animacao
    setTimeout(() => {
      setMessages(prev => 
        prev.map(m => m.id === msg.id ? { ...m, status: 'success' } : m)
      );
      setTravelingMessage(null);
      setActiveConnection(null);
      setAnimationProgress(0);
    }, 1200);
    
    setCurrentStep(nextStep);
  }, [currentStep, flowMessages, fetchWalletBalance, generateWalletToken, selectedBook, walletToken, sessionId]);

  // Auto-play
  useEffect(() => {
    if (!isPlaying) return;
    
    const timer = setTimeout(() => {
      advanceStep();
    }, 1800);
    
    return () => clearTimeout(timer);
  }, [isPlaying, advanceStep]);

  // Controles
  const handleStart = async () => {
    setCurrentStep(-1);
    setMessages([]);
    setActiveNodes(new Set());
    setSourceNode(null);
    setTargetNode(null);
    setActiveConnection(null);
    setSelectedBook(null);
    setCheckoutResult(null);
    setStockBefore(null);
    setStockAfter(null);
    setTravelingMessage(null);
    setWalletBalanceBefore(null);
    setWalletBalanceAfter(null);
    setTransactionId(null);
    setMandateStatus({ intent: false, payment: false });
    setAnimationProgress(0);
    setWalletToken(null);
    setSessionId(null);
    
    // Pre-carregar dados para mostrar valores reais nas mensagens
    try {
      // Buscar livro
      const booksRes = await fetch('/api/books');
      const booksData = await booksRes.json();
      const book = booksData.books?.[0];
      if (book) {
        setSelectedBook(book);
        setStockBefore(book.stock);
      }
      
      // Buscar saldo inicial
      const balance = await fetchWalletBalance();
      setWalletBalanceBefore(balance);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
    
    setIsPlaying(true);
  };

  const handlePause = () => setIsPlaying(false);
  const handleResume = () => setIsPlaying(true);

  if (!isOpen) return null;

  const colorMap: Record<string, { bg: string; border: string; text: string; glow: string }> = {
    blue: { bg: 'bg-blue-500', border: 'border-blue-300', text: 'text-white', glow: 'rgba(59, 130, 246, 0.6)' },
    purple: { bg: 'bg-purple-500', border: 'border-purple-300', text: 'text-white', glow: 'rgba(168, 85, 247, 0.6)' },
    indigo: { bg: 'bg-indigo-500', border: 'border-indigo-300', text: 'text-white', glow: 'rgba(99, 102, 241, 0.6)' },
    green: { bg: 'bg-green-500', border: 'border-green-300', text: 'text-white', glow: 'rgba(34, 197, 94, 0.6)' },
    cyan: { bg: 'bg-cyan-500', border: 'border-cyan-300', text: 'text-white', glow: 'rgba(6, 182, 212, 0.6)' },
    amber: { bg: 'bg-amber-500', border: 'border-amber-300', text: 'text-white', glow: 'rgba(245, 158, 11, 0.6)' },
    emerald: { bg: 'bg-emerald-500', border: 'border-emerald-300', text: 'text-white', glow: 'rgba(16, 185, 129, 0.6)' },
    pink: { bg: 'bg-pink-500', border: 'border-pink-300', text: 'text-white', glow: 'rgba(236, 72, 153, 0.6)' },
    rose: { bg: 'bg-rose-500', border: 'border-rose-300', text: 'text-white', glow: 'rgba(244, 63, 94, 0.6)' },
  };

  const getConnectionColor = (connId: string) => {
    if (activeConnection === connId) return 'stroke-yellow-400';
    // Check if this connection was used
    const [from, to] = connId.split('-');
    const reverseId = `${to}-${from}`;
    const wasUsed = messages.some(m => 
      (m.from === from && m.to === to) || (m.from === to && m.to === from)
    );
    if (wasUsed) return 'stroke-green-500';
    return 'stroke-gray-600';
  };

  return (
    <div className="fixed inset-0 z-50 bg-gray-900">
      <style>{styles}</style>
      
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-r from-blue-600 via-purple-600 to-green-600 flex items-center justify-between px-6 shadow-lg z-20">
        <div className="flex items-center gap-3">
          <Zap size={28} className="text-white" />
          <h1 className="text-xl font-bold text-white">
            Fluxo de Comunicacao - Venda Real com UCP + A2A + AP2
          </h1>
        </div>
        <div className="flex items-center gap-4">
          {!isPlaying && currentStep < 0 && (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-6 py-2 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              <Play size={20} />
              Iniciar Venda Real
            </button>
          )}
          {isPlaying && (
            <button
              onClick={handlePause}
              className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg font-semibold hover:bg-amber-600"
            >
              <Pause size={20} />
              Pausar
            </button>
          )}
          {!isPlaying && currentStep >= 0 && currentStep < flowMessages.length - 1 && (
            <button
              onClick={handleResume}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600"
            >
              <Play size={20} />
              Continuar
            </button>
          )}
          {currentStep >= 0 && (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              <RotateCcw size={20} />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            <X size={24} className="text-white" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="absolute top-16 bottom-0 left-0 right-0 flex">
        {/* Diagrama em Arvore */}
        <div className="flex-1 relative bg-gray-800 overflow-hidden">
          {/* SVG para linhas e animacoes */}
          <svg ref={svgRef} className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }}>
            <defs>
              {/* Gradientes para as linhas */}
              <linearGradient id="lineGradientActive" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#facc15" />
                <stop offset="50%" stopColor="#fef08a" />
                <stop offset="100%" stopColor="#facc15" />
              </linearGradient>
              
              {/* Filtro de brilho */}
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* Linhas de conexao */}
            {connections.map(conn => {
              const fromNode = nodes[conn.from];
              const toNode = nodes[conn.to];
              const isActive = activeConnection === conn.id || activeConnection === `${conn.to}-${conn.from}`;
              
              return (
                <g key={conn.id}>
                  {/* Linha base */}
                  <line
                    x1={`${fromNode.x}%`}
                    y1={`${fromNode.y}%`}
                    x2={`${toNode.x}%`}
                    y2={`${toNode.y}%`}
                    className={clsx(
                      'transition-all duration-300',
                      getConnectionColor(conn.id),
                      isActive ? 'stroke-[4px] line-active' : 'stroke-[2px]'
                    )}
                    style={isActive ? { filter: 'url(#glow)' } : {}}
                  />
                  
                  {/* Particula viajando */}
                  {travelingMessage && 
                   ((travelingMessage.from === conn.from && travelingMessage.to === conn.to) ||
                    (travelingMessage.from === conn.to && travelingMessage.to === conn.from)) && (() => {
                    // Determinar direcao correta
                    const isForward = travelingMessage.from === conn.from;
                    const startX = isForward ? fromNode.x : toNode.x;
                    const startY = isForward ? fromNode.y : toNode.y;
                    const endX = isForward ? toNode.x : fromNode.x;
                    const endY = isForward ? toNode.y : fromNode.y;
                    
                    // Calcular posicao atual baseada no progresso
                    const currentX = startX + (endX - startX) * (animationProgress / 100);
                    const currentY = startY + (endY - startY) * (animationProgress / 100);
                    
                    return (
                      <circle
                        cx={`${currentX}%`}
                        cy={`${currentY}%`}
                        r="10"
                        fill="#facc15"
                        filter="url(#glow)"
                      >
                        <animate
                          attributeName="r"
                          values="8;12;8"
                          dur="0.4s"
                          repeatCount="indefinite"
                        />
                      </circle>
                    );
                  })()}
                </g>
              );
            })}
          </svg>

          {/* Nos circulares */}
          {Object.entries(nodes).map(([id, node]) => {
            const colors = colorMap[node.color];
            const isSource = sourceNode === id;
            const isTarget = targetNode === id;
            const wasActivated = activeNodes.has(id);
            const Icon = node.icon;
            
            return (
              <div
                key={id}
                className={clsx(
                  'absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-300',
                  'w-20 h-20 rounded-full flex flex-col items-center justify-center',
                  'border-4 shadow-lg cursor-pointer',
                  colors.bg, colors.border,
                  wasActivated && 'ring-4 ring-offset-2 ring-offset-gray-800',
                  wasActivated && `ring-${node.color}-400`,
                  isTarget && 'node-vibrating node-glowing'
                )}
                style={{ 
                  left: `${node.x}%`, 
                  top: `${node.y}%`, 
                  zIndex: isSource || isTarget ? 20 : 10,
                  color: isTarget ? colors.glow : undefined,
                  boxShadow: wasActivated ? `0 0 20px ${colors.glow}` : undefined
                }}
              >
                <Icon size={24} className={colors.text} />
                <span className={clsx('text-xs font-bold mt-1', colors.text)}>
                  {node.label}
                </span>
              </div>
            );
          })}

          {/* Legenda */}
          <div className="absolute bottom-4 left-4 flex flex-wrap gap-2 text-sm z-10">
            <span className="px-3 py-1.5 bg-purple-600 text-white rounded-full font-medium">A2A</span>
            <span className="px-3 py-1.5 bg-cyan-600 text-white rounded-full font-medium">UCP</span>
            <span className="px-3 py-1.5 bg-green-600 text-white rounded-full font-medium">AP2</span>
            <span className="px-3 py-1.5 bg-rose-600 text-white rounded-full font-medium">PSP</span>
            <span className="px-3 py-1.5 bg-pink-600 text-white rounded-full font-medium">Wallet</span>
            <span className="px-3 py-1.5 bg-amber-600 text-white rounded-full font-medium">SQL</span>
          </div>

          {/* Info do Produto/Estoque/Wallet - canto superior direito */}
          {(selectedBook || walletBalanceBefore !== null || mandateStatus.intent) && (
            <div className="absolute bottom-4 right-4 bg-gray-700/90 backdrop-blur rounded-lg p-3 text-white shadow-xl z-10 w-[220px] text-xs">
              {/* Produto */}
              {selectedBook && (
                <>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-blue-500 rounded">
                      <Package size={14} />
                    </div>
                    <span className="font-semibold truncate">{selectedBook.title}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Preco:</span>
                      <span className="text-green-400 font-mono">R$ {(selectedBook.price / 100).toFixed(2)}</span>
                    </div>
                    {stockBefore !== null && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Estoque:</span>
                        <span className="font-mono">
                          <span className="text-yellow-400">{stockBefore}</span>
                          {stockAfter !== null && <span className="text-gray-500"> → </span>}
                          {stockAfter !== null && <span className="text-red-400">{stockAfter}</span>}
                        </span>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Mandates */}
              {(mandateStatus.intent || mandateStatus.payment) && (
                <div className={clsx("space-y-1", selectedBook && "mt-2 pt-2 border-t border-gray-600")}>
                  <div className="text-[10px] font-semibold text-green-400 uppercase tracking-wide">AP2 Mandates</div>
                  <div className="flex gap-2">
                    <span className={clsx("flex items-center gap-1", mandateStatus.intent ? "text-green-400" : "text-gray-500")}>
                      {mandateStatus.intent ? <CheckCircle size={10} /> : <span className="w-2.5 h-2.5 rounded-full bg-gray-600" />}
                      Intent
                    </span>
                    <span className={clsx("flex items-center gap-1", mandateStatus.payment ? "text-green-400" : "text-gray-500")}>
                      {mandateStatus.payment ? <CheckCircle size={10} /> : <span className="w-2.5 h-2.5 rounded-full bg-gray-600" />}
                      Payment
                    </span>
                  </div>
                </div>
              )}

              {/* Wallet */}
              {walletBalanceBefore !== null && (
                <div className={clsx("space-y-1", (selectedBook || mandateStatus.intent) && "mt-2 pt-2 border-t border-gray-600")}>
                  <div className="text-[10px] font-semibold text-pink-400 uppercase tracking-wide">Wallet</div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Saldo:</span>
                    <span className="font-mono">
                      <span className="text-pink-400">R$ {(walletBalanceBefore / 100).toFixed(2)}</span>
                      {walletBalanceAfter !== null && <span className="text-gray-500"> → </span>}
                      {walletBalanceAfter !== null && <span className="text-pink-300">R$ {(walletBalanceAfter / 100).toFixed(2)}</span>}
                    </span>
                  </div>
                </div>
              )}

              {/* Transacao PSP */}
              {transactionId && (
                <div className="mt-2 pt-2 border-t border-gray-600">
                  <div className="text-[10px] font-semibold text-rose-400 uppercase tracking-wide">PSP</div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 truncate">{transactionId}</span>
                    <span className="text-green-400">OK</span>
                  </div>
                </div>
              )}

              {/* Resultado Final */}
              {checkoutResult && (
                <div className="mt-2 pt-2 border-t border-gray-600">
                  <div className="flex items-center gap-1 text-green-400 font-medium">
                    <CheckCircle size={12} />
                    Venda Concluida!
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Log de Mensagens */}
        <div className="w-[300px] bg-gray-900 border-l border-gray-700 flex flex-col">
          <div className="p-3 border-b border-gray-700 bg-gray-800">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <MessageSquare size={16} />
              Mensagens
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              Etapa {Math.max(0, currentStep + 1)} de {flowMessages.length}
            </p>
            <div className="mt-1.5 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 transition-all duration-500"
                style={{ width: `${((currentStep + 1) / flowMessages.length) * 100}%` }}
              />
            </div>
          </div>
          
          <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {messages.map((msg) => {
              const fromNode = nodes[msg.from];
              const toNode = nodes[msg.to];
              
              return (
                <div
                  key={msg.id}
                  className={clsx(
                    'p-2 rounded border transition-all duration-300 text-xs',
                    msg.status === 'active' && 'bg-yellow-900/30 border-yellow-500 shadow-sm shadow-yellow-500/20',
                    msg.status === 'success' && 'bg-gray-800/80 border-gray-700',
                    msg.status === 'pending' && 'bg-gray-800/50 border-gray-700 opacity-50'
                  )}
                >
                  {/* Header */}
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="font-mono text-gray-500 w-5 text-[10px]">#{msg.id}</span>
                    <span className={clsx(
                      'px-1.5 py-0.5 text-[10px] font-bold rounded',
                      msg.protocol === 'A2A' && 'bg-purple-600 text-white',
                      msg.protocol === 'UCP' && 'bg-cyan-600 text-white',
                      msg.protocol === 'AP2' && 'bg-green-600 text-white',
                      msg.protocol === 'UCP+AP2' && 'bg-gradient-to-r from-cyan-600 to-green-600 text-white',
                      msg.protocol === 'SQL' && 'bg-amber-600 text-white',
                      msg.protocol === 'PSP' && 'bg-rose-600 text-white',
                      msg.protocol === 'Wallet' && 'bg-pink-600 text-white'
                    )}>
                      {msg.protocol}
                    </span>
                    {msg.status === 'success' && (
                      <CheckCircle size={10} className="text-green-400 ml-auto" />
                    )}
                    {msg.status === 'active' && (
                      <div className="ml-auto w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                    )}
                  </div>
                  
                  {/* From -> To + Action */}
                  <div className="flex items-center gap-1 text-[10px] text-gray-400">
                    <span className={clsx('font-medium', `text-${fromNode?.color}-400`)}>{fromNode?.label}</span>
                    <ArrowDown size={10} className="text-gray-500 rotate-[-90deg]" />
                    <span className={clsx('font-medium', `text-${toNode?.color}-400`)}>{toNode?.label}</span>
                  </div>
                  
                  {/* Action */}
                  <p className="text-white font-medium text-[11px] mt-0.5">{msg.action}</p>
                  
                  {/* Data/Response - compacto */}
                  {msg.data && (
                    <pre className="mt-1 p-1 bg-gray-950 rounded text-[9px] text-green-400 font-mono overflow-x-auto max-h-8 truncate">
                      {msg.data}
                    </pre>
                  )}
                  {msg.response && (
                    <pre className="mt-0.5 p-1 bg-gray-950 rounded text-[9px] text-cyan-400 font-mono overflow-x-auto max-h-8 truncate">
                      ← {msg.response}
                    </pre>
                  )}
                </div>
              );
            })}
            
            {messages.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Zap size={32} className="mx-auto mb-3 opacity-50" />
                <p className="font-medium text-sm">Clique em "Iniciar"</p>
                <p className="text-xs mt-1">Venda real sera executada</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
