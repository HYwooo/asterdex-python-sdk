import pytest
from asterdex.api.v3.auth import EIP712Signer, create_signer as create_v3_signer
from asterdex.exceptions import SignatureError
from tests import TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY


class TestEIP712Signer:
    def test_signer_creation(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        assert signer.user == TESTNET_V3_USER
        assert signer.signer == TESTNET_V3_SIGNER
        assert signer.account is not None

    def test_get_nonce(self):
        EIP712Signer._last_ms = 0
        EIP712Signer._i = 0

        nonce1 = EIP712Signer.get_nonce()
        nonce2 = EIP712Signer.get_nonce()

        assert isinstance(nonce1, int)
        assert nonce2 >= nonce1

    def test_sign(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        params = {"symbol": "BTCUSDT", "side": "BUY"}
        signed, signature = signer.sign(params)

        assert "nonce" in signed
        assert "user" in signed
        assert "signer" in signed
        assert "signature" in signed
        assert signed["user"] == TESTNET_V3_USER
        assert signed["signer"] == TESTNET_V3_SIGNER
        assert isinstance(signature, str)
        assert len(signature) == 130

    def test_sign_preserves_original_params(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        original = {"symbol": "BTCUSDT", "quantity": "0.001"}
        signed, _ = signer.sign(original)

        assert signed["symbol"] == "BTCUSDT"
        assert signed["quantity"] == "0.001"

    def test_get_headers(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        headers = signer.get_headers()
        assert headers == {"Content-Type": "application/x-www-form-urlencoded"}

    def test_create_signer_function(self):
        signer = create_v3_signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        assert isinstance(signer, EIP712Signer)


class TestSignatureError:
    def test_v3_signature_error(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        with pytest.raises(SignatureError):
            signer.sign(None)  # type: ignore
