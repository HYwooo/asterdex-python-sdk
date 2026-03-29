# Aster DEX Python SDK

Aster DEX Python SDK - 支持 V3 (EIP712) 完整 API 的异步交易库

> **语言:** [English](README.md) | [中文](README_zh.md)

## 特性

- 异步优先：基于 aiohttp 和 websockets 的纯异步实现
- V3 EIP712 签名：结构化数据签名，更安全
- WebSocket：内置长连接、自动重连、心跳管理
- HTTP/HTTPS 代理：内置代理支持，支持认证
- 默认 Testnet：安全优先，默认连接测试网
- 类型安全：完整的类型注解
- 分级日志：DEBUG/INFO/WARNING/ERROR 便于调试
- 高性能：连接池复用、内存优化设计
- 漏桶限速器：全局请求限速，优先级队列保障

## 安装

```bash
pip install git+https://github.com/HYwooo/asterdex-python-sdk.git
```

或从源码安装：

```bash
git clone https://github.com/HYwooo/asterdex-python-sdk.git
cd asterdex-python-sdk
pip install -e .
```

## 快速开始（推荐使用 V3 API）

### V3 API（EIP712 认证）

```python
import asyncio
from asterdex import Client, Network

async def main():
    # V3 使用 EIP712 签名（推荐）
    client = Client.v3(
        user="0xYourMainWalletAddress",      # 主账户钱包地址
        signer="0xYourSignerAddress",        # API 钱包地址
        private_key="0xYourPrivateKey",      # 私钥
        network=Network.TESTNET              # 默认 Testnet
    )
    
    # 获取账户信息
    account = await client.get_account_info()
    print(f"账户余额: {account.get('totalWalletBalance')}")
    
    # 下单（市价单）
    order = await client.create_order(
        symbol="BTCUSDT",
        side="BUY",
        type="MARKET",
        quantity="0.001"
    )
    print(f"订单已创建: {order.get('orderId')}")
    
    await client.close()

asyncio.run(main())
```

### 限价单 + 高级参数

```python
order = await client.create_order(
    symbol="BTCUSDT",
    side="BUY",
    type="LIMIT",
    quantity="0.001",
    price="50000",
    time_in_force="GTC",
    reduce_only=False,
    close_position=False,
    stop_price=None,
    position_side="BOTH"
)
```

### WebSocket 实时数据

```python
import asyncio
from asterdex import WebSocketClient, Network

async def main():
    ws = WebSocketClient(network=Network.TESTNET)
    
    @ws.on_book_ticker("BTCUSDT")
    async def on_ticker(ticker):
        print(f"买一: {ticker.bid_price} | 卖一: {ticker.ask_price}")
    
    @ws.on_kline("BTCUSDT", "1m")
    async def on_kline(kline):
        print(f"K线: O={kline.open} H={kline.high} L={kline.low} C={kline.close}")
    
    @ws.on_error
    async def on_error(error):
        print(f"WebSocket 错误: {error}")
    
    await ws.connect()
    print("WebSocket 已连接，等待数据...")
    
    await asyncio.sleep(60)
    await ws.disconnect()

asyncio.run(main())
```

### WebSocket 批量订阅

一次订阅多个 stream，高效便捷：

```python
import asyncio
from asterdex import WebSocketClient, Network

async def main():
    ws = WebSocketClient(network=Network.TESTNET)
    
    @ws.on_book_ticker("BTCUSDT")
    async def on_btc_ticker(ticker):
        print(f"BTC - 买一: {ticker.bid_price} | 卖一: {ticker.ask_price}")
    
    @ws.on_book_ticker("ETHUSDT")
    async def on_eth_ticker(ticker):
        print(f"ETH - 买一: {ticker.bid_price} | 卖一: {ticker.ask_price}")
    
    await ws.connect()
    
    # 批量订阅多个 stream
    streams = ["btcusdt@bookTicker", "ethusdt@bookTicker", "btcusdt@kline_1m"]
    await ws.subscribe_batch(streams)
    print(f"已批量订阅 {len(streams)} 个 stream")
    
    await asyncio.sleep(60)
    await ws.disconnect()

asyncio.run(main())
```

