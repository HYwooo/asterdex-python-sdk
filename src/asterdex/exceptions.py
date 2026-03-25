"""Aster DEX异常定义

定义SDK专用的异常类层次结构。
"""

from typing import Any, Optional


class AsterError(Exception):
    """Aster DEX SDK基础异常类

    所有SDK专用异常的基类。
    """

    def __init__(self, message: str, code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class NetworkError(AsterError):
    """网络相关错误

    包括连接超时、DNS解析失败、SSL错误等。
    """


class APIError(AsterError):
    """API返回错误

    当API返回错误响应时抛出。
    """

    def __init__(self, message: str, code: int, response_data: Optional[dict] = None):
        super().__init__(message, code=code, details=response_data)
        self.response_data = response_data


class AuthenticationError(AsterError):
    """认证错误

    API密钥无效、签名错误等认证相关问题。
    """


class RateLimitError(AsterError):
    """限流错误

    触发API限流时抛出。
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, code=429)
        self.retry_after = retry_after


class ValidationError(AsterError):
    """参数验证错误

    输入参数不符合要求时抛出。
    """

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code=400)
        self.field = field


class OrderError(AsterError):
    """订单操作错误

    下单、撤单等订单操作失败时抛出。
    """

    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        code: Optional[int] = None,
    ):
        super().__init__(message, code=code)
        self.order_id = order_id


class WebSocketError(AsterError):
    """WebSocket错误

    WebSocket连接、订阅等操作失败时抛出。
    """

    def __init__(self, message: str, connection_state: Optional[str] = None):
        super().__init__(message)
        self.connection_state = connection_state


class WSConnectionError(WebSocketError):
    """WebSocket连接错误

    首次连接或重连失败时抛出。
    """

    pass


class WSReconnectError(WebSocketError):
    """WebSocket重连错误

    达到最大重连次数后仍然失败时抛出。
    """

    pass


class WSFallbackError(WebSocketError):
    """WebSocket Fallback错误

    从WebSocket切换到REST API时发生错误。
    """

    pass


class WSTimeoutError(WebSocketError):
    """WebSocket超时错误

    连接超时或消息接收超时。
    """

    pass


class StreamError(AsterError):
    """Stream订阅错误

    订阅或取消订阅stream失败时抛出。
    """


class SignatureError(AsterError):
    """签名错误

    V1 HMAC或V3 EIP712签名失败时抛出。
    """


class TimeoutError(AsterError):
    """请求超时错误

    API请求超过超时时间时抛出。
    """
