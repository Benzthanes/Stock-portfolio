"""
Quantitative Evaluation & Technical Indicator Calculation Engine
Analyzes individual stocks against the 'Super Pullback in Uptrend' dip strategy,
incorporating forward fundamentals (Revenue/Net Income Growth, PEG, Wall St consensus)
and news catalyst monitoring.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news import fetch_batch_news, fetch_batch_catalysts
from src.profiles import get_business_summary

FALLBACK_SL_RATIO = 0.95
MIN_SL_RATIO = 0.5


def atr_stop_loss(close: float, atr: Optional[float]) -> float:
    """1.5 ATR stop, floored at half the price so a huge ATR cannot push the stop to zero or below."""
    if atr and atr > 0:
        return round(max(close - 1.5 * atr, close * MIN_SL_RATIO), 2)
    return round(close * FALLBACK_SL_RATIO, 2)


def evaluate_stock(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a single stock dictionary from TradingView Scanner against technical and fundamental rules.
    Returns computed signals, score points, and risk metrics.
    """
    close = data.get("close") or 0.0
    open_price = data.get("open")
    if open_price is None or open_price <= 0:
        open_price = close
    low = data.get("low") or close
    high = data.get("high") or close
    change_pct = data.get("change") or 0.0

    # Candle & Momentum Confirmation (Falling Knife Shield)
    is_green_candle = (close >= open_price)
    is_red_candle = (close < open_price)
    is_plunge_day = (change_pct <= -3.0) or (is_red_candle and change_pct <= -1.5)

    rsi = data.get("RSI")
    rsi_prev = data.get("RSI[1]")
    rsi_weekly = data.get("RSI|1W")
    stoch_k = data.get("Stoch.RSI.K")
    stoch_d = data.get("Stoch.RSI.D")
    stoch_k_prev = data.get("Stoch.RSI.K[1]")
    stoch_d_prev = data.get("Stoch.RSI.D[1]")
    sma20 = data.get("SMA20")
    sma50 = data.get("SMA50")
    sma200 = data.get("SMA200")
    ema50 = data.get("EMA50")
    ema200 = data.get("EMA200")
    bb_lower = data.get("BB.lower")
    macd_hist = data.get("MACD.hist")
    macd_hist_prev = data.get("MACD.hist[1]")
    mfi = data.get("MoneyFlow")
    adx = data.get("ADX")
    atr = data.get("ATR")
    vol = data.get("volume") or 0.0
    avg_vol_30 = data.get("average_volume_30d_calc") or 1.0

    # Fundamentals
    rev_growth_yoy = data.get("total_revenue_yoy_growth_ttm")
    net_inc_growth_yoy = data.get("net_income_yoy_growth_ttm")
    peg = data.get("price_earnings_growth_ttm")
    pe = data.get("price_earnings_ttm")
    roe = data.get("return_on_equity_fq")
    debt_to_equity = data.get("debt_to_equity_fq")
    fcf = data.get("free_cash_flow_ttm")
    rec_mark = data.get("recommendation_mark")

    # 1. 200-Day Macro Trend
    is_above_sma200 = (close > sma200) if sma200 else False
    is_above_ema200 = (close > ema200) if ema200 else False
    is_above_trend = is_above_sma200 or is_above_ema200

    dist_sma200_pct = ((close - sma200) / sma200 * 100.0) if sma200 else None
    dist_ema200_pct = ((close - ema200) / ema200 * 100.0) if ema200 else None

    # Value Zone: 0% to +5% above 200-day trend lines
    in_value_zone = False
    for dist in [dist_sma200_pct, dist_ema200_pct]:
        if dist is not None and 0.0 <= dist <= 5.0:
            in_value_zone = True
            break

    # Distance to SMA50 & Lower BB
    dist_sma50_pct = ((close - sma50) / sma50 * 100.0) if sma50 else None
    dist_bb_lower_pct = ((close - bb_lower) / bb_lower * 100.0) if bb_lower else None

    # 2. Multi-Indicator Momentum & Confluence
    rsi_hook_up = (rsi > rsi_prev) if (rsi is not None and rsi_prev is not None) else False

    # Stochastic RSI Crossover (require stoch_k >= 10.0 to filter false crosses at sub-10 floor)
    stoch_cross_up = False
    fresh_stoch_cross = False
    if stoch_k is not None and stoch_d is not None:
        stoch_cross_up = (stoch_k > stoch_d)
        if stoch_k_prev is not None and stoch_d_prev is not None:
            fresh_stoch_cross = (stoch_k_prev <= stoch_d_prev) and (stoch_k > stoch_d) and (10.0 <= stoch_k <= 35.0)

    stoch_bullish = stoch_cross_up and (stoch_k is not None and 10.0 <= stoch_k <= 40.0)
    macd_tick_up = (macd_hist > macd_hist_prev) if (macd_hist is not None and macd_hist_prev is not None) else False
    mfi_oversold = (mfi <= 30.0) if mfi is not None else False
    mfi_extreme = (mfi <= 20.0) if mfi is not None else False

    # Actionable Confirmation: Needs green candle or RSI hook up, and not in active plunge
    has_reversal_confirmation = is_green_candle or rsi_hook_up
    is_actionable = has_reversal_confirmation and not is_plunge_day

    # Falling Knife Filter (ADX > 35 indicates strong trending plunge)
    adx_falling_knife = (adx > 35.0) if adx is not None else False
    vol_ratio = (vol / avg_vol_30) if avg_vol_30 > 0 else 1.0

    touch_bb_lower = ((low <= bb_lower * 1.005) or (close <= bb_lower * 1.01)) if bb_lower else False
    weekly_bullish = (rsi_weekly >= 45.0) if rsi_weekly is not None else False
    
    # Trade Setup: ATR Stop Loss & Target calculation
    stop_loss = atr_stop_loss(close, atr)

    target_ma = sma50 or ema50
    if target_ma and target_ma > close:
        take_profit = round(target_ma, 2)
    else:
        take_profit = round(close * 1.08, 2)
        
    risk = max(round(close - stop_loss, 2), 0.01)
    reward = max(round(take_profit - close, 2), 0.0)
    rr_ratio = round(reward / risk, 1)

    # Key Support & Resistance Levels
    if sma200 and sma200 > 0 and sma200 < close and (close - sma200) / close <= 0.08:
        key_support = round(sma200, 2)
        support_desc = "เส้น 200 วัน (SMA 200)"
    elif bb_lower and bb_lower > 0 and bb_lower < close:
        key_support = round(bb_lower, 2)
        support_desc = "ขอบล่าง Bollinger Band"
    else:
        key_support = round(stop_loss, 2)
        support_desc = "แนวรับความผันผวน 1.5 ATR"

    bb_upper = data.get("BB.upper") or 0.0
    if target_ma and target_ma > close:
        key_resistance = round(target_ma, 2)
        resistance_desc = "เส้น 50 วัน (Mean Reversion)"
    elif sma200 and sma200 > close:
        key_resistance = round(sma200, 2)
        resistance_desc = "เส้น 200 วัน (SMA 200)"
    elif bb_upper and bb_upper > close:
        key_resistance = round(bb_upper, 2)
        resistance_desc = "ขอบบน Bollinger Band"
    elif data.get("price_target_average") and data.get("price_target_average") > close:
        key_resistance = round(data.get("price_target_average"), 2)
        resistance_desc = "ราคาเป้าหมายเฉลี่ยสถาบัน"
    else:
        key_resistance = round(take_profit, 2)
        resistance_desc = "เป้าหมายทำกำไร +8%"

    # Earnings Proximity Calculation
    now_ts = int(time.time())
    next_earnings_ts = data.get("earnings_release_next_date")
    past_earnings_ts = data.get("earnings_release_date")
    
    days_to_earnings = None
    earnings_date_str = "-"
    is_earnings_near = False
    
    selected_earnings_ts = None
    if next_earnings_ts and next_earnings_ts > now_ts:
        selected_earnings_ts = next_earnings_ts
    elif past_earnings_ts and past_earnings_ts > now_ts:
        selected_earnings_ts = past_earnings_ts
        
    if selected_earnings_ts:
        diff_days = (selected_earnings_ts - now_ts) / 86400.0
        days_to_earnings = round(diff_days, 1)
        is_earnings_near = (days_to_earnings <= 14.0)
        try:
            earnings_date_str = datetime.fromtimestamp(selected_earnings_ts, tz=timezone.utc).strftime("%d %b %Y")
        except Exception:
            earnings_date_str = str(selected_earnings_ts)

    # Score calculation (0 - 8+ points)
    score_points = 0.0
    signal_tags = []
    
    if is_above_trend:
        score_points += 1.0
        trend_label = "Above SMA200" if is_above_sma200 else "Above EMA200"
        signal_tags.append(trend_label)
        if in_value_zone:
            score_points += 0.5
            signal_tags.append("Value Zone (0-5% to 200D) 💎")
            
    if weekly_bullish:
        score_points += 1.0
        signal_tags.append("Weekly Bullish (RSI≥45)")
    if rsi is not None and rsi <= 30:
        score_points += 1.0
        signal_tags.append("Deep Oversold (RSI≤30)")
    elif rsi is not None and rsi <= 35:
        score_points += 0.5
        signal_tags.append("Oversold (RSI≤35)")
    if rsi_hook_up:
        score_points += 0.5
        signal_tags.append("RSI Hook Up ⤴")
        
    if fresh_stoch_cross:
        score_points += 1.0
        signal_tags.append("Fresh Stoch Cross ✂")
    elif stoch_bullish:
        score_points += 0.5
        signal_tags.append("Stoch Bullish (%K>%D)")
        
    if macd_tick_up:
        score_points += 0.5
        signal_tags.append("MACD Hist Tick 📈")
        
    if mfi_extreme:
        score_points += 0.5
        signal_tags.append("MFI Capitulation (<20) 🌊")
    elif mfi_oversold:
        score_points += 0.25
        signal_tags.append("MFI Oversold (≤30)")
        
    if touch_bb_lower:
        score_points += 0.5
        signal_tags.append("Touch BB Lower Band")
        
    if rr_ratio >= 2.0:
        score_points += 0.5
        signal_tags.append(f"High R:R ({rr_ratio}x) 🎯")
        
    if vol_ratio >= 1.3:
        score_points += 0.5
        signal_tags.append(f"High Vol ({vol_ratio:.1f}x)")

    # Candle price action signals
    if is_green_candle:
        score_points += 0.5
        signal_tags.append("Green Reversal Candle 🕯️🟢")
    elif is_plunge_day:
        score_points -= 1.0
        signal_tags.append("⚠️ Plunge Day (มีดยังหล่น)")

    # Universal Long-Term Value & Fundamental Quality (Across All Sectors)
    if roe is not None:
        if roe >= 25.0:
            score_points += 1.5
            signal_tags.append(f"Elite ROE ({roe:.0f}%) 🏆")
        elif roe >= 15.0:
            score_points += 1.0
            signal_tags.append(f"High ROE ({roe:.0f}%) 💎")
        elif roe < 0.0:
            score_points -= 1.5
            signal_tags.append("⚠️ Neg ROE Trap")

    if fcf is not None and fcf > 0:
        score_points += 0.5
        signal_tags.append("FCF Cash Cow 💵")

    if rev_growth_yoy is not None:
        if rev_growth_yoy >= 15.0:
            score_points += 1.0
            signal_tags.append(f"Rev Growth +{rev_growth_yoy:.0f}% 🚀")
        elif rev_growth_yoy >= 5.0:
            score_points += 0.5
            signal_tags.append(f"Rev Growth +{rev_growth_yoy:.0f}%")
        elif rev_growth_yoy < 0.0:
            score_points -= 1.5
            signal_tags.append("⚠️ Neg Rev Trap")

    if peg is not None:
        if 0.0 < peg <= 1.2:
            score_points += 1.0
            signal_tags.append(f"Attractive PEG {peg:.1f} 💎")
        elif 1.2 < peg <= 1.8:
            score_points += 0.5
            signal_tags.append(f"Fair PEG {peg:.1f}")
        elif peg > 3.0:
            score_points -= 1.0
            signal_tags.append("⚠️ High PEG Overvalued")

    sec = data.get("sector") or ""
    if debt_to_equity is not None and sec != "Finance":
        if 0.0 <= debt_to_equity <= 1.0:
            score_points += 0.5
            signal_tags.append(f"Safe Debt (D/E {debt_to_equity:.1f}) 🛡️")
        elif debt_to_equity > 3.0:
            score_points -= 1.0
            signal_tags.append("⚠️ High Debt Risk")

    if rec_mark is not None and rec_mark <= 1.5:
        score_points += 0.5
        signal_tags.append("Wall St Strong Buy 🌟")

    if adx_falling_knife:
        score_points -= 1.5
        signal_tags.append("⚠️ High ADX Falling Knife")

    # Rating Tier with Reversal Confirmation Guard
    if score_points >= 4.5:
        if is_actionable:
            tier = "⭐⭐⭐ Actionable Dip Buy 🎯"
        else:
            tier = "👀 รอสร้างฐาน (Forming Base - วันทิ้งตัว)"
    elif score_points >= 3.0:
        if is_actionable:
            tier = "⭐⭐ Good Setup (Actionable) 🎯"
        else:
            tier = "⭐ Watchlist (รอแท่งกลับตัว)"
    else:
        if is_plunge_day:
            tier = "👀 รอสร้างฐาน (Forming Base - วันทิ้งตัว)"
        else:
            tier = "⭐ Watchlist"
        
    exchange = data.get("exchange", "NASDAQ")
    ticker = data.get("ticker", data.get("name", ""))
    tv_url = f"https://www.tradingview.com/chart/?symbol={exchange}:{ticker}"
    sector = data.get("sector", "-")
    industry = data.get("industry", "-")
    business_summary = get_business_summary(ticker, sector=sector, industry=industry)

    return {
        "ticker": ticker,
        "exchange": exchange,
        "name": data.get("description") or ticker,
        "sector": sector,
        "industry": industry,
        "business_summary": business_summary,
        "close": close,
        "change_pct": change_pct,
        "rsi": round(rsi, 2) if rsi is not None else None,
        "rsi_prev": round(rsi_prev, 2) if rsi_prev is not None else None,
        "rsi_weekly": round(rsi_weekly, 2) if rsi_weekly is not None else None,
        "stoch_k": round(stoch_k, 2) if stoch_k is not None else None,
        "stoch_d": round(stoch_d, 2) if stoch_d is not None else None,
        "sma50": round(sma50, 2) if sma50 else None,
        "sma200": round(sma200, 2) if sma200 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "ema200": round(ema200, 2) if ema200 else None,
        "bb_lower": round(bb_lower, 2) if bb_lower else None,
        "dist_sma200_pct": round(dist_sma200_pct, 2) if dist_sma200_pct is not None else None,
        "dist_ema200_pct": round(dist_ema200_pct, 2) if dist_ema200_pct is not None else None,
        "dist_sma50_pct": round(dist_sma50_pct, 2) if dist_sma50_pct is not None else None,
        "dist_bb_lower_pct": round(dist_bb_lower_pct, 2) if dist_bb_lower_pct is not None else None,
        "is_above_sma200": is_above_sma200,
        "is_above_ema200": is_above_ema200,
        "is_above_trend": is_above_trend,
        "in_value_zone": in_value_zone,
        "weekly_bullish": weekly_bullish,
        "rsi_hook_up": rsi_hook_up,
        "stoch_cross_up": stoch_cross_up,
        "fresh_stoch_cross": fresh_stoch_cross,
        "macd_tick_up": macd_tick_up,
        "mfi": round(mfi, 1) if mfi is not None else None,
        "mfi_oversold": mfi_oversold,
        "adx": round(adx, 1) if adx is not None else None,
        "adx_falling_knife": adx_falling_knife,
        "atr": round(atr, 2) if atr is not None else None,
        "key_support": key_support,
        "support_desc": support_desc,
        "key_resistance": key_resistance,
        "resistance_desc": resistance_desc,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rr_ratio": rr_ratio,
        "touch_bb_lower": touch_bb_lower,
        "vol_ratio": round(vol_ratio, 2),
        "open": open_price,
        "is_green_candle": is_green_candle,
        "is_red_candle": is_red_candle,
        "is_plunge_day": is_plunge_day,
        "has_reversal_confirmation": has_reversal_confirmation,
        "is_actionable": is_actionable,
        "days_to_earnings": days_to_earnings,
        "earnings_date_str": earnings_date_str,
        "is_earnings_near": is_earnings_near,
        "score_points": round(score_points, 1),
        "tier": tier,
        "signal_tags": signal_tags,
        "tv_url": tv_url,
        "rev_growth_yoy": round(rev_growth_yoy, 1) if rev_growth_yoy is not None else None,
        "net_inc_growth_yoy": round(net_inc_growth_yoy, 1) if net_inc_growth_yoy is not None else None,
        "peg": round(peg, 2) if peg is not None else None,
        "pe": round(pe, 1) if pe is not None else None,
        "roe": round(roe, 1) if roe is not None else None,
        "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity is not None else None,
        "fcf": fcf,
        "rec_mark": round(rec_mark, 2) if rec_mark is not None else None,
        "price_target_average": round(data.get("price_target_average"), 2) if data.get("price_target_average") else None,
        "price_target_high": round(data.get("price_target_high"), 2) if data.get("price_target_high") else None,
        "price_target_low": round(data.get("price_target_low"), 2) if data.get("price_target_low") else None,
        "target_upside_pct": round(((data.get("price_target_average") - close) / close * 100.0), 1) if (data.get("price_target_average") and close > 0) else None,
        "rec_buy": data.get("recommendation_buy"),
        "rec_hold": data.get("recommendation_hold"),
        "rec_sell": data.get("recommendation_sell")
    }


