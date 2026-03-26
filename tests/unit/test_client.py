import pytest
from unittest.mock import AsyncMock
from asterdex import Client, Network
from asterdex.api.v3.client import V3Client
from tests import TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY


class TestV3Client:
    @pytest.mark.asyncio
    async def test_ping(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={})

        result = await client.ping()
        assert result == {}

    @pytest.mark.asyncio
    async def test_noop(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"code": 0})

        result = await client.noop(1234567890123456)
        assert result["code"] == 0

    @pytest.mark.asyncio
    async def test_get_time(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"serverTime": 1234567890})

        result = await client.get_time()
        assert "serverTime" in result

    @pytest.mark.asyncio
    async def test_get_exchange_info(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"symbols": []})

        result = await client.get_exchange_info()
        assert "symbols" in result

    @pytest.mark.asyncio
    async def test_get_order_book(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"bids": [], "asks": []})

        result = await client.get_order_book("BTCUSDT")
        assert "bids" in result

    @pytest.mark.asyncio
    async def test_get_trades(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value=[])

        result = await client.get_trades("BTCUSDT")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_klines(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value=[])

        result = await client.get_klines("BTCUSDT", "1m")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_ticker_24h(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"symbol": "BTCUSDT"})

        result = await client.get_ticker_24h("BTCUSDT")
        assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_get_mark_price(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"symbol": "BTCUSDT"})

        result = await client.get_mark_price("BTCUSDT")
        assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_create_order(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 123})

        result = await client.create_order(
            symbol="BTCUSDT", side="BUY", type="LIMIT", quantity="0.001", price="50000"
        )
        assert result["orderId"] == 123

    @pytest.mark.asyncio
    async def test_create_order_without_price(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 123})

        result = await client.create_order(
            symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.001"
        )
        assert result["orderId"] == 123

    @pytest.mark.asyncio
    async def test_batch_orders(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value=[{"orderId": 123}])

        orders = [
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "0.001",
                "price": "50000",
            }
        ]
        result = await client.batch_orders(orders)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.delete = AsyncMock(return_value={"orderId": 123})

        result = await client.cancel_order("BTCUSDT", 123)
        assert result["orderId"] == 123

    @pytest.mark.asyncio
    async def test_get_order(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"orderId": 123})

        result = await client.get_order("BTCUSDT", 123)
        assert result["orderId"] == 123

    @pytest.mark.asyncio
    async def test_get_open_orders(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value=[])

        result = await client.get_open_orders("BTCUSDT")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_balance(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value=[{"asset": "BTC"}])

        result = await client.get_balance()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_position(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value=[{"symbol": "BTCUSDT"}])

        result = await client.get_position("BTCUSDT")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_account_info(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.get = AsyncMock(return_value={"feeTier": 1})

        result = await client.get_account_info()
        assert "feeTier" in result

    @pytest.mark.asyncio
    async def test_set_leverage(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"leverage": 10})

        result = await client.set_leverage("BTCUSDT", 10)
        assert result["leverage"] == 10

    @pytest.mark.asyncio
    async def test_set_margin_type(self):
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"marginType": "ISOLATED"})

        result = await client.set_margin_type("BTCUSDT", "ISOLATED")
        assert result["marginType"] == "ISOLATED"


class TestClientFactory:
    def test_create_v3_client(self):
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        assert client._client.api_version == "v3"

    def test_v3_client_network(self):
        client = Client.v3(
            user=TESTNET_V3_USER,
            signer=TESTNET_V3_SIGNER,
            private_key=TESTNET_V3_PRIVATE_KEY,
            network=Network.MAINNET,
        )
        assert client._client.base_url == Network.MAINNET.rest_url

    def test_v3_client_testnet(self):
        client = Client.v3(
            user=TESTNET_V3_USER,
            signer=TESTNET_V3_SIGNER,
            private_key=TESTNET_V3_PRIVATE_KEY,
        )
        assert client._client.base_url == Network.TESTNET.rest_url
