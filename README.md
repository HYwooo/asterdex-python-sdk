# Aster DEX Python SDK

Aster DEX Python SDK - Asynchronous trading library with full V3 (EIP712) API support

## Features

- Async-first: Pure async implementation based on aiohttp and websockets
- V3 EIP712 Signature: Structured data signing for enhanced security
- WebSocket: Built-in long connection, auto-reconnect, heartbeat management
- Default Testnet: Safety-first, default to testnet
- Type-safe: Complete type annotations
- Log levels: DEBUG/INFO/WARNING/ERROR for easy debugging
- High performance: Connection pool reuse, memory optimized
- Rate limiter: Global request rate limiting with priority queue

## Installation

```bash
pip install git+https://github.com/HYwooo/asterdex-python-sdk.git
```

Or from source:

```bash
git clone https://github.com/HYwooo/asterdex-python-sdk.git
cd asterdex-python-sdk
pip install -e .
```

## Quick Start (V3 API Recommended)

### V3 API (EIP712 Authentication)

```python
import asyncio
from asterdex import Client, Network

async def main():
    # V3 uses EIP712 signing (recommended)
    client = Client.v3(
        user="0xYourMainWalletAddress",
        signer="0xYourSignerAddress",
        private_key="0xYourPrivateKey",
        network=Network.TESTNET
    )
    
    # Get account info
    account = await client.get_account_info()
    print(f"Balance: {account.get('totalWalletBalance')}")
    
    # Place order (market)
    order = await client.create_order(
        symbol="BTCUSDT",
        side="BUY",
        type="MARKET",
        quantity="0.001"
    )
    print(f"Order created: {order.get('orderId')}")
    
    await client.close()

asyncio.run(main())
```

### Limit Order + Advanced Parameters

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

### WebSocket Real-time Data

```python
import asyncio
from asterdex import WebSocketClient, Network

async def main():
    ws = WebSocketClient(network=Network.TESTNET)
    
    @ws.on_book_ticker("BTCUSDT")
    async def on_ticker(ticker):
        print(f"Bid: {ticker.bid_price} | Ask: {ticker.ask_price}")
    
    @ws.on_kline("BTCUSDT", "1m")
    async def on_kline(kline):
        print(f"Kline: O={kline.open} H={kline.high} L={kline.low} C={kline.close}")
    
    @ws.on_error
    async def on_error(error):
        print(f"WebSocket error: {error}")
    
    await ws.connect()
    print("WebSocket connected, waiting for data...")
    
    await asyncio.sleep(60)
    await ws.disconnect()

asyncio.run(main())
```

---

## Public Endpoints vs Private Endpoints

SDK methods are divided into public endpoints (no auth required) and private endpoints (auth required).

### Public Endpoints (No Auth Required)

```python
client = Client.v3(network=Network.TESTNET)

await client.ping()
await client.get_time()
await client.get_order_book("BTCUSDT")
await client.get_klines("BTCUSDT", "1h")
await client.get_ticker_24h("BTCUSDT")
await client.get_mark_price("BTCUSDT")
```

### Private Endpoints (Auth Required)

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
    print(f"Auth required: {e}")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASTERDEX_NETWORK` | `testnet` | Network: `testnet` or `mainnet` |
| `ASTERDEX_LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ASTERDEX_TIMEOUT` | `30` | Request timeout in seconds |
| `ASTERDEX_MAX_RETRIES` | `3` | Max retry attempts |

### Proxy Configuration

SDK has built-in HTTP/HTTPS proxy support:

```python
from asterdex import Client, WebSocketClient, HybridClient, Network

# HTTP proxy
client = Client.v3(
    user="0x...",
    signer="0x...",
    private_key="0x...",
    network=Network.TESTNET,
    proxy="http://user:password@proxy-host:port"
)

# HTTPS proxy
ws = WebSocketClient(
    network=Network.TESTNET,
    proxy="https://proxy-host:port"
)

# With authentication
hybrid = HybridClient(
    user="0x...",
    signer="0x...",
    private_key="0x...",
    proxy="https://user:password@proxy-host:port"
)
```

**Supported proxy types:**
- `http://` - HTTP proxy
- `https://` - HTTPS proxy

### Logging Configuration

