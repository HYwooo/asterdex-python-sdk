# Aster DEX SDK 详细使用指南

本指南面向 AI Agent 和开发者，详细说明 SDK 的每个模块、类和函数的作用及使用方法。

---

## 📁 项目结构

```
asterdex/
├── __init__.py           # 主入口，导出所有公共API
├── client.py             # 统一客户端入口 (Client.v3)
├── constants.py          # 常量定义 (枚举、网络配置、订单类型等)
├── exceptions.py         # 异常类层次结构
├── logging_config.py    # 日志配置
├── hybrid_client.py     # 混合客户端 (WebSocket + REST自动切换)
│
├── api/
│   ├── base.py          # 基础API客户端 (请求处理、限速、重试)
│   ├── rate_limiter.py  # 漏桶限速器
│   └── v3/
│       ├── client.py    # V3 API客户端 (EIP712签名)
│       └── auth.py      # V3 EIP712签名器
│
├── models/
│   ├── base.py          # 数据模型 (OrderBook, Order, Position等)
│   └── ws.py            # WebSocket数据模型
│
└── websocket/
    └── client.py        # WebSocket客户端
```

---

## 🎯 快速索引

| 需求 | 使用的类/函数 |
|------|--------------|
| 创建V3客户端 | `Client.v3(user, signer, private_key, network)` |
| 市场数据查询 | `client.market.*` 或直接调用 `client.get_xxx()` |
| 下单/撤单 | `client.order.*` 或直接调用 `client.create_order()` |
| WebSocket实时数据 | `WebSocketClient` 类 + `@ws.on_xxx()` 装饰器 |
| 自动降级客户端 | `HybridClient` 类 |
| 异常处理 | `asterdex.exceptions.*` |

---

## 1. 核心模块详解

### 1.1 asterdex.Client (主入口)

**文件**: `asterdex/client.py`

提供统一的客户端创建接口。

#### 创建V3客户端

```python
from asterdex import Client, Network

client = Client.v3(
    user="0x主账户钱包地址",          # 主账户钱包地址 (0x开头)
    signer="0xAPI签名者地址",         # API签名者钱包地址
    private_key="0x私钥",            # 私钥 (0x开头)
    network=Network.TESTNET,         # 默认testnet
    proxy="http://user:pass@host:port"  # 可选: 代理支持
)
```

#### 客户端属性访问

```python
# 市场数据 (所有API版本)
client.market.ping()
client.market.get_order_book("BTCUSDT")
client.market.get_klines("BTCUSDT", "1m")

# 订单操作
client.order.create(symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.001")
client.order.cancel("BTCUSDT", order_id=123)

# 账户操作 (V3)
client.account.get_balance()
client.account.get_position("BTCUSDT")

# 直接调用 (所有方法都在client上)
client.get_order_book("BTCUSDT")
client.create_order(...)
```

---

### 1.2 asterdex.WebSocketClient (WebSocket客户端)

**文件**: `asterdex/websocket/client.py`

用于接收实时市场数据推送。

#### 基础用法

```python
import asyncio
from asterdex import WebSocketClient, Network, ProductType

async def main():
    # 创建客户端
    ws = WebSocketClient(
        network=Network.MAINNET,      # 网络: TESTNET/MAINNET
        product=ProductType.FUTURES,  # 产品: FUTURES(默认)/SPOT
        use_combined=True,            # 使用combined stream格式
        ping_interval=60,             # 心跳间隔(秒)
        proxy="http://host:port"      # 可选: HTTP/HTTPS 代理
    )

    @ws.on_book_ticker("BTCUSDT")
    async def on_ticker(data):
        print(f"买一: {data['b']}, 卖一: {data['a']}")

    @ws.on_kline("BTCUSDT", "1m")
    async def on_kline(data):
        print(f"K线收线: {data['c']}")

    @ws.on_ticker("BTCUSDT")
    async def on_ticker_24h(data):
        print(f"24h涨跌幅: {data['P']}%")

    @ws.on_trade("BTCUSDT")
    async def on_trade(data):
        print(f"成交: {data['p']} @ {data['q']}")

    @ws.on_mark_price("BTCUSDT")
    async def on_mark_price(data):
        print(f"标记价格: {data['p']}")

    @ws.on_error
    async def on_error(err):
        print(f"错误: {err}")

    await ws.connect()
    await asyncio.sleep(60)
    await ws.disconnect()

asyncio.run(main())
```

#### Stream 装饰器

