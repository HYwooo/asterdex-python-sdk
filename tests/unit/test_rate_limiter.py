"""漏桶限速器单元测试"""

import pytest
import asyncio
import time
from asterdex.api.rate_limiter import (
    LeakyBucketRateLimiter,
    RateLimitConfig,
    RequestPriority,
    RateLimitType,
    RateLimitInterval,
    get_rate_limiter,
    update_rate_limits,
)
from asterdex.constants import Network


class TestRateLimitConfig:
    def test_rate_limit_config_creation(self):
        config = RateLimitConfig(
            rate_limit_type=RateLimitType.ORDER,
            interval=RateLimitInterval.MINUTE,
            limit=300,
        )
        assert config.rate_limit_type == RateLimitType.ORDER
        assert config.limit == 300


class TestLeakyBucketRateLimiter:
    def test_limiter_creation(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)
        assert limiter.network == Network.TESTNET
        status = limiter.get_status()
        assert status["raw_request_limit"] > 0
        assert status["order_limit"] > 0

    def test_initial_tokens(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)
        status = limiter.get_status()
        assert status["raw_request_tokens"] > 0
        assert status["order_tokens"] > 0

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        await limiter.acquire(weight=1)

        status = limiter.get_status()
        assert status["raw_request_tokens"] < status["raw_request_limit"]

    @pytest.mark.asyncio
    async def test_priority_bypass(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        initial_tokens = limiter._tokens[RateLimitType.RAW_REQUEST]

        await limiter.acquire(weight=1, is_priority=True)

        status = limiter.get_status()
        assert status["raw_request_tokens"] == initial_tokens

    @pytest.mark.asyncio
    async def test_priority_with_params(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        initial_tokens = limiter._tokens[RateLimitType.RAW_REQUEST]

        await limiter.acquire(weight=1, params={"reduceOnly": "true"})

        status = limiter.get_status()
        assert status["raw_request_tokens"] == initial_tokens

    @pytest.mark.asyncio
    async def test_priority_close_position(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        initial_tokens = limiter._tokens[RateLimitType.RAW_REQUEST]

        await limiter.acquire(weight=1, params={"closePosition": "true"})

        status = limiter.get_status()
        assert status["raw_request_tokens"] == initial_tokens

    @pytest.mark.asyncio
    async def test_order_rate_limiting(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)
        limiter._order_config.limit = 5

        for _ in range(5):
            await limiter.acquire_order()

        status = limiter.get_status()
        assert status["order_tokens"] <= 0

    @pytest.mark.asyncio
    async def test_rate_limiting_waits(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)
        limiter._raw_request_config.limit = 2
        limiter._tokens[RateLimitType.RAW_REQUEST] = 2.0

        start = time.time()
        await limiter.acquire(weight=2)
        await limiter.acquire(weight=2)
        await limiter.acquire(weight=2)
        elapsed = time.time() - start

        assert elapsed > 0.5

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        async def make_request():
            await limiter.acquire(weight=1)

        tasks = [make_request() for _ in range(5)]
        await asyncio.gather(*tasks)

        status = limiter.get_status()
        assert status["raw_request_tokens"] < status["raw_request_limit"]

    def test_parse_rate_limits_from_exchange_info(self):
        rate_limits = [
            {
                "rateLimitType": "RAW_REQUEST",
                "interval": "MINUTE",
                "intervalNum": 1,
                "limit": 5000,
            },
            {
                "rateLimitType": "REQUEST_WEIGHT",
                "interval": "MINUTE",
                "intervalNum": 1,
                "limit": 5000,
            },
            {
                "rateLimitType": "ORDER",
                "interval": "MINUTE",
                "intervalNum": 1,
                "limit": 200,
            },
        ]

        limiter = LeakyBucketRateLimiter(Network.TESTNET, rate_limits=rate_limits)

        assert limiter._raw_request_config.limit == 5000
        assert limiter._request_weight_config.limit == 5000
        assert limiter._order_config.limit == 200

    def test_get_rate_limit_info(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        info = limiter.get_rate_limit_info()

        assert "raw_request" in info
        assert "request_weight" in info
        assert "order" in info
        assert info["raw_request"]["limit"] > 0

    def test_reset_order_count(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)
        limiter._order_count = 10

        limiter.reset_order_count()

        assert limiter._order_count == 0

    def test_is_priority_order_reduce_only_true(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        assert limiter._is_priority_order({"reduceOnly": "true"})
        assert limiter._is_priority_order({"reduceOnly": True})

    def test_is_priority_order_close_position_true(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        assert limiter._is_priority_order({"closePosition": "true"})
        assert limiter._is_priority_order({"closePosition": True})

    def test_is_priority_order_false(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        assert not limiter._is_priority_order({"side": "BUY"})
        assert not limiter._is_priority_order({"reduceOnly": "false"})
        assert not limiter._is_priority_order(None)

    def test_get_status(self):
        limiter = LeakyBucketRateLimiter(Network.TESTNET)

        status = limiter.get_status()

        assert "raw_request_tokens" in status
        assert "request_weight_tokens" in status
        assert "order_tokens" in status
        assert "order_count_this_minute" in status
        assert "raw_request_limit" in status


class TestGlobalRateLimiter:
    def test_get_rate_limiter_singleton(self):
        limiter1 = get_rate_limiter(Network.TESTNET)
        limiter2 = get_rate_limiter(Network.TESTNET)

        assert limiter1 is limiter2

    def test_get_rate_limiter_different_networks(self):
        testnet_limiter = get_rate_limiter(Network.TESTNET)
        mainnet_limiter = get_rate_limiter(Network.MAINNET)

        assert testnet_limiter is not mainnet_limiter

    def test_update_rate_limits(self):
        rate_limits = [
            {
                "rateLimitType": "RAW_REQUEST",
                "interval": "MINUTE",
                "intervalNum": 1,
                "limit": 10000,
            },
        ]

        update_rate_limits(Network.TESTNET, rate_limits)

        limiter = get_rate_limiter(Network.TESTNET)
        assert limiter._raw_request_config.limit == 10000


class TestRequestPriority:
    def test_priority_enum_values(self):
        assert RequestPriority.HIGH.value == 1
        assert RequestPriority.NORMAL.value == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