---

## 公开端点 vs 私有端点

SDK 方法分为公开端点（无需认证）和私有端点（需要认证）。

### 公开端点（无需认证）

```python
client = Client.v3(network=Network.TESTNET)

await client.ping()
await client.get_time()
await client.get_order_book("BTCUSDT")
await client.get_klines("BTCUSDT", "1h")
await client.get_ticker_24h("BTCUSDT")
await client.get_mark_price("BTCUSDT")
```

### 私有端点（需要认证）

```python
client = Client.v3(
    user="0x...",
    signer="0x...",
    private_key="0x...",
    network=Network.TESTNET
)

try:
    await client.get_balance()
except AuthenticationError as e:
    print(f"需要认证: {e}")
```

---

## 全局配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ASTERDEX_NETWORK` | `testnet` | 网络：`testnet` 或 `mainnet` |
| `ASTERDEX_LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR` |
| `ASTERDEX_TIMEOUT` | `30` | 请求超时秒数 |
| `ASTERDEX_MAX_RETRIES` | `3` | 最大重试次数 |

### 代理配置

SDK 内置支持 HTTP/HTTPS 代理：

```python
from asterdex import Client, WebSocketClient, HybridClient, Network

# HTTP 代理
client = Client.v3(
    user="0x...",
    signer="0x...",
    private_key="0x...",
    network=Network.TESTNET,
    proxy="http://user:password@proxy-host:port"
)

# HTTPS 代理
ws = WebSocketClient(
    network=Network.TESTNET,
    proxy="https://proxy-host:port"
)

# 带认证的 HTTPS 代理
hybrid = HybridClient(
    user="0x...",
    signer="0x...",
    private_key="0x...",
    proxy="https://user:password@proxy-host:port"
)
```

**支持的代理类型：**
- `http://` - HTTP 代理
- `https://` - HTTPS 代理

### 日志配置

```python
from asterdex import LogLevel, set_log_level
from asterdex.logging_config import get_logger

set_log_level(LogLevel.DEBUG)

logger = get_logger("asterdex.api.v3")
logger.debug("调试信息")
```

---

## 常量定义

### 网络

```python
from asterdex import Network

Network.TESTNET  # 测试网（默认）
Network.MAINNET  # 主网
```

### 订单类型

```python
from asterdex.constants import (
    ORDER_TYPE_LIMIT,
    ORDER_TYPE_MARKET,
    ORDER_TYPE_STOP,
    ORDER_TYPE_STOP_MARKET,
    ORDER_TYPE_TAKE_PROFIT,
    ORDER_TYPE_TAKE_PROFIT_MARKET,
    ORDER_TYPE_TRAILING_STOP_MARKET,
)
```

### 订单方向

```python
from asterdex.constants import (
    ORDER_SIDE_BUY,   # 买入
    ORDER_SIDE_SELL,  # 卖出
)
```

### 有效时间

```python
from asterdex.constants import (
    TIME_IN_FORCE_GTC,    # Good Till Cancel - 主动取消或成交
    TIME_IN_FORCE_IOC,     # Immediate or Cancel - 立即成交或取消
    TIME_IN_FORCE_FOK,    # Fill or Kill - 全部成交或取消
    TIME_IN_FORCE_GTX,    # Good Till Crossing (Post Only) - 做市商友好，只作为maker成交
    TIME_IN_FORCE_HIDDEN,  # 隐藏订单
)
```

### 保证金模式

```python
from asterdex.constants import (
    MARGIN_TYPE_ISOLATED,  # 逐仓
    MARGIN_TYPE_CROSSED,   # 全仓
)
```

---

## 完整 API 参考

### 市场数据（无需认证）