SECTOR_ALIASES = {
    "financials": ["Finance"],
    "financial": ["Finance"],
    "banking": ["Finance"],
    "banks": ["Finance"],
    "finance": ["Finance"],
    "tech": ["Technology Services", "Electronic Technology"],
    "technology": ["Technology Services", "Electronic Technology"],
    "electronic": ["Electronic Technology"],
    "semiconductor": ["Electronic Technology"],
    "semiconductors": ["Electronic Technology"],
    "chips": ["Electronic Technology"],
    "healthcare": ["Health Technology", "Health Services"],
    "health": ["Health Technology", "Health Services"],
    "pharma": ["Health Technology"],
    "biotech": ["Health Technology"],
    "consumer": ["Consumer Services", "Consumer Non-Durables", "Consumer Durables"],
    "consumer non-durables": ["Consumer Non-Durables"],
    "consumer durables": ["Consumer Durables"],
    "retail": ["Retail Trade"],
    "energy": ["Energy Minerals"],
    "oil": ["Energy Minerals"],
    "utility": ["Utilities"],
    "utilities": ["Utilities"],
    "telecom": ["Communications"],
    "telecommunication": ["Communications"],
    "industrial": ["Industrial Services", "Producer Manufacturing"],
    "industrials": ["Producer Manufacturing", "Industrial Services"],
    "manufacturing": ["Producer Manufacturing"],
    "materials": ["Process Industries"],
}


