import pytest
from asterdex.constants import (
    Network,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    V3_API_VERSION,
)
from asterdex.logging_config import get_logger, set_log_level, LogLevel


class TestConstants:
    def test_network_testnet(self):
        assert "testnet" in Network.TESTNET.rest_url.lower()

    def test_network_mainnet(self):
        assert "testnet" not in Network.MAINNET.rest_url.lower()

    def test_default_timeout(self):
        assert DEFAULT_TIMEOUT == 30

    def test_default_max_retries(self):
        assert DEFAULT_MAX_RETRIES == 3

    def test_v3_api_version(self):
        assert V3_API_VERSION == "v3"


class TestLogging:
    def test_get_logger(self):
        logger = get_logger("test")
        assert logger is not None

    def test_set_log_level(self):
        set_log_level(LogLevel.INFO)