```python
from asterdex import LogLevel, set_log_level
from asterdex.logging_config import get_logger

set_log_level(LogLevel.DEBUG)

logger = get_logger("asterdex.api.v3")
logger.debug("Debug info")
```

---

## Constants

### Network

```python
from asterdex import Network

Network.TESTNET
Network.MAINNET
```

### Order Types

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

### Order Side

```python
from asterdex.constants import (
    ORDER_SIDE_BUY,
    ORDER_SIDE_SELL,
)
```

### Time in Force

```python
from asterdex.constants import (
    TIME_IN_FORCE_GTC,    # Good Till Cancel
    TIME_IN_FORCE_IOC,    # Immediate or Cancel
    TIME_IN_FORCE_FOK,    # Fill or Kill
    TIME_IN_FORCE_GTX,    # Good Till Crossing (Post Only) - market maker friendly
    TIME_IN_FORCE_HIDDEN, # Hidden order
)
```

### Margin Type

```python
from asterdex.constants import (
    MARGIN_TYPE_ISOLATED,
    MARGIN_TYPE_CROSSED,
)
```

---

## API Reference

### Market Data (No Auth Required)

| Method | Description | Endpoint |
|--------|-------------|----------|
| `ping()` | Test connectivity | GET /fapi/v3/ping |
| `get_time()` | Server time | GET /fapi/v3/time |
| `get_exchange_info()` | Exchange info | GET /fapi/v3/exchangeInfo |
| `get_order_book(symbol, limit)` | Order book | GET /fapi/v3/depth |
| `get_trades(symbol, limit)` | Recent trades | GET /fapi/v3/trades |
| `get_klines(symbol, interval, limit, start_time, end_time)` | Klines | GET /fapi/v3/klines |
| `get_ticker_price(symbol)` | Price ticker | GET /fapi/v3/ticker/price |
| `get_book_ticker(symbol)` | Book ticker | GET /fapi/v3/ticker/bookTicker |
| `get_ticker_24h(symbol)` | 24h ticker | GET /fapi/v3/ticker/24hr |
| `get_mark_price(symbol)` | Mark price | GET /fapi/v3/premiumIndex |
| `get_funding_rate(symbol)` | Funding rate | GET /fapi/v3/fundingRate |
| `get_historical_trades(symbol, limit, from_id)` | Historical trades | GET /fapi/v3/historicalTrades |
| `get_agg_trades(symbol, limit, start_time, end_time, from_id)` | Agg trades | GET /fapi/v3/aggTrades |
| `get_index_price_klines(symbol, interval, limit, start_time, end_time)` | Index price klines | GET /fapi/v3/indexPriceKlines |
| `get_mark_price_klines(symbol, interval, limit, start_time, end_time)` | Mark price klines | GET /fapi/v3/markPriceKlines |

### Trading (Requires Signature)

| Method | Description | Endpoint |
|--------|-------------|----------|
| `create_order(...)` | Create order | POST /fapi/v3/order |
| `batch_orders(orders)` | Batch orders | POST /fapi/v3/batchOrders |
| `cancel_order(symbol, order_id)` | Cancel order | DELETE /fapi/v3/order |
| `cancel_all_open_orders(symbol)` | Cancel all | DELETE /fapi/v3/allOpenOrders |
| `cancel_multiple_orders(symbol, order_ids)` | Batch cancel | DELETE /fapi/v3/batchOrders |
| `countdown_cancel_all(symbol, countdown_time)` | Countdown cancel | POST /fapi/v3/countdownCancelAll |
| `set_leverage(symbol, leverage)` | Set leverage | POST /fapi/v3/leverage |
| `set_margin_type(symbol, margin_type)` | Set margin type | POST /fapi/v3/marginType |
| `modify_isolated_margin(symbol, amount, type)` | Modify margin | POST /fapi/v3/positionMargin |
| `change_position_mode(hedge_mode)` | Position mode | POST /fapi/v3/positionSide |
| `set_multi_assets_margin(multi_assets_margin)` | Multi-assets | POST /fapi/v3/multiAssetsMargin |
| `transfer_spot_futures(asset, amount, type)` | Transfer | POST /fapi/v3/transfer |
| `noop(nonce)` | Noop | POST /fapi/v3/noop |

