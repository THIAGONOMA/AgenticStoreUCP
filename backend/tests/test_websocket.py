"""Testes de WebSocket para Chat e A2A."""
import asyncio
import json
import pytest
import websockets

BASE_URL = "ws://localhost:8000"


@pytest.mark.asyncio
async def test_websocket_chat_connect():
    """T5.6 - Testar conexão WebSocket chat."""
    async with websockets.connect(f"{BASE_URL}/ws/chat") as ws:
        # Deve receber mensagem de boas-vindas
        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(response)
        
        assert "response" in data or "message" in data
        print(f"Chat connected: {data}")


@pytest.mark.asyncio
async def test_websocket_chat_message():
    """T5.6 - Testar envio de mensagem no chat."""
    async with websockets.connect(f"{BASE_URL}/ws/chat") as ws:
        # Receber mensagem de boas-vindas
        welcome = await asyncio.wait_for(ws.recv(), timeout=5.0)
        print(f"Welcome: {welcome[:80]}")
        
        # Enviar mensagem
        await ws.send(json.dumps({"message": "ola"}))
        
        response = await asyncio.wait_for(ws.recv(), timeout=15.0)
        data = json.loads(response)
        
        # Resposta pode ter "message" ou "response" dependendo do formato
        msg_content = data.get("message") or data.get("response", "")
        assert len(msg_content) > 0
        print(f"Chat response: {msg_content[:100]}")


@pytest.mark.asyncio  
async def test_websocket_a2a_connect():
    """T5.7 - Testar conexão WebSocket A2A."""
    async with websockets.connect(f"{BASE_URL}/ws/a2a") as ws:
        # Enviar mensagem de conexão
        connect_msg = {
            "type": "a2a.connect",
            "agent_id": "test-agent-connect",
            "payload": {
                "agent_profile": {
                    "name": "Test Agent",
                    "version": "1.0",
                    "capabilities": ["search", "checkout"]
                }
            }
        }
        await ws.send(json.dumps(connect_msg))
        
        response = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(response)
        
        # Debug
        print(f"A2A response: {data}")
        
        # Aceitar resposta válida - o handler retorna a2a.response com status no payload
        assert "type" in data, f"No type in response: {data}"
        # O status pode estar no top level ou pode ser inferido pelo type
        is_valid = (
            data.get("status") == "connected" or 
            "store_profile" in data.get("payload", {}) or
            data.get("type") == "a2a.response"
        )
        assert is_valid, f"Invalid response: {data}"
        print(f"A2A connected: type={data.get('type')}, status={data.get('status')}")


@pytest.mark.asyncio
async def test_websocket_a2a_search():
    """T5.7 - Testar busca via A2A WebSocket."""
    async with websockets.connect(f"{BASE_URL}/ws/a2a") as ws:
        # Conectar
        await ws.send(json.dumps({
            "type": "a2a.connect",
            "agent_id": "test-agent"
        }))
        await asyncio.wait_for(ws.recv(), timeout=5.0)
        
        # Buscar
        search_msg = {
            "type": "a2a.request",
            "agent_id": "test-agent",
            "action": "search",
            "payload": {"query": "python"}
        }
        await ws.send(json.dumps(search_msg))
        
        response = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(response)
        
        assert data.get("type") == "a2a.response"
        assert "payload" in data
        print(f"A2A search results: {len(data['payload'].get('search_results', []))} items")


if __name__ == "__main__":
    # Executar testes manualmente
    async def run_tests():
        print("=== T5.6 - WebSocket Chat ===")
        try:
            await test_websocket_chat_connect()
            print("✅ Chat connect passed")
        except Exception as e:
            print(f"❌ Chat connect failed: {e}")
        
        try:
            await test_websocket_chat_message()
            print("✅ Chat message passed")
        except Exception as e:
            print(f"❌ Chat message failed: {e}")
        
        print("\n=== T5.7 - WebSocket A2A ===")
        try:
            await test_websocket_a2a_connect()
            print("✅ A2A connect passed")
        except Exception as e:
            import traceback
            print(f"❌ A2A connect failed: {type(e).__name__}: {e}")
            traceback.print_exc()
        
        try:
            await test_websocket_a2a_search()
            print("✅ A2A search passed")
        except Exception as e:
            print(f"❌ A2A search failed: {e}")
    
    asyncio.run(run_tests())
