"""Gerenciador de chaves Ed25519 para AP2."""
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class KeyManager:
    """
    Gerenciador de chaves Ed25519 para assinaturas AP2.
    
    Gera par de chaves, assina dados e exporta chave publica em formato JWK.
    """
    
    def __init__(self, key_id: Optional[str] = None):
        """
        Inicializar com novo par de chaves.
        
        Args:
            key_id: Identificador da chave (gerado automaticamente se nao fornecido)
        """
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        
        # Gerar key_id baseado nos primeiros bytes da chave publica
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        if key_id:
            self.key_id = key_id
        else:
            # Gerar ID unico baseado na chave
            key_hash = base64.urlsafe_b64encode(public_bytes[:8]).decode().rstrip("=")
            self.key_id = f"key-{key_hash}"
    
    def sign(self, data: str) -> str:
        """
        Assinar dados com a chave privada.
        
        Args:
            data: String a ser assinada
            
        Returns:
            Assinatura em base64url
        """
        signature = self._private_key.sign(data.encode("utf-8"))
        return base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    def verify(self, data: str, signature: str) -> bool:
        """
        Verificar assinatura.
        
        Args:
            data: Dados originais
            signature: Assinatura em base64url
            
        Returns:
            True se valida
        """
        try:
            # Adicionar padding se necessario
            sig_padded = signature + "=" * (4 - len(signature) % 4)
            sig_bytes = base64.urlsafe_b64decode(sig_padded)
            self._public_key.verify(sig_bytes, data.encode("utf-8"))
            return True
        except Exception:
            return False
    
    def get_public_jwk(self) -> Dict[str, Any]:
        """
        Exportar chave publica em formato JWK (JSON Web Key).
        
        Returns:
            Dicionario JWK
        """
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Base64url encode da coordenada x
        x_coord = base64.urlsafe_b64encode(public_bytes).decode().rstrip("=")
        
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": x_coord,
            "kid": self.key_id,
            "use": "sig",
            "alg": "EdDSA"
        }
    
    def get_private_bytes(self) -> bytes:
        """Obter bytes da chave privada (para backup)."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    @classmethod
    def from_private_bytes(cls, private_bytes: bytes, key_id: str) -> "KeyManager":
        """
        Restaurar KeyManager de bytes da chave privada.
        
        Args:
            private_bytes: Bytes da chave privada
            key_id: ID da chave
            
        Returns:
            Instancia de KeyManager
        """
        instance = cls.__new__(cls)
        instance._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
        instance._public_key = instance._private_key.public_key()
        instance.key_id = key_id
        return instance


# Instancia global para o servidor
_server_key_manager: Optional[KeyManager] = None


def get_server_key_manager() -> KeyManager:
    """Obter KeyManager do servidor (singleton)."""
    global _server_key_manager
    if _server_key_manager is None:
        from ..config import settings
        _server_key_manager = KeyManager(key_id=settings.ap2_key_id)
    return _server_key_manager