| 装饰器 | Stream名称 | 说明 |
|--------|-----------|------|
| `@ws.on_book_ticker("SYMBOL")` | `symbol@bookTicker` | 订单簿更新 (买一/卖一) |
| `@ws.on_kline("SYMBOL", "1m")` | `symbol@kline_1m` | K线数据 |
| `@ws.on_ticker("SYMBOL")` | `symbol@ticker` | 24小时行情 |
| `@ws.on_trade("SYMBOL")` | `symbol@aggTrade` | 聚合成交 |
| `@ws.on_mark_price("SYMBOL")` | `symbol@markPrice` | 标记价格 |
| `@ws.on("custom_stream")` | 自定义 | 通用订阅 |

#### 手动订阅/取消

```python
await ws.connect()

# 订阅
await ws.subscribe("btcusdt@bookTicker")
await ws.subscribe("btcusdt@ticker")

# 取消订阅
await ws.unsubscribe("btcusdt@bookTicker")

# 检查连接状态
print(ws.is_connected)  # True/False
```

---

### 1.3 asterdex.HybridClient (混合客户端)

**文件**: `asterdex/hybrid_client.py`

自动在 WebSocket 和 REST API 之间切换。WebSocket 失败时自动降级到 REST 轮询。

```python
import asyncio
from asterdex import HybridClient, Network

client = HybridClient(
    user="0x...",              # 需要认证时提供
    signer="0x...",
    private_key="0x...",
    network=Network.TESTNET,
    poll_interval=1.0,         # 初始轮询间隔(秒)
    max_poll_interval=5.0,     # 最大轮询间隔
    poll_step=0.5,             # 每次增加间隔
    no_limit=False,            # 是否有轮询上限
    proxy="http://host:port"   # 可选: 代理支持
)

@client.on_book_ticker("BTCUSDT")
async def on_ticker(data):
    print(f"实时价格: {data['b']} / {data['a']}")

await client.connect()
await asyncio.sleep(60)
await client.disconnect()
```

---

### 1.4 asterdex.constants (常量定义)

**文件**: `asterdex/constants.py`

#### 网络枚举

```python
from asterdex import Network

Network.TESTNET  # 测试网
Network.MAINNET  # 主网

# 获取URL
Network.TESTNET.get_rest_url()       # "https://fapi.asterdex-testnet.com"
Network.TESTNET.get_ws_url()         # "wss://fstream.asterdex-testnet.com"
Network.TESTNET.get_rest_url(product=ProductType.SPOT)  # 现货API
```

#### 产品类型枚举

```python
from asterdex import ProductType

ProductType.FUTURES  # 合约
ProductType.SPOT     # 现货
```

#### 订单类型常量

```python
from asterdex import (
    ORDER_SIDE_BUY,          # 买入
    ORDER_SIDE_SELL,         # 卖出
    ORDER_TYPE_LIMIT,        # 限价单
    ORDER_TYPE_MARKET,       # 市价单
    ORDER_TYPE_STOP,         # 止损单
    ORDER_TYPE_STOP_MARKET,  # 止损市价单
    ORDER_TYPE_TAKE_PROFIT,  # 止盈单
    ORDER_TYPE_TAKE_PROFIT_MARKET,  # 止盈市价单
    ORDER_TYPE_TRAILING_STOP_MARKET,  # 追踪止损
)

from asterdex.constants import (
    TIME_IN_FORCE_GTC,       # Good Till Cancel (默认)
    TIME_IN_FORCE_IOC,       # Immediate or Cancel
    TIME_IN_FORCE_FOK,       # Fill or Kill
    TIME_IN_FORCE_GTX,       # Post Only
)

from asterdex.constants import (
    POSITION_SIDE_BOTH,      # 双向持仓
    POSITION_SIDE_LONG,      # 多头
    POSITION_SIDE_SHORT,     # 空头
)

from asterdex.constants import (
    MARGIN_TYPE_ISOLATED,    # 逐仓
    MARGIN_TYPE_CROSSED,     # 全仓
)
```

#### K线间隔

```python
from asterdex import KLINE_INTERVALS

# ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
```

---

### 1.5 asterdex.exceptions (异常类)

**文件**: `asterdex/exceptions.py`

完整的异常继承结构:

```
AsterError (基类)
├── NetworkError          # 网络连接错误
├── APIError              # API返回错误 (包含code)
├── AuthenticationError   # 认证失败
├── RateLimitError        # 触发限流 (code=429)
├── ValidationError       # 参数验证错误 (code=400)
├── OrderError            # 订单操作失败
├── SignatureError        # 签名失败
├── TimeoutError          # 请求超时
├── StreamError           # Stream订阅错误
└── WebSocketError        # WebSocket错误
    ├── WSConnectionError     # 连接失败
    ├── WSReconnectError      # 重连失败
    ├── WSTimeoutError        # 超时
    └── WSFallbackError       # 降级失败
```

