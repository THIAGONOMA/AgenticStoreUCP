"""Testes de seguranca AP2."""
import pytest
from src.security.key_manager import KeyManager
from src.security.ap2_security import AP2Security
from src.security.signatures import RequestSigner, ConformanceHeaders


class TestKeyManager:
    """Testes do KeyManager."""
    
    def test_key_generation(self):
        """Deve gerar par de chaves."""
        km = KeyManager()
        assert km.key_id is not None
        assert km.key_id.startswith("key-")
    
    def test_custom_key_id(self):
        """Deve aceitar key_id customizado."""
        km = KeyManager(key_id="my-custom-key")
        assert km.key_id == "my-custom-key"
    
    def test_sign_and_verify(self):
        """Deve assinar e verificar dados."""
        km = KeyManager()
        data = "Hello, World!"
        
        signature = km.sign(data)
        assert signature is not None
        
        # Verificar com mesma chave
        assert km.verify(data, signature) is True
        
        # Verificar com dados alterados
        assert km.verify("Hello, World?", signature) is False
    
    def test_jwk_export(self):
        """Deve exportar JWK corretamente."""
        km = KeyManager(key_id="test-key")
        jwk = km.get_public_jwk()
        
        assert jwk["kty"] == "OKP"
        assert jwk["crv"] == "Ed25519"
        assert jwk["kid"] == "test-key"
        assert jwk["alg"] == "EdDSA"
        assert "x" in jwk


class TestAP2Security:
    """Testes do AP2Security."""
    
    def test_create_mandate(self):
        """Deve criar mandato JWT."""
        km = KeyManager(key_id="test-key")
        ap2 = AP2Security(key_manager=km)
        
        jwt = ap2.create_mandate(
            amount=5000,
            currency="BRL",
            beneficiary="loja-123"
        )
        
        assert jwt is not None
        parts = jwt.split(".")
        assert len(parts) == 3  # header.payload.signature
    
    def test_validate_mandate(self):
        """Deve validar mandato criado."""
        km = KeyManager(key_id="test-key")
        ap2 = AP2Security(key_manager=km)
        
        jwt = ap2.create_mandate(
            amount=5000,
            currency="BRL",
            beneficiary="loja-123"
        )
        
        result = ap2.validate_mandate(jwt)
        
        assert result.valid is True
        assert result.mandate is not None
        assert result.mandate.max_amount == 5000
        assert result.mandate.currency == "BRL"
    
    def test_validate_mandate_wrong_amount(self):
        """Deve rejeitar se valor excede mandato."""
        km = KeyManager(key_id="test-key")
        ap2 = AP2Security(key_manager=km)
        
        jwt = ap2.create_mandate(
            amount=5000,
            currency="BRL",
            beneficiary="loja-123"
        )
        
        result = ap2.validate_mandate(jwt, required_amount=10000)
        
        assert result.valid is False
        assert "exceeds" in result.error
    
    def test_validate_mandate_wrong_audience(self):
        """Deve rejeitar audience incorreto."""
        km = KeyManager(key_id="test-key")
        ap2 = AP2Security(key_manager=km)
        
        jwt = ap2.create_mandate(
            amount=5000,
            currency="BRL",
            beneficiary="loja-123"
        )
        
        result = ap2.validate_mandate(jwt, expected_audience="loja-456")
        
        assert result.valid is False
        assert "audience" in result.error.lower()


class TestRequestSigner:
    """Testes do RequestSigner."""
    
    def test_sign_request(self):
        """Deve gerar headers de assinatura."""
        km = KeyManager(key_id="test-key")
        signer = RequestSigner(key_manager=km)
        
        headers = signer.sign_request(
            payload={"amount": 100},
            method="POST",
            path="/checkout"
        )
        
        assert "request-id" in headers
        assert "idempotency-key" in headers
        assert "ucp-timestamp" in headers
        assert "ucp-nonce" in headers
        assert "request-signature" in headers
        assert headers["ucp-key-id"] == "test-key"
    
    def test_verify_request(self):
        """Deve verificar request assinado."""
        km = KeyManager(key_id="test-key")
        signer = RequestSigner(key_manager=km)
        
        payload = {"amount": 100}
        headers = signer.sign_request(
            payload=payload,
            method="POST",
            path="/checkout"
        )
        
        valid, error = signer.verify_request(
            headers=headers,
            payload=payload,
            method="POST",
            path="/checkout"
        )
        
        assert valid is True
        assert error is None


class TestConformanceHeaders:
    """Testes do ConformanceHeaders."""
    
    def test_generate_headers(self):
        """Deve gerar headers de conformidade."""
        headers = ConformanceHeaders.generate()
        
        assert "request-id" in headers
        assert "idempotency-key" in headers
        assert "ucp-timestamp" in headers
        assert "ucp-nonce" in headers
