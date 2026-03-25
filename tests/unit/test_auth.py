import pytest
from asterdex.api.v1.auth import HMACSigner, create_signer
from asterdex.api.v3.auth import EIP712Signer, create_signer as create_v3_signer
from asterdex.exceptions import SignatureError
from tests import TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY


class TestHMACSigner:
    def test_signer_creation(self):
        signer = HMACSigner("test_key", "test_secret")
        assert signer.api_key == "test_key"
        assert signer.secret_key == "test_secret"
        assert signer.recv_window == 5000

    def test_signer_with_custom_recv_window(self):
        signer = HMACSigner("test_key", "test_secret", recv_window=10000)
        assert signer.recv_window == 10000

    def test_generate_signature(self):
        signer = HMACSigner("test_key", "test_secret")
        params = {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT"}
        signature = signer._generate_signature(params)
        assert isinstance(signature, str)
        assert len(signature) == 64

    def test_sign_adds_timestamp_and_signature(self):
        signer = HMACSigner("test_key", "test_secret")
        params = {"symbol": "BTCUSDT", "side": "BUY"}
        signed = signer.sign(params)

        assert "timestamp" in signed
        assert "recvWindow" in signed
        assert "signature" in signed
        assert signed["timestamp"].isdigit()

    def test_sign_preserves_original_params(self):
        signer = HMACSigner("test_key", "test_secret")
        original = {"symbol": "BTCUSDT", "side": "BUY"}
        signed = signer.sign(original)

        assert signed["symbol"] == "BTCUSDT"
        assert signed["side"] == "BUY"

    def test_get_headers(self):
        signer = HMACSigner("test_key", "test_secret")
        headers = signer.get_headers()
        assert headers == {"X-MBX-APIKEY": "test_key"}

    def test_create_signer_function(self):
        signer = create_signer("key", "secret")
        assert isinstance(signer, HMACSigner)
        assert signer.api_key == "key"


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
    def test_v1_signature_error(self):
        signer = HMACSigner("key", "secret")
        with pytest.raises(SignatureError):
            signer._generate_signature(None)  # type: ignore

    def test_v3_signature_error(self):
        signer = EIP712Signer(TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY)
        with pytest.raises(SignatureError):
            signer.sign(None)  # type: ignore
