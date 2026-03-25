"""V3 API EIP712认证模块"""

import time
import urllib.parse
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data  # type: ignore

from ...exceptions import SignatureError
from ...logging_config import get_logger

logger = get_logger(__name__)

EIP712_DOMAIN = {
    "name": "AsterSignTransaction",
    "version": "1",
    "chainId": 714,
    "verifyingContract": "0x0000000000000000000000000000000000000000",
}

EIP712_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "Message": [{"name": "msg", "type": "string"}],
}


class EIP712Signer:
    """V3 API EIP712签名器"""

    _last_ms: int = 0
    _i: int = 0

    def __init__(self, user: str, signer: str, private_key: str):
        self.user = user
        self.signer = signer
        self.account = Account.from_key(private_key)

    @classmethod
    def get_nonce(cls) -> int:
        """生成Nonce (微秒级时间戳)"""
        now_ms = int(time.time())
        if now_ms == cls._last_ms:
            cls._i += 1
        else:
            cls._last_ms = now_ms
            cls._i = 0
        return now_ms * 1_000_000 + cls._i

    def sign(self, params: dict[str, Any]) -> tuple[dict[str, Any], str]:
        """签名参数

        Args:
            params: 原始参数

        Returns:
            (包含签名的参数字典, 签名hex)
        """
        try:
            nonce = str(self.get_nonce())
            signed_params = params.copy()
            signed_params["nonce"] = nonce
            signed_params["user"] = self.user
            signed_params["signer"] = self.signer

            query_string = urllib.parse.urlencode(
                {k: v for k, v in signed_params.items() if v is not None}
            )

            typed_data = {
                "types": EIP712_TYPES,
                "primaryType": "Message",
                "domain": EIP712_DOMAIN,
                "message": {"msg": query_string},
            }

            encoded = encode_typed_data(full_message=typed_data)
            signed = self.account.sign_message(encoded)
            signature = signed.signature.hex()

            signed_params["signature"] = signature
            logger.debug(f"V3签名: {query_string[:100]}... -> {signature[:20]}...")
            return signed_params, signature

        except Exception as e:
            raise SignatureError(f"V3签名失败: {e}") from e

    def get_headers(self) -> dict[str, str]:
        """获取认证请求头"""
        return {"Content-Type": "application/x-www-form-urlencoded"}


def create_signer(user: str, signer: str, private_key: str) -> EIP712Signer:
    """创建EIP712签名器"""
    return EIP712Signer(user, signer, private_key)