def filter_stocks(
    raw_stock_data: List[Dict[str, Any]],
    rsi_max: float = 35.0,
    require_sma200: bool = True,
    require_ema200: bool = False,
    weekly_rsi_min: Optional[float] = 45.0,
    require_stoch_cross: bool = False,
    sector_filter: Optional[str] = None,
    min_rr_ratio: Optional[float] = None,
    exclude_falling_knife: bool = True,
    require_growth: bool = False,
    max_peg: Optional[float] = None,
    require_strong_buy: bool = False,
    require_reversal: bool = False
) -> List[Dict[str, Any]]:
    """
    Filter and rank evaluated stocks based on strategy and fundamental criteria.
    """
    evaluated_list = [evaluate_stock(stock) for stock in raw_stock_data]
    filtered = []

    for stock in evaluated_list:
        if sector_filter:
            s_clean = sector_filter.strip().lower()
            target_sectors = SECTOR_ALIASES.get(s_clean, [sector_filter.strip()])
            stock_sector = (stock.get("sector") or "").lower()
            match = False
            for ts in target_sectors:
                if stock_sector and (ts.lower() in stock_sector or stock_sector in ts.lower()):
                    match = True
                    break
            if not match:
                continue

        rsi = stock.get("rsi")
        if rsi is None or rsi > rsi_max:
            continue

        if require_sma200 and not stock["is_above_sma200"]:
            continue

        if require_ema200 and not stock["is_above_ema200"]:
            continue

        if weekly_rsi_min is not None and (stock.get("rsi_weekly") is None or stock["rsi_weekly"] < weekly_rsi_min):
            continue

        if require_stoch_cross and not stock["fresh_stoch_cross"]:
            continue

        if exclude_falling_knife and stock.get("adx_falling_knife"):
            continue

        if require_reversal and not stock.get("is_actionable"):
            continue

        if min_rr_ratio is not None and stock.get("rr_ratio") is not None:
            if stock["rr_ratio"] < min_rr_ratio:
                continue

        # Fundamental Filters
        if require_growth and (stock.get("rev_growth_yoy") is None or stock["rev_growth_yoy"] <= 0):
            continue

        if max_peg is not None:
            peg_val = stock.get("peg")
            if peg_val is None or peg_val > max_peg or peg_val <= 0:
                continue

        if require_strong_buy:
            rec = stock.get("rec_mark")
            if rec is None or rec > 2.0:
                continue

        filtered.append(stock)

    # Sort primarily by is_actionable (actionable first), then score_points, then R:R ratio, then RSI
    filtered.sort(
        key=lambda x: (
            -int(x.get("is_actionable", False)),
            -x["score_points"],
            -(x["rr_ratio"] if x["rr_ratio"] is not None else 0),
            x["rsi"] if x["rsi"] is not None else 999
        )
    )
    return filtered