#### 异常处理示例

```python
from asterdex import Client
from asterdex.exceptions import (
    AsterError,
    APIError,
    AuthenticationError,
    RateLimitError,
    OrderError,
    ValidationError,
)

try:
    client = Client.v3(user="...", signer="...", private_key="...")
    order = await client.create_order(...)
except AuthenticationError as e:
    print(f"认证失败: {e.message}")
except RateLimitError as e:
    print(f"触发限流，等待 {e.retry_after} 秒后重试")
except OrderError as e:
    print(f"订单错误: {e.message}, order_id={e.order_id}")
except ValidationError as e:
    print(f"参数错误: {e.message}, field={e.field}")
except APIError as e:
    print(f"API错误 [{e.code}]: {e.message}")
except AsterError as e:
    print(f"SDK错误: {e}")
```

---

### 1.6 日志配置

**文件**: `asterdex/logging_config.py`

```python
from asterdex import set_log_level, LogLevel, get_logger

# 设置全局日志级别
set_log_level(LogLevel.DEBUG)   # DEBUG/INFO/WARNING/ERROR
set_log_level(LogLevel.INFO)

# 获取特定模块的logger
logger = get_logger("asterdex.api.v3.client")
logger.debug("调试信息")
```

#### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ASTERDEX_NETWORK` | `testnet` | 网络环境 |
| `ASTERDEX_LOG_LEVEL` | `INFO` | 日志级别 |
| `ASTERDEX_TIMEOUT` | `30` | 请求超时(秒) |
| `ASTERDEX_MAX_RETRIES` | `3` | 最大重试次数 |

#### 代理支持

SDK 内置支持 HTTP/HTTPS 代理:

```python
# HTTP 代理
client = Client.v3(..., proxy="http://user:pass@host:port")

# HTTPS 代理
ws = WebSocketClient(..., proxy="https://host:port")

# 带认证的 HTTPS 代理
hybrid = HybridClient(..., proxy="https://user:pass@host:port")
```

---

## 2. API 方法详解

### 2.1 市场数据 (无需认证)

这些方法可以直接调用或通过 `client.market.*` 访问:

```python
client = Client.v3(...)

# 测试连接
await client.ping()

# 服务器时间
await client.get_time()

# 交易所信息 (包含所有交易对规则)
await client.get_exchange_info()

# 订单簿
await client.get_order_book("BTCUSDT", limit=500)  # limit: 5-5000

# 最近成交
await client.get_trades("BTCUSDT", limit=500)

# K线数据
await client.get_klines(
    symbol="BTCUSDT",
    interval="1m",           # K线间隔
    limit=500,
    start_time=None,         # 毫秒时间戳
    end_time=None
)

# 24小时行情
await client.get_ticker_24h("BTCUSDT")  # 不传symbol返回所有

# 标记价格
await client.get_mark_price("BTCUSDT")

# 价格Ticker
await client.get_ticker_price("BTCUSDT")

# 订单簿Ticker
await client.get_book_ticker("BTCUSDT")

# 资金费率
await client.get_funding_rate("BTCUSDT")
```

### 2.2 交易操作 (需要认证)

```python
# 市价买入
order = await client.create_order(
    symbol="BTCUSDT",
    side="BUY",
    type="MARKET",
    quantity="0.001"
)

# 限价卖出
order = await client.create_order(
    symbol="BTCUSDT",
    side="SELL",
    type="LIMIT",
    quantity="0.001",
    price="50000",
    time_in_force="GTC"
)

# 止损单
order = await client.create_order(
    symbol="BTCUSDT",
    side="SELL",
    type="STOP_MARKET",
    quantity="0.001",
    stop_price="49000",
    close_position=True  # 全平仓
)

# 批量下单
orders = await client.batch_orders([
    {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.001"},
    {"symbol": "ETHUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.01"},
])

# 取消订单
await client.cancel_order("BTCUSDT", order_id=123456)

# 查询订单
order = await client.get_order("BTCUSDT", order_id=123456)

# 查询挂单
open_orders = await client.get_open_orders("BTCUSDT")

# 查询所有订单
all_orders = await client.get_all_orders("BTCUSDT", limit=500)
```

### 2.3 账户操作

