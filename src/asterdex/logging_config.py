"""Aster DEX日志配置

提供分级日志功能，支持环境变量ASTERDEX_LOG_LEVEL配置。
"""

import logging
import os
import sys

from .constants import DEFAULT_LOG_LEVEL, LogLevel

_LOGGERS: dict[str, logging.Logger] = {}
_CONFIGURED = False


def _get_color(level: int) -> str:
    """获取日志级别对应的颜色ANSI码"""
    colors = {
        logging.DEBUG: "\033[36m",  # 青色
        logging.INFO: "\033[32m",  # 绿色
        logging.WARNING: "\033[33m",  # 黄色
        logging.ERROR: "\033[31m",  # 红色
        logging.CRITICAL: "\033[35m",  # 紫色
    }
    return colors.get(level, "")


_RESET_COLOR = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        color = _get_color(record.levelno)
        record.levelname = f"{color}{record.levelname}{_RESET_COLOR}"
        return super().format(record)


def _setup_logging(level: LogLevel) -> None:
    """配置全局日志系统"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = level.level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    if sys.stdout.isatty():
        formatter = ColoredFormatter(fmt, datefmt)
    else:
        formatter = logging.Formatter(fmt, datefmt)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger

    Args:
        name: logger名称，通常使用模块路径

    Returns:
        配置好的Logger实例
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    level_str = os.getenv("ASTERDEX_LOG_LEVEL", DEFAULT_LOG_LEVEL.value)
    try:
        level = LogLevel(level_str.upper())
    except ValueError:
        level = DEFAULT_LOG_LEVEL

    _setup_logging(level)
    logger = logging.getLogger(name)
    _LOGGERS[name] = logger
    return logger


def set_log_level(level: LogLevel) -> None:
    """设置全局日志级别

    Args:
        level: 日志级别
    """
    global _CONFIGURED
    _CONFIGURED = False
    _setup_logging(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level.level)

    for handler in root_logger.handlers:
        handler.setLevel(level.level)


def set_module_log_level(name: str, level: LogLevel) -> None:
    """设置特定模块的日志级别

    Args:
        name: 模块名称 (例如 "asterdex.api.v1")
        level: 日志级别
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.level)
