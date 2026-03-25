"""V3 Client 扩展功能单元测试

测试 reduceOnly, closePosition 等扩展功能
"""

import pytest
from unittest.mock import AsyncMock, patch
from asterdex import Client, Network
from asterdex.api.v3.client import V3Client
from tests import TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY


class TestCreateOrderWithOptions:
    """测试 create_order 扩展参数"""

    @pytest.mark.asyncio
    async def test_create_order_with_reduce_only(self):
        """测试创建 reduceOnly 订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 123, "reduceOnly": True})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="SELL",
            type="LIMIT",
            quantity="0.001",
            price="50000",
            reduce_only=True,
        )

        assert result["orderId"] == 123
        client.post.assert_called_once()
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["reduceOnly"] == "true"

    @pytest.mark.asyncio
    async def test_create_order_with_close_position(self):
        """测试创建 closePosition 订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 456, "closePosition": True})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="SELL",
            type="STOP_MARKET",
            quantity="0.001",
            close_position=True,
        )

        assert result["orderId"] == 456
        client.post.assert_called_once()
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["closePosition"] == "true"

    @pytest.mark.asyncio
    async def test_create_order_with_stop_price(self):
        """测试创建止损/止盈订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 789, "type": "STOP"})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="STOP",
            quantity="0.001",
            stop_price="45000",
        )

        assert result["orderId"] == 789
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["stopPrice"] == "45000"

    @pytest.mark.asyncio
    async def test_create_order_with_position_side(self):
        """测试创建持仓方向订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 111, "positionSide": "LONG"})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="LIMIT",
            quantity="0.001",
            price="50000",
            position_side="LONG",
        )

        assert result["orderId"] == 111
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["positionSide"] == "LONG"

    @pytest.mark.asyncio
    async def test_create_market_order_with_reduce_only(self):
        """测试市价单 + reduceOnly"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 222, "type": "MARKET", "reduceOnly": True})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="SELL",
            type="MARKET",
            quantity="0.001",
            reduce_only=True,
        )

        assert result["orderId"] == 222
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["type"] == "MARKET"
        assert signed_params["reduceOnly"] == "true"
        assert "timeInForce" not in signed_params

    @pytest.mark.asyncio
    async def test_create_stop_market_order(self):
        """测试 STOP_MARKET 订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 333, "type": "STOP_MARKET"})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="STOP_MARKET",
            quantity="0.001",
            stop_price="51000",
        )

        assert result["orderId"] == 333
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["type"] == "STOP_MARKET"
        assert signed_params["stopPrice"] == "51000"

    @pytest.mark.asyncio
    async def test_create_take_profit_market_order(self):
        """测试 TAKE_PROFIT_MARKET 订单"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client.post = AsyncMock(return_value={"orderId": 444, "type": "TAKE_PROFIT_MARKET"})

        result = await client.create_order(
            symbol="BTCUSDT",
            side="SELL",
            type="TAKE_PROFIT_MARKET",
            quantity="0.001",
            stop_price="52000",
        )

        assert result["orderId"] == 444
        call_args = client.post.call_args
        signed_params = call_args[1]["data"]
        assert signed_params["type"] == "TAKE_PROFIT_MARKET"


class TestClientWrapperWithOptions:
    """测试 Client wrapper 的扩展参数"""

    @pytest.mark.asyncio
    async def test_client_order_create_with_reduce_only(self):
        """测试通过 Client.order.create 创建 reduceOnly 订单"""
        with patch.object(V3Client, "create_order", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"orderId": 555}

            client = Client.v3(
                user=TESTNET_V3_USER,
                signer=TESTNET_V3_SIGNER,
                private_key=TESTNET_V3_PRIVATE_KEY,
            )

            result = await client.order.create(
                symbol="BTCUSDT",
                side="SELL",
                type="LIMIT",
                quantity="0.001",
                price="50000",
                reduce_only=True,
            )

            assert result["orderId"] == 555
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["reduce_only"] is True
            await client.close()

    @pytest.mark.asyncio
    async def test_client_order_create_with_close_position(self):
        """测试通过 Client.order.create 创建 closePosition 订单"""
        with patch.object(V3Client, "create_order", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"orderId": 666}

            client = Client.v3(
                user=TESTNET_V3_USER,
                signer=TESTNET_V3_SIGNER,
                private_key=TESTNET_V3_PRIVATE_KEY,
            )

            result = await client.order.create(
                symbol="BTCUSDT",
                side="SELL",
                type="STOP_MARKET",
                quantity="0.001",
                close_position=True,
            )

            assert result["orderId"] == 666
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["close_position"] is True
            await client.close()


class TestRateLimiterIntegration:
    """测试限速器集成"""

    def test_client_has_rate_limiter(self):
        """测试客户端有 rate_limiter 属性"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        assert hasattr(client, "rate_limiter")
        assert client.rate_limiter is not None

    def test_client_rate_limiter_network(self):
        """测试客户端限速器使用正确的网络"""
        client_testnet = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )
        client_mainnet = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.MAINNET
        )

        assert client_testnet.rate_limiter.network == Network.TESTNET
        assert client_mainnet.rate_limiter.network == Network.MAINNET

    def test_update_rate_limits(self):
        """测试更新限速配置"""
        client = V3Client(
            TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY, Network.TESTNET
        )

        rate_limits = [
            {
                "rateLimitType": "RAW_REQUEST",
                "interval": "MINUTE",
                "intervalNum": 1,
                "limit": 10000,
            },
        ]

        client.update_rate_limits(rate_limits)

        assert client.rate_limiter._raw_request_config.limit == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