```python
# 账户余额
balance = await client.get_account_info()

# 持仓信息
position = await client.get_position("BTCUSDT")

# 调整杠杆
await client.set_leverage("BTCUSDT", leverage=10)

# 调整保证金模式
await client.set_margin_type("BTCUSDT", margin_type="ISOLATED")

# 调整逐仓保证金
await client.modify_isolated_margin("BTCUSDT", amount="100", type=1)  # 1=增加, 2=减少

# 手续费率
rate = await client.get_commission_rate("BTCUSDT")

# 成交历史
trades = await client.get_user_trades("BTCUSDT", limit=500)
```

---

## 3. 数据模型

### 3.1 主要模型类

```python
from asterdex.models import (
    OrderBook,       # 订单簿
    Trade,           # 成交记录
    Ticker24h,       # 24小时行情
    MarkPrice,       # 标记价格
    Kline,           # K线数据
    ExchangeInfo,    # 交易所信息
    Balance,         # 余额
    Position,        # 持仓
    Order,           # 订单
    AccountInfo,     # 账户信息
    FundingRate,     # 资金费率
)
```

### 3.2 WebSocket模型

```python
from asterdex.models.ws import (
    WSBookTicker,    # 订单簿更新
    WSKline,         # K线
    WSTicker,        # 行情
    WSAggTrade,      # 聚合成交
    WSMarkPrice,     # 标记价格
    WSOrderUpdate,   # 订单更新
    WSBalanceUpdate, # 余额更新
    WSLiquidation,   # 强平
    WSMarginCall,    # 追保
)
```

---

## 4. 完整示例

### 4.1 交易机器人基础框架

```python
import asyncio
from asterdex import (
    Client, WebSocketClient, Network,
    ORDER_SIDE_BUY, ORDER_TYPE_MARKET
)

class TradingBot:
    def __init__(self, user, signer, private_key):
        self.client = Client.v3(
            user=user,
            signer=signer,
            private_key=private_key,
            network=Network.TESTNET
        )
        self.ws = None
        self.last_price = None

    async def start(self):
        # 启动WebSocket
        self.ws = WebSocketClient(network=Network.TESTNET)
        
        @self.ws.on_ticker("BTCUSDT")
        async def on_ticker(data):
            self.last_price = float(data['c'])
            print(f"当前价格: {self.last_price}")
            
            # 简单的交易逻辑
            if self.should_buy():
                await self.execute_buy()

        @self.ws.on_error
        async def on_error(err):
            print(f"WebSocket错误: {err}")

        await self.ws.connect()
        
        # 主循环
        while True:
            await asyncio.sleep(60)
            
    def should_buy(self):
        # 你的交易逻辑
        return False
        
    async def execute_buy(self):
        try:
            order = await self.client.create_order(
                symbol="BTCUSDT",
                side=ORDER_SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity="0.001"
            )
            print(f"买入订单成交: {order['orderId']}")
        except Exception as e:
            print(f"下单失败: {e}")

    async def stop(self):
        if self.ws:
            await self.ws.disconnect()
        await self.client.close()

async def main():
    bot = TradingBot(
        user="0x...",
        signer="0x...",
        private_key="0x..."
    )
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()

asyncio.run(main())
```

---

## 5. 常见问题

### Q: 如何区分测试网和主网?

```python
from asterdex import Network

# 方式1: 创建客户端时指定
client = Client.v3(..., network=Network.TESTNET)
client = Client.v3(..., network=Network.MAINNET)

# 方式2: 环境变量
# ASTERDEX_NETWORK=testnet (默认)
# ASTERDEX_NETWORK=mainnet
```

### Q: V1和V3有什么区别?

- **V1**: HMAC SHA256 签名，传统 API Key 方式
- **V3**: EIP712 签名，基于以太坊钱包，更安全

**推荐使用 V3 API**

### Q: WebSocket 连接失败怎么办?

1. 检查网络
2. 使用 `HybridClient` 自动降级到 REST
3. 调整重连参数

### Q: 触发限流怎么办?

SDK 内置漏桶限速器，会自动等待重试。可以查看:

```python
status = client.rate_limiter.get_status()
print(status)
```

### Q: 如何获取帮助?

- 查看 [test_report.md](./test_report.md) 了解测试结果
- 查看 [README.md](./README.md) 了解完整API

---

## 6. 类型注解

SDK 完全使用类型注解，支持 IDE 自动补全:

```python
from asterdex import Client, Network
from asterdex.models import Order, Position

# IDE 会提示正确的参数
order: Order = await client.get_order("BTCUSDT", order_id=123)
position: Position = await client.get_position("BTCUSDT")
```

---

*本指南最后更新于 2026-03-25*