| 方法 | 说明 | API 端点 |
|------|------|---------|
| `ping()` | 测试连接 | GET /fapi/v3/ping |
| `get_time()` | 服务器时间 | GET /fapi/v3/time |
| `get_exchange_info()` | 交易所信息 | GET /fapi/v3/exchangeInfo |
| `get_order_book(symbol, limit)` | 订单簿 | GET /fapi/v3/depth |
| `get_trades(symbol, limit)` | 最近成交 | GET /fapi/v3/trades |
| `get_klines(symbol, interval, limit, start_time, end_time)` | K线数据 | GET /fapi/v3/klines |
| `get_ticker_price(symbol)` | 价格 Ticker | GET /fapi/v3/ticker/price |
| `get_book_ticker(symbol)` | 订单簿 Ticker | GET /fapi/v3/ticker/bookTicker |
| `get_ticker_24h(symbol)` | 24小时行情 | GET /fapi/v3/ticker/24hr |
| `get_mark_price(symbol)` | 标记价格 | GET /fapi/v3/premiumIndex |
| `get_funding_rate(symbol)` | 资金费率 | GET /fapi/v3/fundingRate |
| `get_historical_trades(symbol, limit, from_id)` | 历史成交 | GET /fapi/v3/historicalTrades |
| `get_agg_trades(symbol, limit, start_time, end_time, from_id)` | 聚合交易 | GET /fapi/v3/aggTrades |
| `get_index_price_klines(symbol, interval, limit, start_time, end_time)` | 指数价格 K线 | GET /fapi/v3/indexPriceKlines |
| `get_mark_price_klines(symbol, interval, limit, start_time, end_time)` | 标记价格 K线 | GET /fapi/v3/markPriceKlines |

### 交易（需要签名）

| 方法 | 说明 | API 端点 |
|------|------|---------|
| `create_order(...)` | 创建订单 | POST /fapi/v3/order |
| `batch_orders(orders)` | 批量下单 | POST /fapi/v3/batchOrders |
| `cancel_order(symbol, order_id)` | 取消订单 | DELETE /fapi/v3/order |
| `cancel_all_open_orders(symbol)` | 取消所有挂单 | DELETE /fapi/v3/allOpenOrders |
| `cancel_multiple_orders(symbol, order_ids)` | 批量取消订单 | DELETE /fapi/v3/batchOrders |
| `countdown_cancel_all(symbol, countdown_time)` | 定时取消所有 | POST /fapi/v3/countdownCancelAll |
| `set_leverage(symbol, leverage)` | 调整杠杆 | POST /fapi/v3/leverage |
| `set_margin_type(symbol, margin_type)` | 保证金模式 | POST /fapi/v3/marginType |
| `modify_isolated_margin(symbol, amount, type)` | 调整逐仓保证金 | POST /fapi/v3/positionMargin |
| `change_position_mode(hedge_mode)` | 切换持仓模式 | POST /fapi/v3/positionSide |
| `set_multi_assets_margin(multi_assets_margin)` | 多资产保证金 | POST /fapi/v3/multiAssetsMargin |
| `transfer_spot_futures(asset, amount, type)` | 现货合约转账 | POST /fapi/v3/transfer |
| `noop(nonce)` | Noop 操作 | POST /fapi/v3/noop |

### 用户数据（需要签名）

| 方法 | 说明 | API 端点 |
|------|------|---------|
| `get_order(symbol, order_id)` | 查询订单 | GET /fapi/v3/order |
| `get_single_open_order(symbol, order_id)` | 查询单笔挂单 | GET /fapi/v3/openOrder |
| `get_open_orders(symbol)` | 查询挂单 | GET /fapi/v3/openOrders |
| `get_all_orders(symbol, limit, start_time, end_time)` | 查询所有订单 | GET /fapi/v3/allOrders |
| `get_balance()` | 账户余额 | GET /fapi/v3/balance |
| `get_account_info()` | 账户信息 | GET /fapi/v3/account |
| `get_position(symbol)` | 持仓信息 | GET /fapi/v3/positionRisk |
| `get_user_trades(symbol, limit, start_time, end_time)` | 成交历史 | GET /fapi/v3/userTrades |
| `get_income_history(symbol, limit, start_time, end_time)` | 收益历史 | GET /fapi/v3/income |
| `get_commission_rate(symbol)` | 手续费率 | GET /fapi/v3/commissionRate |
| `get_leverage_bracket(symbol)` | 杠杆分级 | GET /fapi/v3/leverageBracket |
| `get_position_margin_history(symbol, limit, start_time, end_time)` | 保证金历史 | GET /fapi/v3/positionMargin/history |
| `get_adl_quantile(symbol)` | ADL 分位 | GET /fapi/v3/adlQuantile |
| `get_force_orders(symbol, limit, start_time, end_time)` | 强平订单 | GET /fapi/v3/forceOrders |
| `get_position_mode()` | 持仓模式 | GET /fapi/v3/positionSide |
| `get_multi_assets_margin()` | 多资产模式 | GET /fapi/v3/multiAssetsMargin |

