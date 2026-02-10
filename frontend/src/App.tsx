// App principal da Livraria UCP
import { useState } from 'react';
import { Header, BookList, Cart, Chat, FlowVisualizer } from './components';
import { Zap } from 'lucide-react';

function App() {
  const [isFlowPanelOpen, setFlowPanelOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="mb-12 text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Bem-vindo a Livraria Virtual
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Explore nosso catalogo e converse com nosso assistente de IA para
            encontrar o livro perfeito para voce.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-4">
            <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              UCP - Universal Commerce Protocol
            </div>
            <div className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
              A2A - Agent to Agent
            </div>
            <div className="px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              AP2 - Agent Payments
            </div>
          </div>

          {/* Botao para abrir visualizacao do fluxo */}
          <button
            onClick={() => setFlowPanelOpen(true)}
            className="mt-8 inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-green-600 text-white rounded-xl hover:from-blue-700 hover:via-purple-700 hover:to-green-700 transition-all shadow-lg hover:shadow-xl text-lg font-semibold"
          >
            <Zap size={24} />
            Demonstracao Interativa: Venda Real com A2A + UCP + AP2
          </button>
        </section>

        {/* Catalogo */}
        <section id="catalogo">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            Catalogo de Livros
          </h3>
          <BookList />
        </section>

        {/* Sobre UCP */}
        <section id="sobre" className="mt-16 py-12 bg-white rounded-lg shadow-sm">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Sobre o Protocolo UCP
            </h3>
            <p className="text-gray-600 mb-6">
              Esta livraria demonstra o{' '}
              <strong>Universal Commerce Protocol (UCP)</strong>, um padrao
              aberto para comercio agente. Agentes de IA podem descobrir nossa
              loja, navegar produtos e realizar compras de forma autonoma.
            </p>
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl mb-2">🔍</div>
                <h4 className="font-semibold mb-2">Discovery</h4>
                <p className="text-sm text-gray-500">
                  Endpoint padronizado para descoberta de capacidades
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl mb-2">🤖</div>
                <h4 className="font-semibold mb-2">A2A</h4>
                <p className="text-sm text-gray-500">
                  Comunicacao entre agentes para orquestracao
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl mb-2">💳</div>
                <h4 className="font-semibold mb-2">AP2</h4>
                <p className="text-sm text-gray-500">
                  Pagamentos seguros com mandatos criptograficos
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            Livraria Virtual UCP - Demonstracao de Comercio Agentico
          </p>
          <p className="text-gray-500 text-sm mt-2">
            UCP Discovery: <code>/.well-known/ucp</code>
          </p>
        </div>
      </footer>

      {/* Cart Drawer */}
      <Cart />

      {/* Chat Widget */}
      <Chat />

      {/* Flow Visualizer Panel */}
      <FlowVisualizer
        isOpen={isFlowPanelOpen}
        onClose={() => setFlowPanelOpen(false)}
      />
    </div>
  );
}

export default App;
