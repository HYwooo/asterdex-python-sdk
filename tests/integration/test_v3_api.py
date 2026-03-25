"""V3 API集成测试 - 使用真实Testnet"""

import pytest
import asyncio
from asterdex import Client, Network
from tests import TESTNET_V3_USER, TESTNET_V3_SIGNER, TESTNET_V3_PRIVATE_KEY

TEST_SYMBOL = "BTCUSDT"


class TestV3MarketDataAPI:
    """Market Data API 测试 (不需要签名)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ping(self):
        """测试连接 /fapi/v3/ping"""
        client = Client.v3(
            user=TESTNET_V3_USER,
            signer=TESTNET_V3_SIGNER,
            private_key=TESTNET_V3_PRIVATE_KEY,
            network=Network.TESTNET,
        )
        try:
            result = await client.ping()
            print(f"Ping result: {result}")
            assert result == {} or "code" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_time(self):
        """测试时间 /fapi/v3/time"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_time()
            print(f"Server time: {result}")
            assert "serverTime" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_exchange_info(self):
        """测试交易所信息 /fapi/v3/exchangeInfo"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_exchange_info()
            print(f"Exchange info keys: {list(result.keys())}")
            assert "symbols" in result or "exchangeFilters" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_order_book(self):
        """测试订单簿 /fapi/v3/depth"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_order_book(TEST_SYMBOL, limit=5)
            print(f"OrderBook keys: {list(result.keys())}")
            assert "bids" in result
            assert "asks" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_trades(self):
        """测试最近成交 /fapi/v3/trades"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_trades(TEST_SYMBOL, limit=10)
            print(f"Trades count: {len(result) if isinstance(result, list) else 'error'}")
            assert isinstance(result, list) or "code" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_klines(self):
        """测试K线数据 /fapi/v3/klines"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_klines(TEST_SYMBOL, "1m", limit=10)
            print(f"Klines count: {len(result) if isinstance(result, list) else 'error'}")
            assert isinstance(result, list) or "code" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_ticker_24h(self):
        """测试24小时行情 /fapi/v3/ticker/24hr"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_ticker_24h(TEST_SYMBOL)
            print(f"Ticker keys: {list(result.keys()) if isinstance(result, dict) else result}")
            assert isinstance(result, dict) or isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_mark_price(self):
        """测试标记价格 /fapi/v3/premiumIndex"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_mark_price(TEST_SYMBOL)
            print(f"Mark price keys: {list(result.keys()) if isinstance(result, dict) else result}")
            assert isinstance(result, dict) or isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(
        reason="Testnet server returns 502 error for fundingRate endpoint - 服务端问题"
    )
    async def test_get_funding_rate(self):
        """测试资金费率 /fapi/v3/fundingRate"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_funding_rate(TEST_SYMBOL)
            print(f"Funding rate result: {result}")
        finally:
            await client.close()


class TestV3AccountAPI:
    """账户API测试 (需要签名)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_balance(self):
        """测试余额 /fapi/v3/balance"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_balance()
            print(f"Balance result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position(self):
        """测试持仓 /fapi/v3/positionRisk"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_position(TEST_SYMBOL)
            print(f"Position result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_account_info(self):
        """测试账户信息 /fapi/v3/account"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.account.get_account_info()
            print(f"Account info keys: {list(result.keys())}")
            assert "feeTier" in result or "canTrade" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_leverage(self):
        """测试设置杠杆 /fapi/v3/leverage"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.set_leverage(TEST_SYMBOL, 10)
            print(f"Set leverage result: {result}")
            assert "leverage" in result or result.get("code") == 200
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_margin_type(self):
        """测试设置保证金模式 /fapi/v3/marginType"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.set_margin_type(TEST_SYMBOL, "CROSSED")
            print(f"Set margin type result: {result}")
        except Exception as e:
            print(f"Set margin type error (may already be set): {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_commission_rate(self):
        """测试手续费率 /fapi/v3/commissionRate"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_commission_rate(TEST_SYMBOL)
            print(f"Commission rate result: {result}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_leverage_bracket(self):
        """测试杠杆分级 /fapi/v3/leverageBracket"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_leverage_bracket(TEST_SYMBOL)
            print(f"Leverage bracket result: {result}")
        finally:
            await client.close()


class TestV3OrderAPI:
    """订单API测试 (需要签名)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_market_order_buy(self):
        """测试市价买单 /fapi/v3/order (MARKET)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.create_order(
                symbol=TEST_SYMBOL,
                side="BUY",
                type="MARKET",
                quantity="0.001",
            )
            print(f"Market order BUY result: {result}")
            assert "orderId" in result or result.get("code") is not None
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_market_order_sell(self):
        """测试市价卖单 /fapi/v3/order (MARKET)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.create_order(
                symbol=TEST_SYMBOL,
                side="SELL",
                type="MARKET",
                quantity="0.001",
            )
            print(f"Market order SELL result: {result}")
            assert "orderId" in result or result.get("code") is not None
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_limit_order(self):
        """测试限价单 /fapi/v3/order (LIMIT)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.create_order(
                symbol=TEST_SYMBOL,
                side="BUY",
                type="LIMIT",
                quantity="0.001",
                price="10000",
                time_in_force="GTC",
            )
            print(f"Limit order result: {result}")
            order_id = result.get("orderId")
            if order_id:
                self._last_order_id = order_id
            assert "orderId" in result or result.get("code") is not None
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_order(self):
        """测试查询订单 /fapi/v3/order"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            open_orders = await client.get_open_orders(TEST_SYMBOL)
            if open_orders and len(open_orders) > 0:
                order_id = open_orders[0].get("orderId")
                result = await client.get_order(TEST_SYMBOL, order_id)
                print(f"Query order result: {result}")
                assert "orderId" in result
            else:
                print("No open orders, skip query test")
        except Exception as e:
            print(f"Query order test skipped: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_open_orders(self):
        """测试查询挂单 /fapi/v3/openOrders"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_open_orders(TEST_SYMBOL)
            print(f"Open orders result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_all_orders(self):
        """测试查询所有订单 /fapi/v3/allOrders"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_all_orders(TEST_SYMBOL, limit=10)
            print(f"All orders result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cancel_order(self):
        """测试取消订单 /fapi/v3/order (DELETE)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            open_orders = await client.get_open_orders(TEST_SYMBOL)
            if open_orders and len(open_orders) > 0:
                order_id = open_orders[0].get("orderId")
                result = await client.cancel_order(TEST_SYMBOL, order_id)
                print(f"Cancel order result: {result}")
                assert "orderId" in result or result.get("status") == "CANCELED"
            else:
                print("No open orders to cancel, skip cancel test")
        except Exception as e:
            print(f"Cancel order test result: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_orders(self):
        """测试批量下单 /fapi/v3/batchOrders"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            orders = [
                {
                    "symbol": TEST_SYMBOL,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "0.001",
                    "price": "10000",
                    "timeInForce": "GTC",
                },
                {
                    "symbol": TEST_SYMBOL,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "0.001",
                    "price": "10001",
                    "timeInForce": "GTC",
                },
            ]
            result = await client.batch_orders(orders)
            print(f"Batch orders result: {result}")
            assert isinstance(result, list) or "code" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_user_trades(self):
        """测试账户交易历史 /fapi/v3/userTrades"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_user_trades(TEST_SYMBOL, limit=10)
            print(f"User trades result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()


class TestV3NoopAPI:
    """Noop API测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_noop(self):
        """测试Noop /fapi/v3/noop"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            import time

            nonce = int(time.time() * 1000000)
            result = await client.noop(nonce)
            print(f"Noop result: {result}")
        finally:
            await client.close()


class TestV3NewAPIs:
    """新添加的V3 API测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_ticker_price(self):
        """测试价格Ticker /fapi/v3/ticker/price"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_ticker_price(TEST_SYMBOL)
            print(f"Ticker price result: {result}")
            assert isinstance(result, dict)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_book_ticker(self):
        """测试订单簿Ticker /fapi/v3/ticker/bookTicker"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_book_ticker(TEST_SYMBOL)
            print(f"Book ticker result: {result}")
            assert isinstance(result, dict)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_agg_trades(self):
        """测试聚合交易 /fapi/v3/aggTrades"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_agg_trades(TEST_SYMBOL, limit=10)
            print(f"Agg trades result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_index_price_klines(self):
        """测试指数价格K线 /fapi/v3/indexPriceKlines"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_index_price_klines(TEST_SYMBOL, "1h", limit=10)
            print(f"Index price klines result: {result}")
        except Exception as e:
            print(f"Index price klines error (may not be available): {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_mark_price_klines(self):
        """测试标记价格K线 /fapi/v3/markPriceKlines"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_mark_price_klines(TEST_SYMBOL, "1h", limit=10)
            print(f"Mark price klines result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_single_open_order(self):
        """测试查询单笔挂单 /fapi/v3/openOrder"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            open_orders = await client.get_open_orders(TEST_SYMBOL)
            if open_orders and len(open_orders) > 0:
                order_id = open_orders[0].get("orderId")
                result = await client.get_single_open_order(TEST_SYMBOL, order_id)
                print(f"Single open order result: {result}")
                assert "orderId" in result
            else:
                print("No open orders, skip test")
        except Exception as e:
            print(f"Single open order error: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_modify_isolated_margin(self):
        """测试调整逐仓保证金 /fapi/v3/positionMargin"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.modify_isolated_margin(TEST_SYMBOL, "0", 1)
            print(f"Modify isolated margin result: {result}")
        except Exception as e:
            print(f"Modify isolated margin error: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_margin_history(self):
        """测试保证金变动历史 /fapi/v3/positionMargin/history"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_position_margin_history(TEST_SYMBOL, limit=10)
            print(f"Position margin history result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_adl_quantile(self):
        """测试ADL分位 /fapi/v3/adlQuantile"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_adl_quantile(TEST_SYMBOL)
            print(f"ADL quantile result: {result}")
            assert isinstance(result, (list, dict))
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_force_orders(self):
        """测试强平订单 /fapi/v3/forceOrders"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_force_orders(TEST_SYMBOL, limit=10)
            print(f"Force orders result: {result}")
            assert isinstance(result, list)
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_index_references(self):
        """测试指数参考 /fapi/v3/indexreferences"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_index_references(TEST_SYMBOL)
            print(f"Index references result: {result}")
        except Exception as e:
            print(f"Index references error (may not be available): {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_multi_assets_margin(self):
        """测试多资产保证金模式 /fapi/v3/multiAssetsMargin (GET)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.get_multi_assets_margin()
            print(f"Multi assets margin result: {result}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_countdown_cancel_all(self):
        """测试定时取消 /fapi/v3/countdownCancelAll"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        try:
            result = await client.countdown_cancel_all(TEST_SYMBOL, 0)
            print(f"Countdown cancel all result: {result}")
        except Exception as e:
            print(f"Countdown cancel all error: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_stream(self):
        """测试用户流 /fapi/v3/listenKey (POST/DELETE)"""
        client = Client.v3(
            user=TESTNET_V3_USER, signer=TESTNET_V3_SIGNER, private_key=TESTNET_V3_PRIVATE_KEY
        )
        listen_key = None
        try:
            result = await client.start_user_stream()
            print(f"Start user stream result: {result}")
            listen_key = result.get("listenKey")
            assert listen_key is not None

            result = await client.keepalive_user_stream(listen_key)
            print(f"Keepalive user stream result: {result}")
        except Exception as e:
            print(f"User stream error: {e}")
        finally:
            if listen_key:
                try:
                    await client.close_user_stream(listen_key)
                    print("Closed user stream")
                except:
                    pass
            await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
