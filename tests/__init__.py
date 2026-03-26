"""测试配置"""

import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"环境变量 {name} 未设置，请创建 .env.local 文件")
    return value


TESTNET_V3_USER = _require_env("ASTERDEX_TEST_USER")
TESTNET_V3_SIGNER = _require_env("ASTERDEX_TEST_SIGNER")
TESTNET_V3_PRIVATE_KEY = _require_env("ASTERDEX_TEST_PRIVATE_KEY")
