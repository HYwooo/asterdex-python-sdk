"""全局漏桶限速器

实现基于漏桶算法的请求限速，支持优先级队列让 Close Position/Reduce Only 订单优先处理。
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..constants import (
    DEFAULT_RATE_LIMIT_ORDER,
    DEFAULT_RATE_LIMIT_RAW_REQUEST,
    DEFAULT_RATE_LIMIT_REQUEST_WEIGHT,
    Network,
    RateLimitInterval,
    RateLimitType,
)
from ..logging_config import get_logger

logger = get_logger(__name__)


class RequestPriority(Enum):
    """请求优先级"""

    HIGH = 1  # Close Position / Reduce Only
    NORMAL = 2


@dataclass
class RateLimitConfig:
    """限速配置"""

    rate_limit_type: RateLimitType
    interval: RateLimitInterval
    limit: int
    num: int = 1


class LeakyBucketRateLimiter:
    """漏桶限速器

    使用令牌桶算法实现请求限速，支持:
    - RAW_REQUEST: 原始请求次数限制
    - REQUEST_WEIGHT: 请求权重限制
    - ORDER: 订单频率限制

    优先级机制: Close Position 和 Reduce Only 订单具有最高优先级，
    不受限速影响且优先处理。
    """

    def __init__(
        self,
        network: Network = Network.TESTNET,
        rate_limits: Optional[list[dict[str, Any]]] = None,
    ):
        self.network = network

        self._raw_request_config = RateLimitConfig(
            rate_limit_type=RateLimitType.RAW_REQUEST,
            interval=RateLimitInterval.MINUTE,
            limit=DEFAULT_RATE_LIMIT_RAW_REQUEST,
        )
        self._request_weight_config = RateLimitConfig(
            rate_limit_type=RateLimitType.REQUEST_WEIGHT,
            interval=RateLimitInterval.MINUTE,
            limit=DEFAULT_RATE_LIMIT_REQUEST_WEIGHT,
        )
        self._order_config = RateLimitConfig(
            rate_limit_type=RateLimitType.ORDER,
            interval=RateLimitInterval.MINUTE,
            limit=DEFAULT_RATE_LIMIT_ORDER,
        )

        self._tokens: dict[RateLimitType, float] = {
            RateLimitType.RAW_REQUEST: float(DEFAULT_RATE_LIMIT_RAW_REQUEST),
            RateLimitType.REQUEST_WEIGHT: float(DEFAULT_RATE_LIMIT_REQUEST_WEIGHT),
            RateLimitType.ORDER: float(DEFAULT_RATE_LIMIT_ORDER),
        }

        self._last_leak_time = time.time()
        self._order_count = 0

        self._lock = asyncio.Lock()
        self._priority_queue: list[tuple[RequestPriority, float]] = []

        if rate_limits:
            self._parse_rate_limits(rate_limits)

    def _parse_rate_limits(self, rate_limits: list[dict[str, Any]]) -> None:
        """从 exchangeInfo 解析限速配置"""
        for limit in rate_limits:
            rate_limit_type = limit.get("rateLimitType")
            limit_type = limit.get("limitType")
            interval_num = limit.get("intervalNum", 1)
            interval_letter = limit.get("interval", "MINUTE")
            limit_value = limit.get("limit", 0)

            if not rate_limit_type:
                continue

            try:
                if "RAW_REQUEST" in rate_limit_type.upper():
                    self._raw_request_config.limit = limit_value
                    self._tokens[RateLimitType.RAW_REQUEST] = float(limit_value)
                elif "REQUEST_WEIGHT" in rate_limit_type.upper():
                    self._request_weight_config.limit = limit_value
                    self._tokens[RateLimitType.REQUEST_WEIGHT] = float(limit_value)
                elif "ORDER" in rate_limit_type.upper():
                    self._order_config.limit = limit_value
                    self._tokens[RateLimitType.ORDER] = float(limit_value)
            except (ValueError, KeyError):
                logger.warning(f"Failed to parse rate limit: {limit}")

        logger.info(
            f"Rate limits updated: RAW={self._raw_request_config.limit}, "
            f"WEIGHT={self._request_weight_config.limit}, ORDER={self._order_config.limit}"
        )

    def _is_priority_order(self, params: Optional[dict[str, Any]] = None, path: str = "") -> bool:
        """判断是否为优先级订单

        Close Position 和 Reduce Only 订单具有最高优先级
        """
        if params is None:
            return False

        close_position = params.get("closePosition") or params.get("close_position")
        reduce_only = params.get("reduceOnly") or params.get("reduce_only")

        return (
            close_position == "true"
            or close_position is True
            or reduce_only == "true"
            or reduce_only is True
        )

    async def acquire(
        self,
        weight: int = 1,
        is_priority: bool = False,
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        """获取请求令牌

        Args:
            weight: 请求权重
            is_priority: 是否为优先级请求
            params: 请求参数，用于检测优先级订单
        """
        if is_priority or self._is_priority_order(params):
            logger.debug("Priority request bypasses rate limiting")
            return

        async with self._lock:
            self._leak()

            min_tokens = min(
                self._tokens[RateLimitType.RAW_REQUEST] - weight,
                self._tokens[RateLimitType.REQUEST_WEIGHT] - weight,
            )

            if min_tokens < 0:
                wait_time = abs(min_tokens) / self._get_leak_rate()
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._leak()

            self._tokens[RateLimitType.RAW_REQUEST] -= weight
            self._tokens[RateLimitType.REQUEST_WEIGHT] -= weight

    async def acquire_order(self) -> None:
        """获取订单令牌 (ORDER 限速)"""
        async with self._lock:
            self._leak()

            tokens = self._tokens[RateLimitType.ORDER]
            if tokens < 1:
                wait_time = (1 - tokens) / self._get_order_leak_rate()
                logger.warning(f"Order rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._leak()

            self._tokens[RateLimitType.ORDER] -= 1
            self._order_count += 1

    def release(self, weight: int = 1) -> None:
        """释放令牌 (仅用于记录，不实际退还)"""
        pass

    def release_order(self) -> None:
        """释放订单令牌"""
        pass

    def _leak(self) -> None:
        """漏桶漏水 - 根据时间流逝补充令牌"""
        now = time.time()
        elapsed = now - self._last_leak_time

        leak_rate = self._get_leak_rate()
        order_leak_rate = self._get_order_leak_rate()

        for limit_type in [RateLimitType.RAW_REQUEST, RateLimitType.REQUEST_WEIGHT]:
            current = self._tokens[limit_type]
            config = (
                self._raw_request_config
                if limit_type == RateLimitType.RAW_REQUEST
                else self._request_weight_config
            )
            self._tokens[limit_type] = min(config.limit, current + elapsed * leak_rate)

        self._tokens[RateLimitType.ORDER] = min(
            self._order_config.limit, self._tokens[RateLimitType.ORDER] + elapsed * order_leak_rate
        )

        self._last_leak_time = now

    def _get_leak_rate(self) -> float:
        """获取普通请求的泄漏速率 (令牌/秒)"""
        return self._raw_request_config.limit / 60.0

    def _get_order_leak_rate(self) -> float:
        """获取订单的泄漏速率 (令牌/秒)"""
        return self._order_config.limit / 60.0

    def get_status(self) -> dict[str, Any]:
        """获取限速器状态"""
        self._leak()
        return {
            "raw_request_tokens": round(self._tokens[RateLimitType.RAW_REQUEST], 2),
            "request_weight_tokens": round(self._tokens[RateLimitType.REQUEST_WEIGHT], 2),
            "order_tokens": round(self._tokens[RateLimitType.ORDER], 2),
            "order_count_this_minute": self._order_count,
            "raw_request_limit": self._raw_request_config.limit,
            "request_weight_limit": self._request_weight_config.limit,
            "order_limit": self._order_config.limit,
        }

    def get_rate_limit_info(self) -> dict[str, Any]:
        """获取限速信息"""
        return {
            "raw_request": {
                "limit": self._raw_request_config.limit,
                "remaining": int(self._tokens[RateLimitType.RAW_REQUEST]),
            },
            "request_weight": {
                "limit": self._request_weight_config.limit,
                "remaining": int(self._tokens[RateLimitType.REQUEST_WEIGHT]),
            },
            "order": {
                "limit": self._order_config.limit,
                "remaining": int(self._tokens[RateLimitType.ORDER]),
            },
        }

    def reset_order_count(self) -> None:
        """重置订单计数"""
        self._order_count = 0


_global_rate_limiters: dict[str, LeakyBucketRateLimiter] = {}


def get_rate_limiter(network: Network = Network.TESTNET) -> LeakyBucketRateLimiter:
    """获取全局限速器实例"""
    key = network.value
    if key not in _global_rate_limiters:
        _global_rate_limiters[key] = LeakyBucketRateLimiter(network)
    return _global_rate_limiters[key]


def update_rate_limits(network: Network, rate_limits: list[dict[str, Any]]) -> None:
    """更新全局限速配置"""
    limiter = get_rate_limiter(network)
    limiter._parse_rate_limits(rate_limits)
