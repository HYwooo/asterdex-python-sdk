"""V1 API HMAC认证模块"""

import hashlib
import hmac
import time
from typing import Any

from ...exceptions import SignatureError
from ...logging_config import get_logger

logger = get_logger(__name__)


class HMACSigner:
    """V1 API HMAC签名器"""

    def __init__(self, api_key: str, secret_key: str, recv_window: int = 5000):
        self.api_key = api_key
        self.secret_key = secret_key
        self.recv_window = recv_window

    def _generate_signature(self, params: dict[str, Any]) -> str:
        """生成HMAC SHA256签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        try:
            sorted_params = sorted(params.items())
            query_string = "&".join(f"{k}={v}" for k, v in sorted_params if v)
            signature = hmac.new(
                self.secret_key.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            logger.debug(f"签名: {query_string} -> {signature}")
            return signature
        except Exception as e:
            raise SignatureError(f"生成签名失败: {e}") from e

    def sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """签名参数

        Args:
            params: 原始参数

        Returns:
            包含签名和时间戳的参数字典
        """
        signed_params = params.copy()
        signed_params["timestamp"] = str(int(time.time() * 1000))
        signed_params["recvWindow"] = str(self.recv_window)
        signed_params["signature"] = self._generate_signature(signed_params)
        return signed_params

    def get_headers(self) -> dict[str, str]:
        """获取认证请求头"""
        return {"X-MBX-APIKEY": self.api_key}


def create_signer(api_key: str, secret_key: str) -> HMACSigner:
    """创建HMAC签名器"""
    return HMACSigner(api_key, secret_key)