### User Data (Requires Signature)

| Method | Description | Endpoint |
|--------|-------------|----------|
| `get_order(symbol, order_id)` | Get order | GET /fapi/v3/order |
| `get_single_open_order(symbol, order_id)` | Get open order | GET /fapi/v3/openOrder |
| `get_open_orders(symbol)` | Get open orders | GET /fapi/v3/openOrders |
| `get_all_orders(symbol, limit, start_time, end_time)` | Get all orders | GET /fapi/v3/allOrders |
| `get_balance()` | Get balance | GET /fapi/v3/balance |
| `get_account_info()` | Account info | GET /fapi/v3/account |
| `get_position(symbol)` | Position | GET /fapi/v3/positionRisk |
| `get_user_trades(symbol, limit, start_time, end_time)` | User trades | GET /fapi/v3/userTrades |
| `get_income_history(symbol, limit, start_time, end_time)` | Income history | GET /fapi/v3/income |
| `get_commission_rate(symbol)` | Commission rate | GET /fapi/v3/commissionRate |
| `get_leverage_bracket(symbol)` | Leverage bracket | GET /fapi/v3/leverageBracket |
| `get_position_margin_history(symbol, limit, start_time, end_time)` | Margin history | GET /fapi/v3/positionMargin/history |
| `get_adl_quantile(symbol)` | ADL quantile | GET /fapi/v3/adlQuantile |
| `get_force_orders(symbol, limit, start_time, end_time)` | Force orders | GET /fapi/v3/forceOrders |
| `get_position_mode()` | Position mode | GET /fapi/v3/positionSide |
| `get_multi_assets_margin()` | Multi-assets mode | GET /fapi/v3/multiAssetsMargin |

### User Stream (WebSocket Required)

| Method | Description | Endpoint |
|--------|-------------|----------|
| `start_user_stream()` | Start user stream | POST /fapi/v3/listenKey |
| `keepalive_user_stream(listen_key)` | Keepalive | PUT /fapi/v3/listenKey |
| `close_user_stream(listen_key)` | Close stream | DELETE /fapi/v3/listenKey |

---

## Rate Limiter

SDK has a global leaky bucket rate limiter:

- **RAW_REQUEST**: Raw request limit (default 6000/min)
- **REQUEST_WEIGHT**: Request weight limit (default 6000/min)
- **ORDER**: Order frequency limit (default 300/min)

### Priority Queue

Close Position and Reduce Only orders have highest priority, no limit.

```python
status = client.rate_limiter.get_status()
print(f"Remaining requests: {status['raw_request_tokens']}")
print(f"Remaining orders: {status['order_tokens']}")
```

---

## Error Handling

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
        print(f"Auth failed: {e}")
    except RateLimitError as e:
        print(f"Rate limited: {e}")
    except OrderError as e:
        print(f"Order error: {e}")
    except APIError as e:
        print(f"API error: {e.code} - {e.message}")
    except AsterError as e:
        print(f"SDK error: {e}")

asyncio.run(main())
```

---

## Requirements

- Python >= 3.9
- aiohttp >= 3.9.0
- websockets >= 12.0
- eth-account >= 0.11.0

---

## Disclaimer

This software is provided "as is" without warranty of any kind. In no event shall the authors be liable for any claims, damages, or liabilities arising from the use of this software.

**By using this software, you understand and accept the risks. Please ensure:**

1. Only use accounts and funds you can afford to lose
2. Test thoroughly before production use
3. Understand the risks of cryptocurrency trading
4. Comply with local laws and regulations

---

## License

### Main License: Apache 2.0

This library is licensed under Apache License 2.0.

This means:
- You can use this library in commercial projects
- You can modify the source code
- You can distribute modified versions
- You can link this library to your applications without open sourcing

### Third-party Libraries

| Library | License |
|---------|---------|
| aiohttp | Apache 2.0 |
| websockets | BSD |
| pydantic | MIT |
| eth-account | Apache 2.0 |
| hexbytes | Apache 2.0 |
| typing-extensions | PSF |

---

## Acknowledgments

- [Aster DEX](https://www.asterdex.com/) - API support
- [eth-account](https://github.com/ethereum/eth-account) - EIP712 implementation