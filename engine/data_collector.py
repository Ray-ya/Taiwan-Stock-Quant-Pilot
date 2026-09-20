"""
Taiwan-Stock-Quant-Pilot - Robust Data Collector
支援 TWSE CSV/JSON 行情自動解析、週末/假日自動向前尋找最近交易日、鉅亨網即時重大新聞
"""

import csv
import datetime
import io
import json
import ssl
import urllib.request
from typing import Dict, List, Any

CTX = ssl._create_unverified_context()

TARGET_STOCK_POOL = [
    "2330", "2317", "2454", "2382", "2308", "2412", "2881", "2882", "2303", "3711",
    "2891", "3231", "2603", "2886", "2357", "1216", "2884", "2892", "2885", "5880",
    "2880", "1301", "1303", "2002", "2887", "3008", "2379", "6669", "2345", "3034",
    "2327", "2395", "4938", "2890", "5876", "2801", "2609", "2615", "1101", "2912",
    "3045", "4904", "9910", "1504", "1519", "1513", "1503", "2376", "2356", "3661"
]

def fetch_twse_daily_quotes() -> Dict[str, Dict[str, Any]]:
    """
    抓取 TWSE 全市場每日收盤行情 (STOCK_DAY_ALL)
    """
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=open_data"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    results = {}
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            content = resp.read().decode("utf-8-sig", errors="ignore")
            reader = csv.reader(io.StringIO(content))
            header = next(reader, None)
            for row in reader:
                if len(row) < 9:
                    continue
                code = row[1].strip()
                name = row[2].strip()
                try:
                    volume = int(float(row[3].replace(",", ""))) // 1000  # 成交張數
                    open_p = float(row[5].replace(",", "")) if row[5] not in ["--", ""] else 0.0
                    high_p = float(row[6].replace(",", "")) if row[6] not in ["--", ""] else 0.0
                    low_p = float(row[7].replace(",", "")) if row[7] not in ["--", ""] else 0.0
                    close_p = float(row[8].replace(",", "")) if row[8] not in ["--", ""] else 0.0
                    change_p = float(row[9].replace(",", "").replace("+", "")) if row[9] not in ["--", ""] else 0.0
                    
                    results[code] = {
                        "code": code,
                        "name": name,
                        "volume": volume,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "close": close_p,
                        "change": change_p
                    }
                except Exception:
                    continue
    except Exception as e:
        print(f"[Warn] fetch_twse_daily_quotes error: {e}")
    return results

def fetch_twse_institutional_investors(days_back: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    抓取最近一個有效交易日的三大法人買賣超 (T86)
    會自動從今天向前推回尋找有效開盤日
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    now = datetime.datetime.now()
    for delta in range(days_back):
        target_date = now - datetime.timedelta(days=delta)
        date_str = target_date.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALLBUT0999&response=json"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("stat") == "OK" and "data" in data and len(data["data"]) > 0:
                    results = {}
                    for row in data["data"]:
                        code = row[0].strip()
                        try:
                            foreign_shares = int(row[4].replace(",", "")) // 1000
                            trust_shares = int(row[10].replace(",", "")) // 1000
                            dealer_shares = int(row[11].replace(",", "")) // 1000
                            total_shares = int(row[18].replace(",", "")) // 1000
                            results[code] = {
                                "date": date_str,
                                "foreign": foreign_shares,
                                "trust": trust_shares,
                                "dealer": dealer_shares,
                                "total": total_shares
                            }
                        except Exception:
                            continue
                    return results
        except Exception:
            continue
    return {}

def fetch_cnyes_market_news(limit: int = 15) -> List[Dict[str, Any]]:
    """
    抓取鉅亨網最新台股重大新聞
    """
    url = f"https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("items", {}).get("data", [])
            news_list = []
            for item in items:
                title = item.get("title", "")
                summary = item.get("summary", "")
                publish_at = item.get("publishAt", 0)
                time_str = datetime.datetime.fromtimestamp(publish_at).strftime("%Y-%m-%d %H:%M") if publish_at else ""
                news_list.append({
                    "title": title,
                    "summary": summary,
                    "time": time_str,
                    "newsId": item.get("newsId")
                })
            return news_list
    except Exception as e:
        print(f"[Warn] fetch_cnyes_market_news error: {e}")
        return []

if __name__ == "__main__":
    print("Testing data_collector.py...")
    quotes = fetch_twse_daily_quotes()
    print(f"Total Quotes: {len(quotes)}. 2330:", quotes.get("2330"))
    inst = fetch_twse_institutional_investors()
    print(f"Total Institutional: {len(inst)}. 2330:", inst.get("2330"))
    news = fetch_cnyes_market_news(5)
    print(f"Total News: {len(news)}. Top: {news[0]['title'] if news else 'None'}")