def fetch_macro_market_regime(timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch SPY and QQQ technical indicators to gauge market-wide pullback pressure.
    """
    try:
        from src.tradingview import fetch_screener_data
        data = fetch_screener_data(["AMEX:SPY", "NASDAQ:QQQ"], timeout=timeout)
        spy_d = next((d for d in data if d.get("ticker") == "SPY"), {})
        qqq_d = next((d for d in data if d.get("ticker") == "QQQ"), {})

        spy_chg = spy_d.get("change") or 0.0
        qqq_chg = qqq_d.get("change") or 0.0
        spy_rsi = spy_d.get("RSI")
        qqq_rsi = qqq_d.get("RSI")
        spy_sma50 = spy_d.get("SMA50")
        qqq_sma50 = qqq_d.get("SMA50")
        spy_close = spy_d.get("close") or 0.0
        qqq_close = qqq_d.get("close") or 0.0

        spy_below_50 = (spy_close < spy_sma50) if (spy_close and spy_sma50) else False
        qqq_below_50 = (qqq_close < qqq_sma50) if (qqq_close and qqq_sma50) else False

        is_macro_pullback = (
            spy_below_50 or qqq_below_50 or
            spy_chg <= -1.2 or qqq_chg <= -1.8 or
            (spy_rsi is not None and spy_rsi < 40) or
            (qqq_rsi is not None and qqq_rsi < 38)
        )

        return {
            "is_macro_pullback": is_macro_pullback,
            "status": "⚠️ PULLBACK REGIME" if is_macro_pullback else "🟢 HEALTHY BULL REGIME",
            "spy": {"close": spy_close, "change": spy_chg, "rsi": round(spy_rsi, 1) if spy_rsi else None, "below_sma50": spy_below_50},
            "qqq": {"close": qqq_close, "change": qqq_chg, "rsi": round(qqq_rsi, 1) if qqq_rsi else None, "below_sma50": qqq_below_50},
            "warning": "ตลาดรวม (SPY/QQQ) กำลังปรับฐานหลุดต่ำกว่าเส้น SMA 50 วัน สถาบันกำลังลดพอร์ตเทขายในภาพรวม ควรงดรีบช้อนรับมีดในแท่งแดง และรอแท่งกลับตัวยืนยันก่อนเข้าซื้อเสมอ!" if is_macro_pullback else "ตลาดรวมอยู่ในเกณฑ์ปกติ สามารถพิจารณาช้อนซื้อตามแนวรับได้ตามแผน"
        }
    except Exception:
        return {
            "is_macro_pullback": False,
            "status": "⚪ UNKNOWN",
            "spy": {},
            "qqq": {},
            "warning": "ไม่สามารถตรวจสอบดัชนีตลาดรวมได้"
        }


def generate_markdown_report(
    matched_stocks: List[Dict[str, Any]],
    total_scanned: int,
    rsi_max: float,
    require_sma200: bool,
    weekly_rsi_min: Optional[float],
    universe_name: str = "S&P 100 + Nasdaq 100",
    sector_name: Optional[str] = None,
    require_ema200: bool = False,
    min_rr_ratio: Optional[float] = None,
    require_growth: bool = False,
    macro_regime: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format screened results into a clean, detailed Markdown report with TradingView links and live news.
    """
    if macro_regime is None:
        macro_regime = fetch_macro_market_regime()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# 📊 US Stock Dip Screener Report")
    lines.append(f"*Generated at: {now_str} | Total Scanned: {total_scanned} stocks ({universe_name})*\n")

    if macro_regime and macro_regime.get("status"):
        spy_info = macro_regime.get("spy", {})
        qqq_info = macro_regime.get("qqq", {})
        spy_parts = []
        if spy_info.get("close"):
            spy_parts.append(f"${spy_info['close']:.2f}")
        if spy_info.get("change") is not None:
            spy_parts.append(f"({spy_info['change']:+.2f}%)")
        spy_str = f"SPY {' '.join(spy_parts)}" if spy_parts else "SPY -"

        qqq_parts = []
        if qqq_info.get("close"):
            qqq_parts.append(f"${qqq_info['close']:.2f}")
        if qqq_info.get("change") is not None:
            qqq_parts.append(f"({qqq_info['change']:+.2f}%)")
        qqq_str = f"QQQ {' '.join(qqq_parts)}" if qqq_parts else "QQQ -"

        alert_type = "WARNING" if macro_regime.get("is_macro_pullback") else "NOTE"
        lines.append(f"> [!{alert_type}]")
        lines.append(f"> **ภาวะตลาดรวม (Macro Guard):** {macro_regime.get('status')} [{spy_str} | {qqq_str}]")
        lines.append(f"> {macro_regime.get('warning')}")
        lines.append("")

    lines.append("### 🎯 Criteria Applied (Super Pullback in Uptrend & Knife Guard):")
    lines.append(f"- **Daily RSI:** ≤ {rsi_max} (Oversold)")
    trend_rules = []
    if require_sma200:
        trend_rules.append("Price > SMA 200")
    if require_ema200:
        trend_rules.append("Price > EMA 200")
    if not trend_rules:
        trend_rules.append("❌ Trend Filter Disabled")
    lines.append(f"- **Trend Filters:** {', '.join(trend_rules)}")
    
    if weekly_rsi_min:
        lines.append(f"- **Weekly RSI Filter:** ≥ {weekly_rsi_min} (Weekly Bull Cycle)")
    lines.append("- **Falling Knife Guard:** กรองแท่งเทียนทิ้งตัวแดงหนัก (Plunge Day) และคัดแยกสถานะจุดเข้าซื้อ (Actionable vs Wait for Base)")
    if min_rr_ratio:
        lines.append(f"- **Min R:R Ratio:** ≥ {min_rr_ratio}x")
    if require_growth:
        lines.append("- **Quality Growth Filter:** Revenue YoY > 0% Active 🛡️")
    if sector_name:
        lines.append(f"- **Sector Filter:** {sector_name}")
    lines.append("")

    if not matched_stocks:
        lines.append("> [!NOTE]")
        lines.append(f"> ไม่พบหุ้นใน Universe ที่เข้าเกณฑ์เงื่อนไขทั้งหมด (RSI Day ≤ {rsi_max}" +
                     (f" และ Trend Filter Active" if (require_sma200 or require_ema200) else "") +
                     (f" และ Weekly RSI ≥ {weekly_rsi_min}" if weekly_rsi_min else "") +
                     (f" ในหมวด {sector_name}" if sector_name else "") +
                     "). ตลาดอาจอยู่ในช่วงขาขึ้นแข็งแกร่งหรือไม่มีหุ้นขนาดใหญ่ย่อตัวลึกในขณะนี้")
        lines.append("")
        lines.append("💡 *คำแนะนำ: สามารถลองปรับ `--rsi-max 40` หรือปิด Weekly Filter ด้วย `--no-weekly-filter` เพื่อดูหุ้นที่เริ่มย่อตัวระยะสั้น*")
        return "\n".join(lines)

    lines.append(f"### 🔍 Found {len(matched_stocks)} Matched Stocks:\n")
    lines.append("| Ticker | Company | Price | 1D Chg | RSI | vs 200D Trend | Stoch RSI | MFI | Fundamentals | แนวรับ / ต้าน (Plan) | R:R | Signals & Setup | Chart |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |")

    # Collect top tickers for news catalysts
    top_tickers = [s["ticker"] for s in matched_stocks[:3]]
    catalysts_map = fetch_batch_catalysts(top_tickers, max_items=4) if top_tickers else {}

    for s in matched_stocks:
        ticker = s["ticker"]
        name = s["name"][:14] + (".." if len(s["name"]) > 14 else "")
        price = f"${s['close']:.2f}"
        chg_sign = "+" if s["change_pct"] > 0 else ""
        chg_color = f"{chg_sign}{s['change_pct']:.2f}%"
        
        rsi_str = f"**{s['rsi']}**" if s['rsi'] is not None else "-"
        if s['rsi_hook_up']:
            rsi_str += " ⤴"
            
        dist_s = s.get("dist_sma200_pct")
        dist_e = s.get("dist_ema200_pct")
        if dist_e is not None and dist_s is not None:
            trend_str = f"SMA:{dist_s:+0.1f}%<br>EMA:{dist_e:+0.1f}%"
        elif dist_s is not None:
            trend_str = f"SMA:{dist_s:+0.1f}%"
        else:
            trend_str = "-"
            
        stoch_str = f"K:{s['stoch_k']} D:{s['stoch_d']}" if (s['stoch_k'] is not None and s['stoch_d'] is not None) else "-"
        if s.get("fresh_stoch_cross"):
            stoch_str += " ✂🟢"
        elif s.get("stoch_cross_up"):
            stoch_str += " 🟢"
            
        mfi_val = s.get("mfi")
        mfi_str = f"{mfi_val}" if mfi_val is not None else "-"
        if mfi_val is not None and mfi_val <= 20.0:
            mfi_str += " 🌊"
        elif mfi_val is not None and mfi_val <= 30.0:
            mfi_str += " 💧"

        # Fundamentals & Analyst target display (Quality & Value across all sectors)
        rev_g = f"{s['rev_growth_yoy']:+.0f}%" if s['rev_growth_yoy'] is not None else "-"
        roe_s = f"ROE {s['roe']:.0f}%" if s.get('roe') is not None else ""
        peg_s = f"PEG {s['peg']:.1f}" if s['peg'] is not None else "PEG -"
        t_avg = f"${s['price_target_average']:.0f}" if s.get('price_target_average') else "-"
        t_up = f"({s['target_upside_pct']:+.0f}%)" if s.get('target_upside_pct') is not None else ""
        fund_line1 = f"Rev {rev_g}" + (f" | {roe_s}" if roe_s else "")
        fund_line2 = f"{peg_s} | 🎯 {t_avg} {t_up}"
        fund_str = f"<small>{fund_line1}<br>{fund_line2}</small>"
            
        # Trade plan: Support, Resistance, and Stop Loss
        sl_val = s.get("stop_loss", 0.0)
        tp_val = s.get("take_profit", 0.0)
        supp_val = s.get("key_support", sl_val)
        res_val = s.get("key_resistance", tp_val)
        plan_str = f"รับ ${supp_val:.2f}<br>ต้าน ${res_val:.2f}<br><small>SL ${sl_val:.2f}</small>"
        
        rr_val = s.get("rr_ratio", 0.0)
        rr_badge = f"**{rr_val}x**" if rr_val >= 2.0 else f"{rr_val}x"
        
        badge = s["tier"]
        tags_str = ", ".join(s["signal_tags"][:3])
        
        chart_link = f"[📈 Chart]({s['tv_url']})"
        
        earnings_alert = ""
        if s["is_earnings_near"]:
            earnings_alert = f" <br>⚠️ *Earnings in {s['days_to_earnings']}d ({s['earnings_date_str']})*"
            
        biz = s.get("business_summary", "")
        lines.append(f"| **[{ticker}]({s['tv_url']})** | {name}<br><small>*{biz}*</small> | {price} | {chg_color} | {rsi_str} | <small>{trend_str}</small> | <small>{stoch_str}</small> | {mfi_str} | <small>{fund_str}</small> | <small>{plan_str}</small> | {rr_badge} | {badge}<br><small>{tags_str}{earnings_alert}</small> | {chart_link} |")

    # Business Overview Section
    lines.append("\n---")
    lines.append("### 🏢 ภาพรวมลักษณะธุรกิจของหุ้นที่ติดสแกน (Business Profiles)")
    for idx, s in enumerate(matched_stocks, 1):
        lines.append(f"{idx}. **[{s['ticker']}] {s['name']}:** {s.get('business_summary', '-')}.")

    # Catalyst & News Watch for Top Setups (Good vs Bad News & Beginner Summary)
    if catalysts_map:
        lines.append("\n---")
        lines.append("### ⚖️ ตาชั่งข่าวดี vs ข่าวร้ายของหุ้นติดสแกน (Bullish vs Bearish Catalysts)")
        matched_map = {s["ticker"]: s for s in matched_stocks}
        for t, cat in catalysts_map.items():
            s_item = matched_map.get(t, {})
            biz_desc = s_item.get("business_summary", "")
            lines.append(f"\n#### 🎯 [{t}] {s_item.get('name', t)} - *{biz_desc}*")

            bullish = cat.get("bullish", [])
            bearish = cat.get("bearish", [])
            fetch_ok = cat.get("fetch_ok", True)

            if not fetch_ok:
                lines.append("⚠️ **ดึงข่าวไม่สำเร็จ:** ยังสรุปข่าวดีหรือข่าวร้ายของหุ้นตัวนี้ไม่ได้ ควรตรวจสอบข่าวเองก่อนตัดสินใจ.")
            lines.append("🟢 **ข่าวดีและปัจจัยบวก (Bullish Catalysts):**")
            if not fetch_ok:
                lines.append("- -")
            elif bullish:
                for b in bullish:
                    title_link = f"[{b['title']}]({b['link']})" if b.get("link") else b["title"]
                    lines.append(f"- **[{b['source']}]** {title_link} *({b['published']})*")
            else:
                lines.append("- ยังไม่มีข่าวด้านบวกโดดเด่นในรอบสัปดาห์นี้.")

            lines.append("🔴 **ข่าวร้ายและสาเหตุที่ราคาย่อตัว (Bearish Risks):**")
            if not fetch_ok:
                lines.append("- -")
            elif bearish:
                for b in bearish:
                    title_link = f"[{b['title']}]({b['link']})" if b.get("link") else b["title"]
                    lines.append(f"- **[{b['source']}]** {title_link} *({b['published']})*")
            else:
                lines.append("- ไม่พบข่าวด้านลบในพาดหัวล่าสุดที่ดึงมาได้ (จัดกลุ่มด้วยคีย์เวิร์ด ไม่ได้ยืนยันสาเหตุที่ราคาย่อตัว).")

            # Beginner Suitability based on real volatility (ATR%) and sector safety
            sec = s_item.get("sector") or ""
            atr = s_item.get("atr")
            close_p = s_item.get("close")
            atr_pct = (atr / close_p * 100.0) if (atr and close_p and close_p > 0) else None

            if s_item.get("is_plunge_day"):
                chg_val = s_item.get("change_pct", 0)
                suitability_badge = f"🔴 เสี่ยงสูงมาก (แท่งแดงทิ้งตัวแรง {chg_val:+.1f}% มีดยังไม่หยุดตก แนะนำให้อยู่เฉยๆ รอแท่งกลับตัว)"
            elif atr_pct is None:
                suitability_badge = "⚪ ไม่มีข้อมูลความผันผวน (-) ประเมินความเหมาะสมไม่ได้"
            elif atr_pct <= 2.5 and sec in ("Finance", "Health Technology", "Consumer Non-Durables", "Utilities"):
                suitability_badge = f"🟢 เหมาะกับมือใหม่มาก (ความผันผวนต่ำเพียง {atr_pct:.1f}%/วัน พื้นฐานมั่นคง)"
            elif atr_pct <= 4.0:
                suitability_badge = f"🟡 เหมาะกับคนมีประสบการณ์ (หุ้นเติบโต ผันผวนปานกลาง {atr_pct:.1f}%/วัน)"
            else:
                suitability_badge = f"🔴 เสี่ยงสูง (ความผันผวนสูง {atr_pct:.1f}%/วัน ต้องมีวินัย Stop Loss เคร่งครัด)"

            # Beginner Layman Verdict
            lines.append("👶 **สรุปภาษาคน สำหรับมือใหม่:**")
            lines.append(f"- **ระดับความเหมาะสม:** {suitability_badge}")
            rev_g = s_item.get("rev_growth_yoy")
            growth_txt = f"รายได้เติบโต {rev_g:+.1f}% YoY" if rev_g is not None else "ไม่มีข้อมูลการเติบโตของรายได้ (-)"
            plan_sl = s_item.get("stop_loss", 0.0)
            plan_tp = s_item.get("take_profit", 0.0)

            target_txt = ""
            if s_item.get("price_target_average"):
                t_avg = s_item["price_target_average"]
                t_up = s_item.get("target_upside_pct", 0)
                b_cnt = s_item.get("rec_buy", 0) or 0
                h_cnt = s_item.get("rec_hold", 0) or 0
                s_cnt = s_item.get("rec_sell", 0) or 0
                target_txt = f" สถาบันการเงินวอลล์สตรีทให้ราคาเป้าหมายเฉลี่ยที่ ${t_avg:.2f} (มีโอกาสเติบโต Upside {t_up:+.1f}%) โดยมี {b_cnt} สถาบันแนะนำซื้อ ({h_cnt} ถือ / {s_cnt} ขาย)."

            supp_p = s_item.get("key_support", plan_sl)
            supp_d = s_item.get("support_desc", "จุดรับทางเทคนิค")
            res_p = s_item.get("key_resistance", plan_tp)
            res_d = s_item.get("resistance_desc", "จุดขายทำกำไร")

            action_note = ""
            if s_item.get("is_plunge_day"):
                action_note = " ⚠️ **คำเตือนมือใหม่:** วันนี้เป็นแท่งทิ้งตัวแดงหนัก ห้ามรีบกดซื้อไม้ใหญ่ ควรรอดูพรุ่งนี้ว่าปิดเขียวหรือหยุดลงหรือไม่ก่อนตัดสินใจ."

            lines.append(
                f"- หุ้น {t} ทำธุรกิจ{biz_desc}. "
                f"ราคาลงมาในโซนรับทางเทคนิค RSI อยู่ที่ {s_item.get('rsi')} และ{growth_txt}.{target_txt} "
                f"สำหรับมือใหม่: แนวรับสำคัญอยู่ที่ **${supp_p:.2f}** ({supp_d}), "
                f"แนวต้านเป้าหมายทำกำไรอยู่ที่ **${res_p:.2f}** ({res_d}), "
                f"และตั้งจุดยอมแพ้ตัดขาดทุน (Stop Loss) ที่ **${plan_sl:.2f}**.{action_note}"
            )

    lines.append("\n---")
    lines.append("### 🗡️ เช็กลิสต์ 3 ข้อ ป้องกันการรับมีดหล่น (Falling Knife Protection Checklist)")
    lines.append("1. **ไม่ซื้อในวันที่แท่งเทียนเป็นสีแดงทึบ:** รอให้มีแท่งกลับตัวปิดเขียว (Close >= Open) หรือ RSI Hook Up ยืนยันแรงรับก่อน.")
    lines.append("2. **งบการเงินไม่ติดลบและสถาบันไม่เทขาย:** รายได้ YoY ต้องไม่ติดลบรุนแรง และมตินักวิเคราะห์สถาบันต้องแนะนำซื้อมากกว่าขาย.")
    lines.append("3. **ระวังตลาดรวม (SPY/QQQ):** หากดัชนีหลักหลุดเส้น 50 วันพร้อมกัน ให้ชะลอการเข้าซื้อหรือลดขนาดไม้ลงครึ่งหนึ่งเสมอ.")

    lines.append("\n---")
    lines.append("### 🪜 สูตรแบ่ง 3 ไม้ช้อนซื้อ สำหรับมือใหม่ (3-Step Dip Money Management)")
    lines.append("- **ไม้ที่ 1 (30%):** เข้าซื้อเมื่อราคาแตะโซนรับ Value Zone (ใกล้เส้น 200 วัน ในระยะ 0% ถึง +5%).")
    lines.append("- **ไม้ที่ 2 (40%):** เข้าซื้อเมื่อเกิดสัญญาณกลับตัวยืนยัน เช่น RSI Hook Up (⤴) หรือ Stoch RSI Golden Cross (✂🟢).")
    lines.append("- **ไม้ที่ 3 (30%):** เก็บเป็นเงินสดสำรอง หรือซื้อเพิ่มเมื่อราคาวิ่งทะลุแนวต้านแรกเพื่อยืนยันรอบขาขึ้น.")

    lines.append("\n---")
    lines.append("### 📖 พจนานุกรมแปลศัพท์ฉบับ 1 บรรทัด สำหรับคนอยากช้อนซื้อ (Dip Buying Glossary)")
    lines.append("- **Value Zone 💎:** โซนราคาใกล้เส้น 200 วัน เป็นจุดที่กองทุนและสถาบันใหญ่ใช้สะสมหุ้นเพราะต้นทุนปลอดภัย.")
    lines.append("- **RSI Oversold (≤35):** ภาวะที่ราคาถูกเทขายหนักจนราคาถูกลงมาก มีโอกาสดีดตัวกลับสูง.")
    lines.append("- **Stoch RSI Golden Cross (✂🟢):** เส้นอินดิเคเตอร์ตัดขึ้น บ่งบอกว่าแรงขายเริ่มหมดและแรงซื้อกำลังกลับมา.")
    lines.append("- **Stop Loss (SL):** ราคาตัดขาดทุนเด็ดขาดหากตลาดผิดทาง เพื่อปกป้องเงินก้อนใหญ่ไว้.")
    lines.append("- **Take Profit (TP):** ราคาเป้าหมายทำกำไรเพื่อล็อกผลตอบแทนเข้าพอร์ต.")
    lines.append("\n---")
    lines.append("### 🧪 ทดลองช้อนซื้อในพอร์ตจำลอง (Simulated Paper Trading)")
    lines.append("หากสนใจหุ้นตัวไหนในลิสต์นี้ สามารถสั่งได้ทันทีในห้องแชท เช่น:")
    lines.append("- `ซื้อ BNY ในพอร์ตจำลอง` (หรือ `ช้อน BNY ตัวละหมื่น` ระบบจะใช้วงเงินเริ่มต้น ฿10,000)")
    lines.append("- `ซื้อ JPM 20000 ในพอร์ตจำลอง` (ระบุจำนวนเงินที่ต้องการได้ตามสะดวก)")
    lines.append("ระบบจะจำลองเข้าซื้อที่ราคาตลาดสด คำนวณจุด TP/SL และอัปเดต [portfolio_dip_sim.html](reports/portfolio_dip_sim.html) ให้ทันที.")
    lines.append("\n---")
    lines.append("⚠️ **คำเตือนความเสี่ยง (Risk Disclaimer):** รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลเชิงปริมาณและสถิติตลาดจาก TradingView เพื่อเป็นข้อมูลประกอบการตัดสินใจเบื้องต้นเท่านั้น ไม่ใช่คำแนะนำหรือการชักชวนให้ซื้อขายหลักทรัพย์ การลงทุนมีความเสี่ยง ผู้ลงทุนควรศึกษาข้อมูลและบริหารความเสี่ยงอย่างรอบคอบเสมอ.")

    return "\n".join(lines)
