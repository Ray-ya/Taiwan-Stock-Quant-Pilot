import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.sentiment_analyzer import analyze_sentiment, summarize_market_news_sentiment
from engine.strategy_engine import MultiLevelStrategyEngine
from backtest.backtester import run_monte_carlo_backtest

class TestTaiwanStockQuantPilot(unittest.TestCase):
    def test_sentiment_analyzer(self):
        bull_title = "外資大買台積電 營收創高大單加碼"
        res = analyze_sentiment(bull_title)
        self.assertGreater(res["score"], 0.5)
        self.assertIn("BULLISH", res["sentiment"])

        bear_title = "外資大賣 營收重摔 調降評等走跌"
        res2 = analyze_sentiment(bear_title)
        self.assertLess(res2["score"], -0.3)
        self.assertIn("BEARISH", res2["sentiment"])

    def test_strategy_engine(self):
        fake_quotes = {
            "2412": {"code": "2412", "name": "中華電", "volume": 10000, "close": 125.0, "change": 0.5},
            "2330": {"code": "2330", "name": "台積電", "volume": 50000, "close": 1000.0, "change": 25.0},
            "2303": {"code": "2303", "name": "聯電", "volume": 60000, "close": 55.0, "change": 3.0}
        }
        fake_inst = {
            "2412": {"total": 500, "foreign": 300, "trust": 200},
            "2330": {"total": 12000, "foreign": 9000, "trust": 2000},
            "2303": {"total": 15000, "foreign": 11000, "trust": 3000}
        }
        engine = MultiLevelStrategyEngine(fake_quotes, fake_inst, 0.5)
        report = engine.generate_full_allocation_report()

        self.assertIn("strategy_100", report)
        self.assertIn("strategy_70", report)
        self.assertIn("strategy_50", report)
        self.assertTrue(len(report["strategy_100"]) > 0)
        self.assertTrue(len(report["strategy_70"]) > 0)
        self.assertTrue(len(report["strategy_50"]) > 0)

    def test_backtester(self):
        res = run_monte_carlo_backtest(trades_count=100)
        self.assertIn("combined_cycle_win_rate", res)
        self.assertIn("max_drawdown_pct", res)

if __name__ == "__main__":
    unittest.main()
