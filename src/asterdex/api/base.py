"""API基础HTTP客户端

基于aiohttp的REST API客户端，包含重试、超时、日志、限速等功能。
"""

import asyncio
from typing import Any, Optional

import aiohttp

from ..constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, Network
from ..exceptions import APIError, NetworkError, RateLimitError, TimeoutError
from ..logging_config import get_logger
from .rate_limiter import LeakyBucketRateLimiter, get_rate_limiter

logger = get_logger(__name__)


class BaseAPIClient:
    """API基础客户端"""

    def __init__(
        self,
        network: Network = Network.TESTNET,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.base_url = network.rest_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_used: int = 0
        self._rate_limiter: Optional[LeakyBucketRateLimiter] = None
        self._network = network

    @property
    def rate_limiter(self) -> LeakyBucketRateLimiter:
        """获取限速器实例"""
        if self._rate_limiter is None:
            self._rate_limiter = get_rate_limiter(self._network)
        return self._rate_limiter

    def update_rate_limits(self, rate_limits: list[dict[str, Any]]) -> None:
        """从 exchangeInfo 更新限速配置"""
        self.rate_limiter._parse_rate_limits(rate_limits)

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建aiohttp会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """发送HTTP请求

        Args:
            method: HTTP方法
            path: API路径
            params: URL查询参数
            data: 请求体数据
            headers: 请求头

        Returns:
            响应JSON数据

        Raises:
            APIError: API返回错误
            NetworkError: 网络错误
            RateLimitError: 触发限流
        """
        is_priority = self._is_priority_request(path, params, data)
        request_data = data or params

        if method in ["POST", "PUT", "DELETE"] and "order" in path.lower():
            await self.rate_limiter.acquire_order()

        await self.rate_limiter.acquire(weight=1, is_priority=is_priority, params=request_data)

        url = f"{self.base_url}{path}"
        session = await self._get_session()

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"请求: {method} {url} params={params} data={data}")

                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=headers,
                ) as response:
                    self._rate_limit_used = int(response.headers.get("X-MBX-USED-WEIGHT-1M", 0))

                    text = await response.text()

                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"触发限流, retry_after={retry_after}")
                        raise RateLimitError(retry_after=retry_after)

                    if response.status >= 500:
                        logger.warning(f"服务器错误 {response.status}, 重试 {attempt + 1}")
                        last_error = APIError(
                            f"Server error: {response.status}",
                            response.status,
                        )
                        await asyncio.sleep(2**attempt)
                        continue

                    if response.status >= 400:
                        try:
                            error_data = await response.json()
                        except Exception:
                            error_data = {"msg": text}

                        code_value = error_data.get("code")
                        code = int(code_value) if code_value is not None else response.status
                        msg = error_data.get("msg", "Unknown error")
                        logger.error(f"API错误: {code} - {msg}")
                        raise APIError(msg, code, error_data)

                    logger.debug(f"响应: {text[:500]}")

                    try:
                        result = await response.json()
                    except Exception:
                        result = {"raw": text}

                    return result

            except RateLimitError:
                raise
            except APIError:
                raise
            except asyncio.TimeoutError:
                logger.warning(f"请求超时, 重试 {attempt + 1}")
                last_error = TimeoutError(f"Request timeout: {url}")
                await asyncio.sleep(2**attempt)
            except aiohttp.ClientError as e:
                logger.warning(f"网络错误: {e}, 重试 {attempt + 1}")
                last_error = NetworkError(f"Network error: {e}")
                await asyncio.sleep(2**attempt)

        raise last_error or NetworkError("Max retries exceeded")

    def _is_priority_request(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """判断是否为优先级请求

        Close Position 和 Reduce Only 订单具有最高优先级，不受限速影响
        """
        request_data = data or params

        if request_data is None:
            return False

        close_position = request_data.get("closePosition")
        reduce_only = request_data.get("reduceOnly")

        return (
            close_position == "true"
            or close_position is True
            or reduce_only == "true"
            or reduce_only is True
        )

    async def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """发送GET请求"""
        return await self._request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """发送POST请求"""
        return await self._request("POST", path, data=data, headers=headers)

    async def put(
        self,
        path: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """发送PUT请求"""
        return await self._request("PUT", path, data=data, headers=headers)

    async def delete(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """发送DELETE请求"""
        return await self._request("DELETE", path, params=params, headers=headers)

    @property
    def rate_limit_used(self) -> int:
        """获取当前使用的限流权重"""
        return self._rate_limit_used
