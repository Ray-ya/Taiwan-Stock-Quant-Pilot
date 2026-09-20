"""
Taiwan-Stock-Quant-Pilot - Daily Report Generator & Broadcaster
產出排版清晰、專業扎實的每日台股量化晨報，並支援自動推播與本地保存
"""

import datetime
import os
import sys

# Windows 終端機 UTF-8 輸出防護
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 將上一層目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data_collector import fetch_twse_daily_quotes, fetch_twse_institutional_investors, fetch_cnyes_market_news
from engine.sentiment_analyzer import summarize_market_news_sentiment
from engine.strategy_engine import MultiLevelStrategyEngine

def generate_morning_report() -> str:
    """
    彙整所有數據，產生每日台股量化晨報文本
    """
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 抓取數據
    quotes = fetch_twse_daily_quotes()
    inst = fetch_twse_institutional_investors()
    news = fetch_cnyes_market_news(10)
    sentiment_res = summarize_market_news_sentiment(news)

    # 2. 策略引擎運算
    engine = MultiLevelStrategyEngine(quotes, inst, sentiment_res.get("overall_score", 0.0))
    report_data = engine.generate_full_allocation_report()

    # 3. 組裝文字報告
    lines = []
    lines.append(f"📊【小R 台股量化決策晨報】")
    lines.append(f"🕒 產出時間：{now_str} (Asia/Taipei)")
    lines.append(f"🌐 核心資料庫：TWSE 即時行情、三大法人籌碼、鉅亨網重大財經")
    lines.append("-" * 38)
    lines.append("")
    
    # 新聞與市場情緒
    lines.append(f"📰【總體市場新聞與情緒量化指標】")
    lines.append(f"• 市場情緒評分：{sentiment_res['overall_score']} ({sentiment_res['overall_sentiment']})")
    lines.append(f"• 採樣焦點新聞：")
    for i, n in enumerate(news[:3], 1):
        lines.append(f"  {i}. {n['title']}")
    lines.append("")
    lines.append("-" * 38)

    # 策略 1：100% 結構套利與防守
    lines.append("🛡️【第一層：100% 確定性結構收益與防守】")
    lines.append("• 資金建議配置：40% (穩健防守底倉)")
    lines.append("• 模型核心：高股息防守/結構性定價偏誤，極高抗跌與收益確定性")
    for s in report_data["strategy_100"]:
        lines.append(f"▶ 標的：{s['code']} {s['name']} (現價 {s['close']})")
        lines.append(f"  - 建議進場區間：{s['entry_price']}")
        lines.append(f"  - 停損機制 (SL)：{s['stop_loss']}")
        lines.append(f"  - 目標停利 (TP)：{s['take_profit']}")
        lines.append(f"  - 籌碼量能：成交 {s['signals']['volume']}，法人買超 {s['signals']['inst_total']}")
    lines.append("")
    lines.append("-" * 38)

    # 策略 2：70% 主力共振波段
    lines.append("🚀【第二層：70% 主力鎖碼共振波段】")
    lines.append("• 資金建議配置：40% (核心資產成長引擎)")
    lines.append("• 模型核心：外資/投信連續鎖碼 + 量增突破均線，波段勝率 70%")
    for s in report_data["strategy_70"]:
        lines.append(f"▶ 標的：{s['code']} {s['name']} (現價 {s['close']})")
        lines.append(f"  - 建議進場區間：{s['entry_price']}")
        lines.append(f"  - 停損機制 (SL)：{s['stop_loss']}")
        lines.append(f"  - 目標停利 (TP)：{s['take_profit']}")
        lines.append(f"  - 主力信號：外資 {s['signals']['foreign_buy']} / 投信 {s['signals']['trust_buy']}，量能 {s['signals']['volume']}")
        lines.append(f"  - 策略解析：{s['logic']}")
    lines.append("")
    lines.append("-" * 38)

    # 策略 3：50% 爆量突破動能
    lines.append("⚡【第三層：50% 爆量突破動能 (盈虧比 3:1)】")
    lines.append("• 資金建議配置：20% (衛星衝刺超額獲利)")
    lines.append("• 模型核心：大賺小賠 (嚴格 5% 停損博取 15%~20% 突破行情)")
    for s in report_data["strategy_50"]:
        lines.append(f"▶ 標的：{s['code']} {s['name']} (現價 {s['close']})")
        lines.append(f"  - 建議進場方式：{s['entry_price']}")
        lines.append(f"  - 停損機制 (SL)：{s['stop_loss']}")
        lines.append(f"  - 奔馳目標 (TP)：{s['take_profit']}")
        lines.append(f"  - 突破動能：單日成交 {s['signals']['volume']}，漲幅 {s['signals']['change']}")
    lines.append("")
    lines.append("-" * 38)

    # 總體配置與風控法則
    lines.append("💡【台股資產配置與嚴格風控指引】")
    lines.append("1. 資金分配比例：40% 防守底倉 + 40% 主力波段 + 20% 爆量衝刺。")
    lines.append("2. 停損鐵律：任何部位到達設定停損價，無條件嚴格執行停損，絕不停損單延後。")
    lines.append("3. 開盤觀察：08:45 ~ 09:00 期貨開盤與 09:00 現貨試撮，若出現大幅跳空請待開盤 15 分鐘後再行進場。")

    report_text = "\n".join(lines)
    return report_text

if __name__ == "__main__":
    report = generate_morning_report()
    print(report)
    
    # 保存到本機檔案
    report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "LATEST_MORNING_REPORT.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[OK] Report saved to {report_file}")
