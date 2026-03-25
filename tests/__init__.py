"""测试配置"""

import os


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"环境变量 {name} 未设置，请创建 .env.local 文件")
    return value


TESTNET_V3_USER = _require_env("ASTERDEX_TEST_USER")
TESTNET_V3_SIGNER = _require_env("ASTERDEX_TEST_SIGNER")
TESTNET_V3_PRIVATE_KEY = _require_env("ASTERDEX_TEST_PRIVATE_KEY")
TEST_V1_API_KEY = _require_env("TEST_V1_API_KEY")
TEST_V1_SECRET_KEY = _require_env("TEST_V1_SECRET_KEY")