### 用户流（WebSocket 需要）

| 方法 | 说明 | API 端点 |
|------|------|---------|
| `start_user_stream()` | 开启用户流 | POST /fapi/v3/listenKey |
| `keepalive_user_stream(listen_key)` | 续期用户流 | PUT /fapi/v3/listenKey |
| `close_user_stream(listen_key)` | 关闭用户流 | DELETE /fapi/v3/listenKey |

---

## 漏桶限速器

SDK 内置全局漏桶限速器，支持：

- **RAW_REQUEST**：原始请求限速（默认 6000/min）
- **REQUEST_WEIGHT**：请求权重限速（默认 6000/min）
- **ORDER**：订单频率限速（默认 300/min）

### 优先级队列

Close Position 和 Reduce Only 订单具有最高优先级，不受限速影响。

```python
status = client.rate_limiter.get_status()
print(f"剩余请求次数: {status['raw_request_tokens']}")
print(f"剩余订单次数: {status['order_tokens']}")
```

---

## 错误处理

```python
import asyncio
from asterdex import Client
from asterdex.exceptions import (
    AsterError,
    APIError,
    AuthenticationError,
    RateLimitError,
    WebSocketError,
    OrderError,
    ValidationError,
    SignatureError,
    TimeoutError,
)

async def main():
    try:
        client = Client.v3(user="...", signer="...", private_key="...")
        order = await client.create_order(...)
    except AuthenticationError as e:
        print(f"认证失败: {e}")
    except RateLimitError as e:
        print(f"触发限流: {e}")
    except OrderError as e:
        print(f"订单错误: {e}")
    except APIError as e:
        print(f"API 错误: {e.code} - {e.message}")
    except AsterError as e:
        print(f"SDK 错误: {e}")

asyncio.run(main())
```

---

## 要求

- Python >= 3.9
- aiohttp >= 3.9.0
- websockets >= 12.0
- eth-account >= 0.11.0

---

## 免责条款

本软件按"原样"提供，不提供任何明示或暗示的保证。在法律允许的范围内，作者不对因使用本软件而产生的任何损失承担责任，包括但不限于：

- 交易亏损
- API 调用错误
- 网络连接问题
- 数据丢失
- 任何间接、附带、特殊或后果性损害

**使用本软件即表示您理解并接受这些风险。请确保：**

1. 仅使用您可以承受损失的账户和资金
2. 在生产环境使用前进行充分测试
3. 了解加密货币交易的风险
4. 遵守当地法律法规

---

## 许可证

### 主许可证：Apache 2.0

本库采用 Apache License 2.0 许可证。

这意味着：
- 您可以在商业项目中使用本库
- 您可以修改本库源代码
- 您可以分发修改后的版本
- 您可以将本库链接到您的应用程序中，无需开源

### 依赖库的许可证

本库使用以下第三方库：

| 库 | 许可证 |
|---|--------|
| aiohttp | Apache 2.0 |
| websockets | BSD |
| pydantic | MIT |
| eth-account | Apache 2.0 |
| hexbytes | Apache 2.0 |
| typing-extensions | PSF |

---

## 致谢

- [Aster DEX](https://www.asterdex.com/) - 提供 API 支持
- [eth-account](https://github.com/ethereum/eth-account) - EIP712 签名实现