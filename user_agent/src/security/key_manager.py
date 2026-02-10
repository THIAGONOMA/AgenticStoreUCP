"""Gerenciador de chaves Ed25519 para User Agent."""
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class UserKeyManager:
    """
    Gerenciador de chaves Ed25519 para o User Agent.
    
    Diferente do servidor, o User Agent pode persistir suas chaves.
    """
    
    def __init__(self, key_id: Optional[str] = None):
        """
        Inicializar com novo par de chaves.
        
        Args:
            key_id: Identificador da chave
        """
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        if key_id:
            self.key_id = key_id
        else:
            key_hash = base64.urlsafe_b64encode(public_bytes[:8]).decode().rstrip("=")
            self.key_id = f"user-key-{key_hash}"
    
    def sign(self, data: str) -> str:
        """Assinar dados."""
        signature = self._private_key.sign(data.encode("utf-8"))
        return base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    def verify(self, data: str, signature: str) -> bool:
        """Verificar assinatura."""
        try:
            sig_padded = signature + "=" * (4 - len(signature) % 4)
            sig_bytes = base64.urlsafe_b64decode(sig_padded)
            self._public_key.verify(sig_bytes, data.encode("utf-8"))
            return True
        except Exception:
            return False
    
    def get_public_jwk(self) -> Dict[str, Any]:
        """Exportar chave publica em JWK."""
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        x_coord = base64.urlsafe_b64encode(public_bytes).decode().rstrip("=")
        
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": x_coord,
            "kid": self.key_id,
            "use": "sig",
            "alg": "EdDSA"
        }
    
    def save_to_file(self, filepath: str):
        """Salvar chave privada em arquivo."""
        private_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        data = {
            "key_id": self.key_id,
            "private_key": base64.b64encode(private_bytes).decode()
        }
        
        import json
        Path(filepath).write_text(json.dumps(data))
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "UserKeyManager":
        """Carregar chave de arquivo."""
        import json
        data = json.loads(Path(filepath).read_text())
        
        private_bytes = base64.b64decode(data["private_key"])
        
        instance = cls.__new__(cls)
        instance._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
        instance._public_key = instance._private_key.public_key()
        instance.key_id = data["key_id"]
        
        return instance


# Instancia global
_user_key_manager: Optional[UserKeyManager] = None


def get_user_key_manager() -> UserKeyManager:
    """Obter KeyManager do usuario (singleton)."""
    global _user_key_manager
    if _user_key_manager is None:
        from ..config import settings
        _user_key_manager = UserKeyManager(key_id=settings.user_key_id)
    return _user_key_manager
