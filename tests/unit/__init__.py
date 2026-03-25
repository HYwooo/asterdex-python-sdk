import pytest
from asterdex.api.v1.auth import HMACSigner
from asterdex.api.v3.auth import EIP712Signer


class TestHMACSigner:
    def test_sign_generates_signature(self):
        signer = HMACSigner("test_key", "test_secret")
        params = {"symbol": "BTCUSDT", "side": "BUY"}
        signed = signer.sign(params)

        assert "signature" in signed
        assert "timestamp" in signed
        assert signed["symbol"] == "BTCUSDT"

    def test_sign_adds_timestamp(self):
        signer = HMACSigner("api_key", "secret")
        params = {"test": "value"}
        signed = signer.sign(params)

        assert signed["timestamp"] is not None
        assert len(signed["timestamp"]) == 13

    def test_sign_adds_recv_window(self):
        signer = HMACSigner("key", "secret", recv_window=3000)
        params = {}
        signed = signer.sign(params)

        assert signed["recvWindow"] == "3000"

    def test_get_headers(self):
        signer = HMACSigner("my_key", "my_secret")
        headers = signer.get_headers()

        assert headers["X-MBX-APIKEY"] == "my_key"


class TestEIP712Signer:
    def test_signer_initialization(self):
        signer = EIP712Signer(user="0x123", signer="0x123", private_key="0xabc")
        assert signer.user == "0x123"
        assert signer.signer == "0x123"

    def test_get_nonce_unique(self):
        nonce1 = EIP712Signer.get_nonce()
        import time

        time.sleep(0.0001)
        nonce2 = EIP712Signer.get_nonce()
        assert nonce2 > nonce1

    def test_sign_returns_params_and_signature(self):
        signer = EIP712Signer(
            user="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
        )
        params, sig = signer.sign({"symbol": "BTCUSDT"})

        assert "nonce" in params
        assert "user" in params
        assert "signer" in params
        assert "signature" in params
        assert sig is not None
        assert len(sig) == 130

    def test_get_headers(self):
        signer = EIP712Signer("0x1", "0x1", "0x1")
        headers = signer.get_headers()

        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
