import pytest
from asterdex.exceptions import (
    AsterError,
    NetworkError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    OrderError,
    WebSocketError,
    StreamError,
    SignatureError,
    TimeoutError,
)


class TestExceptions:
    def test_aster_error_base(self):
        err = AsterError("Test error")
        assert str(err) == "Test error"
        assert err.message == "Test error"
        assert err.code is None

    def test_aster_error_with_code(self):
        err = AsterError("Test error", code=500)
        assert "[500] Test error" in str(err)
        assert err.code == 500

    def test_aster_error_with_details(self):
        err = AsterError("Test error", details={"key": "value"})
        assert err.details == {"key": "value"}

    def test_network_error(self):
        err = NetworkError("Network failed")
        assert "Network failed" in str(err)
        assert isinstance(err, AsterError)

    def test_api_error(self):
        err = APIError("API failed", 400, {"msg": "error"})
        assert "API failed" in str(err)
        assert err.code == 400
        assert err.response_data == {"msg": "error"}

    def test_authentication_error(self):
        err = AuthenticationError("Auth failed")
        assert "Auth failed" in str(err)
        assert isinstance(err, AsterError)

    def test_rate_limit_error(self):
        err = RateLimitError(retry_after=60)
        assert err.code == 429
        assert err.retry_after == 60

    def test_rate_limit_error_default(self):
        err = RateLimitError()
        assert err.code == 429
        assert err.retry_after is None

    def test_validation_error(self):
        err = ValidationError("Invalid param", field="symbol")
        assert "Invalid param" in str(err)
        assert err.code == 400
        assert err.field == "symbol"

    def test_order_error(self):
        err = OrderError("Order failed", order_id="12345", code=400)
        assert "Order failed" in str(err)
        assert err.order_id == "12345"
        assert err.code == 400

    def test_websocket_error(self):
        err = WebSocketError("WS failed", connection_state="disconnected")
        assert "WS failed" in str(err)
        assert err.connection_state == "disconnected"

    def test_stream_error(self):
        err = StreamError("Stream failed")
        assert "Stream failed" in str(err)
        assert isinstance(err, AsterError)

    def test_signature_error(self):
        err = SignatureError("Sign failed")
        assert "Sign failed" in str(err)
        assert isinstance(err, AsterError)

    def test_timeout_error(self):
        err = TimeoutError("Request timeout")
        assert "Request timeout" in str(err)
        assert isinstance(err, AsterError)
