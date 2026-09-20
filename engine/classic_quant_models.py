"""
Classic Quantitative Trading Models Distillation Engine (十大經典量化交易模型萃取模組)
針對台股市場特性（10% 漲跌幅、三大法人籌碼、融資融券、T+2 結算、除權息旺季、盤中逐筆撮合）進行在地化調適與嚴謹數學建模。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

class ClassicQuantDistillery:
    """
    全球公認前十大經典量化交易模型萃取與訊號生成器
    涵蓋數學推導、台股在地化參數與結構化訊號輸出
    """

    # -------------------------------------------------------------
    # 1. 雙動量模型 (Dual Momentum - Gary Antonacci)
    # -------------------------------------------------------------
    @staticmethod
    def dual_momentum(prices: pd.Series, benchmark_prices: pd.Series, lookback: int = 60, risk_free_rate: float = 0.015) -> Dict[str, Any]:
        """
        數學原理：
        - 絕對動量 (Absolute Momentum / Time-Series Momentum):
          R_abs = (P_t / P_{t-L}) - 1
          判斷 R_abs > R_f (無風險利率或0)，濾除系統性下行風險。
        - 相對動量 (Relative Momentum / Cross-Sectional Momentum):
          R_rel = R_asset - R_benchmark
          判斷超額報酬是否大於0，選擇強勢領頭資產。
        台股在地化：
          考量台股加權指數高權值集中度 (台積電佔比逾30%)，以大盤作為 Benchmark，
          並設定 60 日 (季線循環) 檢驗季度除權息與季底作帳效應。
        """
        if len(prices) < lookback or len(benchmark_prices) < lookback:
            return {"signal": "HOLD", "score": 0.0, "reason": "資料長度不足"}

        asset_return = float((prices.iloc[-1] / prices.iloc[-lookback]) - 1.0)
        bench_return = float((benchmark_prices.iloc[-1] / benchmark_prices.iloc[-lookback]) - 1.0)
        rf_period = risk_free_rate * (lookback / 252.0)

        absolute_momentum = asset_return > rf_period
        relative_momentum = asset_return > bench_return

        if absolute_momentum and relative_momentum:
            signal = "STRONG_BUY"
            score = round(asset_return - bench_return, 4)
            reason = f"絕對動量 (+{asset_return:.2%}) 超越無風險門檻且相對動量強於大盤 (+{bench_return:.2%})"
        elif absolute_momentum and not relative_momentum:
            signal = "WEAK_BUY"
            score = round(asset_return, 4)
            reason = f"具備正絕對動量 (+{asset_return:.2%})，但動能落後於大盤 (+{bench_return:.2%})"
        else:
            signal = "CASH/DEFENSIVE"
            score = round(asset_return, 4)
            reason = f"絕對動量轉負 ({asset_return:.2%}) 或低於基準，建議轉換至防守底倉或現金"

        return {
            "model": "Dual Momentum",
            "signal": signal,
            "asset_return": round(asset_return, 4),
            "bench_return": round(bench_return, 4),
            "excess_return": round(asset_return - bench_return, 4),
            "score": score,
            "reason": reason
        }

    # -------------------------------------------------------------
    # 2. 統計套利與配對交易 (Pairs Trading / Cointegration - Gatev et al.)
    # -------------------------------------------------------------
    @staticmethod
    def pairs_trading(series_a: pd.Series, series_b: pd.Series, lookback: int = 60, entry_z: float = 2.0, exit_z: float = 0.5) -> Dict[str, Any]:
        """
        數學原理：
        - 假設兩同業資產價格序列具有協整關係 (Cointegrated)：
          ln(P_{A,t}) = alpha + beta * ln(P_{B,t}) + epsilon_t
          殘差 (Spread) S_t = P_{A,t} / P_{B,t} 或 S_t = ln(P_{A,t}) - beta * ln(P_{B,t}) 為平穩序列 I(0)。
        - 正規化 Z-Score:
          Z_t = (S_t - mu_S) / sigma_S
        台股在地化：
          適用台股同族群權值配對（如 2303聯電 vs 6770力積電、2330台積電 vs 2454聯發科、2881富邦金 vs 2882國泰金）。
          注意台股放空融券限額與停券（股東會、除權息）限制。
        """
        if len(series_a) < lookback or len(series_b) < lookback:
            return {"signal": "HOLD", "z_score": 0.0, "reason": "資料不足"}

        # 計算價格比率 Spread
        spread = series_a.iloc[-lookback:] / series_b.iloc[-lookback:]
        mean = float(spread.mean())
        std = float(spread.std())

        if std == 0:
            return {"signal": "HOLD", "z_score": 0.0, "reason": "標準差為零"}

        current_spread = float(spread.iloc[-1])
        z_score = float((current_spread - mean) / std)

        if z_score >= entry_z:
            signal = "SHORT_A_LONG_B"
            reason = f"Z-Score ({z_score:.2f}) 突破上限 (+{entry_z})，價差顯著高估，做空 A 做多 B 進行均值回歸套利"
        elif z_score <= -entry_z:
            signal = "LONG_A_SHORT_B"
            reason = f"Z-Score ({z_score:.2f}) 跌破下限 (-{entry_z})，價差顯著低估，做多 A 做空 B 進行均值回歸套利"
        elif abs(z_score) <= exit_z:
            signal = "EXIT_CONVERGENCE"
            reason = f"Z-Score ({z_score:.2f}) 收斂至安全平倉區間 (+/-{exit_z})，獲利平倉"
        else:
            signal = "HOLD"
            reason = f"Z-Score ({z_score:.2f}) 處於常態震盪無套利空間"

        return {
            "model": "Pairs Trading",
            "signal": signal,
            "z_score": round(z_score, 2),
            "current_spread": round(current_spread, 4),
            "mean_spread": round(mean, 4),
            "std_spread": round(std, 4),
            "reason": reason
        }

    # -------------------------------------------------------------
    # 3. 布林通道均值回歸與擠壓突破 (Bollinger Bands Squeeze & Mean Reversion)
    # -------------------------------------------------------------
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, num_std: float = 2.0) -> Dict[str, Any]:
        """
        數學原理：
        - 中軌 (Mid Band) = MA_N(P) = (1/N) * sum(P_{t-i})
        - 上軌 (Upper Band) = Mid + k * sigma
        - 下軌 (Lower Band) = Mid - k * sigma
        - 帶寬 (Bandwidth) = (Upper - Lower) / Mid
        - %B 指標 = (Close - Lower) / (Upper - Lower)
        台股在地化：
          20日 (月線) 為台股主力防守最常用週期。台股有 10% 漲跌幅限制，當帶寬壓縮小於 8% 時進入 Squeeze，
          一遇爆量即容易啟動連續單向趨勢；若無爆量則在上下軌執行均值回歸。
        """
        if len(prices) < period:
            return {"signal": "HOLD", "reason": "資料不足"}

        rolling_mean = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()

        mid = float(rolling_mean.iloc[-1])
        std = float(rolling_std.iloc[-1])
        upper = mid + (num_std * std)
        lower = mid - (num_std * std)
        curr = float(prices.iloc[-1])

        bandwidth = float((upper - lower) / mid) if mid > 0 else 0.0
        percent_b = float((curr - lower) / (upper - lower)) if (upper - lower) > 0 else 0.5

        if bandwidth < 0.08:
            signal = "VOLATILITY_SQUEEZE"
            reason = f"布林帶寬壓縮至極限 ({bandwidth:.2%})，預示極窄整理即將爆發強烈單向行情"
        elif curr <= lower:
            signal = "OVERSOLD_REBOUND"
            reason = f"股價 ({curr}) 觸碰或跌破下軌 ({lower:.2f})，%B={percent_b:.2f}，觸發超賣均值回歸買點"
        elif curr >= upper:
            signal = "OVERBOUGHT_REVERSION"
            reason = f"股價 ({curr}) 突破上軌 ({upper:.2f})，%B={percent_b:.2f}，短線過熱面臨均值收斂拉回"
        else:
            signal = "NEUTRAL"
            reason = f"股價於軌道內健康運行 (中軌: {mid:.2f}, 帶寬: {bandwidth:.2%})"

        return {
            "model": "Bollinger Bands",
            "signal": signal,
            "upper": round(upper, 2),
            "mid": round(mid, 2),
            "lower": round(lower, 2),
            "bandwidth": round(bandwidth, 4),
            "percent_b": round(percent_b, 4),
            "reason": reason
        }

    # -------------------------------------------------------------
    # 4. 法瑪-三因子/五因子模型多因子選股 (Fama-French Multi-Factor)
    # -------------------------------------------------------------
    @staticmethod
    def fama_french_scoring(market_cap: float, pb_ratio: float, roe: float, asset_growth: float) -> Dict[str, Any]:
        """
        數學原理：
        - Fama-French 5-Factor 資產定價模型：
          E(R_i) - R_f = beta_i*(R_m - R_f) + s_i*SMB + h_i*HML + r_i*RMW + c_i*CMA
          SMB: 規模溢價 (Small Minus Big)
          HML: 價值溢價 (High Minus Low, Book-to-Market)
          RMW: 獲利能力溢價 (Robust Minus Weak Operating Profitability)
          CMA: 投資風格溢價 (Conservative Minus Aggressive Investment)
        台股在地化：
          - 市值 (Market Cap)：50~1000 億新台幣之實質成長中型股享顯著超額報酬 (SMB)；
          - P/B (股價淨值比)：傳產/金融在 P/B < 1.5 具極高防守安全邊際 (HML)；
          - ROE：權益報酬率 >= 18% 驗證台股高階半導體與關鍵零組件之高定價權 (RMW)；
          - 資產增長率：避免盲目資本膨脹，成長率 < 15% 具備穩健自由現金流 (CMA)。
        """
        score = 0.0
        details = []

        # 1. SMB: 中型成長股加權
        if 50.0 <= market_cap <= 1000.0:
            score += 25.0
            details.append("規模因子(SMB): 處於 50~1000 億最佳流動性與高成長擴張區間 (+25)")
        else:
            score += 15.0
            details.append("規模因子(SMB): 超大型權值股具備法人避險與流動性溢價 (+15)")

        # 2. HML: 股價淨值比 (Book-to-Market 倒數)
        if pb_ratio < 1.5:
            score += 25.0
            details.append(f"價值因子(HML): P/B 為 {pb_ratio:.2f} (< 1.5)，具備高度價值低估安全邊際 (+25)")
        elif pb_ratio < 2.5:
            score += 15.0
            details.append(f"價值因子(HML): P/B 為 {pb_ratio:.2f}，估值處於合理區間 (+15)")
        else:
            score += 5.0
            details.append(f"價值因子(HML): P/B 為 {pb_ratio:.2f}，估值偏高 (+5)")

        # 3. RMW: 獲利能力 (ROE)
        if roe >= 18.0:
            score += 30.0
            details.append(f"盈利因子(RMW): ROE 達 {roe:.1f}% (>= 18%)，具備高毛利與產業護城河 (+30)")
        elif roe >= 10.0:
            score += 18.0
            details.append(f"盈利因子(RMW): ROE 達 {roe:.1f}%，營運獲利穩健健全 (+18)")
        else:
            score += 5.0
            details.append(f"盈利因子(RMW): ROE 為 {roe:.1f}%，資本運用效率偏弱 (+5)")

        # 4. CMA: 投資保守程度 (低資產盲目擴張)
        if asset_growth < 15.0:
            score += 20.0
            details.append(f"投資因子(CMA): 資產成長率 {asset_growth:.1f}% (< 15%)，資本開支自律穩健 (+20)")
        else:
            score += 5.0
            details.append(f"投資因子(CMA): 資產擴張速度達 {asset_growth:.1f}%，需留意自由現金流消耗 (+5)")

        grade = "EXCELLENT" if score >= 80 else "GOOD" if score >= 60 else "POOR"
        return {
            "model": "Fama-French 5-Factor",
            "score": round(score, 1),
            "grade": grade,
            "details": details
        }

    # -------------------------------------------------------------
    # 5. 成交量加權平均價與微觀訂單流 (VWAP / Order Flow Microstructure)
    # -------------------------------------------------------------
    @staticmethod
    def vwap_order_flow(high: float, low: float, close: float, volume: float, cum_vol: float, cum_pv: float, inside_vol: float, outside_vol: float) -> Dict[str, Any]:
        """
        數學原理：
        - VWAP (Volume-Weighted Average Price):
          VWAP_t = sum(P_i * V_i) / sum(V_i)
          其中 P_i 為典型價格 (High + Low + Close) / 3。
        - 訂單流失衡 (Order Flow Imbalance / Inflow Ratio):
          OFI = V_outside / (V_inside + V_outside)
          反映主動買單 (Taker Buy) 與主動賣單 (Taker Sell) 之微觀壓力差。
        台股在地化：
          台股自 2020 導入盤中逐筆撮合 (Continuous Trading)，
          外盤成交代表買方主動以賣價吃單 (主動積極)，內盤成交代表賣方主動以買價摜壓。
          VWAP 被法人大戶視為今日真實持倉成本防守線。
        """
        typical_price = (high + low + close) / 3.0
        new_cum_pv = cum_pv + (typical_price * volume)
        new_cum_vol = cum_vol + volume
        vwap = new_cum_pv / new_cum_vol if new_cum_vol > 0 else close

        total_matched = inside_vol + outside_vol
        inflow_ratio = outside_vol / total_matched if total_matched > 0 else 0.5

        if close > vwap and inflow_ratio > 0.58:
            signal = "BULLISH_ORDER_FLOW"
            reason = f"收盤價 ({close}) 站穩主力成本線 VWAP ({vwap:.2f}) 且外盤主動買單佔比高達 {inflow_ratio:.1%}"
        elif close < vwap and inflow_ratio < 0.42:
            signal = "BEARISH_ORDER_FLOW"
            reason = f"收盤價 ({close}) 跌破主力成本線 VWAP ({vwap:.2f}) 且內盤主動賣單佔比達 {1.0 - inflow_ratio:.1%}"
        else:
            signal = "NEUTRAL_FLOW"
            reason = f"價格圍繞主力 VWAP ({vwap:.2f}) 震盪換手，內外盤力道均衡 ({inflow_ratio:.1%})"

        return {
            "model": "VWAP Order Flow",
            "vwap": round(vwap, 2),
            "inflow_ratio": round(inflow_ratio, 3),
            "signal": signal,
            "reason": reason
        }

    # -------------------------------------------------------------
    # 6. 唐奇安通道與海龜趨勢突破 (Donchian Breakout / Turtle Trading)
    # -------------------------------------------------------------
    @staticmethod
    def donchian_breakout(highs: pd.Series, lows: pd.Series, closes: pd.Series, entry_period: int = 20, exit_period: int = 10) -> Dict[str, Any]:
        """
        數學原理：
        - 上軌 Upper_t = max(High_{t-1}, ..., High_{t-N})
        - 下軌 Lower_t = min(Low_{t-1}, ..., Low_{t-M})
        - 真實波動區間 (ATR / N 指標):
          TR_t = max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)
          ATR_k = EMA_k(TR)
        - 進場：突破 N 日高點做多；出場：跌破 M 日低點離場。
        - 停損設為 Entry - 2 * ATR，部位大小 Unit = (Capital * 1%) / (ATR * Multiplier)。
        台股在地化：
          針對台股 10% 漲跌幅，海龜 20 日突破往往搭配投信買盤；
          當突破發生時，以 2ATR 作為移動停損能完美避開隔日沖主力洗盤震盪。
        """
        if len(highs) < entry_period or len(lows) < entry_period:
            return {"signal": "HOLD", "reason": "資料不足"}

        n_high = float(highs.iloc[-entry_period-1:-1].max())
        n_low = float(lows.iloc[-exit_period-1:-1].min())
        curr_price = float(closes.iloc[-1])

        # 計算 ATR 14
        tr = np.maximum(highs - lows, np.maximum(abs(highs - closes.shift(1)), abs(lows - closes.shift(1))))
        atr = float(tr.rolling(window=14).mean().iloc[-1]) if len(tr) >= 14 else 1.0

        if curr_price > n_high:
            signal = "TURTLE_LONG_ENTRY"
            stop_loss = round(curr_price - 2.0 * atr, 2)
            reason = f"股價 ({curr_price}) 強勢突破 20 日高點 ({n_high:.2f})，觸發海龜進場訊號 (2ATR 停損: {stop_loss})"
        elif curr_price < n_low:
            signal = "TURTLE_EXIT"
            stop_loss = 0.0
            reason = f"股價 ({curr_price}) 跌破 10 日出場低點 ({n_low:.2f})，海龜多頭波段部位強制出場結利/停損"
        else:
            signal = "IN_CHANNEL"
            stop_loss = round(curr_price - 2.0 * atr, 2)
            reason = f"股價於通道內運行 (上軌突破線: {n_high:.2f}, 下軌離場線: {n_low:.2f})"

        return {
            "model": "Donchian Turtle Trading",
            "signal": signal,
            "atr_14": round(atr, 2),
            "stop_loss_suggested": stop_loss,
            "upper_channel": round(n_high, 2),
            "lower_channel": round(n_low, 2),
            "reason": reason
        }

    # -------------------------------------------------------------
    # 7. 波動率突破系統 (Volatility Breakout - Larry Williams)
    # -------------------------------------------------------------
    @staticmethod
    def volatility_breakout(today_open: float, prev_high: float, prev_low: float, curr_price: float, k: float = 0.6) -> Dict[str, Any]:
        """
        數學原理：
        - Range_{t-1} = High_{t-1} - Low_{t-1}
        - 觸發進場價 P_{trigger} = Open_t + k * Range_{t-1}
        - 核心概念：以昨日市場能量範圍作為量尺，當今日開盤後上漲幅度突破此量尺之 k 倍時，
          動能具備極高機率維持至收盤。
        台股在地化：
          台股 09:00 開盤具備高流動性衝擊，台股最佳實證參數 k 通常落在 0.5 ~ 0.7 之間。
          若觸發突破且開盤量放大，常形成當日強勢單向盤或直奔漲停。
        """
        prev_range = prev_high - prev_low
        trigger_price = today_open + (k * prev_range)

        if curr_price >= trigger_price:
            signal = "VOLATILITY_BREAKOUT_BUY"
            reason = f"現價 ({curr_price}) 突破 Larry Williams 波動率爆發線 ({trigger_price:.2f}, k={k})，日內強烈多頭動能成形"
        else:
            signal = "WAIT_FOR_BREAKOUT"
            reason = f"現價 ({curr_price}) 尚未達到突破閾值 ({trigger_price:.2f})，距離觸發點尚差 {trigger_price - curr_price:.2f} 元"

        return {
            "model": "Volatility Breakout (Larry Williams)",
            "signal": signal,
            "trigger_price": round(trigger_price, 2),
            "range": round(prev_range, 2),
            "k": k,
            "reason": reason
        }

    # -------------------------------------------------------------
    # 8. 全天候風險平價配置 (Risk Parity - Ray Dalio / Bridgewater)
    # -------------------------------------------------------------
    @staticmethod
    def risk_parity_weights(volatilities: Dict[str, float]) -> Dict[str, Any]:
        """
        數學原理：
        - 資產組合風險總變異數：sigma_p^2 = w^T * Sigma * w
        - 第 i 個資產之邊際風險貢獻 (Marginal Risk Contribution):
          MRC_i = (Sigma * w)_i / sigma_p
        - 風險貢獻 (Risk Contribution):
          RC_i = w_i * MRC_i
        - 目標：RC_1 = RC_2 = ... = RC_n = sigma_p / n
        - 在資產間相關係數相對獨立或同質假設下，權重反比於各自波動率：
          w_i propto 1 / sigma_i
        台股在地化：
          配置於高波動科技權值 (2330)、穩健金融 (2886/2891)、電信防守 (2412) 及台美公債 ETF (00679B)，
          以波動率倒數調控權重，消除單一電子產業崩盤之整體下行威脅。
        """
        inv_vols = {asset: 1.0 / vol for asset, vol in volatilities.items() if vol > 0}
        total_inv_vol = sum(inv_vols.values())
        weights = {asset: round(inv_vol / total_inv_vol, 4) for asset, inv_vol in inv_vols.items()}

        return {
            "model": "Risk Parity (全天候資產配置)",
            "weights": weights,
            "philosophy": "使防守資產與高成長資產之邊際風險貢獻完全均等，消除傳統 60/40 股權過度暴露之缺陷"
        }

    # -------------------------------------------------------------
    # 9. 事件驅動除權息與指數成分調整套利 (Event-Driven Arbitrage)
    # -------------------------------------------------------------
    @staticmethod
    def event_driven_arbitrage(historical_fill_rate: float, days_to_dividend: int, institutional_net_buy: int, yield_rate: float) -> Dict[str, Any]:
        """
        數學原理：
        - 預期除息價 P_{ex} = P_{pre} - Div
        - 填息機率條件模型：
          P(Fill | HistRate, InstFlow, Yield) = f(HistoricalFillRate, NetBuy, Yield)
        - 當歷史填息率 > 85%、現金殖利率 > 4%、且除息前法人籌碼無出逃反而吸籌時，
          具備結構性填息 Alpha。
        台股在地化：
          每年 6~8 月台股除權息大拜拜，特定壽險金控、高息 ETF (0056/00878/00919) 成份股調整與除息除權具有極高在地可預測性。
        """
        if historical_fill_rate >= 0.90 and yield_rate >= 4.5 and institutional_net_buy > 0:
            signal = "STRONG_EVENT_ARBITRAGE"
            confidence = "HIGH (歷史填息確定性 90%+)"
            reason = f"歷史填息率達 {historical_fill_rate:.0%}，現金殖利率 {yield_rate:.1f}%，除息前法人吸籌 {institutional_net_buy} 張，填息動能極高"
        elif historical_fill_rate >= 0.80 and yield_rate >= 4.0:
            signal = "MODERATE_EVENT_ARBITRAGE"
            confidence = "MEDIUM"
            reason = f"高殖利率 ({yield_rate:.1f}%) 且歷史填息率穩健 ({historical_fill_rate:.0%})，具備事件驅動套利條件"
        else:
            signal = "AVOID_TRAP"
            confidence = "LOW"
            reason = f"歷史填息率偏低或無主力籌碼鎖碼，恐面臨貼息與除息後動能衰退風險"

        return {
            "model": "Event-Driven Arbitrage (除權息與指數成分套利)",
            "signal": signal,
            "confidence": confidence,
            "reason": reason
        }

    # -------------------------------------------------------------
    # 10. 機器學習特徵集成多因子模型 (Machine Learning Factor Ensemble / XGBoost-LightGBM)
    # -------------------------------------------------------------
    @staticmethod
    def ml_factor_ensemble(features: Dict[str, float]) -> Dict[str, Any]:
        """
        數學原理：
        - 梯度提升決策樹 (GBDT / LightGBM):
          y_hat_i = sum_{m=1}^M f_m(x_i),  f_m in F
        - 損失函數二階泰勒展開優化：
          L^{(t)} approx sum [ g_i * f_t(x_i) + 0.5 * h_i * f_t^2(x_i) ] + Omega(f_t)
        台股在地化特徵工程：
          - 法人籌碼集中度 (30%): 外資+投信佔比推升台股權值與中型飆股之首要核心特徵；
          - 量能爆發度 (25%): 突破 5 日均量 2 倍以上之換手動能；
          - 財經新聞情感 (20%): 鉅亨網/財訊等即時非結構化文字 NLP 情緒分數；
          - 均線多頭排列度 (15%): 5MA > 20MA > 60MA 趨勢排列得分；
          - 乖離率合理度 (10%): 防止 5 日乖離過大引發技術性短線回檔。
        """
        weights = {
            "institutional_ratio": 0.30,   # 法人籌碼集中度權重 30%
            "volume_surge": 0.25,          # 量能爆發度 25%
            "news_sentiment": 0.20,        # 新聞輿情特徵 20%
            "moving_average_trend": 0.15,  # 均線多頭排列 15%
            "bias_ratio": 0.10             # 乖離率合理性 10%
        }

        composite_score = sum(features.get(k, 0.0) * w for k, w in weights.items())
        normalized_score = round(min(max(composite_score, 0.0), 100.0), 2)

        if normalized_score >= 80.0:
            action = "STRONG_BUY_PREDICTION"
        elif normalized_score >= 60.0:
            action = "BUY_PREDICTION"
        elif normalized_score <= 35.0:
            action = "SELL_AVOID_PREDICTION"
        else:
            action = "NEUTRAL_HOLD"

        return {
            "model": "Machine Learning Factor Ensemble (LightGBM/XGBoost 模擬)",
            "predicted_score": normalized_score,
            "action": action,
            "feature_attribution": weights,
            "input_features": features
        }
