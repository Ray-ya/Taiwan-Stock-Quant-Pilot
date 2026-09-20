import unittest
import sys
import os
import pandas as pd
import numpy as np

# 加入根目錄至 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.data_collector import fetch_cnyes_market_news
from engine.sentiment_analyzer import analyze_sentiment, summarize_market_news_sentiment
from engine.strategy_engine import MultiLevelStrategyEngine
from engine.classic_quant_models import ClassicQuantDistillery

class TestQuantSystem(unittest.TestCase):
    def test_sentiment_scoring(self):
        bull_title = "外資大買 營收創高 獲利強勁狂飆"
        res = analyze_sentiment(bull_title)
        self.assertGreater(res["score"], 0.5)
        self.assertIn("BULLISH", res["sentiment"])

        bear_title = "外資大賣 營收重摔 調降評等走跌"
        res2 = analyze_sentiment(bear_title)
        self.assertLess(res2["score"], -0.5)
        self.assertIn("BEARISH", res2["sentiment"])

    def test_all_ten_classic_models(self):
        """
        全覆蓋測試：十大經典量化交易模型
        """
        # 1. 雙動量模型 (Dual Momentum)
        prices = pd.Series([100, 105, 110, 115, 120])
        bench = pd.Series([100, 101, 102, 103, 104])
        res_mom = ClassicQuantDistillery.dual_momentum(prices, bench, lookback=4)
        self.assertEqual(res_mom["signal"], "STRONG_BUY")
        self.assertIn("excess_return", res_mom)

        # 2. 統計套利與配對交易 (Pairs Trading)
        series_a = pd.Series([10, 11, 12, 13, 20])
        series_b = pd.Series([10, 10, 10, 10, 10])
        res_pair = ClassicQuantDistillery.pairs_trading(series_a, series_b, lookback=5, entry_z=1.5)
        self.assertIn("z_score", res_pair)
        self.assertIn(res_pair["signal"], ["SHORT_A_LONG_B", "LONG_A_SHORT_B", "HOLD", "EXIT_CONVERGENCE"])

        # 3. 布林通道 (Bollinger Bands Squeeze & Mean Reversion)
        s = pd.Series([10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18])
        res_bb = ClassicQuantDistillery.bollinger_bands(s, period=10)
        self.assertIn("signal", res_bb)
        self.assertIn("bandwidth", res_bb)
        self.assertIn("percent_b", res_bb)

        # 4. 法瑪-五因子選股打分 (Fama-French Multi-Factor)
        res_ff = ClassicQuantDistillery.fama_french_scoring(market_cap=200, pb_ratio=1.2, roe=22.0, asset_growth=8.0)
        self.assertEqual(res_ff["grade"], "EXCELLENT")
        self.assertGreaterEqual(res_ff["score"], 80)

        # 5. VWAP 與微觀訂單流 (VWAP / Order Flow)
        res_vwap = ClassicQuantDistillery.vwap_order_flow(
            high=102.0, low=99.0, close=101.5, volume=5000,
            cum_vol=20000, cum_pv=2010000, inside_vol=1500, outside_vol=3500
        )
        self.assertEqual(res_vwap["signal"], "BULLISH_ORDER_FLOW")
        self.assertGreater(res_vwap["inflow_ratio"], 0.58)

        # 6. 唐奇安通道與海龜突破 (Donchian Turtle Breakout)
        highs = pd.Series(range(100, 125))
        lows = pd.Series(range(90, 115))
        closes = pd.Series(range(95, 120))
        # 最後一筆讓價格突破前 20 日高點
        closes.iloc[-1] = 130
        res_turtle = ClassicQuantDistillery.donchian_breakout(highs, lows, closes, entry_period=20, exit_period=10)
        self.assertEqual(res_turtle["signal"], "TURTLE_LONG_ENTRY")
        self.assertGreater(res_turtle["stop_loss_suggested"], 0)

        # 7. 波動率突破 (Larry Williams Volatility Breakout)
        res_vb = ClassicQuantDistillery.volatility_breakout(today_open=100, prev_high=105, prev_low=95, curr_price=107, k=0.6)
        self.assertEqual(res_vb["signal"], "VOLATILITY_BREAKOUT_BUY")

        # 8. 全天候風險平價配置 (Risk Parity)
        vols = {"AssetA": 0.10, "AssetB": 0.20}
        rp = ClassicQuantDistillery.risk_parity_weights(vols)
        self.assertAlmostEqual(rp["weights"]["AssetA"] + rp["weights"]["AssetB"], 1.0, places=2)
        self.assertGreater(rp["weights"]["AssetA"], rp["weights"]["AssetB"])

        # 9. 事件驅動套利 (Event-Driven Arbitrage)
        res_event = ClassicQuantDistillery.event_driven_arbitrage(historical_fill_rate=0.95, days_to_dividend=5, institutional_net_buy=3000, yield_rate=5.2)
        self.assertEqual(res_event["signal"], "STRONG_EVENT_ARBITRAGE")
        self.assertIn("HIGH", res_event["confidence"])

        # 10. 機器學習因子集成 (Machine Learning Factor Ensemble)
        features = {
            "institutional_ratio": 90.0,
            "volume_surge": 85.0,
            "news_sentiment": 80.0,
            "moving_average_trend": 90.0,
            "bias_ratio": 70.0
        }
        res_ml = ClassicQuantDistillery.ml_factor_ensemble(features)
        self.assertEqual(res_ml["action"], "STRONG_BUY_PREDICTION")
        self.assertGreaterEqual(res_ml["predicted_score"], 80.0)

    def test_multi_level_engine(self):
        sample_quotes = {
            "2412": {"code": "2412", "name": "中華電", "volume": 20000, "close": 145.0, "change": 0.5},
            "2303": {"code": "2303", "name": "聯電", "volume": 120000, "close": 155.0, "change": 4.5}
        }
        sample_inst = {
            "2412": {"foreign": 2000, "trust": 500, "total": 2500},
            "2303": {"foreign": 15000, "trust": 8000, "total": 23000}
        }
        engine = MultiLevelStrategyEngine(quotes=sample_quotes, inst=sample_inst)
        signals = engine.evaluate_all_strategies()
        self.assertIn("100_percent_structure", signals)
        self.assertIn("70_percent_momentum", signals)
        self.assertIn("50_percent_breakout", signals)

        # 測試報告生成器介面相容性
        report_data = engine.generate_full_allocation_report()
        self.assertIn("strategy_100", report_data)
        self.assertIn("strategy_70", report_data)
        self.assertIn("strategy_50", report_data)
        self.assertIn("capital_allocation", report_data)

if __name__ == "__main__":
    unittest.main()
