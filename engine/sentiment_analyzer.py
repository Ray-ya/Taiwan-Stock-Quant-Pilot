"""
Taiwan-Stock-Quant-Pilot - Sentiment & Trend Analyzer
財經新聞情緒量化評分與題材關鍵字熱度分析
"""

import re
from typing import List, Dict, Any

# 正向/偏多情緒關鍵字與權重
BULLISH_KEYWORDS = {
    "大買": 3.0, "狂買": 3.0, "漲停": 3.5, "創高": 2.5, "突破": 2.0, "利多": 2.5,
    "飆升": 2.5, "旺季": 1.5, "成長": 1.5, "倍增": 2.5, "暴增": 2.5, "回溫": 1.5,
    "獲利佳": 2.0, "調升": 2.0, "擴產": 2.0, "大單": 2.5, "加碼": 2.0, "買超": 2.0,
    "看好": 1.5, "續強": 1.8, "營收創高": 3.0, "轉虧為盈": 3.0, "供不應求": 2.5, "站回": 1.5
}

# 負向/偏空情緒關鍵字與權重
BEARISH_KEYWORDS = {
    "大賣": -3.0, "狂賣": -3.0, "跌停": -3.5, "破底": -3.0, "下挫": -2.0, "重挫": -3.0,
    "利空": -2.5, "暴跌": -3.0, "腰斬": -3.5, "衰退": -2.0, "急凍": -2.5, "調降": -2.0,
    "虧損": -2.0, "減產": -2.0, "砍單": -3.0, "跳水": -3.0, "賣超": -2.0, "看淡": -1.5,
    "走疲": -1.8, "示警": -2.0, "賣壓": -1.5, "逆風": -2.0, "提防": -1.5
}

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    量化分析文字/新聞的情緒得分
    返回:
      score: 正規化後情緒分數 (-1.0 ~ +1.0)
      sentiment: "BULLISH" | "BEARISH" | "NEUTRAL"
      matched_bullish: 匹配到的多方詞
      matched_bearish: 匹配到的空方詞
    """
    bullish_hits = []
    bearish_hits = []
    raw_score = 0.0

    for kw, weight in BULLISH_KEYWORDS.items():
        if kw in text:
            bullish_hits.append(kw)
            raw_score += weight

    for kw, weight in BEARISH_KEYWORDS.items():
        if kw in text:
            bearish_hits.append(kw)
            raw_score += weight

    # 使用雙曲正切 (tanh) 概念平滑映射至 [-1.0, 1.0]
    normalized_score = round(max(min(raw_score / 6.0, 1.0), -1.0), 2)
    
    if normalized_score >= 0.25:
        sentiment = "BULLISH (偏多)"
    elif normalized_score <= -0.25:
        sentiment = "BEARISH (偏空)"
    else:
        sentiment = "NEUTRAL (中立/觀望)"

    return {
        "score": normalized_score,
        "sentiment": sentiment,
        "matched_bullish": bullish_hits,
        "matched_bearish": bearish_hits
    }

def summarize_market_news_sentiment(news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    彙整整體市場新聞情緒趨勢
    """
    if not news_list:
        return {"overall_score": 0.0, "overall_sentiment": "NEUTRAL", "bullish_ratio": 0.5, "sample_count": 0}

    total_score = 0.0
    bullish_count = 0
    bearish_count = 0

    for item in news_list:
        full_text = f"{item.get('title', '')} {item.get('summary', '')}"
        res = analyze_sentiment(full_text)
        item["sentiment_analysis"] = res
        total_score += res["score"]
        if res["score"] > 0:
            bullish_count += 1
        elif res["score"] < 0:
            bearish_count += 1

    avg_score = round(total_score / len(news_list), 2)
    if avg_score >= 0.2:
        overall_sentiment = "BULLISH (市場偏多氛圍)"
    elif avg_score <= -0.2:
        overall_sentiment = "BEARISH (市場避險保守)"
    else:
        overall_sentiment = "NEUTRAL (盤整震盪觀望)"

    return {
        "overall_score": avg_score,
        "overall_sentiment": overall_sentiment,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "sample_count": len(news_list),
        "analyzed_news": news_list
    }

if __name__ == "__main__":
    test_text = "集團作帳行情助攻，外資投信同步大買，台股暴增成交量站回高點"
    print("Test Single:", analyze_sentiment(test_text))
