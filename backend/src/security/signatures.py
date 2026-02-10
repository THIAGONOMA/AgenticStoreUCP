"""Assinaturas de requests UCP."""
import json
import time
import uuid
from typing import Dict, Any, Optional, Tuple

from .key_manager import KeyManager, get_server_key_manager


class RequestSigner:
    """
    Assinador de requests UCP.
    
    Gera headers de conformidade UCP com assinaturas criptograficas.
    """
    
    def __init__(self, key_manager: Optional[KeyManager] = None):
        """
        Inicializar assinador.
        
        Args:
            key_manager: KeyManager para assinaturas
        """
        self.key_manager = key_manager or get_server_key_manager()
    
    def sign_request(
        self,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        path: str = "/"
    ) -> Dict[str, str]:
        """
        Gerar headers de conformidade UCP com assinatura.
        
        Args:
            payload: Corpo da requisicao (opcional)
            method: Metodo HTTP
            path: Caminho da requisicao
            
        Returns:
            Dicionario com headers UCP
        """
        # Gerar valores unicos
        request_id = str(uuid.uuid4())
        idempotency_key = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex[:16]
        
        # Serializar payload de forma canonica (ordenado)
        if payload:
            payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        else:
            payload_str = ""
        
        # Construir string para assinatura
        # Formato: timestamp.nonce.method.path.payload_hash
        signing_input = f"{timestamp}.{nonce}.{method}.{path}.{payload_str}"
        
        # Assinar
        signature = self.key_manager.sign(signing_input)
        
        return {
            "request-id": request_id,
            "idempotency-key": idempotency_key,
            "ucp-timestamp": timestamp,
            "ucp-nonce": nonce,
            "request-signature": signature,
            "ucp-key-id": self.key_manager.key_id
        }
    
    def verify_request(
        self,
        headers: Dict[str, str],
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        path: str = "/",
        max_age_seconds: int = 300
    ) -> Tuple[bool, Optional[str]]:
        """
        Verificar assinatura de uma requisicao.
        
        Args:
            headers: Headers da requisicao
            payload: Corpo da requisicao
            method: Metodo HTTP
            path: Caminho
            max_age_seconds: Idade maxima da requisicao
            
        Returns:
            Tupla (valido, mensagem_erro)
        """
        try:
            # Extrair headers necessarios
            timestamp = headers.get("ucp-timestamp")
            nonce = headers.get("ucp-nonce")
            signature = headers.get("request-signature")
            key_id = headers.get("ucp-key-id")
            
            if not all([timestamp, nonce, signature]):
                return False, "Missing required headers"
            
            # Verificar idade
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > max_age_seconds:
                return False, "Request too old or from future"
            
            # Reconstruir string de assinatura
            if payload:
                payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            else:
                payload_str = ""
            
            signing_input = f"{timestamp}.{nonce}.{method}.{path}.{payload_str}"
            
            # Verificar assinatura
            if not self.key_manager.verify(signing_input, signature):
                return False, "Invalid signature"
            
            return True, None
            
        except Exception as e:
            return False, str(e)


class ConformanceHeaders:
    """
    Gerador de headers de conformidade UCP.
    
    Versao simplificada para quando assinatura nao e necessaria.
    """
    
    @staticmethod
    def generate(include_signature: bool = False) -> Dict[str, str]:
        """
        Gerar headers de conformidade UCP.
        
        Args:
            include_signature: Se deve incluir assinatura
            
        Returns:
            Dicionario com headers
        """
        headers = {
            "request-id": str(uuid.uuid4()),
            "idempotency-key": str(uuid.uuid4()),
            "ucp-timestamp": str(int(time.time())),
            "ucp-nonce": uuid.uuid4().hex[:16]
        }
        
        if include_signature:
            signer = RequestSigner()
            signed_headers = signer.sign_request()
            headers.update(signed_headers)
        
        return headers


# Instancia global
_request_signer: Optional[RequestSigner] = None


def get_request_signer() -> RequestSigner:
    """Obter RequestSigner (singleton)."""
    global _request_signer
    if _request_signer is None:
        _request_signer = RequestSigner()
    return _request_signer
