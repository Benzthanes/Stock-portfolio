"""
Chart Data & Technical Analysis Engine
Fetches 6-month daily OHLCV candles, computes Swing High/Low,
Fibonacci Retracements (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%),
SMA 50, SMA 200, and Volume profiles for automated programmatic charting.
"""

import json
import math
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.http import http_get
from src.scoring import (
    EARNINGS_GUARD_DAYS,
    ETF_TICKERS,
    FundamentalScore,
    StockScore,
    TimingScore,
    score_fundamentals,
    score_stock,
    score_timing,
    grade_for,
    STARS_BY_GRADE,
    ETF_STARS,
)
from src.earnings_calendar import (
    get_confirmed_earnings_dates,
    calculate_confirmed_earnings_reaction,
    get_earnings_timing,
    get_earnings_calendar_hash,
)

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "candles_cache.json"
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours
PATTERN_WIN_RATE_NOTE = "ไม่มีสถิติยืนยัน (heuristic)"
ANCHOR_BARS = 504
INDICATOR_SCHEMA_VERSION = 17
EARNINGS_CALENDAR_HASH = get_earnings_calendar_hash()

# Heuristic constants for swing signals (heuristic ไม่ผ่าน backtest)
SWING_FIBO_TOLERANCE = 0.035      # heuristic ไม่ผ่าน backtest: กรอบความคลาดเคลื่อนแนวรับ Fibonacci
SWING_RSI_OVERSOLD = 38.0         # heuristic ไม่ผ่าน backtest: ระดับ RSI Oversold เริ่มต้น
SWING_RSI_HOOK_LOW = 42.0         # heuristic ไม่ผ่าน backtest: ระดับดีดยกฐาน RSI
SWING_VOL_RATIO_BUY = 1.15        # heuristic ไม่ผ่าน backtest: อัตราส่วนวอลุ่มซื้อเทียบเฉลี่ย 20 วัน
SWING_SL_RATIO_BUY = 0.965        # heuristic ไม่ผ่าน backtest: Stop Loss 3.5% ใต้ swing low
SWING_TP_RATIO_BUY = 1.12         # heuristic ไม่ผ่าน backtest: Take Profit 12%
SWING_RSI_OVERBOUGHT = 68.0       # heuristic ไม่ผ่าน backtest: ระดับ Overbought ฝั่งขาย swing
SWING_VOL_RATIO_SELL = 1.25       # heuristic ไม่ผ่าน backtest: อัตราส่วนวอลุ่มเทขาย
SWING_SL_RATIO_SELL = 1.025       # heuristic ไม่ผ่าน backtest: Stop Loss 2.5% เหนือ swing peak
SWING_TP_RATIO_SELL = 0.92        # heuristic ไม่ผ่าน backtest: Take Profit 8% ใต้ราคาขาย
RSI_OVERBOUGHT_THRESHOLD = 70.0   # heuristic ไม่ผ่าน backtest: ระดับ RSI Overbought สำหรับ TRIM

# Heuristic constants for chart pattern detection (heuristic ไม่ผ่าน backtest)
MAX_BOX_RANGE_SPAN_PCT = 0.15          # heuristic: เพดานความกว้างกรอบ (high - low) / low สูงสุด 15% สำหรับ Consolidation Box
DOUBLE_PATTERN_MIN_WIDTH_BARS = 6      # heuristic: ระยะห่างขั้นต่ำระหว่างยอด/ฐานสำหรับ Double Top/Bottom (~6 แท่ง)
DOUBLE_PATTERN_MIN_SWING_PCT = 0.05    # heuristic: การเด้งหรือย่อตัวขั้นต่ำสำหรับ Double Top/Bottom (~5-6%)
DOUBLE_PATTERN_PRICE_TOLERANCE_PCT = 0.045  # heuristic: ส่วนต่างราคาสูงสุดระหว่างยอด/ฐานคู่ (4.5%)
MAX_CHANNEL_SLOPE_DIFF_RATIO = 0.25    # heuristic: ส่วนต่างความชันสัมพัทธ์สูงสุด 25% สำหรับ Ascending Channel ขนาน


def _round_price(x: float) -> float:
    x = float(x)
    return round(x, 4) if abs(x) < 10 else round(x, 2)


def fetch_ticker_candles(ticker: str) -> List[Dict[str, Any]]:
    """
    Fetch all daily OHLCV candles since entering the market (inception/IPO) from Yahoo Finance v8 API.
    """
    clean_ticker = ticker.replace(".", "-").upper().strip()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_ticker}?period1=0&period2=9999999999&interval=1d"
    data = json.loads(http_get(url, timeout=10).decode("utf-8"))
    res = data.get("chart", {}).get("result", [])
    if not res:
        return []
    chart_res = res[0]
    timestamps = chart_res.get("timestamp", [])
    quote = chart_res.get("indicators", {}).get("quote", [{}])[0]
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    volumes = quote.get("volume", [])

    candles = []
    for i in range(len(timestamps)):
        if (
            i >= len(opens)
            or i >= len(highs)
            or i >= len(lows)
            or i >= len(closes)
        ):
            continue
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        if None in (o, h, l, c):
            continue
        v = volumes[i] if (i < len(volumes) and volumes[i] is not None) else 0
        t_str = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
        # Clamp high and low to enforce OHLC invariant integrity: high >= max(o, c), low <= min(o, c)
        clamped_h = max(float(h), float(o), float(c))
        clamped_l = min(float(l), float(o), float(c))
        candles.append({
            "time": t_str,
            "open": _round_price(o),
            "high": _round_price(clamped_h),
            "low": _round_price(clamped_l),
            "close": _round_price(c),
            "volume": int(v)
        })
    return candles


def detect_chart_patterns(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Classical Technical Chart Pattern Detection Engine.
    Detects Head & Shoulders, Inverted H&S, Triple Bottom/Top, Double Bottom (W),
    Double Top (M), Bull/Bear Flags, Ascending/Descending/Symmetrical Triangles,
    Expanding Triangles (Megaphones), Wedges, and Channels.
    """
    if not candles or len(candles) < 30:
        return None

    recent = candles[-75:] if len(candles) >= 75 else candles
    highs = [max(c["high"], c.get("open", c["high"]), c["close"]) for c in recent]
    lows = [min(c["low"], c.get("open", c["low"]), c["close"]) for c in recent]
    closes = [c["close"] for c in recent]
    times = [c["time"] for c in recent]
    n = len(recent)
    current_price = closes[-1]

    # Find local swing highs and swing lows (k=3 rolling window)
    k = 3
    peaks = []
    troughs = []
    for i in range(k, n - k):
        if all(highs[i] >= highs[i + j] for j in range(-k, k + 1) if j != 0):
            peaks.append({"idx": i, "time": times[i], "price": highs[i]})
        if all(lows[i] <= lows[i + j] for j in range(-k, k + 1) if j != 0):
            troughs.append({"idx": i, "time": times[i], "price": lows[i]})

    detected = None

    # 1. Head & Shoulders (Bearish Reversal)
    if len(peaks) >= 3:
        p1, p2, p3 = peaks[-3], peaks[-2], peaks[-1]
        if p2["price"] > p1["price"] * 1.02 and p2["price"] > p3["price"] * 1.02:
            shoulder_diff = abs(p1["price"] - p3["price"]) / p1["price"]
            if shoulder_diff <= 0.055:
                inter_troughs = [t for t in troughs if p1["idx"] < t["idx"] < p3["idx"]]
                t_left = [t for t in inter_troughs if p1["idx"] < t["idx"] < p2["idx"]]
                t_right = [t for t in inter_troughs if p2["idx"] < t["idx"] < p3["idx"]]

                if t_left:
                    tl = min(t_left, key=lambda x: x["price"])
                else:
                    b1 = recent[p1["idx"] + 1: p2["idx"]]
                    if b1:
                        c_min = min(b1, key=lambda c: c["low"])
                        tl = {"idx": p1["idx"] + 1 + b1.index(c_min), "time": c_min["time"], "price": c_min["low"]}
                    else:
                        tl = None

                if t_right:
                    tr = min(t_right, key=lambda x: x["price"])
                else:
                    b2 = recent[p2["idx"] + 1: p3["idx"]]
                    if b2:
                        c_min = min(b2, key=lambda c: c["low"])
                        tr = {"idx": p2["idx"] + 1 + b2.index(c_min), "time": c_min["time"], "price": c_min["low"]}
                    else:
                        tr = None

                if tl and tr and p1["idx"] < tl["idx"] < p2["idx"] < tr["idx"] < p3["idx"]:
                    neck_val = min(tl["price"], tr["price"])
                    head_h = p2["price"] - neck_val
                    target = round(neck_val - head_h, 2)
                    detected = {
                        "name": "Head & Shoulders (หัวและไหล่กลับทิศ)",
                        "type": "Bearish Reversal",
                        "badge": "🔴 หัวและไหล่ (Head & Shoulders)",
                        "summary": f"เกิดรูปแบบ Head & Shoulders หัวอยู่ที่ ${p2['price']:.2f} มี Neckline รับที่ ${neck_val:.2f}",
                        "neckline": round(neck_val, 2),
                        "breakout": round(neck_val, 2),
                        "target": target,
                        "upside_pct": round((target - current_price) / current_price * 100, 1),
                        "psychology": "แรงซื้อพยายามดันทำจุดสูงสุดใหม่ (Head) แต่ถูกสถาบันเทขายทำกำไร จากนั้นความพยายามดันครั้งถัดมา (Right Shoulder) มีพลังลดลงอย่างเห็นได้ชัดและไม่สามารถทำจุดสูงสุดใหม่ได้ บ่งชี้การกระจายหุ้น (Distribution) และการสูญเสียการควบคุมของผู้ซื้อ",
                        "structure": f"ไหล่ซ้าย (${p1['price']:.2f}) • หัว (${p2['price']:.2f}) • ไหล่ขวา (${p3['price']:.2f}) • Neckline รับสำคัญ (${neck_val:.2f})",
                        "action_plan": f"หากราคาหลุดเส้น Neckline ${neck_val:.2f} ให้ขายตัดขาดทุนหรือขายทำกำไรปกป้องเงินทุน (Exit/Trim) เป้าหมายลงสู่ ${target:.2f}",
                        "invalidation": f"รูปแบบจะล้มเหลว (Invalidated) ทันทีหากราคากลับขึ้นมายืนเหนือจุดสูงสุดของไหล่ขวา ${p3['price']:.2f}",
                        "win_rate": PATTERN_WIN_RATE_NOTE,
                        "target_calc": f"วัดความสูงจาก Head (${p2['price']:.2f}) ถึง Neckline (${neck_val:.2f}) รวม {head_h:.2f} แล้วลบลงมาจาก Neckline",
                        "key_points": [
                            {"name": "Left Shoulder", "time": p1["time"], "price": p1["price"], "role": "start"},
                            {"name": "Left Neckline Trough", "time": tl["time"], "price": tl["price"]},
                            {"name": "Head", "time": p2["time"], "price": p2["price"]},
                            {"name": "Right Neckline Trough", "time": tr["time"], "price": tr["price"]},
                            {"name": "Right Shoulder", "time": p3["time"], "price": p3["price"]},
                        ],
                        "lines": [
                            {"name": "Neckline Support", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": neck_val}, {"time": times[-1], "value": neck_val}]}
                        ]
                    }

    # 2. Inverted Head & Shoulders (Bullish Reversal)
    if not detected and len(troughs) >= 3:
        t1, t2, t3 = troughs[-3], troughs[-2], troughs[-1]
        if t2["price"] < t1["price"] * 0.98 and t2["price"] < t3["price"] * 0.98:
            shoulder_diff = abs(t1["price"] - t3["price"]) / t1["price"]
            if shoulder_diff <= 0.055:
                inter_peaks = [p for p in peaks if t1["idx"] < p["idx"] < t3["idx"]]
                p_left = [p for p in inter_peaks if t1["idx"] < p["idx"] < t2["idx"]]
                p_right = [p for p in inter_peaks if t2["idx"] < p["idx"] < t3["idx"]]

                if p_left:
                    pl = max(p_left, key=lambda x: x["price"])
                else:
                    b1 = recent[t1["idx"] + 1: t2["idx"]]
                    if b1:
                        c_max = max(b1, key=lambda c: c["high"])
                        pl = {"idx": t1["idx"] + 1 + b1.index(c_max), "time": c_max["time"], "price": c_max["high"]}
                    else:
                        pl = None

                if p_right:
                    pr = max(p_right, key=lambda x: x["price"])
                else:
                    b2 = recent[t2["idx"] + 1: t3["idx"]]
                    if b2:
                        c_max = max(b2, key=lambda c: c["high"])
                        pr = {"idx": t2["idx"] + 1 + b2.index(c_max), "time": c_max["time"], "price": c_max["high"]}
                    else:
                        pr = None

                if pl and pr and t1["idx"] < pl["idx"] < t2["idx"] < pr["idx"] < t3["idx"]:
                    neck_val = max(pl["price"], pr["price"])
                    head_h = neck_val - t2["price"]
                    target = round(neck_val + head_h, 2)
                    detected = {
                        "name": "Inverted Head & Shoulders (หัวไหล่กลับหัว)",
                        "type": "Bullish Reversal",
                        "badge": "🟢 หัวไหล่กลับหัว (Inv H&S)",
                        "summary": f"เกิดรูปแบบ Inverted H&S หัวอยู่ที่ ${t2['price']:.2f} ลุ้นทะลุ Neckline ${neck_val:.2f}",
                        "neckline": round(neck_val, 2),
                        "breakout": round(neck_val, 2),
                        "target": target,
                        "upside_pct": round((target - current_price) / current_price * 100, 1),
                        "psychology": "แรงขายพยายามกดราคาทำจุดต่ำสุดใหม่ (Head) แต่พบแรงดูดซับของสถาบัน (Smart Money Accumulation) จากนั้นการทิ้งตัวครั้งถัดมา (Right Shoulder) ยกฐานสูงขึ้น สะท้อนว่าแรงขายหมดกำลังและผู้ซื้อเริ่มคุมตลาด",
                        "structure": f"ไหล่ซ้าย (${t1['price']:.2f}) • หัวลึกสุด (${t2['price']:.2f}) • ไหล่ขวายกฐาน (${t3['price']:.2f}) • Neckline ต้าน (${neck_val:.2f})",
                        "action_plan": f"เข้าซื้อสะสม (BUY/DCA) เมื่อราคาทะลุ Neckline ${neck_val:.2f} พร้อม Volume หนาแน่น ตั้งเป้าหมายทำกำไรที่ ${target:.2f}",
                        "invalidation": f"รูปแบบจะล้มเหลวหากราคาหลุดจุดต่ำสุดของไหล่ขวา ${t3['price']:.2f}",
                        "win_rate": PATTERN_WIN_RATE_NOTE,
                        "target_calc": f"วัดระยะลึกจาก Neckline (${neck_val:.2f}) ลงไปถึง Head (${t2['price']:.2f}) รวม {head_h:.2f} แล้วบวกขึ้นจาก Neckline",
                        "key_points": [
                            {"name": "Left Shoulder", "time": t1["time"], "price": t1["price"], "role": "start"},
                            {"name": "Left Neckline Peak", "time": pl["time"], "price": pl["price"]},
                            {"name": "Head", "time": t2["time"], "price": t2["price"]},
                            {"name": "Right Neckline Peak", "time": pr["time"], "price": pr["price"]},
                            {"name": "Right Shoulder", "time": t3["time"], "price": t3["price"]},
                        ],
                        "lines": [
                            {"name": "Neckline Breakout", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": neck_val}, {"time": times[-1], "value": neck_val}]}
                        ]
                    }

    # 3. Triple Bottom
    if not detected and len(troughs) >= 3:
        t1, t2, t3 = troughs[-3], troughs[-2], troughs[-1]
        diffs = [abs(t1["price"] - t2["price"]) / t1["price"], abs(t2["price"] - t3["price"]) / t2["price"], abs(t1["price"] - t3["price"]) / t1["price"]]
        if max(diffs) <= 0.035:
            mid_peaks = [p for p in peaks if t1["idx"] < p["idx"] < t3["idx"]]
            p_mid1 = [p for p in mid_peaks if t1["idx"] < p["idx"] < t2["idx"]]
            p_mid2 = [p for p in mid_peaks if t2["idx"] < p["idx"] < t3["idx"]]

            if p_mid1:
                pm1 = max(p_mid1, key=lambda x: x["price"])
            else:
                b1 = recent[t1["idx"] + 1: t2["idx"]]
                if b1:
                    c_max = max(b1, key=lambda c: c["high"])
                    pm1 = {"idx": t1["idx"] + 1 + b1.index(c_max), "time": c_max["time"], "price": c_max["high"]}
                else:
                    pm1 = None

            if p_mid2:
                pm2 = max(p_mid2, key=lambda x: x["price"])
            else:
                b2 = recent[t2["idx"] + 1: t3["idx"]]
                if b2:
                    c_max = max(b2, key=lambda c: c["high"])
                    pm2 = {"idx": t2["idx"] + 1 + b2.index(c_max), "time": c_max["time"], "price": c_max["high"]}
                else:
                    pm2 = None

            if pm1 and pm2 and t1["idx"] < pm1["idx"] < t2["idx"] < pm2["idx"] < t3["idx"]:
                neck_p = max(pm1["price"], pm2["price"])
                min_floor = min(t1["price"], t2["price"], t3["price"])
                target = round(neck_p + (neck_p - min_floor), 2)

                # Check for post-bounce high after t3
                post_peaks = [p for p in peaks if p["idx"] > t3["idx"]]
                if post_peaks:
                    end_p = post_peaks[0]
                else:
                    post_win = recent[t3["idx"] + 1:]
                    if post_win:
                        max_h = max(c["high"] for c in post_win)
                        end_c = [c for c in post_win if c["high"] == max_h][0]
                        end_p = {"name": "Rebound High", "time": end_c["time"], "price": end_c["high"], "idx": t3["idx"] + 1 + post_win.index(end_c)}
                    else:
                        end_p = None

                key_pts = [
                    {"name": "Bottom 1", "time": t1["time"], "price": t1["price"], "role": "start"},
                    {"name": "Neckline Peak 1", "time": pm1["time"], "price": pm1["price"]},
                    {"name": "Bottom 2", "time": t2["time"], "price": t2["price"]},
                    {"name": "Neckline Peak 2", "time": pm2["time"], "price": pm2["price"]},
                    {"name": "Bottom 3", "time": t3["time"], "price": t3["price"]},
                ]
                if end_p and end_p["time"] != t3["time"]:
                    key_pts.append({"name": "Rebound (ขาขวาดีดตัว)", "time": end_p["time"], "price": end_p["price"]})

                detected = {
                    "name": "Bullish Triple Bottom (สามฐานแข็งแกร่ง)",
                    "type": "Bullish Reversal",
                    "badge": "🟢 สามฐานกระทิง (Triple Bottom)",
                    "summary": f"ทดสอบแนวรับ 3 ครั้งไม่หลุดใกล้ ${min_floor:.2f} โซนดูดซับแรงขายสมบูรณ์แบบ",
                    "neckline": round(neck_p, 2),
                    "breakout": round(neck_p, 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ราคาทดสอบแนวรับเดิมถึง 3 ครั้ง แต่ไม่มีแรงขายใดสามารถกดให้หลุดลงไปได้ แสดงถึงแนวรับหินผา (Institutional Strong Floor) ที่สถาบันตั้งรับซื้อไม่อั้นจนอุปทานหมดตลาด",
                    "structure": f"ฐานแนวรับ 3 ครั้งต่ำสุด ${min_floor:.2f} • Neckline แนวต้านเบรกเอาท์ ${neck_p:.2f}",
                    "action_plan": f"ซื้อสะสมใกล้โซนฐาน ${min_floor:.2f} หรือ Follow Buy เมื่อปิดเบรก Neckline ${neck_p:.2f} เป้าหมาย ${target:.2f}",
                    "invalidation": f"Stop Loss ทันทีหากราคาปิดหลุดฐานต่ำสุด ${min_floor:.2f}",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดความสูงจากฐาน ${min_floor:.2f} ถึงยอด Neckline ${neck_p:.2f} แล้วนำไปบวกเพิ่มจากยอด Neckline",
                    "key_points": key_pts,
                    "lines": [
                        {"name": "Triple Support Floor", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": min_floor}, {"time": times[-1], "value": min_floor}]},
                        {"name": "Neckline Breakout", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": neck_p}, {"time": times[-1], "value": neck_p}]}
                    ]
                }

    # 4. Triangles, Wedges, Expanding Triangles, Channels (Evaluated before Double Top/Bottom to avoid hiding 4-point patterns)
    # In a valid geometric 4-point pattern, peaks and troughs must alternate (P1 < T1 < P2 < T2 or T1 < P1 < T2 < P2).
    # Consecutive troughs followed by consecutive peaks (e.g. T1 < T2 < P1 < P2) is a trend reversal/rally, not a triangle.
    if not detected and len(peaks) >= 2 and len(troughs) >= 2 and (
        (peaks[-2]["idx"] < troughs[-2]["idx"] < peaks[-1]["idx"] < troughs[-1]["idx"])
        or (troughs[-2]["idx"] < peaks[-2]["idx"] < troughs[-1]["idx"] < peaks[-1]["idx"])
    ):
        p1, p2 = peaks[-2], peaks[-1]
        t1, t2 = troughs[-2], troughs[-1]

        # Geometry Guard: troughs must be strictly below their respective peaks
        if t1["price"] < p1["price"] and t2["price"] < p2["price"]:
            peak_slope = (p2["price"] - p1["price"]) / max(1, (p2["idx"] - p1["idx"]))
            trough_slope = (t2["price"] - t1["price"]) / max(1, (t2["idx"] - t1["idx"]))

            p_val = lambda x: p1["price"] + peak_slope * (x - p1["idx"])
            t_val = lambda x: t1["price"] + trough_slope * (x - t1["idx"])

            start_idx = min(p1["idx"], t1["idx"])
            end_idx = max(p2["idx"], t2["idx"])

            start_spread = p_val(start_idx) - t_val(start_idx)
            end_spread = p_val(end_idx) - t_val(end_idx)

            # Lines must not cross inside the pattern body
            lines_valid = (
                start_spread > 0
                and end_spread > 0
                and p_val(p2["idx"]) > t_val(p2["idx"])
                and p_val(t2["idx"]) > t_val(t2["idx"])
            )

            # Ascending Triangle: Flat Resistance (p1 ~= p2), Rising Support (t2 > t1)
            if lines_valid and abs(p2["price"] - p1["price"]) / p1["price"] <= 0.025 and t2["price"] > t1["price"] * 1.015 and 0 < end_spread < start_spread:
                flat_res = round((p1["price"] + p2["price"]) / 2, 2)
                target = round(flat_res + (flat_res - t1["price"]), 2)
                raw_pts = [
                    {"name": "Upper Resistance 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                    {"name": "Ascending Low 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                    {"name": "Upper Resistance 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                    {"name": "Ascending Low 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                ]
                raw_pts.sort(key=lambda x: x["idx"])
                raw_pts[0]["role"] = "start"
                kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                detected = {
                    "name": "Ascending Triangle (สามเหลี่ยมลู่ขึ้น)",
                    "type": "Bullish Continuation",
                    "badge": "🟢 สามเหลี่ยมลู่ขึ้น (Ascending Triangle)",
                    "summary": f"แนวต้านคงที่ ${flat_res:.2f} ขณะที่แนวรับยกฐานสูงขึ้นเรื่อยๆ รอจังหวะเบรกเอาท์",
                    "neckline": flat_res,
                    "breakout": flat_res,
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "แม้จะมีแรงขายกั้นไว้ที่แนวต้านแนวนอน แต่ผู้ซื้อยินดีซื้อในราคาที่แพงขึ้นเรื่อยๆ ทำให้จุดต่ำสุดยกตัวสูงขึ้นอย่างต่อเนื่อง (Higher Lows) บ่งบอกว่าแรงขายที่แนวต้านกำลังจะถูกดูดซับจนหมดสิ้น",
                    "structure": f"แนวต้านแนวนอน (${flat_res:.2f}) • แนวรับเฉียงขึ้นยกฐานจาก ${t1['price']:.2f} มาที่ ${t2['price']:.2f}",
                    "action_plan": f"ดักซื้อสะสมเมื่อราคาลงแตะแนวรับเฉียงขึ้น หรือเคาะซื้อ Follow Buy เมื่อปิดเหนือ ${flat_res:.2f} เป้าหมาย ${target:.2f}",
                    "invalidation": f"รูปแบบเสียทรงหากราคาหลุดแนวรับเฉียงขึ้น",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดความกว้างของสามเหลี่ยมที่ฐานแรก (${flat_res - t1['price']:.2f}) บวกเพิ่มจากจุดต้าน ${flat_res:.2f}",
                    "key_points": kp,
                    "lines": [
                        {"name": "Flat Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": flat_res}, {"time": times[-1], "value": flat_res}]},
                        {"name": "Ascending Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                    ]
                }
            # Descending Triangle: Falling Resistance (p2 < p1), Flat Support (t1 ~= t2)
            elif lines_valid and abs(t2["price"] - t1["price"]) / t1["price"] <= 0.025 and p2["price"] < p1["price"] * 0.985 and 0 < end_spread < start_spread:
                flat_sup = round((t1["price"] + t2["price"]) / 2, 2)
                target = round(flat_sup - (p1["price"] - flat_sup), 2)
                raw_pts = [
                    {"name": "Descending High 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                    {"name": "Horizontal Floor 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                    {"name": "Descending High 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                    {"name": "Horizontal Floor 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                ]
                raw_pts.sort(key=lambda x: x["idx"])
                raw_pts[0]["role"] = "start"
                kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                detected = {
                    "name": "Descending Triangle (สามเหลี่ยมกดไฮ)",
                    "type": "Bearish Continuation",
                    "badge": "🔴 สามเหลี่ยมลู่ลง (Descending Triangle)",
                    "summary": f"แนวรับคงที่ ${flat_sup:.2f} ขณะที่จุดสูงสุดถูกกดต่ำลง บ่งชี้แรงขายสะสมต่อเนื่อง",
                    "neckline": flat_sup,
                    "breakout": flat_sup,
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ผู้ขายกดราคาลงมาต่อเนื่องจนทำ Lower Highs ขณะที่แนวรับเดิมเริ่มเปราะบาง สะท้อนแรงขายกดดันสะสมจากสถาบัน",
                    "structure": f"แนวรับแบนราบ (${flat_sup:.2f}) • แนวต้านเฉียงกดต่ำลงต่อเนื่อง",
                    "action_plan": f"ระมัดระวังแรงเทขาย หากหลุดแนวรับ ${flat_sup:.2f} ให้ขายตัดขาดทุนทันที เป้าหมายขาลง ${target:.2f}",
                    "invalidation": f"รูปแบบล้มเหลวหากเบรกทะลุเส้นแนวต้านเฉียงกดขึ้นไปได้",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดความสูงสามเหลี่ยมแล้วหักลบออกจากแนวรับ ${flat_sup:.2f}",
                    "key_points": kp,
                    "lines": [
                        {"name": "Descending Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                        {"name": "Flat Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": flat_sup}, {"time": times[-1], "value": flat_sup}]}
                    ]
                }
            # Symmetrical Expanding Triangle (Megaphone / Broadening)
            elif lines_valid and p2["price"] > p1["price"] * 1.02 and t2["price"] < t1["price"] * 0.98 and end_spread > start_spread > 0:
                height = p2["price"] - t2["price"]
                target = round(p2["price"] + height * 0.5, 2)
                raw_pts = [
                    {"name": "Expanding High 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                    {"name": "Expanding Low 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                    {"name": "Expanding High 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                    {"name": "Expanding Low 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                ]
                raw_pts.sort(key=lambda x: x["idx"])
                raw_pts[0]["role"] = "start"
                kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                detected = {
                    "name": "Expanding Triangle (สามเหลี่ยมปากแตรขยายตัว)",
                    "type": "High Volatility",
                    "badge": "📢 ปากแตรขยายตัว (Expanding Triangle)",
                    "summary": f"ความผันผวนขยายตัวออกทั้งสองฝั่ง Higher High และ Lower Low สวิงรุนแรง",
                    "neckline": round(p2["price"], 2),
                    "breakout": round(p2["price"], 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "สภาวะความผันผวนสูงมาก เกิดศึกชิงขั้วระหว่างฝั่งกระทิงและหมี ทำให้สวิงหลุดทั้งแนวต้านและแนวรับ (High Volatility Squeeze)",
                    "structure": f"กรอบราคาขยายกว้างออกทั้งสองฝั่ง ระหว่างแนวรับ ${t2['price']:.2f} ถึงแนวต้าน ${p2['price']:.2f}",
                    "action_plan": "เน้น Swing Trade ตามกรอบ หรือรอให้ราคากลับเข้าสู่การบีบอัดก่อนเข้าสถานะใหญ่",
                    "invalidation": "ผันผวนรุนแรง ควรวาง Stop Loss กว้าง 2.0 ATR",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"เป้าหมายสวิงที่ ${target:.2f}",
                    "key_points": kp,
                    "lines": [
                        {"name": "Diverging Resistance", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                        {"name": "Diverging Support", "color": "#f43f5e", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                    ]
                }
            # Symmetrical Triangle
            elif lines_valid and p2["price"] < p1["price"] * 0.985 and t2["price"] > t1["price"] * 1.015 and 0 < end_spread < start_spread:
                height = p1["price"] - t1["price"]
                target = round(current_price + height * 0.75, 2)
                raw_pts = [
                    {"name": "Lower High 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                    {"name": "Higher Low 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                    {"name": "Lower High 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                    {"name": "Higher Low 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                ]
                raw_pts.sort(key=lambda x: x["idx"])
                raw_pts[0]["role"] = "start"
                kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                detected = {
                    "name": "Symmetrical Triangle (สามเหลี่ยมบีบอัด)",
                    "type": "Neutral Breakout",
                    "badge": "⚖️ สามเหลี่ยมบีบอัด (Symmetrical Triangle)",
                    "summary": f"ความผันผวนบีบแคบระหว่าง ${t2['price']:.2f} - ${p2['price']:.2f} เตรียมพร้อมระเบิดทิศทาง",
                    "neckline": round(p2["price"], 2),
                    "breakout": round(p2["price"], 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ทั้งผู้ซื้อและผู้ขายกำลังลังเล ปริมาณการซื้อขายลดฮวบลงเรื่อยๆ บ่งชี้การสะสมพลังครั้งใหญ่ (Volatility Contraction) ก่อนจะเลือกทิศทางระเบิดแรง",
                    "structure": f"กรอบแนวต้านเฉียงลงและแนวรับเฉียงขึ้น บีบแคบเข้ามาที่โซน ${t2['price']:.2f} - ${p2['price']:.2f}",
                    "action_plan": f"รอการ Breakout ชัดเจนฝั่งใดฝั่งหนึ่ง หากทะลุขึ้นเป้าหมายแรกอยู่ที่ ${target:.2f}",
                    "invalidation": "หากราคาสวิงตัดไปมาโดยไร้ Volume ถือเป็น False Breakout",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดความกว้างสูงสุดของสามเหลี่ยม ({p1['price'] - t1['price']:.2f}) นำไปทาบจากจุดเบรก",
                    "key_points": kp,
                    "lines": [
                        {"name": "Upper Resistance Line", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                        {"name": "Lower Support Line", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                    ]
                }
            # Falling Wedge (Bullish Reversal)
            elif (
                lines_valid
                and p2["price"] < p1["price"]
                and t2["price"] < t1["price"]
                and peak_slope < 0
                and trough_slope < 0
                and trough_slope > peak_slope
                and 0 < end_spread < start_spread
            ):
                target = round(p1["price"], 2)
                raw_pts = [
                    {"name": "Wedge High 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                    {"name": "Wedge Low 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                    {"name": "Wedge High 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                    {"name": "Wedge Low 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                ]
                raw_pts.sort(key=lambda x: x["idx"])
                raw_pts[0]["role"] = "start"
                kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                detected = {
                    "name": "Bullish Falling Wedge (ลิ่มเฉียงลงสะสมแรง)",
                    "type": "Bullish Reversal",
                    "badge": "🟢 ลิ่มลู่ลง (Falling Wedge)",
                    "summary": f"กรอบราคาเฉียงลงบีบแคบลงเรื่อยๆ เป็นสัญญาณพร้อมทะยานกลับตัวขึ้นเมื่อทะลุกรอบต้าน",
                    "neckline": round(p2["price"], 2),
                    "breakout": round(p2["price"], 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ราคาค่อยๆ ซึมลงแต่ช่วงการลงบีบแคบลงเรื่อยๆ สะท้อนว่าแรงขายเริ่มอ่อนแรงลงอย่างมาก ขณะที่สถาบันเริ่มแอบดูดซับของ (Smart Money Absorption) จนเกิดแรงดีดกลับรุนแรง",
                    "structure": f"แนวต้านและแนวรับเฉียงลงทั้งคู่แต่ลู่เข้าหากัน ปลายลิ่มบีบแคบใกล้ ${current_price:.2f}",
                    "action_plan": f"เข้าซื้อสะสมในปลายลิ่ม หรือเคาะซื้อเมื่อทะลุกรอบบน ${p2['price']:.2f} เป้าหมายยอดลิ่มเดิมที่ ${target:.2f}",
                    "invalidation": f"รูปแบบเสียทรงหากราคาหลุดเส้นรับล่างของลิ่ม",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"เป้าหมายเชิงเทคนิคคือจุดเริ่มต้นของลิ่มที่ ${p1['price']:.2f}",
                    "key_points": kp,
                    "lines": [
                        {"name": "Upper Wedge Resistance", "color": "#38bdf8", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                        {"name": "Lower Wedge Support", "color": "#10b981", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                    ]
                }
            # Channel Up / Rising Trend (Heuristic: Must have parallel slopes within MAX_CHANNEL_SLOPE_DIFF_RATIO)
            elif lines_valid and p2["price"] > p1["price"] and t2["price"] > t1["price"] and peak_slope > 0 and trough_slope > 0:
                avg_slope = (peak_slope + trough_slope) / 2.0
                slope_diff_ratio = abs(peak_slope - trough_slope) / max(1e-6, avg_slope)
                if slope_diff_ratio <= MAX_CHANNEL_SLOPE_DIFF_RATIO:
                    target = round(p2["price"] * 1.08, 2)
                    raw_pts = [
                        {"name": "Channel High 1", "time": p1["time"], "price": p1["price"], "idx": p1["idx"]},
                        {"name": "Channel Low 1", "time": t1["time"], "price": t1["price"], "idx": t1["idx"]},
                        {"name": "Channel High 2", "time": p2["time"], "price": p2["price"], "idx": p2["idx"]},
                        {"name": "Channel Low 2", "time": t2["time"], "price": t2["price"], "idx": t2["idx"]},
                    ]
                    raw_pts.sort(key=lambda x: x["idx"])
                    raw_pts[0]["role"] = "start"
                    kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
                    detected = {
                        "name": "Bullish Ascending Channel (ช่องคู่ขนานขาขึ้น)",
                        "type": "Bullish Trend",
                        "badge": "🟢 ช่องราคาขาขึ้น (Ascending Channel)",
                        "summary": f"ยกทั้งจุดสูงสุดและต่ำสุดขึ้นต่อเนื่อง (Higher Highs & Higher Lows) แข็งแกร่ง",
                        "neckline": round(p2["price"], 2),
                        "breakout": round(p2["price"], 2),
                        "target": target,
                        "upside_pct": round((target - current_price) / current_price * 100, 1),
                        "psychology": "แนวโน้มขาขึ้นแข็งแกร่งและมีระเบียบวินัยสูง มีการทำ Higher Highs และ Higher Lows ต่อเนื่อง บ่งชี้ว่ามีเงินทุนสถาบันไหลเข้าสม่ำเสมอ",
                        "structure": f"กรอบแนวรับแนวต้านขนานกันเฉียงขึ้น ยอดล่าสุดอยู่ที่ ${p2['price']:.2f} ฐานล่าสุดอยู่ที่ ${t2['price']:.2f}",
                        "action_plan": f"เข้าซื้อทุกครั้งที่ราคาย่อตัวลงมาทดสอบกรอบล่างของ Channel และขายทำกำไรบางส่วนที่กรอบบน เป้าหมาย ${target:.2f}",
                        "invalidation": f"ระวังหากราคาหลุดกรอบล่าง Channel อาจเข้าสู่ช่วงการพักฐานใหญ่",
                        "win_rate": PATTERN_WIN_RATE_NOTE,
                        "target_calc": f"เป้าหมายแนวต้านกรอบบนคำนวณที่ ${target:.2f}",
                        "key_points": kp,
                        "lines": [
                            {"name": "Upper Channel Line", "color": "#10b981", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2['idx']), 2)}]},
                            {"name": "Lower Channel Support", "color": "#38bdf8", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2['idx']), 2)}]}
                        ]
                    }

    # 5. Double Bottom (W-Shape)
    if not detected and len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        mid_peaks = [p for p in peaks if t1["idx"] < p["idx"] < t2["idx"]]
        if mid_peaks:
            neck_p = max(mid_peaks, key=lambda x: x["price"])
            price_diff = abs(t1["price"] - t2["price"]) / t1["price"]
            bounce = (neck_p["price"] - min(t1["price"], t2["price"])) / min(t1["price"], t2["price"])
            pattern_h = neck_p["price"] - min(t1["price"], t2["price"])
            width = t2["idx"] - t1["idx"]
            if (
                price_diff <= DOUBLE_PATTERN_PRICE_TOLERANCE_PCT
                and bounce >= DOUBLE_PATTERN_MIN_SWING_PCT
                and width >= DOUBLE_PATTERN_MIN_WIDTH_BARS
            ):
                # Find left rim of W (must be near neck_p in price and within 3-10 bars before t1)
                win_len = min(10, t1["idx"])
                left_win = recent[t1["idx"] - win_len: t1["idx"]] if win_len >= 2 else []
                start_p = None
                if left_win:
                    candidates = [c for c in left_win if c["high"] >= min(t1["price"], t2["price"]) + pattern_h * 0.7 and c["high"] <= neck_p["price"] + pattern_h * 1.25]
                    if candidates:
                        best_c = min(candidates, key=lambda c: abs(c["high"] - neck_p["price"]))
                        start_p = {"name": "Left Rim (ขอบซ้าย W)", "time": best_c["time"], "price": best_c["high"]}

                # Find post-bounce swing high after t2
                post_peaks = [p for p in peaks if p["idx"] > t2["idx"]]
                if post_peaks:
                    end_p = post_peaks[0]
                else:
                    post_win = recent[t2["idx"] + 1:]
                    if post_win:
                        max_h = max(c["high"] for c in post_win)
                        end_c = [c for c in post_win if c["high"] == max_h][0]
                        end_p = {"name": "Rebound High", "time": end_c["time"], "price": end_c["high"]}
                    else:
                        end_p = {"name": "Rebound High", "time": times[-1], "price": closes[-1]}

                key_pts = []
                if start_p:
                    key_pts.append({"name": start_p["name"], "time": start_p["time"], "price": start_p["price"], "role": "start"})
                    start_time = start_p["time"]
                else:
                    start_time = t1["time"]

                key_pts.extend([
                    {"name": "Bottom 1 (ฐานแรก)", "time": t1["time"], "price": t1["price"], "role": "" if start_p else "start"},
                    {"name": "Neckline Peak (ยอดกลาง W)", "time": neck_p["time"], "price": neck_p["price"]},
                    {"name": "Bottom 2 (ฐานที่สอง)", "time": t2["time"], "price": t2["price"]},
                    {"name": "Rebound (ขาขวาดีดตัว)", "time": end_p["time"], "price": end_p["price"]},
                ])

                target = round(neck_p["price"] + pattern_h, 2)
                detected = {
                    "name": "Bullish Double Bottom (W-Shape)",
                    "type": "Bullish Reversal",
                    "badge": "🟢 รูปแบบกระทิง (Double Bottom)",
                    "summary": f"ตรวจพบจุดต่ำสุดคู่ใกล้ ${t1['price']:.2f} และ ${t2['price']:.2f} มี Neckline ต้านที่ ${neck_p['price']:.2f}",
                    "neckline": round(neck_p["price"], 2),
                    "breakout": round(neck_p["price"], 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "หลังการทดสอบจุดต่ำสุดครั้งแรก เกิดการดีดตัวและลงมาทดสอบจุดเดิมอีกครั้ง แต่ผู้ขายไม่สามารถทำ Lower Low ได้ ผู้ซื้อสถาบันชิงเข้าซื้อตัดหน้า ทำให้เกิดฐานคู่ทรง W พร้อมแรงส่งขาขึ้นรอบใหม่",
                    "structure": f"ฐานแรก (${t1['price']:.2f}) ➔ ยอดกลาง Neckline (${neck_p['price']:.2f}) ➔ ฐานที่สอง (${t2['price']:.2f}) ➔ แรงส่งดีดตัว (${end_p['price']:.2f})",
                    "action_plan": f"เข้าซื้อเมื่อแท่งเทียนปิดทะลุ Neckline ${neck_p['price']:.2f} ด้วย Volume หนาแน่น เป้าหมาย ${target:.2f}",
                    "invalidation": f"รูปแบบจะล้มเหลวหากราคาปิดหลุดต่ำกว่าฐานที่ 2 (${t2['price']:.2f})",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดส่วนสูงฐานคู่ถึงยอดกลาง (${pattern_h:.2f}) บวกเพิ่มจากยอด Neckline",
                    "key_points": key_pts,
                    "lines": [
                        {"name": "Neckline Breakout", "color": "#38bdf8", "style": 2, "points": [{"time": start_time, "value": neck_p["price"]}, {"time": times[-1], "value": neck_p["price"]}]},
                        {"name": "Double Bottom Support Floor", "color": "#10b981", "style": 1, "points": [{"time": t1["time"], "value": min(t1["price"], t2["price"])}, {"time": times[-1], "value": min(t1["price"], t2["price"])}]}
                    ]
                }

    # 6. Double Top (M-Shape)
    if not detected and len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        mid_troughs = [t for t in troughs if p1["idx"] < t["idx"] < p2["idx"]]
        if mid_troughs:
            neck_t = min(mid_troughs, key=lambda x: x["price"])
            price_diff = abs(p1["price"] - p2["price"]) / p1["price"]
            drop = (max(p1["price"], p2["price"]) - neck_t["price"]) / max(p1["price"], p2["price"])
            pattern_h = max(p1["price"], p2["price"]) - neck_t["price"]
            width = p2["idx"] - p1["idx"]
            if (
                price_diff <= DOUBLE_PATTERN_PRICE_TOLERANCE_PCT
                and drop >= DOUBLE_PATTERN_MIN_SWING_PCT
                and width >= DOUBLE_PATTERN_MIN_WIDTH_BARS
            ):
                # Find left base of M (must be near neck_t in price and within 3-10 bars before p1)
                win_len = min(10, p1["idx"])
                left_win = recent[p1["idx"] - win_len: p1["idx"]] if win_len >= 2 else []
                start_t = None
                if left_win:
                    candidates = [c for c in left_win if c["low"] <= max(p1["price"], p2["price"]) - pattern_h * 0.7 and c["low"] >= neck_t["price"] - pattern_h * 1.25]
                    if candidates:
                        best_c = min(candidates, key=lambda c: abs(c["low"] - neck_t["price"]))
                        start_t = {"name": "Left Base (ฐานซ้าย M)", "time": best_c["time"], "price": best_c["low"]}

                # Find post-drop swing low after p2
                post_troughs = [t for t in troughs if t["idx"] > p2["idx"]]
                if post_troughs:
                    end_t = post_troughs[0]
                else:
                    post_win = recent[p2["idx"] + 1:]
                    if post_win:
                        min_l = min(c["low"] for c in post_win)
                        end_c = [c for c in post_win if c["low"] == min_l][0]
                        end_t = {"name": "Drop Low", "time": end_c["time"], "price": end_c["low"]}
                    else:
                        end_t = {"name": "Drop Low", "time": times[-1], "price": closes[-1]}

                key_pts = []
                if start_t:
                    key_pts.append({"name": start_t["name"], "time": start_t["time"], "price": start_t["price"], "role": "start"})
                    start_time = start_t["time"]
                else:
                    start_time = p1["time"]

                key_pts.extend([
                    {"name": "Peak 1 (ยอดแรก)", "time": p1["time"], "price": p1["price"], "role": "" if start_t else "start"},
                    {"name": "Neckline Trough (ฐานกลาง M)", "time": neck_t["time"], "price": neck_t["price"]},
                    {"name": "Peak 2 (ยอดที่สอง)", "time": p2["time"], "price": p2["price"]},
                    {"name": "Breakdown (ขาขวาทิ้งตัว)", "time": end_t["time"], "price": end_t["price"]},
                ])

                target = round(neck_t["price"] - pattern_h, 2)
                detected = {
                    "name": "Bearish Double Top (M-Shape)",
                    "type": "Bearish Reversal",
                    "badge": "🔴 รูปแบบหมี (Double Top)",
                    "summary": f"ตรวจพบจุดสูงสุดคู่ใกล้ ${p1['price']:.2f} และ ${p2['price']:.2f} มี Neckline รับที่ ${neck_t['price']:.2f}",
                    "neckline": round(neck_t["price"], 2),
                    "breakout": round(neck_t["price"], 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ราคาพยายามทดสอบจุดสูงสุดเดิมเป็นครั้งที่สองแต่ถูกแรงขายเททับสะท้อนว่าผู้ซื้อหมดแรงขับเคลื่อน (Buyer Exhaustion) และเกิดการกระจายหุ้นของสถาบันก่อนทิ้งตัวลง",
                    "structure": f"ยอดแรก (${p1['price']:.2f}) ➔ ฐานรับกลาง Neckline (${neck_t['price']:.2f}) ➔ ยอดที่สอง (${p2['price']:.2f}) ➔ ขาขวาทิ้งตัว (${end_t['price']:.2f})",
                    "action_plan": f"ขายทำกำไร (Trim/TP) หรือตั้ง Stop Loss เมื่อราคาหลุด Neckline ${neck_t['price']:.2f} เป้าหมายขาลง ${target:.2f}",
                    "invalidation": f"รูปแบบล้มเหลวหากราคาเบรกทะลุยอดสูงสุด ${max(p1['price'], p2['price']):.2f}",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดส่วนสูงของยอดคู่แล้วหักลบออกจาก Neckline ${neck_t['price']:.2f}",
                    "key_points": key_pts,
                    "lines": [
                        {"name": "Neckline Support", "color": "#38bdf8", "style": 2, "points": [{"time": start_time, "value": neck_t["price"]}, {"time": times[-1], "value": neck_t["price"]}]},
                        {"name": "Double Top Resistance Ceiling", "color": "#f43f5e", "style": 1, "points": [{"time": p1["time"], "value": max(p1["price"], p2["price"])}, {"time": times[-1], "value": max(p1["price"], p2["price"])}]}
                    ]
                }


    # 6. Bull Flag / Bear Flag Check
    if not detected and n >= 25:
        sub_lows = lows[-25:-8]
        sub_highs = highs[-25:-8]
        pole_base = min(sub_lows)
        pole_peak = max(sub_highs)
        base_sub_idx = sub_lows.index(pole_base)
        peak_sub_idx = sub_highs.index(pole_peak)
        pole_gain = (pole_peak - pole_base) / pole_base
        if pole_gain >= 0.08 and base_sub_idx < peak_sub_idx:
            base_real_idx = -25 + base_sub_idx
            peak_real_idx = -25 + peak_sub_idx
            flag_highs = highs[-8:]
            flag_lows = lows[-8:]
            flag_high = max(flag_highs)
            flag_low = min(flag_lows)
            if flag_high <= pole_peak * 1.01 and flag_low >= pole_base + (pole_peak - pole_base) * 0.45:
                target = round(flag_high + (pole_peak - pole_base), 2)
                f_high_idx = -8 + flag_highs.index(flag_high)
                f_low_idx = -8 + flag_lows.index(flag_low)
                flag_swings = sorted([
                    {"name": "Flag Resistance", "time": times[f_high_idx], "price": flag_high, "idx": n + f_high_idx},
                    {"name": "Flag Support", "time": times[f_low_idx], "price": flag_low, "idx": n + f_low_idx}
                ], key=lambda x: x["idx"])
                kp = [
                    {"name": "Pole Base (จุดเริ่มเสาธง)", "time": times[base_real_idx], "price": pole_base, "role": "start"},
                    {"name": "Pole Peak (ยอดเสาธง)", "time": times[peak_real_idx], "price": pole_peak},
                ] + [{"name": s["name"], "time": s["time"], "price": s["price"]} for s in flag_swings]
                detected = {
                    "name": "Bullish Flag (ธงสะสมพลังขาขึ้น)",
                    "type": "Bullish Continuation",
                    "badge": "🚩 ธงกระทิง (Bull Flag)",
                    "summary": f"เกิดเสาธงขาขึ้นสูง {pole_gain*100:.1f}% ตามด้วยการพักตัวในกรอบธงแคบๆ ลุ้นระเบิดเป้าหมาย ${target:.2f}",
                    "neckline": round(flag_high, 2),
                    "breakout": round(flag_high, 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "หลังราคาพุ่งแรงเป็นเสาธง เกิดการพักตัวสั้นๆ ในกรอบแคบเพื่อเขย่าเอาผู้เล่นที่ไม่มีความมั่นใจออกไป (Shakeout) โดยปริมาณการซื้อขายลดลงระหว่างพักตัวก่อนจะระเบิดทะลุต่อ",
                    "structure": f"เสาธงสูง {pole_gain*100:.1f}% (${pole_base:.2f} ถึง ${pole_peak:.2f}) • กรอบธงสะสม (${flag_low:.2f} ถึง ${flag_high:.2f})",
                    "action_plan": f"เข้าซื้อทันทีที่ราคาเบรกทะลุกรอบบน ${flag_high:.2f} หรือซื้อสะสมแถวกรอบล่าง ${flag_low:.2f} เป้าหมาย ${target:.2f}",
                    "invalidation": f"รูปแบบเสียทรงหากราคาหลุดต่ำกว่ากรอบล่าง ${flag_low:.2f}",
                    "win_rate": PATTERN_WIN_RATE_NOTE,
                    "target_calc": f"วัดความสูงของเสาธง ({pole_peak - pole_base:.2f}) แล้วนำไปทาบต่อจากจุดเบรกเอาท์ของกรอบธง",
                    "key_points": kp,
                    "lines": [
                        {"name": "Flagpole", "color": "#facc15", "style": 0, "points": [{"time": times[base_real_idx], "value": pole_base}, {"time": times[peak_real_idx], "value": pole_peak}]},
                        {"name": "Flag Resistance", "color": "#10b981", "style": 2, "points": [{"time": times[-8], "value": flag_high}, {"time": times[-1], "value": flag_high}]},
                        {"name": "Flag Support", "color": "#38bdf8", "style": 2, "points": [{"time": times[-8], "value": flag_low}, {"time": times[-1], "value": flag_low}]}
                    ]
                }

    # 8. Fallback: Range Consolidation Box (Tight accumulation only, span <= MAX_BOX_RANGE_SPAN_PCT)
    if not detected and n >= 30:
        prior_high = max(highs[-30:-1])
        prior_low = min(lows[-30:-1])
        if closes[-1] > prior_high:
            recent_high = prior_high
            recent_low = prior_low
            h_sub = highs[-30:-1].index(recent_high)
            l_sub = lows[-30:-1].index(recent_low)
        else:
            recent_high = max(highs[-30:])
            recent_low = min(lows[-30:])
            h_sub = highs[-30:].index(recent_high)
            l_sub = lows[-30:].index(recent_low)

        span_pct = (recent_high - recent_low) / max(1e-6, recent_low)
        # Heuristic guard: tight accumulation box must not exceed MAX_BOX_RANGE_SPAN_PCT (15%),
        # and price must reside inside the box boundary or just break out (within 3%).
        if span_pct <= MAX_BOX_RANGE_SPAN_PCT and (recent_low <= current_price <= recent_high * 1.03):
            h_idx = -30 + h_sub
            l_idx = -30 + l_sub
            start_idx = -30
            raw_pts = [
                {"name": "Box Start (จุดเริ่มกรอบ)", "time": times[start_idx], "price": closes[start_idx], "idx": n + start_idx},
                {"name": "Box Resistance", "time": times[h_idx], "price": recent_high, "idx": n + h_idx},
                {"name": "Box Support", "time": times[l_idx], "price": recent_low, "idx": n + l_idx},
            ]
            raw_pts.sort(key=lambda x: x["idx"])
            raw_pts[0]["role"] = "start"
            kp = [{"name": x["name"], "time": x["time"], "price": x["price"], "role": x.get("role", "")} for x in raw_pts]
            detected = {
                "name": "Consolidation Box (กรอบสะสมพลัง)",
                "type": "Neutral Consolidation",
                "badge": "📦 กรอบพักตัว (Box Range)",
                "summary": f"ราคาเคลื่อนไหวไซด์เวย์ในกรอบสะสม ${recent_low:.2f} - ${recent_high:.2f}",
                "neckline": round(recent_high, 2),
                "breakout": round(recent_high, 2),
                "target": None,
                "upside_pct": None,
                "psychology": "ราคาพักตัวรอปัจจัยหนุนใหม่ มีการสะสมหุ้นในกรอบระหว่างผู้ซื้อที่ตั้งรับด้านล่างและผู้ขายที่ขายทำกำไรด้านบน",
                "structure": f"กรอบแนวรับ ${recent_low:.2f} และแนวต้าน ${recent_high:.2f}",
                "action_plan": f"ตั้งรับใกล้แนวรับ ${recent_low:.2f} หรือ Follow Buy เมื่อเบรกทะลุกรอบบน ${recent_high:.2f}",
                "invalidation": f"Stop Loss หากราคาปิดหลุดแนวรับ ${recent_low:.2f}",
                "win_rate": PATTERN_WIN_RATE_NOTE,
                "target_calc": "วัดจากความสูงของกรอบสะสมพลัง 50% (คำนวณเป้าหมายเมื่อยืนยันเบรกเอาท์)",
                "key_points": kp,
                "lines": [
                    {"name": "Box Resistance", "color": "#f43f5e", "style": 2, "points": [{"time": times[-30], "value": recent_high}, {"time": times[-1], "value": recent_high}]},
                    {"name": "Box Support", "color": "#10b981", "style": 2, "points": [{"time": times[-30], "value": recent_low}, {"time": times[-1], "value": recent_low}]}
                ]
            }

    # Universal Pattern Lifecycle & Invalidation Guard
    if detected:
        pat_name = detected.get("name", "")
        pat_type = detected.get("type", "")
        is_bullish = ("bullish" in pat_type.lower() or "inv" in pat_name.lower() or "flag" in pat_name.lower() or "ascending" in pat_name.lower()) and "descending triangle" not in pat_name.lower()
        is_bearish = "bearish" in pat_type.lower() or "descending triangle" in pat_name.lower()

        support_level = None
        resistance_level = None

        # 1. Determine key support and resistance / breakout levels
        if "Double Bottom" in pat_name or "Triple Bottom" in pat_name:
            floor_lines = [l for l in detected.get("lines", []) if "support" in l["name"].lower() or "floor" in l["name"].lower()]
            if floor_lines:
                support_level = floor_lines[0]["points"][0]["value"]
            resistance_level = detected.get("neckline")
        elif "Double Top" in pat_name:
            ceil_lines = [l for l in detected.get("lines", []) if "ceiling" in l["name"].lower() or "resistance" in l["name"].lower()]
            if ceil_lines:
                resistance_level = ceil_lines[0]["points"][0]["value"]
            support_level = detected.get("neckline")
        elif "Head & Shoulders" in pat_name and "Inverted" not in pat_name:
            support_level = detected.get("neckline")
            r_shoulder = [kp for kp in detected.get("key_points", []) if "right shoulder" in kp["name"].lower()]
            if r_shoulder:
                resistance_level = r_shoulder[0]["price"]
        elif "Inverted Head & Shoulders" in pat_name:
            resistance_level = detected.get("neckline")
            r_shoulder = [kp for kp in detected.get("key_points", []) if "right shoulder" in kp["name"].lower()]
            if r_shoulder:
                support_level = r_shoulder[0]["price"]
        elif "Descending Triangle" in pat_name:
            # Floor is horizontal flat support
            support_level = detected.get("neckline")
            res_lines = [l for l in detected.get("lines", []) if "resistance" in l["name"].lower()]
            if res_lines:
                resistance_level = res_lines[0]["points"][0]["value"]
        elif any(k in pat_name for k in ["Triangle", "Wedge", "Flag", "Channel"]):
            resistance_level = detected.get("breakout") or detected.get("neckline")
            sup_lines = [l for l in detected.get("lines", []) if "support" in l["name"].lower()]
            if sup_lines:
                support_level = min(p["value"] for p in sup_lines[0]["points"])

        # Extract slope and points for support and resistance lines if available
        sup_lines_all = [l for l in detected.get("lines", []) if "support" in l["name"].lower() or "floor" in l["name"].lower() or "lower" in l["name"].lower()]
        res_lines_all = [l for l in detected.get("lines", []) if "resistance" in l["name"].lower() or "ceiling" in l["name"].lower() or "upper" in l["name"].lower() or "neckline" in l["name"].lower()]

        s_slope = 0.0
        s_p1_val = support_level
        s_bar_idx = 0
        has_dynamic_support = False
        if sup_lines_all:
            s_pts = sup_lines_all[0]["points"]
            s_p1_time = s_pts[0]["time"]
            s_p1_val = s_pts[0]["value"]
            s_end_val = s_pts[-1]["value"]
            s_idx = [i for i, tm in enumerate(times) if tm == s_p1_time]
            s_bar_idx = s_idx[0] if s_idx else 0
            s_end_time = s_pts[-1]["time"]
            s_end_idx = [i for i, tm in enumerate(times) if tm == s_end_time]
            s_end_bar = s_end_idx[0] if s_end_idx else (n - 1)
            s_span = max(1, s_end_bar - s_bar_idx)
            s_slope = (s_end_val - s_p1_val) / s_span
            if abs(s_slope) > 1e-6:
                has_dynamic_support = True
            if support_level is None:
                support_level = s_p1_val

        r_slope = 0.0
        r_p1_val = resistance_level
        r_bar_idx = 0
        has_dynamic_resistance = False
        if res_lines_all:
            r_pts = res_lines_all[0]["points"]
            r_p1_time = r_pts[0]["time"]
            r_p1_val = r_pts[0]["value"]
            r_end_val = r_pts[-1]["value"]
            r_idx = [i for i, tm in enumerate(times) if tm == r_p1_time]
            r_bar_idx = r_idx[0] if r_idx else 0
            r_end_time = r_pts[-1]["time"]
            r_end_idx = [i for i, tm in enumerate(times) if tm == r_end_time]
            r_end_bar = r_end_idx[0] if r_end_idx else (n - 1)
            r_span = max(1, r_end_bar - r_bar_idx)
            r_slope = (r_end_val - r_p1_val) / r_span
            if abs(r_slope) > 1e-6:
                has_dynamic_resistance = True
            if resistance_level is None:
                resistance_level = r_p1_val

        # 2. Find post-pattern candle slice (from the last key point time or t2/p2 for double patterns)
        kp_indices = []
        if "Double Bottom" in pat_name:
            t2_pts = [kp for kp in detected.get("key_points", []) if "bottom 2" in kp["name"].lower() or "ฐานที่สอง" in kp["name"]]
            if t2_pts and "time" in t2_pts[0]:
                matching = [i for i, tm in enumerate(times) if tm == t2_pts[0]["time"]]
                if matching:
                    kp_indices = [matching[-1]]
        elif "Double Top" in pat_name:
            p2_pts = [kp for kp in detected.get("key_points", []) if "peak 2" in kp["name"].lower() or "ยอดที่สอง" in kp["name"]]
            if p2_pts and "time" in p2_pts[0]:
                matching = [i for i, tm in enumerate(times) if tm == p2_pts[0]["time"]]
                if matching:
                    kp_indices = [matching[-1]]

        if not kp_indices:
            for kp in detected.get("key_points", []):
                if "idx" in kp:
                    kp_indices.append(kp["idx"])
                elif "time" in kp:
                    matching = [i for i, tm in enumerate(times) if tm == kp["time"]]
                    if matching:
                        kp_indices.append(matching[-1])
        latest_kp_idx = max(kp_indices) if kp_indices else max(0, n - 6)

        post_candles = recent[latest_kp_idx:]
        post_closes = [c["close"] for c in post_candles]

        # 3. Evaluate Bullish Patterns
        if is_bullish:
            breakdown_indices = []
            for i, c in enumerate(post_candles):
                bar_idx = latest_kp_idx + i
                cur_floor = (s_p1_val + s_slope * (bar_idx - s_bar_idx)) if has_dynamic_support else (support_level or 0.0)
                if cur_floor > 0 and (c["close"] < cur_floor * 0.995 or c["low"] < cur_floor * 0.985):
                    breakdown_indices.append(i)

            if breakdown_indices:
                first_break_idx = latest_kp_idx + breakdown_indices[0]
                bars_since_break = n - 1 - first_break_idx
                if bars_since_break > 12:
                    detected = None
                else:
                    break_floor = (s_p1_val + s_slope * (first_break_idx - s_bar_idx)) if has_dynamic_support else (support_level or 0.0)
                    detected["status"] = "failed"
                    detected["badge"] = f"🔴 รูปแบบล้มเหลว (Pattern Failed - หลุด ${break_floor:.2f})"
                    detected["type"] = "Failed Pattern (เสียทรง)"
                    detected["summary"] = f"รูปแบบ {detected['name']} ล้มเหลวเนื่องจากราคาปิดหลุดแนวรับ ${break_floor:.2f} (ราคาปิดล่าสุด ${current_price:.2f})"
                    detected["action_plan"] = f"⚠️ รูปแบบเสียทรง ห้ามเข้าซื้อหรือให้ Stop Loss ทันที ราคาปิดหลุดแนวรับสำคัญ ${break_floor:.2f} กลายเป็นขาลงต่อเนื่อง"
                    detected["target"] = None
                    detected["upside_pct"] = None
                    detected["lines"].append({
                        "name": f"Breakdown Floor (${break_floor:.2f})",
                        "color": "#ef4444",
                        "style": 2,
                        "points": [{"time": times[first_break_idx], "value": round(break_floor, 2)}, {"time": times[-1], "value": round(break_floor, 2)}]
                    })
                    # Append Breakdown leg to key_points so the skeleton connects through the broken floor
                    valid_break_indices = [i for i in breakdown_indices if i > 0]
                    target_break_idx = valid_break_indices[0] if valid_break_indices else breakdown_indices[0]
                    break_slice = post_candles[target_break_idx:]
                    if break_slice:
                        break_c = min(break_slice, key=lambda c: c["low"])
                        if not detected.get("key_points") or break_c["time"] != detected["key_points"][-1]["time"]:
                            detected.setdefault("key_points", []).append({
                                "name": "Breakdown (หลุดแนวรับ)",
                                "time": break_c["time"],
                                "price": round(break_c["low"], 2)
                            })
                            if "structure" in detected and "หลุดแนวรับ" not in detected["structure"]:
                                detected["structure"] += f" ➔ ⚠️ หลุดแนวรับ Breakdown (${break_c['low']:.2f})"
            else:
                is_breakout = False
                for i, c in enumerate(post_candles):
                    bar_idx = latest_kp_idx + i
                    cur_roof = (r_p1_val + r_slope * (bar_idx - r_bar_idx)) if has_dynamic_resistance else (resistance_level or 0.0)
                    if cur_roof > 0 and c["close"] >= cur_roof * 1.002:
                        is_breakout = True
                        break

                if is_breakout:
                    detected["status"] = "confirmed"
                    detected["badge"] = detected.get("badge", "").replace("🟢", "✅").replace("รูปแบบกระทิง", "ยืนยันเบรกเอาท์ (Confirmed)")
                else:
                    detected["status"] = "forming"
                    detected["badge"] = detected.get("badge", "").replace("🟢", "🟡").replace("รูปแบบกระทิง", "กำลังก่อตัว (Forming - รอเบรก)")
                    cur_res_str = f"${resistance_level:.2f}" if resistance_level else "ต้าน"
                    detected["action_plan"] = f"ราคากำลังทดสอบแนวต้าน Neckline {cur_res_str} ห้ามชิงซื้อจนกว่าแท่งเทียนจะปิดทะลุแนวต้านยืนยัน"

        # 4. Evaluate Bearish Patterns
        elif is_bearish and support_level is not None:
            if "Descending Triangle" in pat_name:
                flat_floor = support_level
                failed_indices = [
                    i for i, c in enumerate(post_candles)
                    if c["close"] > ((r_p1_val + r_slope * (latest_kp_idx + i - r_bar_idx)) if has_dynamic_resistance else (resistance_level or flat_floor)) * 1.008
                ]
                if failed_indices:
                    first_break_idx = latest_kp_idx + failed_indices[0]
                    bars_since_break = n - 1 - first_break_idx
                    if bars_since_break > 12:
                        detected = None
                    else:
                        break_roof = (r_p1_val + r_slope * (first_break_idx - r_bar_idx)) if has_dynamic_resistance else (resistance_level or flat_floor)
                        detected["status"] = "failed"
                        detected["badge"] = f"🟢 รูปแบบหมีล้มเหลว (Bear Failed - ทะลุแนวต้านเฉียง ${break_roof:.2f})"
                        detected["type"] = "Failed Pattern (เบรกทะลุต้าน)"
                        detected["target"] = None
                        detected["upside_pct"] = None
                elif any(c["close"] <= flat_floor * 0.998 for c in post_candles):
                    detected["status"] = "confirmed"
                else:
                    detected["status"] = "forming"
            elif resistance_level is not None:
                breakout_indices = [i for i, c in enumerate(post_candles) if c["close"] > resistance_level * 1.008]
                if breakout_indices:
                    first_break_idx = latest_kp_idx + breakout_indices[0]
                    bars_since_break = n - 1 - first_break_idx
                    if bars_since_break > 12:
                        detected = None
                    else:
                        detected["status"] = "failed"
                        detected["badge"] = f"🟢 รูปแบบหมีล้มเหลว (Bear Failed - ทะลุ ${resistance_level:.2f})"
                        detected["type"] = "Failed Pattern (เบรกทะลุต้าน)"
                        detected["target"] = None
                        detected["upside_pct"] = None
                        valid_break_indices = [i for i in breakout_indices if i > 0]
                        target_break_idx = valid_break_indices[0] if valid_break_indices else breakout_indices[0]
                        break_slice = post_candles[target_break_idx:]
                        if break_slice:
                            break_c = max(break_slice, key=lambda c: c["high"])
                            if not detected.get("key_points") or break_c["time"] != detected["key_points"][-1]["time"]:
                                detected.setdefault("key_points", []).append({
                                    "name": "Breakout (ทะลุต้าน)",
                                    "time": break_c["time"],
                                    "price": round(break_c["high"], 2)
                                })
                                if "structure" in detected and "ทะลุต้าน" not in detected["structure"]:
                                    detected["structure"] += f" ➔ ✅ ทะลุต้าน Breakout (${break_c['high']:.2f})"
                else:
                    if support_level and any(c <= support_level * 0.998 for c in post_closes):
                        detected["status"] = "confirmed"
                    else:
                        detected["status"] = "forming"

        # 5. Evaluate Neutral / Volatility Patterns (Expanding Triangle, Symmetrical Triangle, Box Range)
        else:
            detected.setdefault("status", "forming")
            if "Triangle" in pat_name:
                is_breakout = False
                is_breakdown = False
                break_roof_val = r_p1_val
                break_floor_val = s_p1_val
                for i, c in enumerate(post_candles):
                    bar_idx = latest_kp_idx + i
                    roof = (r_p1_val + r_slope * (bar_idx - r_bar_idx)) if has_dynamic_resistance else (resistance_level or c["close"])
                    floor = (s_p1_val + s_slope * (bar_idx - s_bar_idx)) if has_dynamic_support else (support_level or c["close"])
                    if c["close"] >= roof * 1.002:
                        is_breakout = True
                        break_roof_val = roof
                        break
                    elif c["close"] <= floor * 0.995:
                        is_breakdown = True
                        break_floor_val = floor
                        break

                if is_breakout:
                    detected["status"] = "confirmed"
                    detected["badge"] = "✅ ยืนยันเบรกเอาท์ (Confirmed Breakout)"
                elif is_breakdown:
                    detected["status"] = "broke_down"
                    detected["badge"] = f"🔻 หลุดกรอบล่าง (Breakdown - หลุด ${break_floor_val:.2f})"
                    detected["type"] = "Bearish Breakdown (เบรกลง)"
                    detected["summary"] = f"รูปแบบ {detected['name']} หลุดแนวรับกรอบล่าง (${break_floor_val:.2f})"
                    detected["action_plan"] = f"⚠️ ราคาหลุดแนวรับกรอบล่าง ชะลอการลงทุนหรือตัดขาดทุนตามแผน"
                    detected["target"] = None
                    detected["upside_pct"] = None
                else:
                    detected["status"] = "forming"
            elif "Consolidation Box" in pat_name:
                box_res = detected.get("neckline")
                box_sup_lines = [l for l in detected.get("lines", []) if "support" in l["name"].lower()]
                box_sup = box_sup_lines[0]["points"][0]["value"] if box_sup_lines else None
                if box_res and any(c >= box_res * 1.002 for c in post_closes):
                    detected["status"] = "confirmed"
                    box_h = box_res - (box_sup if box_sup is not None else box_res * 0.95)
                    detected["target"] = round(box_res + box_h * 0.5, 2)
                    detected["upside_pct"] = round((detected["target"] - current_price) / current_price * 100, 1)
                    detected["target_calc"] = f"ความสูงของกรอบบวกเพิ่มจากแนวต้าน 50% เป้าหมาย ${detected['target']:.2f}"
                elif box_sup and any(c <= box_sup * 0.995 for c in post_closes):
                    detected["status"] = "failed"
                    detected["target"] = None
                    detected["upside_pct"] = None
                    detected["target_calc"] = "-"
                else:
                    detected["status"] = "forming"
                    detected["target"] = None
                    detected["upside_pct"] = None
                    detected["target_calc"] = "วัดจากความสูงของกรอบสะสมพลัง 50% (คำนวณเป้าหมายเมื่อยืนยันเบรกเอาท์)"
            else:
                if resistance_level and any(c >= resistance_level * 1.002 for c in post_closes):
                    detected["status"] = "confirmed"
                elif support_level and any(c <= support_level * 0.995 for c in post_closes):
                    detected["status"] = "failed"


    if detected:
        detected.setdefault("status", "forming")

    return detected


BULLISH_DEVELOPING_WAVE_TYPES = {
    "Bullish Impulse (1-2-3-4-5)",
    "Emerging Bullish Impulse (1-2-3)",
    "New Cycle Wave (1) Breakout",
}


def detect_elliott_wave(candles: List[Dict[str, Any]], is_macro: bool = False) -> Optional[Dict[str, Any]]:
    """
    Detects Elliott Wave structures (Impulse 1-2-3-4-5, Emerging 1-2-3, Corrective A-B-C,
    Bearish Impulse 1-2-3-4-5, and New Motive Cycle Breakouts) strictly adhering to
    LuxAlgo Elliott Wave principles & 3 Cardinal Rules:
      1. Cardinal Rule 1: Wave 2 never retraces beyond the origin of Wave 1 (W2 > W0 bullish, W2 < W0 bearish).
      2. Cardinal Rule 2: Wave 4 never enters the price territory of Wave 1 (W4 > W1 bullish, W4 < W1 bearish).
      3. Cardinal Rule 3: Wave 3 is NEVER the shortest wave among motive waves (len3 != min(len1, len3, len5)).
      4. LuxAlgo Post-Impulse Fibonacci Retracement Grid (50.0%, 61.8% Golden Pocket, 76.4%, 85.4% Invalidation Floor).
      5. Next Cycle Start Detection: Flags New Motive Cycle Wave (1) when price breaks above Wave 5 peak after ABC correction.
      6. Invalidation Status Tracking: Supports active, completed, and invalidated wave states.
    """
    degree_label = "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)"

    if not candles or len(candles) < 20:
        return {
            "detected": False,
            "type": "Insufficient Data",
            "direction": "neutral",
            "status": "none",
            "degree": degree_label,
            "current_wave": "ข้อมูลแท่งเทียนไม่เพียงพอ",
            "current_wave_badge": "N/A",
            "summary": "ข้อมูลแท่งเทียนไม่เพียงพอต่อการวิเคราะห์โครงสร้างคลื่น",
            "points": [],
            "lines": [],
            "target": None,
            "invalidation": None,
            "fibo_pullback": None,
            "cycle_signal": None,
        }

    recent = candles if is_macro else (candles[-252:] if len(candles) >= 252 else candles)
    current_c = recent[-1]
    current_p = round(float(current_c["close"]), 2)
    current_t = current_c["time"]

    # Adaptive volatility threshold for multi-scale zigzag
    sample = recent[-60:] if len(recent) >= 60 else recent
    diffs = [abs(sample[i]["close"] - sample[i - 1]["close"]) / max(1e-4, sample[i - 1]["close"]) for i in range(1, len(sample))]
    avg_vol = sum(diffs) / len(diffs) if diffs else 0.015
    base_thresh = max(0.025, min(0.10, avg_vol * (4.0 if is_macro else 3.0)))

    best_swings = []
    target_count = 10 if not is_macro else 8

    for mult in [1.0, 1.3, 0.75, 1.8, 0.5, 2.2]:
        thresh = base_thresh * mult
        swings = []
        last_type = None
        last_p = recent[0]["close"]
        last_idx = 0
        for i, c in enumerate(recent):
            p = c["close"]
            if last_type is None:
                if p >= last_p * (1 + thresh):
                    last_type = "high"
                    last_p = c["high"]
                    last_idx = i
                    swings.append({"type": "low", "time": recent[0]["time"], "price": round(recent[0]["low"], 2), "idx": 0})
                elif p <= last_p * (1 - thresh):
                    last_type = "low"
                    last_p = c["low"]
                    last_idx = i
                    swings.append({"type": "high", "time": recent[0]["time"], "price": round(recent[0]["high"], 2), "idx": 0})
            elif last_type == "high":
                if c["high"] > last_p:
                    last_p = c["high"]
                    last_idx = i
                elif c["low"] <= last_p * (1 - thresh):
                    swings.append({"type": "high", "time": recent[last_idx]["time"], "price": round(last_p, 2), "idx": last_idx})
                    last_type = "low"
                    last_p = c["low"]
                    last_idx = i
            elif last_type == "low":
                if c["low"] < last_p:
                    last_p = c["low"]
                    last_idx = i
                elif c["high"] >= last_p * (1 + thresh):
                    swings.append({"type": "low", "time": recent[last_idx]["time"], "price": round(last_p, 2), "idx": last_idx})
                    last_type = "high"
                    last_p = c["high"]
                    last_idx = i

        if last_type == "high":
            swings.append({"type": "high", "time": recent[last_idx]["time"], "price": round(last_p, 2), "idx": last_idx})
        elif last_type == "low":
            swings.append({"type": "low", "time": recent[last_idx]["time"], "price": round(last_p, 2), "idx": last_idx})

        if 5 <= len(swings) <= 18:
            best_swings = swings
            break
        if not best_swings or abs(len(swings) - target_count) < abs(len(best_swings) - target_count):
            best_swings = swings

    if len(best_swings) < 3:
        return {
            "detected": False,
            "type": "No Clear Wave / Consolidation",
            "direction": "neutral",
            "status": "none",
            "degree": degree_label,
            "current_wave": "ไม่มีโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์",
            "current_wave_badge": "Consolidation",
            "summary": "ไม่พบโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์ (ราคาอยู่ในสภาวะพักฐาน ปรับฐาน หรือสะสมพลังไซด์เวย์ แนะนำอ้างอิง Classical Chart Pattern หรือแนวรับต้าน EMA)",
            "points": [],
            "lines": [],
            "target": None,
            "invalidation": None,
            "fibo_pullback": None,
            "cycle_signal": None,
        }

    n_sw = len(best_swings)

    def _clean_points(pts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clean: List[Dict[str, Any]] = []
        seen = set()
        for p in pts:
            if p["time"] not in seen:
                seen.add(p["time"])
                clean.append(p)
            else:
                clean[-1] = p
        return clean

    def _calc_luxalgo_fibo(w0: float, w5: float, is_bull: bool = True) -> Optional[Dict[str, Any]]:
        diff = abs(w5 - w0)
        if diff <= 0:
            return None
        if is_bull:
            f500 = round(w5 - diff * 0.500, 2)
            f618 = round(w5 - diff * 0.618, 2)
            f764 = round(w5 - diff * 0.764, 2)
            f854 = round(w5 - diff * 0.854, 2)
            broken = current_p < f854
        else:
            f500 = round(w5 + diff * 0.500, 2)
            f618 = round(w5 + diff * 0.618, 2)
            f764 = round(w5 + diff * 0.764, 2)
            f854 = round(w5 + diff * 0.854, 2)
            broken = current_p > f854
        return {
            "fib_500": f500,
            "fib_618": f618,
            "fib_764": f764,
            "fib_854": f854,
            "floor_broken": broken,
        }

    # -------------------------------------------------------------------------
    # 1. New Motive Cycle Start (LuxAlgo Circle Signal: Breakout after ABC)
    # -------------------------------------------------------------------------
    if n_sw >= 4:
        for k in range(max(0, n_sw - 5), n_sw - 3):
            s_top, sa, sb, sc = best_swings[k:k + 4]
            if s_top["type"] == "high" and sa["type"] == "low" and sb["type"] == "high" and sc["type"] == "low":
                if sb["price"] < s_top["price"] and sa["price"] < s_top["price"] and sc["price"] < sb["price"]:
                    # If current price breaks above the previous Wave 5 / Wave B top
                    if current_p > s_top["price"] * 0.995:
                        pts = [
                            {"wave": "(5)", "time": s_top["time"], "price": s_top["price"], "label": "Prior Wave (5) Peak"},
                            {"wave": "(A)", "time": sa["time"], "price": sa["price"], "label": "Wave (A) Drop"},
                            {"wave": "(B)", "time": sb["time"], "price": sb["price"], "label": "Wave (B) Rebound"},
                            {"wave": "(C)", "time": sc["time"], "price": sc["price"], "label": "Wave (C) Base Floor"},
                            {"wave": "(1)", "time": current_t, "price": current_p, "label": "🟢 New Cycle (1) Breakout"},
                        ]
                        clean_pts = _clean_points(pts)
                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        target_new = round(current_p + (s_top["price"] - sc["price"]) * 1.618, 2)
                        return {
                            "detected": True,
                            "type": "New Cycle Wave (1) Breakout",
                            "direction": "bullish",
                            "status": "active",
                            "degree": degree_label,
                            "current_wave": "🟢 New Cycle Wave (1) ระเบิดทะลุ High เดิม",
                            "current_wave_badge": "New Cycle (1)",
                            "summary": f"เกิดสัญญาณ LuxAlgo New Motive Cycle Breakout หลังจบการพักฐาน A-B-C โดยราคาเบรกทะลุยอดดอยเดิม ${s_top['price']:.2f} เริ่มต้นคลื่นลูกใหม่",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target_new,
                            "invalidation": round(sc["price"], 2),
                            "fibo_pullback": _calc_luxalgo_fibo(sc["price"], current_p, is_bull=True),
                            "cycle_signal": "New Bullish Motive Cycle Initiated",
                        }

    # -------------------------------------------------------------------------
    # 2. Active Bullish Impulse (0)-(1)-(2)-(3)-(4) -> developing Wave (5)
    # -------------------------------------------------------------------------
    for k in range(max(0, n_sw - 6), n_sw - 4):
        s0, s1, s2, s3, s4 = best_swings[k:k + 5]
        if s0["type"] == "low" and s1["type"] == "high" and s2["type"] == "low" and s3["type"] == "high" and s4["type"] == "low":
            len1 = s1["price"] - s0["price"]
            len3 = s3["price"] - s2["price"]

            # Cardinal Rules: W2 > W0, W3 > W1 and strong, W4 > W1 (no overlap)
            if s2["price"] > s0["price"] and s3["price"] > s1["price"] and len3 >= len1 * 0.85 and s4["price"] > s1["price"]:
                idx_s4 = s4["idx"]
                candles_after_s4 = recent[idx_s4:]
                floor_breached = any(c["low"] < s4["price"] * 0.99 for c in candles_after_s4)
                swings_after_s4 = n_sw - 1 - (k + 4)

                if not floor_breached and swings_after_s4 <= 1 and current_p >= s4["price"]:
                    target5 = round(s4["price"] + max(len1, len3 * 0.618), 2)
                    inval = round(s4["price"], 2)
                    is_pushing = current_p >= s4["price"] * 1.02
                    curr_w_str = "Wave (5) กำลังขยายตัวสู่เป้าหมาย" if is_pushing else "Wave (4) โซนฐานแนวรับสะสม"
                    curr_badge = "Wave (5)" if is_pushing else "Wave (4)"

                    pts = [
                        {"wave": "(0)", "time": s0["time"], "price": s0["price"], "label": "Start Wave (0)"},
                        {"wave": "(1)", "time": s1["time"], "price": s1["price"], "label": "Wave (1) Impulse"},
                        {"wave": "(2)", "time": s2["time"], "price": s2["price"], "label": "Wave (2) Retrace"},
                        {"wave": "(3)", "time": s3["time"], "price": s3["price"], "label": "Wave (3) Expansion"},
                        {"wave": "(4)", "time": s4["time"], "price": s4["price"], "label": "Wave (4) Base Floor"},
                        {"wave": "(5)", "time": current_t, "price": current_p, "label": f"{curr_badge} ปัจจุบัน"},
                    ]
                    clean_pts = _clean_points(pts)
                    lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                    fibo_pb = _calc_luxalgo_fibo(s0["price"], max(s3["price"], current_p), is_bull=True)
                    return {
                        "detected": True,
                        "type": "Bullish Impulse (1-2-3-4-5)",
                        "direction": "bullish",
                        "status": "active",
                        "degree": degree_label,
                        "current_wave": curr_w_str,
                        "current_wave_badge": curr_badge,
                        "summary": f"เกิดโครงสร้างคลื่นขาขึ้น Bullish Impulse (1-2-3-4-5) ตามกฎ LuxAlgo โดย Wave (3) อยู่ที่ ${s3['price']:.2f} และ Wave (4) ฐานรับที่ ${s4['price']:.2f}",
                        "points": clean_pts,
                        "lines": lns,
                        "target": target5,
                        "invalidation": inval,
                        "fibo_pullback": fibo_pb,
                        "cycle_signal": None,
                    }

    # -------------------------------------------------------------------------
    # 3. Completed Bullish Impulse (0)-(1)-(2)-(3)-(4)-(5)
    # -------------------------------------------------------------------------
    if n_sw >= 6:
        s0, s1, s2, s3, s4, s5 = best_swings[-6:]
        if s0["type"] == "low" and s1["type"] == "high" and s2["type"] == "low" and s3["type"] == "high" and s4["type"] == "low" and s5["type"] == "high":
            len1 = s1["price"] - s0["price"]
            len3 = s3["price"] - s2["price"]
            len5 = s5["price"] - s4["price"]

            # Strict LuxAlgo Cardinal Rule 3: Wave 3 is NEVER the shortest wave
            is_w3_not_shortest = len3 != min(len1, len3, len5)

            if s2["price"] > s0["price"] and s3["price"] > s1["price"] and s4["price"] > s1["price"] and s5["price"] > s3["price"] and is_w3_not_shortest:
                pts = [
                    {"wave": "(0)", "time": s0["time"], "price": s0["price"], "label": "Start Wave (0)"},
                    {"wave": "(1)", "time": s1["time"], "price": s1["price"], "label": "Wave (1) Impulse"},
                    {"wave": "(2)", "time": s2["time"], "price": s2["price"], "label": "Wave (2) Retrace"},
                    {"wave": "(3)", "time": s3["time"], "price": s3["price"], "label": "Wave (3) Expansion"},
                    {"wave": "(4)", "time": s4["time"], "price": s4["price"], "label": "Wave (4) Base Floor"},
                    {"wave": "(5)", "time": s5["time"], "price": s5["price"], "label": "Wave (5) Peak"},
                ]
                lns = [{"time": p["time"], "value": p["price"]} for p in pts]
                fibo_pb = _calc_luxalgo_fibo(s0["price"], s5["price"], is_bull=True)
                return {
                    "detected": True,
                    "type": "Bullish Impulse Completed (1-2-3-4-5)",
                    "direction": "bullish",
                    "status": "completed",
                    "degree": degree_label,
                    "current_wave": "Wave (5) Peak จบรอบคลื่นสมบูรณ์",
                    "current_wave_badge": "Wave (5) Peak",
                    "summary": f"คลื่นขาขึ้น Bullish Impulse (1-2-3-4-5) จบรอบสมบูรณ์ที่ยอดคลื่น (5) ระดับ ${s5['price']:.2f} ตามเกณฑ์ LuxAlgo กำลังเข้าสู่ช่วงพักฐาน Corrective Phase",
                    "points": pts,
                    "lines": lns,
                    "target": round(s5["price"], 2),
                    "invalidation": round(s4["price"], 2),
                    "fibo_pullback": fibo_pb,
                    "cycle_signal": None,
                }

    # -------------------------------------------------------------------------
    # 4. Bearish Impulse (1-2-3-4-5) (LuxAlgo dir == -1: Downtrend Motive Waves)
    # -------------------------------------------------------------------------
    if n_sw >= 5:
        # Check for completed or active Bearish Impulse
        for k in range(max(0, n_sw - 6), n_sw - 4):
            chunk = best_swings[k:k + 5]
            s0, s1, s2, s3, s4 = chunk
            if s0["type"] == "high" and s1["type"] == "low" and s2["type"] == "high" and s3["type"] == "low" and s4["type"] == "high":
                len1 = s0["price"] - s1["price"]
                len3 = s2["price"] - s3["price"]

                # Bearish Cardinal Rules: W2 < W0, W3 < W1, W4 < W1 (no overlap)
                if s2["price"] < s0["price"] and s3["price"] < s1["price"] and s4["price"] < s1["price"] and len3 >= len1 * 0.85:
                    idx_s4 = s4["idx"]
                    candles_after_s4 = recent[idx_s4:]
                    roof_breached = any(c["high"] > s4["price"] * 1.01 for c in candles_after_s4)

                    if not roof_breached and current_p <= s4["price"]:
                        target_bear5 = round(max(0.01, s4["price"] - max(len1, len3 * 0.618)), 2)
                        inval_bear = round(s4["price"], 2)

                        pts = [
                            {"wave": "(0)", "time": s0["time"], "price": s0["price"], "label": "Start Top (0)"},
                            {"wave": "(1)", "time": s1["time"], "price": s1["price"], "label": "Bearish Wave (1)"},
                            {"wave": "(2)", "time": s2["time"], "price": s2["price"], "label": "Bearish Wave (2) Rebound"},
                            {"wave": "(3)", "time": s3["time"], "price": s3["price"], "label": "Bearish Wave (3) Expansion"},
                            {"wave": "(4)", "time": s4["time"], "price": s4["price"], "label": "Bearish Wave (4) Roof"},
                            {"wave": "(5)", "time": current_t, "price": current_p, "label": "Bearish Wave (5) กำลังลง"},
                        ]
                        clean_pts = _clean_points(pts)
                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        fibo_pb = _calc_luxalgo_fibo(s0["price"], current_p, is_bull=False)
                        return {
                            "detected": True,
                            "type": "Bearish Impulse (1-2-3-4-5)",
                            "direction": "bearish",
                            "status": "active",
                            "degree": degree_label,
                            "current_wave": "Bearish Wave (5) ขาลงโมเมนตัมกำลังทิ้งตัว",
                            "current_wave_badge": "Bear Wave (5)",
                            "summary": f"เกิดโครงสร้างคลื่นขาลง Bearish Impulse (1-2-3-4-5) ตามเกณฑ์ LuxAlgo โดย Wave (4) ชนแนวต้าน ${s4['price']:.2f} และกำลังทิ้งตัวสู่ Wave (5)",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target_bear5,
                            "invalidation": inval_bear,
                            "fibo_pullback": fibo_pb,
                            "cycle_signal": None,
                        }

    # -------------------------------------------------------------------------
    # 5. Emerging Bullish Impulse (0)-(1)-(2) -> developing Wave (3)
    # -------------------------------------------------------------------------
    if n_sw >= 3:
        for k in range(max(0, n_sw - 4), n_sw - 2):
            s0, s1, s2 = best_swings[k:k + 3]
            if s0["type"] == "low" and s1["type"] == "high" and s2["type"] == "low":
                if s2["price"] > s0["price"] and s1["price"] > s0["price"] * 1.05:
                    idx_s2 = s2["idx"]
                    candles_after_s2 = recent[idx_s2:]
                    floor_breached = any(c["low"] < s2["price"] * 0.99 for c in candles_after_s2)
                    swings_after_s2 = n_sw - 1 - (k + 2)

                    if not floor_breached and swings_after_s2 <= 1 and current_p >= s2["price"] * 1.01:
                        len1 = s1["price"] - s0["price"]
                        target3 = round(s2["price"] + len1 * 1.618, 2)
                        inval = round(s2["price"], 2)

                        pts = [
                            {"wave": "(0)", "time": s0["time"], "price": s0["price"], "label": "Wave (0) Base"},
                            {"wave": "(1)", "time": s1["time"], "price": s1["price"], "label": "Wave (1) Impulse"},
                            {"wave": "(2)", "time": s2["time"], "price": s2["price"], "label": "Wave (2) Retrace Floor"},
                            {"wave": "(3)", "time": current_t, "price": current_p, "label": "Wave (3) ปัจจุบัน"},
                        ]
                        clean_pts = _clean_points(pts)
                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        fibo_pb = _calc_luxalgo_fibo(s0["price"], current_p, is_bull=True)
                        return {
                            "detected": True,
                            "type": "Emerging Bullish Impulse (1-2-3)",
                            "direction": "bullish",
                            "status": "active",
                            "degree": degree_label,
                            "current_wave": "Wave (3) Impulse กำลังดีดตัวขยายตัว",
                            "current_wave_badge": "Wave (3)",
                            "summary": f"เกิดโครงสร้างต้นรอบคลื่น Wave (1-2-3) โดย Wave (2) ยกฐานรับที่ ${s2['price']:.2f} และกำลังวิ่งขึ้นทดสอบเป้าหมาย Wave (3)",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target3,
                            "invalidation": inval,
                            "fibo_pullback": fibo_pb,
                            "cycle_signal": None,
                        }

    # -------------------------------------------------------------------------
    # 6. Clean Corrective Wave (A-B-C) with LuxAlgo Retracement Levels
    # -------------------------------------------------------------------------
    if n_sw >= 3:
        for k in range(max(0, n_sw - 4), n_sw - 2):
            s_top, sa, sb = best_swings[k:k + 3]
            if s_top["type"] == "high" and sa["type"] == "low" and sb["type"] == "high":
                if sb["price"] < s_top["price"] and sa["price"] < s_top["price"] * 0.95:
                    idx_sb = sb["idx"]
                    candles_after_sb = recent[idx_sb:]
                    roof_breached = any(c["high"] > sb["price"] * 1.01 for c in candles_after_sb)
                    swings_after_sb = n_sw - 1 - (k + 2)

                    if not roof_breached and swings_after_sb <= 1 and current_p <= sb["price"]:
                        len_a = s_top["price"] - sa["price"]
                        target_c = round(max(0.01, sb["price"] - len_a * 1.0), 2)
                        inval = round(sb["price"], 2)

                        pts = [
                            {"wave": "(5)", "time": s_top["time"], "price": s_top["price"], "label": "Wave (5) Cycle Peak"},
                            {"wave": "(A)", "time": sa["time"], "price": sa["price"], "label": "Wave (A) Initial Drop"},
                            {"wave": "(B)", "time": sb["time"], "price": sb["price"], "label": "Wave (B) Rebound High"},
                            {"wave": "(C)", "time": current_t, "price": current_p, "label": "Wave (C) ปัจจุบัน"},
                        ]
                        clean_pts = _clean_points(pts)
                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        fibo_pb = _calc_luxalgo_fibo(sa["price"], s_top["price"], is_bull=True)
                        return {
                            "detected": True,
                            "type": "Corrective Wave (A-B-C)",
                            "direction": "bearish",
                            "status": "active",
                            "degree": degree_label,
                            "current_wave": "Corrective Wave (C) กำลังปรับฐานหาจุดสมดุล",
                            "current_wave_badge": "Wave (C)",
                            "summary": f"โครงสร้างคลื่นปรับฐาน Corrective (A-B-C) หลังยอดดอย ${s_top['price']:.2f} โดยมีรีบาวด์ Wave (B) ที่ ${sb['price']:.2f}",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target_c,
                            "invalidation": inval,
                            "fibo_pullback": fibo_pb,
                            "cycle_signal": None,
                        }

    # -------------------------------------------------------------------------
    # 7. Consolidation / Sideway (No valid unbroken wave)
    # -------------------------------------------------------------------------
    return {
        "detected": False,
        "type": "No Clear Wave / Consolidation",
        "direction": "neutral",
        "status": "none",
        "degree": degree_label,
        "current_wave": "ไม่มีโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์",
        "current_wave_badge": "Consolidation",
        "summary": "ไม่พบโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์ (ราคาอยู่ในสภาวะพักฐาน ปรับฐาน หรือสะสมพลังไซด์เวย์ แนะนำอ้างอิง Classical Chart Pattern หรือแนวรับต้าน EMA)",
        "points": [],
        "lines": [],
        "target": None,
        "invalidation": None,
        "fibo_pullback": None,
        "cycle_signal": None,
    }


def detect_earnings_history(
    candles: List[Dict[str, Any]],
    ticker: Optional[str] = None,
    days_to_earnings: Optional[float] = None,
    is_etf: bool = False,
) -> List[Dict[str, Any]]:
    """
    Quarterly earnings announcement reaction detection.
    When a ticker with confirmed announcement dates (2024-2026) is provided,
    calculates exact price reactions for those confirmed announcement dates.
    For ETFs or unannounced pending periods, returns no premature or false markers.
    If ticker is None, falls back to volume spike detection for mock candle tests.
    """
    if is_etf or not candles or len(candles) < 2:
        return []

    if ticker:
        ticker = ticker.strip().upper()
        if ticker in ETF_TICKERS:
            return []
        confirmed_dates = get_confirmed_earnings_dates(ticker)
        if confirmed_dates:
            return calculate_confirmed_earnings_reaction(candles, confirmed_dates, ticker=ticker)
        return []

    # Fallback to volume spike heuristic only when ticker is not provided (e.g. synthetic test candles)
    recent = candles[-750:] if len(candles) >= 750 else candles
    q_len = 62 if len(recent) >= 62 else len(recent)

    is_pending = False
    if days_to_earnings is not None:
        try:
            val = float(days_to_earnings)
            if 0.0 <= val <= 45.0:
                is_pending = True
        except (ValueError, TypeError):
            pass

    # Slice backwards from the most recent candle
    chunks = []
    end = len(recent)
    is_first = True
    while end > 0:
        start = max(0, end - q_len)
        chunk = recent[start:end]
        if is_first and is_pending:
            is_first = False
            end = start
            continue
        is_first = False
        if len(chunk) >= min(20, q_len):
            chunks.append((start, chunk))
        end = start

    raw_events = []
    for start_idx, chunk in chunks:
        max_c = max(chunk, key=lambda c: c.get("volume", 0))
        idx = start_idx + chunk.index(max_c)
        if idx > 0:
            avg_vol = sum(c.get("volume", 0) for c in chunk) / len(chunk)
            if avg_vol > 0 and max_c.get("volume", 0) >= avg_vol * 1.3:
                prev_c = recent[idx - 1]
                if prev_c.get("close", 0) > 0:
                    pct = round(((max_c["close"] - prev_c["close"]) / prev_c["close"]) * 100, 1)
                    raw_events.append({
                        "time": max_c["time"],
                        "idx": idx,
                        "volume": max_c.get("volume", 0),
                        "reaction_pct": pct,
                        "text": f"🗓️ {pct:+.1f}%",
                        "color": "#10b981" if pct >= 0 else "#f43f5e",
                        "position": "belowBar" if pct >= 0 else "aboveBar",
                    })

    raw_events.sort(key=lambda x: x["time"])
    deduped = []
    for ev in raw_events:
        if not deduped:
            deduped.append(ev)
        else:
            prev = deduped[-1]
            if abs(ev["idx"] - prev["idx"]) < 35:
                if ev["volume"] > prev["volume"]:
                    deduped[-1] = ev
            else:
                deduped.append(ev)

    for ev in deduped:
        ev.pop("idx", None)
        ev.pop("volume", None)
    return deduped


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    """Wilder RSI from smoothed averages. No losses gives 100, as TradingView ta.rsi and calcRSI in chart.js do."""
    if avg_loss <= 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def _rma(values: List[float], period: int) -> List[float]:
    """Wilder smoothing (TradingView ta.rma / ta.atr). Warm-up bars use the expanding mean."""
    out = [0.0] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        if i < period:
            total += v
            out[i] = total / (i + 1)
        else:
            out[i] = (out[i - 1] * (period - 1) + v) / period
    return out


def _calc_ema_series(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    k = 2.0 / (period + 1.0)
    ema = [values[0]]
    for i in range(1, len(values)):
        ema.append(values[i] * k + ema[-1] * (1.0 - k))
    return ema


def compute_cdc_actionzone(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes CDC ActionZone V3 2020 (by Uncle Chaloke) using EMA 12 and EMA 26.
    4-Color Status System:
    - Green (#22c55e): Bullish (EMA12 > EMA26) and Close > EMA12 (Strong Buy / Hold)
    - Blue (#38bdf8): Bullish (EMA12 > EMA26) and Close <= EMA12 (Pullback / Buy on Dip)
    - Orange (#f59e0b): Bearish (EMA12 < EMA26) and Close > EMA12 (Bearish Rebound)
    - Red (#ef4444): Bearish (EMA12 < EMA26) and Close <= EMA12 (Strong Sell / Cash)
    """
    if not candles or len(candles) < 2:
        return {
            "status": "NEUTRAL",
            "zone": "neutral",
            "zone_th": "ข้อมูลไม่เพียงพอ",
            "badge_color": "#94a3b8",
            "signal": None,
            "fast_ema12": 0.0,
            "slow_ema26": 0.0,
            "candle_colors": []
        }

    closes = [float(c["close"]) for c in candles]
    ema12 = _calc_ema_series(closes, 12)
    ema26 = _calc_ema_series(closes, 26)

    candle_colors = []
    zones = []

    for i in range(len(candles)):
        c = candles[i]
        c_close = closes[i]
        e12 = ema12[i]
        e26 = ema26[i]

        is_bull = e12 > e26
        if is_bull:
            if c_close > e12:
                zone = "green"
                color = "#22c55e"
            else:
                zone = "blue"
                color = "#38bdf8"
        else:
            if c_close > e12:
                zone = "orange"
                color = "#f59e0b"
            else:
                zone = "red"
                color = "#ef4444"

        zones.append(zone)
        candle_colors.append({
            "time": c["time"],
            "color": color,
            "zone": zone,
            "ema12": round(e12, 2),
            "ema26": round(e26, 2)
        })

    last_zone = zones[-1]
    last_e12 = round(ema12[-1], 2)
    last_e26 = round(ema26[-1], 2)

    if last_zone == "green":
        status = "BULLISH"
        zone_th = "โซนเขียว (ถือรันเทรนด์ / Buy & Hold)"
        badge_color = "#22c55e"
    elif last_zone == "blue":
        status = "BULLISH_PULLBACK"
        zone_th = "โซนฟ้า (ย่อตัวในขาขึ้น / Buy on Dip)"
        badge_color = "#38bdf8"
    elif last_zone == "orange":
        status = "BEARISH_REBOUND"
        zone_th = "โซนส้ม (รีบาวด์ในขาลง / อย่าเพิ่งรับ)"
        badge_color = "#f59e0b"
    else:
        status = "BEARISH"
        zone_th = "โซนแดง (ถือเงินสด / Sell & Cash)"
        badge_color = "#ef4444"

    signal = None
    if len(zones) >= 2:
        prev_bull = ema12[-2] > ema26[-2]
        curr_bull = ema12[-1] > ema26[-1]
        if not prev_bull and curr_bull:
            signal = "BUY_GOLDEN_CROSS"
        elif prev_bull and not curr_bull:
            signal = "SELL_DEATH_CROSS"

    return {
        "status": status,
        "zone": last_zone,
        "zone_th": zone_th,
        "badge_color": badge_color,
        "signal": signal,
        "fast_ema12": last_e12,
        "slow_ema26": last_e26,
        "candle_colors": candle_colors
    }


def compute_luxalgo_support_resistance(
    candles: List[Dict[str, Any]],
    left_bars: int = 15,
    right_bars: int = 12,
    vol_thresh: float = 20.0
) -> Dict[str, Any]:
    """
    Computes Support and Resistance Levels with Breaks matching LuxAlgo TradingView script:
    1. Pivot High & Pivot Low (left_bars=15, right_bars=12).
    2. Volume Oscillator: 100 * (EMA(vol, 5) - EMA(vol, 10)) / EMA(vol, 10).
    3. Breaks & Wicks:
       - Breakout (Vol): Close crosses above resistance, not (open - low > close - open), osc > vol_thresh.
       - Breakdown (Vol): Close crosses below support, not (open - close < high - open), osc > vol_thresh.
       - Bull Wick: Close crosses above resistance, open - low > close - open (fakeout rejection).
       - Bear Wick: Close crosses below support, open - close < high - open (fakeout rejection).
    """
    if not candles or len(candles) < max(left_bars + right_bars + 1, 30):
        return {
            "resistance": None,
            "support": None,
            "volume_osc": 0.0,
            "recent_breaks": [],
            "current_signal": None,
            "summary": "ข้อมูลแท่งเทียนไม่เพียงพอ"
        }

    n = len(candles)
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    opens = [float(c["open"]) for c in candles]
    volumes = [float(c["volume"]) for c in candles]

    short_ema = _calc_ema_series(volumes, 5)
    long_ema = _calc_ema_series(volumes, 10)
    osc = [
        100.0 * (short_ema[i] - long_ema[i]) / max(1.0, long_ema[i])
        for i in range(n)
    ]

    pivot_high = [None] * n
    pivot_low = [None] * n

    for i in range(left_bars, n - right_bars):
        h = highs[i]
        if all(h >= highs[j] for j in range(i - left_bars, i + right_bars + 1) if j != i):
            pivot_high[i + right_bars] = h
        l = lows[i]
        if all(l <= lows[j] for j in range(i - left_bars, i + right_bars + 1) if j != i):
            pivot_low[i + right_bars] = l

    res_level = None
    sup_level = None
    res_history = [None] * n
    sup_history = [None] * n

    for i in range(n):
        if pivot_high[i] is not None:
            res_level = pivot_high[i]
        if pivot_low[i] is not None:
            sup_level = pivot_low[i]
        res_history[i] = res_level
        sup_history[i] = sup_level

    breaks = []
    start_check = max(1, n - 60)
    for i in range(start_check, n):
        cur_res = res_history[i - 1]
        cur_sup = sup_history[i - 1]
        if cur_res is None or cur_sup is None:
            continue
        o = opens[i]
        c = closes[i]
        h = highs[i]
        l = lows[i]
        t = candles[i]["time"]
        v_osc = round(osc[i], 1)

        # Bullish break / Wick
        if closes[i - 1] <= cur_res and c > cur_res:
            is_bull_wick = (o - l) > (c - o)
            if is_bull_wick:
                breaks.append({
                    "time": t, "type": "BULL_WICK", "price": h, "level": round(cur_res, 2),
                    "label": "⚠️ Bull Wick", "desc": f"แทงทะลุ ${cur_res:.2f} แต่โดนแรงขายกดกลับทิ้งไส้บน (Fakeout)"
                })
            elif v_osc > vol_thresh:
                breaks.append({
                    "time": t, "type": "BREAKOUT_VOL", "price": c, "level": round(cur_res, 2),
                    "label": "🟢 Breakout (Vol)", "desc": f"เบรกทะลุแนวต้าน ${cur_res:.2f} พร้อม Volume Surge +{v_osc}%"
                })

        # Bearish break / Wick
        if closes[i - 1] >= cur_sup and c < cur_sup:
            is_bear_wick = (o - c) < (h - o)
            if is_bear_wick:
                breaks.append({
                    "time": t, "type": "BEAR_WICK", "price": l, "level": round(cur_sup, 2),
                    "label": "⚠️ Bear Wick", "desc": f"หลุด ${cur_sup:.2f} แต่มีแรงซื้อดึงกลับทิ้งไส้ล่าง (Fakeout)"
                })
            elif v_osc > vol_thresh:
                breaks.append({
                    "time": t, "type": "BREAKDOWN_VOL", "price": c, "level": round(cur_sup, 2),
                    "label": "🔴 Breakdown (Vol)", "desc": f"หลุดแนวรับ ${cur_sup:.2f} พร้อม Volume Surge +{v_osc}%"
                })

    last_signal = breaks[-1] if breaks else None
    active_res = round(res_level, 2) if res_level else None
    active_sup = round(sup_level, 2) if sup_level else None
    current_osc = round(osc[-1], 1)

    summary_parts = []
    if active_res: summary_parts.append(f"แนวต้านสวิง LuxAlgo ${active_res:.2f}")
    if active_sup: summary_parts.append(f"แนวรับสวิง LuxAlgo ${active_sup:.2f}")
    if last_signal: summary_parts.append(f"สัญญาณล่าสุด: {last_signal['label']} ({last_signal['time']})")

    return {
        "resistance": active_res,
        "support": active_sup,
        "volume_osc": current_osc,
        "recent_breaks": breaks[-8:],
        "current_signal": last_signal,
        "summary": " • ".join(summary_parts) if summary_parts else "ไม่พบจุดสวิงที่มีนัยสำคัญ"
    }


def compute_smart_money_concepts(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes Smart Money Concepts (SMC) matching LuxAlgo TradingView script:
    1. Fair Value Gaps (FVG) with unmitigated status tracking (Demand / Supply zones).
    2. Order Blocks (OB): Last opposing candle before significant institutional displacement.
    3. Market Structure: CHoCH (Change of Character) & BOS (Break of Structure).
    """
    if not candles or len(candles) < 20:
        return {
            "unmitigated_fvgs": [],
            "order_blocks": [],
            "market_structure": "Neutral",
            "summary": "ข้อมูลแท่งเทียนไม่เพียงพอ"
        }

    n = len(candles)
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    opens = [float(c["open"]) for c in candles]

    # 1. Fair Value Gaps (FVG)
    unmit_bull = []
    unmit_bear = []
    for i in range(2, n):
        # Bullish FVG (Demand)
        if lows[i] > highs[i - 2]:
            bottom = highs[i - 2]
            top = lows[i]
            gap = round(top - bottom, 2)
            mitigated = any(lows[k] <= bottom for k in range(i + 1, n))
            if not mitigated:
                unmit_bull.append({
                    "time": candles[i]["time"],
                    "type": "BULLISH_FVG",
                    "bottom": round(bottom, 2),
                    "top": round(top, 2),
                    "gap": gap,
                    "label": f"🟢 FVG Demand ${bottom:.2f} - ${top:.2f}"
                })
        # Bearish FVG (Supply)
        elif highs[i] < lows[i - 2]:
            bottom = highs[i]
            top = lows[i - 2]
            gap = round(top - bottom, 2)
            mitigated = any(highs[k] >= top for k in range(i + 1, n))
            if not mitigated:
                unmit_bear.append({
                    "time": candles[i]["time"],
                    "type": "BEARISH_FVG",
                    "bottom": round(bottom, 2),
                    "top": round(top, 2),
                    "gap": gap,
                    "label": f"🔴 FVG Supply ${bottom:.2f} - ${top:.2f}"
                })

    # 2. Order Blocks (OB)
    order_blocks = []
    sample_diffs = [abs(closes[k] - closes[k - 1]) for k in range(1, min(60, n))]
    avg_candle_size = sum(sample_diffs) / len(sample_diffs) if sample_diffs else 1.0

    start_ob = max(1, n - 40)
    for i in range(start_ob, n):
        body = abs(closes[i] - opens[i])
        if body > avg_candle_size * 1.8:
            # Bullish displacement
            if closes[i] > opens[i] and closes[i - 1] <= opens[i - 1]:
                ob_bottom = lows[i - 1]
                ob_top = highs[i - 1]
                mitigated = any(lows[k] <= ob_bottom for k in range(i + 1, n))
                if not mitigated:
                    order_blocks.append({
                        "time": candles[i - 1]["time"],
                        "type": "BULLISH_OB",
                        "bottom": round(ob_bottom, 2),
                        "top": round(ob_top, 2),
                        "level": round((ob_bottom + ob_top) / 2.0, 2),
                        "label": f"🛡️ Demand Order Block ${ob_bottom:.2f} - ${ob_top:.2f}"
                    })
            # Bearish displacement
            elif closes[i] < opens[i] and closes[i - 1] >= opens[i - 1]:
                ob_bottom = lows[i - 1]
                ob_top = highs[i - 1]
                mitigated = any(highs[k] >= ob_top for k in range(i + 1, n))
                if not mitigated:
                    order_blocks.append({
                        "time": candles[i - 1]["time"],
                        "type": "BEARISH_OB",
                        "bottom": round(ob_bottom, 2),
                        "top": round(ob_top, 2),
                        "level": round((ob_bottom + ob_top) / 2.0, 2),
                        "label": f"🛑 Supply Order Block ${ob_bottom:.2f} - ${ob_top:.2f}"
                    })

    # 3. Market Structure (CHoCH / BOS)
    # A break needs a close beyond the latest confirmed swing (5 bars each side).
    # Merely trading near a 20-day low used to count as Bearish BOS, which flagged every dip.
    swing = 5
    pivot_high = pivot_low = None
    for i in range(n - 1 - swing, max(swing, n - 120) - 1, -1):
        if pivot_high is None and highs[i] == max(highs[i - swing:i + swing + 1]):
            pivot_high = highs[i]
        if pivot_low is None and lows[i] == min(lows[i - swing:i + swing + 1]):
            pivot_low = lows[i]
        if pivot_high is not None and pivot_low is not None:
            break
    current_p = closes[-1]
    if pivot_high is not None and current_p > pivot_high:
        ms, structure = "Bullish BOS (Break of Structure)", "BULLISH"
    elif pivot_low is not None and current_p < pivot_low:
        ms, structure = "Bearish BOS (Break of Structure)", "BEARISH"
    else:
        ms, structure = "Internal Consolidation", "NEUTRAL"

    demand_test = any(
        ob["type"] == "BULLISH_OB" and min(lows[-3:]) <= ob["top"] * 1.01 and current_p >= ob["bottom"]
        for ob in order_blocks
    )

    active_fvgs = (unmit_bull[-3:] + unmit_bear[-3:])
    active_obs = order_blocks[-4:]

    summary_parts = []
    if unmit_bull:
        latest_bf = unmit_bull[-1]
        summary_parts.append(f"มีโซนสะสม Demand FVG ที่ ${latest_bf['bottom']:.2f} - ${latest_bf['top']:.2f}")
    if unmit_bear:
        latest_sf = unmit_bear[-1]
        summary_parts.append(f"มีโซนขาย Supply FVG ที่ ${latest_sf['bottom']:.2f} - ${latest_sf['top']:.2f}")

    return {
        "unmitigated_fvgs": active_fvgs,
        "order_blocks": active_obs,
        "market_structure": ms,
        "structure": structure,
        "pivot_high": round(pivot_high, 2) if pivot_high is not None else None,
        "pivot_low": round(pivot_low, 2) if pivot_low is not None else None,
        "demand_test": demand_test,
        "summary": " • ".join(summary_parts) if summary_parts else "โครงสร้างสถาบันอยู่ในกรอบปกติ"
    }


def compute_squeeze_momentum(
    candles: List[Dict[str, Any]],
    bb_length: int = 20,
    bb_mult: float = 2.0,
    kc_length: int = 20,
    kc_mult: float = 1.5
) -> Dict[str, Any]:
    """
    Computes Squeeze Momentum Indicator [LazyBear] matching TradingView Pine Script:
    1. Bollinger Bands (20, 2.0).
    2. Keltner Channels (20, 1.5) with True Range.
    3. Squeeze state:
       - Squeeze ON: LowerBB > LowerKC and UpperBB < UpperKC (volatility compression)
       - Squeeze OFF / FIRED: LowerBB < LowerKC and UpperBB > UpperKC (volatility expansion)
       - No Squeeze: Normal
    4. Linear regression momentum histogram:
       val = linreg(close - avg((highest(high, 20) + lowest(low, 20))/2, sma(close, 20)), 20)
    """
    if not candles or len(candles) < 20:
        return {
            "status": "NO_SQUEEZE",
            "squeeze_on": False,
            "squeeze_fired": False,
            "momentum": 0.0,
            "direction": "NEUTRAL",
            "summary": "ข้อมูลไม่เพียงพอ",
            "histogram": []
        }

    n = len(candles)
    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    # Bollinger Bands
    sma_close = [0.0] * n
    std_close = [0.0] * n
    for i in range(n):
        start_idx = max(0, i - bb_length + 1)
        window = closes[start_idx : i + 1]
        m = sum(window) / len(window)
        sma_close[i] = m
        var = sum((x - m) ** 2 for x in window) / len(window)
        std_close[i] = math.sqrt(max(0.0, var))

    upper_bb = [sma_close[i] + bb_mult * std_close[i] for i in range(n)]
    lower_bb = [sma_close[i] - bb_mult * std_close[i] for i in range(n)]

    # True Range & Keltner Channels
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))

    sma_tr = [0.0] * n
    for i in range(n):
        start_idx = max(0, i - kc_length + 1)
        window = tr[start_idx : i + 1]
        sma_tr[i] = sum(window) / len(window)

    upper_kc = [sma_close[i] + kc_mult * sma_tr[i] for i in range(n)]
    lower_kc = [sma_close[i] - kc_mult * sma_tr[i] for i in range(n)]

    # Momentum delta series
    deltas = [0.0] * n
    for i in range(n):
        start_idx = max(0, i - kc_length + 1)
        hh = max(highs[start_idx : i + 1])
        ll = min(lows[start_idx : i + 1])
        avg_hhlc = (hh + ll) / 2.0
        mid = (avg_hhlc + sma_close[i]) / 2.0
        deltas[i] = closes[i] - mid

    mom_values = [0.0] * n
    hist_entries = []

    for i in range(n):
        L = min(kc_length, i + 1)
        if L < 3:
            val = deltas[i]
        else:
            w = deltas[i - L + 1 : i + 1]
            mean_y = sum(w) / L
            mean_x = (L - 1) / 2.0
            denom = L * (L * L - 1) / 12.0
            num = sum((j - mean_x) * w[j] for j in range(L))
            slope = num / denom if denom > 0 else 0.0
            val = mean_y + slope * mean_x

        mom_values[i] = round(val, 3)

        # Squeeze state
        sqz_on = (lower_bb[i] > lower_kc[i]) and (upper_bb[i] < upper_kc[i])
        sqz_off = (lower_bb[i] < lower_kc[i]) and (upper_bb[i] > upper_kc[i])

        # Colors
        prev_val = mom_values[i - 1] if i > 0 else val
        if val > 0:
            bcolor = "#10b981" if val >= prev_val else "#047857"
        else:
            bcolor = "#f43f5e" if val <= prev_val else "#881337"

        dot_color = "#f97316" if sqz_on else ("#10b981" if sqz_off else "#38bdf8")

        hist_entries.append({
            "time": candles[i]["time"],
            "value": mom_values[i],
            "color": bcolor,
            "sqz_on": sqz_on,
            "sqz_off": sqz_off,
            "dot_color": dot_color
        })

    latest = hist_entries[-1]
    prev = hist_entries[-2] if len(hist_entries) >= 2 else latest
    is_sqz_on = latest["sqz_on"]
    is_sqz_fired = (not latest["sqz_on"]) and prev["sqz_on"]

    if is_sqz_on:
        status = "SQUEEZE_ON"
        summary = "เกิดสภาวะ Squeeze ON ความผันผวนบีบอัดแคบ กำลังสะสมพลังรอระเบิดทิศทาง"
    elif is_sqz_fired:
        status = "SQUEEZE_FIRED"
        summary = f"เกิดสัญญาณ Squeeze Fired ระเบิดกรอบความผันผวน ({'ขาขึ้นรุนแรง 🟢' if latest['value'] > 0 else 'ขาลงรุนแรง ⚠️'})"
    else:
        status = "NORMAL"
        summary = f"สภาวะปกติ โมเมนตัมเอียงไปทาง {'ฝั่งซื้อ' if latest['value'] > 0 else 'ฝั่งขาย'}"

    return {
        "status": status,
        "squeeze_on": is_sqz_on,
        "squeeze_fired": is_sqz_fired,
        "momentum": latest["value"],
        "direction": "BULLISH" if latest["value"] > 0 else "BEARISH",
        "summary": summary,
        "histogram": hist_entries[-120:]
    }


# Note: WAE, VFI, WaveTrend, and UT Bot were removed because they showed
# no predictive edge in backtesting (see data/backtest_scoring.json).


def compute_chandelier_exit(
    candles: List[Dict[str, Any]],
    length: int = 22,
    mult: float = 3.0
) -> Dict[str, Any]:
    """
    Computes Chandelier Exit [everget]:
    Volatility-based trailing stop-loss indicator.
    """
    if not candles or len(candles) < 25:
        return {
            "status": "NEUTRAL",
            "direction": "NEUTRAL",
            "trailing_stop": 0.0,
            "long_stop": 0.0,
            "short_stop": 0.0,
            "buy_signal": False,
            "sell_signal": False,
            "summary": "ข้อมูลไม่เพียงพอ",
            "series": []
        }

    n = len(candles)
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]

    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))

    atr = _rma(tr, length)

    long_stops = [0.0] * n
    short_stops = [0.0] * n
    dirs = [1] * n
    series_data = []

    for i in range(n):
        start_idx = max(0, i - length + 1)
        highest_close = max(closes[start_idx : i + 1])
        lowest_close = min(closes[start_idx : i + 1])
        band = mult * atr[i]

        curr_long_stop = highest_close - band
        curr_short_stop = lowest_close + band

        if i == 0:
            long_stops[i] = curr_long_stop
            short_stops[i] = curr_short_stop
            dirs[i] = 1
        else:
            prev_long = long_stops[i - 1]
            prev_short = short_stops[i - 1]
            prev_c = closes[i - 1]

            if prev_c > prev_long:
                long_stops[i] = max(curr_long_stop, prev_long)
            else:
                long_stops[i] = curr_long_stop

            if prev_c < prev_short:
                short_stops[i] = min(curr_short_stop, prev_short)
            else:
                short_stops[i] = curr_short_stop

            if closes[i] > prev_short:
                dirs[i] = 1
            elif closes[i] < prev_long:
                dirs[i] = -1
            else:
                dirs[i] = dirs[i - 1]

        long_stops[i] = round(long_stops[i], 2)
        short_stops[i] = round(short_stops[i], 2)
        active_stop = long_stops[i] if dirs[i] == 1 else short_stops[i]

        buy_sig = (i > 0 and dirs[i] == 1 and dirs[i - 1] == -1)
        sell_sig = (i > 0 and dirs[i] == -1 and dirs[i - 1] == 1)

        series_data.append({
            "time": candles[i]["time"],
            "stop": active_stop,
            "dir": dirs[i],
            "buy": buy_sig,
            "sell": sell_sig
        })

    last_dir = dirs[-1]
    last_long = long_stops[-1]
    last_short = short_stops[-1]
    last_active = last_long if last_dir == 1 else last_short
    last_buy = series_data[-1]["buy"]
    last_sell = series_data[-1]["sell"]

    if last_buy:
        status = "BUY_SIGNAL"
        summary = f"เกิดสัญญาณซื้อ Chandelier Exit! ทะลุกรอบต้าน เริ่มต้นรอบ Long มีแนว Trailing Stop ที่ ${last_long:.2f}"
    elif last_sell:
        status = "SELL_SIGNAL"
        summary = f"เกิดสัญญาณขาย Chandelier Exit! หลุดแนว Trailing Stop ที่ ${last_long:.2f}"
    elif last_dir == 1:
        status = "LONG"
        summary = f"แนวโน้มหลักถือรันเทรนด์ (LONG) ราคายืนเหนือ Chandelier Trailing Stop (${last_long:.2f})"
    else:
        status = "SHORT"
        summary = f"แนวโน้มชะลอตัว (SHORT/CASH) ราคาอยู่ใต้แนวต้าน Chandelier Stop (${last_short:.2f})"

    return {
        "status": status,
        "direction": "LONG" if last_dir == 1 else "SHORT",
        "trailing_stop": last_active,
        "long_stop": last_long,
        "short_stop": last_short,
        "buy_signal": last_buy,
        "sell_signal": last_sell,
        "summary": summary,
        "series": series_data[-120:]
    }


# Note: Hull Suite and Lorentzian Classification were removed because
# they showed no predictive edge or were redundant with EMA in backtesting.


SUPER_INVESTORS_DATA: Dict[str, List[Dict[str, Any]]] = {
    "LLY": [
        {
            "name": "Stanley Druckenmiller",
            "fund": "Duquesne Family Office",
            "icon": "🦅",
            "shares_str": "650,000 หุ้น ($680M)",
            "action": "TOP 5 HOLDING",
            "action_color": "#38bdf8",
            "summary": "ถือเป็น 1 ใน 5 อันดับแรกของพอร์ต มองเป็นหุ้นเทคโนโลยีชีวภาพที่มี Growth สูงจากยาลดความอ้วน GLP-1"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "1.2M หุ้น ($1.42B)",
            "action": "BUY (+18%)",
            "action_color": "#10b981",
            "summary": "กองทุน Quant Hedge Fund อันดับ 1 ของโลก เพิ่มน้ำหนักการลงทุนอย่างต่อเนื่อง"
        },
        {
            "name": "Ray Dalio",
            "fund": "Bridgewater Associates",
            "icon": "🌊",
            "shares_str": "260,000 หุ้น ($310M)",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองในพอร์ต All-Weather มองกลุ่มสุขภาพขนาดใหญ่เป็นสินทรัพย์ต้านทานวัฏจักรเศรษฐกิจ"
        },
        {
            "name": "Vanguard & BlackRock",
            "fund": "Institutional Giants",
            "icon": "🐋",
            "shares_str": "สัดส่วนรวม 15.6% ($18.5B)",
            "action": "CORE ACCUMULATE",
            "action_color": "#818cf8",
            "summary": "ผู้ถือหุ้นสถาบันรายใหญ่ที่สุด มีเม็ดเงินไหลเข้าสม่ำเสมอผ่านกองทุนดัชนี S&P 500 และ Healthcare ETFs"
        }
    ],
    "NVDA": [
        {
            "name": "Stanley Druckenmiller",
            "fund": "Duquesne Family Office",
            "icon": "🦅",
            "shares_str": "$820M (ต้นทุนต่ำ)",
            "action": "TRIM PROFIT",
            "action_color": "#facc15",
            "summary": "เข้าซื้อตั้งแต่ยุคแรกและทำกำไรมหาศาล ปัจจุบันคงสถานะแกนนำ AI Hardware แต่ทยอยแบ่งขายล็อกกำไร"
        },
        {
            "name": "Nancy Pelosi",
            "fund": "US Congress Disclosures",
            "icon": "🏛️",
            "shares_str": "Call Options $5M+",
            "action": "BULLISH CALLS",
            "action_color": "#10b981",
            "summary": "อดีตประธานสภาผู้แทนฯ สหรัฐ เข้าซื้อสัญญาสิทธิซื้อหุ้น (Call Options) ล่วงหน้าตามรอบการเติบโตของเซมิคอนดักเตอร์"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$3.2B (Top Holding)",
            "action": "ACTIVE ACCUMULATE",
            "action_color": "#10b981",
            "summary": "ถือครองในฐานะหัวใจหลักของสภาพคล่องและโมเมนตัมตลาดหุ้นเทคโนโลยีสหรัฐ"
        },
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$450M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองเกาะกระแสความต้องการชิป Blackwell และการขยายดาต้าเซ็นเตอร์ของกลุ่ม Hyperscalers"
        }
    ],
    "AAPL": [
        {
            "name": "Warren Buffett",
            "fund": "Berkshire Hathaway",
            "icon": "🎩",
            "shares_str": "300M หุ้น (~$70B)",
            "action": "CORE ANCHOR (28%)",
            "action_color": "#38bdf8",
            "summary": "หุ้นอันดับ 1 ในพอร์ตลงทุนของบัฟเฟตต์ มองว่าเป็นสินค้าอุปโภคบริโภคระดับพรีเมียมที่มี Brand Loyalty และ Ecosystem แข็งแกร่งที่สุดในโลก"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$2.1B",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองสินทรัพย์สภาพคล่องสูงเพื่อเป็นแกนค้ำประกันพอร์ตฟอลิโอ"
        },
        {
            "name": "Ray Dalio",
            "fund": "Bridgewater Associates",
            "icon": "🌊",
            "shares_str": "$480M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "มอง Apple เป็นหุ้น Cash Cow ที่มีกระแสเงินสดอิสระมหาศาลและการซื้อหุ้นคืนสม่ำเสมอ"
        }
    ],
    "MSFT": [
        {
            "name": "Bill Gates",
            "fund": "Gates Foundation Trust",
            "icon": "💻",
            "shares_str": "$14.8B (33% ของพอร์ต)",
            "action": "FOUNDATION CORE",
            "action_color": "#38bdf8",
            "summary": "สัดส่วนการถือครองหลักของมูลนิธิบิลและเมลินดา เกตส์ ขับเคลื่อนด้วยเงินปันผลและการเติบโตของ Azure"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$2.8B",
            "action": "BUY (+12%)",
            "action_color": "#10b981",
            "summary": "เพิ่มสัดส่วนรับการนำ Generative AI เข้าไปผสานใน Microsoft 365 Copilot และบริการคลาวด์"
        },
        {
            "name": "Stanley Druckenmiller",
            "fund": "Duquesne Family Office",
            "icon": "🦅",
            "shares_str": "$520M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "เชื่อมั่นในความเป็นผู้นำด้านแพลตฟอร์มซอฟต์แวร์ระดับองค์กร"
        }
    ],
    "AMZN": [
        {
            "name": "Warren Buffett",
            "fund": "Berkshire Hathaway",
            "icon": "🎩",
            "shares_str": "10,000,000 หุ้น ($1.9B)",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองระยะยาวในฐานะผู้นำโครงสร้างพื้นฐานคลาวด์ระดับโลก (AWS) และอีคอมเมิร์ซ"
        },
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$950M (Top 3 Holdings)",
            "action": "CONVICTION BUY",
            "action_color": "#10b981",
            "summary": "เป็นหนึ่งในหุ้นที่เดวิด เทปเปอร์ มั่นใจสูงสุด โดยมองว่าอัตรากำไรจากการดำเนินงานของ AWS กำลังขยายตัว"
        },
        {
            "name": "Chase Coleman",
            "fund": "Tiger Global",
            "icon": "🐯",
            "shares_str": "$1.2B",
            "action": "CORE POSITION",
            "action_color": "#38bdf8",
            "summary": "หุ้นหลักกลุ่ม Consumer Tech และ AI Infrastructure"
        }
    ],
    "GOOGL": [
        {
            "name": "Bill Ackman",
            "fund": "Pershing Square",
            "icon": "💼",
            "shares_str": "$2.1B (18% ของพอร์ต)",
            "action": "TOP CONVICTION",
            "action_color": "#10b981",
            "summary": "เข้าซื้อก้อนใหญ่ช่วงตลาดกังวลเรื่อง AI แย่ง Search มองว่าคูเมือง (Moat) ของ Search และ YouTube ยังไร้คู่แข่ง"
        },
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$880M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ชอบความแข็งแกร่งของงบการเงินและศักยภาพของ Google Cloud"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$2.2B",
            "action": "BUY",
            "action_color": "#10b981",
            "summary": "เพิ่มสถานะเพื่อเกาะกระแสการเติบโตของโมเดล Gemini และฮาร์ดแวร์ TPU"
        }
    ],
    "PLTR": [
        {
            "name": "Peter Thiel",
            "fund": "Founders Fund / Strategic Whale",
            "icon": "⚡",
            "shares_str": "110M หุ้น (ผู้ร่วมก่อตั้ง)",
            "action": "CO-FOUNDER ANCHOR",
            "action_color": "#38bdf8",
            "summary": "เสาหลักแห่ง Silicon Valley ผู้ร่วมก่อตั้ง Palantir และมีวิสัยทัศน์ด้านซอฟต์แวร์ความมั่นคงระดับชาติ"
        },
        {
            "name": "Cathie Wood",
            "fund": "ARK Invest",
            "icon": "🚀",
            "shares_str": "ถือใน ARKK & ARKW",
            "action": "HIGH CONVICTION",
            "action_color": "#10b981",
            "summary": "มอง AIP (Artificial Intelligence Platform) เป็นซอฟต์แวร์ระดับปฏิวัติอุตสาหกรรมองค์กรเอกชนและกองทัพ"
        },
        {
            "name": "Nancy Pelosi",
            "fund": "US Congress Disclosures",
            "icon": "🏛️",
            "shares_str": "รายงานการถือครอง",
            "action": "DISCLOSED POSITION",
            "action_color": "#818cf8",
            "summary": "มีรายงานการซื้อขายหุ้นเทคโนโลยีความมั่นคงและการป้องกันประเทศในสภาคองเกรส"
        }
    ],
    "CRWD": [
        {
            "name": "Cathie Wood",
            "fund": "ARK Invest",
            "icon": "🚀",
            "shares_str": "เพิ่ม 450,000 หุ้น",
            "action": "DIP BUYER",
            "action_color": "#10b981",
            "summary": "เข้าช้อนซื้อทันทีช่วงราคาดิ่งจากเหตุการณ์ Windows Outage มองคูเมืองของแพลตฟอร์ม Falcon ยังยากจะหาใครแทน"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$420M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองในฐานะผู้นำตลาด Endpoint Security และ Cloud Workload Protection"
        }
    ],
    "ISRG": [
        {
            "name": "Terry Smith",
            "fund": "Fundsmith",
            "icon": "🇬🇧",
            "shares_str": "Top 10 Holding",
            "action": "LONG COMPOUNDER",
            "action_color": "#38bdf8",
            "summary": "วอร์เรน บัฟเฟตต์ แห่งเกาะอังกฤษ เลือกลงทุนใน Intuitive Surgical จากโมเดลธุรกิจขายใบมีดและอุปกรณ์ผ่าตัดสิ้นเปลือง (Razor-and-Blade)"
        },
        {
            "name": "Vanguard & BlackRock",
            "fund": "Institutional Whales",
            "icon": "🐋",
            "shares_str": "รวมกว่า 16.5%",
            "action": "PASSIVE ACCUMULATE",
            "action_color": "#818cf8",
            "summary": "ถือครองระยะยาวในฐานะผู้นำหุ่นยนต์ผ่าตัด Da Vinci ที่มีการใช้งานเพิ่มขึ้นทั่วโลก"
        }
    ],
    "BAC": [
        {
            "name": "Warren Buffett",
            "fund": "Berkshire Hathaway",
            "icon": "🎩",
            "shares_str": "> 10% ของบริษัท",
            "action": "FAVORITE BANK",
            "action_color": "#38bdf8",
            "summary": "ธนาคารพาณิชย์ที่บัฟเฟตต์ชื่นชมและถือครองยาวนานที่สุด ให้ความไว้วางใจในการบริหารของ Brian Moynihan"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$850M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ถือครองรับประโยชน์จากโครงสร้างอัตราดอกเบี้ยและค่าธรรมเนียมวาณิชธนกิจ"
        }
    ],
    "C": [
        {
            "name": "Warren Buffett",
            "fund": "Berkshire Hathaway",
            "icon": "🎩",
            "shares_str": "55M หุ้น (~$3.2B)",
            "action": "TURNAROUND BET",
            "action_color": "#38bdf8",
            "summary": "เข้าซื้อช่วงราคาเทรดต่ำกว่ามูลค่าทางบัญชี (Price-to-Book < 1.0) ดักการฟื้นตัวจากการปรับโครงสร้างของ Jane Fraser"
        },
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$320M",
            "action": "VALUE HOLD",
            "action_color": "#10b981",
            "summary": "หุ้นกลุ่มการเงินสาย Deep Value ที่มีอัปไซด์สูงเมื่อเศรษฐกิจฟื้นตัว"
        }
    ],
    "JPM": [
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$850M",
            "action": "LONG CONVICTION",
            "action_color": "#38bdf8",
            "summary": "ธนาคารที่ทรงอิทธิพลและมีงบดุลแข็งแกร่งที่สุดในสหรัฐ (Fortress Balance Sheet)"
        },
        {
            "name": "Vanguard & BlackRock",
            "fund": "Institutional Giants",
            "icon": "🐋",
            "shares_str": "รวม 22%",
            "action": "CORE FINANCIAL",
            "action_color": "#818cf8",
            "summary": "แกนหลักของกลุ่มการเงินในทุกพอร์ตฟอลิโอสถาบัน"
        }
    ],
    "VRT": [
        {
            "name": "Stanley Druckenmiller",
            "fund": "Duquesne Family Office",
            "icon": "🦅",
            "shares_str": "ถือครองสัดส่วนสำคัญ",
            "action": "AI INFRASTRUCTURE",
            "action_color": "#10b981",
            "summary": "เลือกลงทุนใน Vertiv เพื่อเกาะกระแสระบบระบายความร้อนดาต้าเซ็นเตอร์ด้วยของเหลว (Liquid Cooling) ที่ชิป AI รุ่นใหม่จำเป็นต้องใช้"
        },
        {
            "name": "Chase Coleman",
            "fund": "Tiger Global",
            "icon": "🐯",
            "shares_str": "$650M",
            "action": "BUY (+25%)",
            "action_color": "#10b981",
            "summary": "หนึ่งในหุ้นโครงสร้างพื้นฐาน AI ที่สร้างผลตอบแทนโดดเด่นที่สุดในพอร์ต"
        }
    ],
    "NOW": [
        {
            "name": "Chase Coleman",
            "fund": "Tiger Global",
            "icon": "🐯",
            "shares_str": "$1.1B (Top SaaS)",
            "action": "TOP 5 HOLDING",
            "action_color": "#38bdf8",
            "summary": "หุ้น Enterprise Software อันดับ 1 ของพอร์ต มีอัตราการต่อสัญญาและขยายการใช้งานสูงเป็นพิเศษ"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$780M",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "ผู้ให้บริการระบบดิจิทัลเวิร์กโฟลว์แก่องค์กรขนาดใหญ่ระดับ Fortune 500"
        }
    ],
    "ARM": [
        {
            "name": "Masayoshi Son",
            "fund": "SoftBank Group",
            "icon": "📱",
            "shares_str": "90% ของทั้งบริษัท",
            "action": "MAJORITY OWNER",
            "action_color": "#a78bfa",
            "summary": "วาฬยักษ์ใหญ่ตัวจริง ถือครอง 90% ของบริษัท คุมสถาปัตยกรรมชิปสมาร์ทโฟน 99% ของโลกและกำลังขยายเข้าสู่ดาต้าเซ็นเตอร์"
        },
        {
            "name": "Cathie Wood",
            "fund": "ARK Invest",
            "icon": "🚀",
            "shares_str": "ถือใน ARKW & ARKQ",
            "action": "EDGE AI BET",
            "action_color": "#10b981",
            "summary": "มองว่าการประมวลผล AI บนสมาร์ทโฟนและอุปกรณ์พกพาจำเป็นต้องใช้สถาปัตยกรรมประหยัดพลังงานของ Arm"
        }
    ],
    "MU": [
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$620M",
            "action": "CYCLICAL LEADER",
            "action_color": "#10b981",
            "summary": "เดิมพันรอบวัฏจักรชิปหน่วยความจำ HBM (High Bandwidth Memory) ที่กำลังขาดแคลนในตลาด AI"
        },
        {
            "name": "Stanley Druckenmiller",
            "fund": "Duquesne Family Office",
            "icon": "🦅",
            "shares_str": "ถือครองตามรอบวัฏจักร",
            "action": "MEMORY SUPERCYCLE",
            "action_color": "#38bdf8",
            "summary": "เล่นรอบการฟื้นตัวของราคาชิป DRAM และ NAND"
        }
    ],
    "VST": [
        {
            "name": "David Tepper",
            "fund": "Appaloosa Management",
            "icon": "🐎",
            "shares_str": "$480M",
            "action": "AI POWER PLAY",
            "action_color": "#10b981",
            "summary": "ลงทุนใน Vistra เพื่อรับประโยชน์จากความต้องการพลังงานไฟฟ้ามหาศาลของดาต้าเซ็นเตอร์ AI และโรงไฟฟ้านิวเคลียร์"
        },
        {
            "name": "Dan Loeb",
            "fund": "Third Point",
            "icon": "⚡",
            "shares_str": "Top 10 Holding",
            "action": "NUCLEAR CONVICTION",
            "action_color": "#10b981",
            "summary": "มองการทำสัญญาขายไฟฟ้าระยะยาวกับบริษัทเทคโนโลยียักษ์ใหญ่เป็นแหล่งสร้างกระแสเงินสดที่เติบโตสูง"
        }
    ],
    "APP": [
        {
            "name": "Steve Cohen",
            "fund": "Point72 Asset Management",
            "icon": "🎯",
            "shares_str": "ถือครองสัดส่วนหลัก",
            "action": "AI ADVERTISING",
            "action_color": "#10b981",
            "summary": "ได้รับแรงขับเคลื่อนจากโมเดล AI AXON 2.0 ในการจับคู่โฆษณาเกมและอีคอมเมิร์ซที่สร้างรายได้โตระเบิด"
        },
        {
            "name": "Ken Griffin",
            "fund": "Citadel Advisors",
            "icon": "🏰",
            "shares_str": "$350M",
            "action": "BUY",
            "action_color": "#10b981",
            "summary": "หนึ่งในหุ้นซอฟต์แวร์ที่ทำผลงานราคาพุ่งแรงที่สุดแห่งปี"
        }
    ],
    "ABNB": [
        {
            "name": "Chase Coleman",
            "fund": "Tiger Global",
            "icon": "🐯",
            "shares_str": "$580M",
            "action": "TRAVEL COMPOUNDER",
            "action_color": "#38bdf8",
            "summary": "แพลตฟอร์มที่พักระดับโลกที่ไร้ต้นทุนสินทรัพย์ (Asset-Light) และมีกระแสเงินสดอิสระสูง"
        },
        {
            "name": "Baillie Gifford",
            "fund": "Scottish Mortgage",
            "icon": "🏰",
            "shares_str": "ถือครองระยะยาว",
            "action": "HOLD",
            "action_color": "#38bdf8",
            "summary": "เชื่อมั่นในการขยายตัวของเทรนด์การทำงานทางไกลและการท่องเที่ยวระยะยาว"
        }
    ],
    "MNST": [
        {
            "name": "Warren Buffett",
            "fund": "Berkshire Hathaway (via Coca-Cola)",
            "icon": "🎩",
            "shares_str": "พันธมิตรโคคา-โคล่า (19.5%)",
            "action": "BEVERAGE MOAT",
            "action_color": "#38bdf8",
            "summary": "ได้รับประโยชน์จากเครือข่ายกระจายสินค้าทั่วโลกของ Coca-Cola และมีอัตรากำไรขั้นต้นสูงกว่า 50%"
        },
        {
            "name": "Vanguard & BlackRock",
            "fund": "Institutional Whales",
            "icon": "🐋",
            "shares_str": "รวม 17.5%",
            "action": "DEFENSIVE COMPOUND",
            "action_color": "#818cf8",
            "summary": "หุ้นเครื่องดื่มชูกำลังที่มีสถิติผลตอบแทนทบต้นชนะตลาดมาอย่างต่อเนื่อง"
        }
    ],
}


SUPER_INVESTORS_AS_OF = "ข้อมูลรวบรวมเอง ยังไม่ได้ยืนยันกับ SEC 13F ล่าสุด ใช้เป็นข้อมูลอ้างอิงเท่านั้น"


def get_super_investors(ticker: str) -> List[Dict[str, Any]]:
    """
    Returns curated super investors, famous billionaires, and notable whales holding the stock.
    """
    return [{**w, "as_of": SUPER_INVESTORS_AS_OF} for w in _curated_super_investors(ticker)]


def _curated_super_investors(ticker: str) -> List[Dict[str, Any]]:
    if ticker in SUPER_INVESTORS_DATA:
        return SUPER_INVESTORS_DATA[ticker]

    return [
        {
            "name": "Vanguard Group",
            "fund": "Passive & Index Whales",
            "icon": "🐋",
            "shares_str": "ผู้ถือหุ้นสถาบันรายใหญ่ (~8-10%)",
            "action": "PASSIVE HOLD",
            "action_color": "#38bdf8",
            "summary": f"ถือครองหุ้น {ticker} ผ่านกองทุนดัชนีชั้นนำระดับโลกและ ETF อิงดัชนี"
        },
        {
            "name": "BlackRock (iShares)",
            "fund": "Institutional Asset Management",
            "icon": "🏰",
            "shares_str": "ผู้ถือหุ้นสถาบันรายใหญ่ (~6-8%)",
            "action": "INDEX FLOW",
            "action_color": "#818cf8",
            "summary": f"ผู้จัดการกองทุนที่ใหญ่ที่สุดในโลก ถือครองหุ้น {ticker} เป็นสินทรัพย์อ้างอิงของสถาบันทั่วโลก"
        },
        {
            "name": "State Street Global Advisors",
            "fund": "SPDR ETF Whales",
            "icon": "🌐",
            "shares_str": "สถาบันชั้นนำ (~4-5%)",
            "action": "ACCUMULATE",
            "action_color": "#10b981",
            "summary": f"ถือครองกระจายความเสี่ยงเพื่อสะท้อนผลการดำเนินงานของกลุ่มอุตสาหกรรมในตลาดหุ้นสหรัฐ"
        }
    ]


def _lookup_cached_stock_score(ticker: str) -> Optional[Dict[str, Any]]:
    if not ticker:
        return None
    ticker_clean = ticker.strip().upper()
    try:
        data_dir = Path(os.environ.get("FILTER_STOCK_DATA_DIR") or (Path(__file__).resolve().parent.parent / "data"))
        p = data_dir / "account_summary.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            for pos in data.get("positions", []):
                if pos.get("ticker") == ticker_clean:
                    sc = pos.get("stock_score")
                    if isinstance(sc, dict) and "grade" in sc:
                        return sc
                    if pos.get("grade"):
                        return {
                            "grade": pos["grade"],
                            "stars": STARS_BY_GRADE.get(pos["grade"], 1),
                            "total": None,
                            "reasons": [],
                            "timing": {"entry_signal": False},
                            "earnings_guard": False,
                        }
    except Exception:
        pass
    return None


def _lookup_cached_fundamental(ticker: str) -> Optional[FundamentalScore]:
    if not ticker:
        return None
    ticker_clean = ticker.strip().upper()
    try:
        data_dir = Path(os.environ.get("FILTER_STOCK_DATA_DIR") or (Path(__file__).resolve().parent.parent / "data"))
        p = data_dir / "financials_cache.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            entry = data.get(ticker_clean, {})
            quarters = entry.get("quarters", [])
            if quarters:
                latest = quarters[-1]
                rev_g = latest.get("rev_growth_yoy")
                net_g = latest.get("net_income_growth_yoy")
                roe = latest.get("roe")
                de = latest.get("debt_to_equity")
                fcf_v = latest.get("fcf")
                return score_fundamentals(ticker_clean, None, rev_g, net_g, roe, None, de, fcf_v)
    except Exception:
        pass
    return None


def compute_ai_confluence_signals(
    candles: List[Dict[str, Any]],
    fibo_levels: Dict[str, float],
    pattern: Optional[Dict[str, Any]],
    poc_price: float,
    current_st_trend: str,
    current_rsi: float,
    current_macd_hist: float,
    atr_val: float,
    cdc_zone: Optional[str] = None,
    elliott_wave: Optional[Dict[str, Any]] = None,
    pivots: Optional[Dict[str, Any]] = None,
    luxalgo_sr: Optional[Dict[str, Any]] = None,
    smc: Optional[Dict[str, Any]] = None,
    squeeze_mom: Optional[Dict[str, Any]] = None,
    chandelier_exit: Optional[Dict[str, Any]] = None,
    ticker: Optional[str] = None,
    days_to_earnings: Optional[float] = None,
    is_etf: bool = False,
    stock_score: Optional[Dict[str, Any]] = None,
    fundamental: Optional[FundamentalScore] = None,
) -> List[Dict[str, Any]]:
    """
    Multi-Technical Confluence Decision Engine.
    Evaluates Trend, Momentum, Value/Fibo, and Technical Confluence.
    Action and score derive strictly from the unified scoring system (EMA200 zone + fundamentals),
    with RSI Hook serving as entry trigger, while unbacked indicators are informational.
    """
    if not candles or len(candles) < 20:
        return []

    n = len(candles)
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    times = [c["time"] for c in candles]

    # Pre-calculate rolling 20D average volume
    vol20_avg = [volumes[0]] * n
    for i in range(19, n):
        vol20_avg[i] = sum(volumes[i - 19 : i + 1]) / 20.0

    # Pre-calculate EMA 50 & 200
    ema50_vals = [closes[0]] * n
    k50 = 2.0 / 51.0
    for i in range(1, n):
        ema50_vals[i] = closes[i] * k50 + ema50_vals[i - 1] * (1 - k50)

    ema200_vals = [closes[0]] * n
    k200 = 2.0 / 201.0
    for i in range(1, n):
        ema200_vals[i] = closes[i] * k200 + ema200_vals[i - 1] * (1 - k200)

    # Pre-calculate RSI 14
    rsi_vals = [50.0] * n
    gains, losses = [], []
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains.append(max(0.0, diff))
        losses.append(max(0.0, -diff))
    if len(gains) >= 14:
        avg_g = sum(gains[:14]) / 14.0
        avg_l = sum(losses[:14]) / 14.0
        rsi_vals[14] = _rsi_value(avg_g, avg_l)
        for i in range(15, n):
            avg_g = (avg_g * 13.0 + gains[i - 1]) / 14.0
            avg_l = (avg_l * 13.0 + losses[i - 1]) / 14.0
            rsi_vals[i] = _rsi_value(avg_g, avg_l)

    curr_close = closes[-1]
    curr_low = lows[-1]
    curr_high = highs[-1]
    if current_rsi is None:
        current_rsi = rsi_vals[-1]

    # Calculate unified scoring metrics
    dist_ema200 = round(((curr_close - ema200_vals[-1]) / ema200_vals[-1]) * 100.0, 2) if ema200_vals[-1] > 0 else None
    rsi_prev_val = rsi_vals[-2] if len(rsi_vals) > 1 else None
    timing_score = score_timing(dist_ema200, current_rsi, rsi_prev_val)

    resolved_stock_score = stock_score
    if not resolved_stock_score:
        if fundamental is not None:
            resolved_stock_score = score_stock(fundamental, timing_score, days_to_earnings)
        elif is_etf or (ticker and ticker in ETF_TICKERS):
            etf_fund = score_fundamentals(ticker or "ETF", None, None, None, None, None, None, None)
            resolved_stock_score = score_stock(etf_fund, timing_score, days_to_earnings)
        elif ticker:
            cached_sc = _lookup_cached_stock_score(ticker)
            if cached_sc:
                resolved_stock_score = cached_sc
            else:
                cached_fund = _lookup_cached_fundamental(ticker)
                if cached_fund:
                    resolved_stock_score = score_stock(cached_fund, timing_score, days_to_earnings)
                else:
                    empty_fund = score_fundamentals(ticker, None, None, None, None, None, None, None)
                    resolved_stock_score = score_stock(empty_fund, timing_score, days_to_earnings)
        else:
            empty_fund = FundamentalScore(applicable=True, points=0.0, max_points=0, pct=None, coverage=0.0, grade="N/A", metrics={}, reasons=[])
            resolved_stock_score = score_stock(empty_fund, timing_score, days_to_earnings)

    grade = resolved_stock_score.get("grade", "N/A")
    curr_score = max(1, min(5, resolved_stock_score.get("stars", 1)))
    is_guard = bool(resolved_stock_score.get("earnings_guard")) or (days_to_earnings is not None and 0 <= days_to_earnings <= EARNINGS_GUARD_DAYS)

    signals = []
    scan_start = max(15, n - 220)  # scan past ~10-11 months

    # Historical markers must only see bars up to the swing (plus the k_window that confirms it).
    # Today's fibo grid, POC and pattern include later bars, so they are rebuilt or skipped per bar.
    def causal_fibo(i: int) -> Dict[str, float]:
        lo_i = max(0, i - 251)
        hi_v, lo_v = max(highs[lo_i:i + 1]), min(lows[lo_i:i + 1])
        rng = max(1e-6, hi_v - lo_v)
        return {"0.0": hi_v, "50.0": hi_v - 0.5 * rng, "61.8": hi_v - 0.618 * rng, "78.6": hi_v - 0.786 * rng}

    # 1. Detect Swing Troughs (RULE_ENTRY / RULE_DCA Signals)
    # A swing trough at bar i is confirmed at bar i + k_window (causal confirmation).
    # Heuristic markers: Only emitted if current grade is A+, A, or ETF.
    k_window = 3
    if grade in ("A+", "A", "ETF"):
        for i in range(scan_start, n - k_window):
            if all(lows[i] <= lows[i + j] for j in range(-k_window, k_window + 1) if j != 0):
                c_low = lows[i]
                confirm_idx = i + k_window
                c_close = closes[confirm_idx]
                v_avg = max(1.0, vol20_avg[confirm_idx])

                reasons = []
                score = 0
                fib_i = causal_fibo(confirm_idx)

                # Factor 1: Value / Fibonacci Golden Pocket
                f618 = fib_i["61.8"]
                f500 = fib_i["50.0"]
                if f618 > 0 and abs(c_low - f618) / f618 <= SWING_FIBO_TOLERANCE:
                    score += 1
                    reasons.append(f"โซนราคาคุณค่า: ทดสอบแนวรับ Fibonacci 61.8% Golden Pocket (${f618:.2f})")
                elif f500 > 0 and abs(c_low - f500) / f500 <= SWING_FIBO_TOLERANCE:
                    score += 1
                    reasons.append(f"โซนราคาคุณค่า: เด้งทดสอบแนวรับ Fibonacci 50.0% (${f500:.2f})")

                # Factor 2: Momentum / RSI Hook
                c_rsi = rsi_vals[confirm_idx]
                if c_rsi <= SWING_RSI_OVERSOLD:
                    score += 1
                    reasons.append(f"โมเมนตัมกลับตัว: RSI เข้าสู่โซน Oversold ({c_rsi:.1f}) พร้อมส่งสัญญาณ Bullish Hook")
                elif confirm_idx > 1 and rsi_vals[confirm_idx] > rsi_vals[confirm_idx - 1] and rsi_vals[confirm_idx - 1] <= SWING_RSI_HOOK_LOW:
                    score += 1
                    reasons.append(f"โมเมนตัมกลับตัว: RSI ดีดยกฐานกลับตัวจากโซนต่ำ ({c_rsi:.1f})")

                # Factor 3: Volume Confirmation
                vol_ratio = volumes[confirm_idx] / v_avg
                if vol_ratio >= SWING_VOL_RATIO_BUY:
                    score += 1
                    reasons.append(f"สภาพคล่องสถาบัน: ปริมาณการซื้อขายพุ่งสูง {vol_ratio:.1f}x ของค่าเฉลี่ย 20 วัน ยืนยันแรงซื้อดูดซับ")

                # Factor 4: Trend Alignment
                c_ema200 = ema200_vals[confirm_idx]
                c_ema50 = ema50_vals[confirm_idx]
                if c_close >= c_ema200:
                    score += 1
                    reasons.append(f"แนวโน้มระยะยาว: ราคายืนเหนือ EMA 200 (${c_ema200:.2f}) โครงสร้างหลักเป็นขาขึ้น")
                elif c_close >= c_ema50:
                    score += 1
                    reasons.append(f"แนวโน้มระยะกลาง: ราคายืนเหนือ EMA 50 (${c_ema50:.2f})")

                if score >= 3:
                    is_entry = score >= 4
                    sl = round(c_low * SWING_SL_RATIO_BUY, 2)
                    tp = round(c_close * SWING_TP_RATIO_BUY, 2)
                    rr = round((tp - c_close) / max(0.01, c_close - sl), 1)
                    sig_type = "RULE_ENTRY" if is_entry else "RULE_DCA"
                    act_txt = "จุดเข้าตามกฎ" if is_entry else "จุดสะสมตามกฎ"
                    badge_txt = f"💎 จุดเข้าตามกฎ ({score}/5) (ไม่ผ่าน backtest)" if is_entry else f"🔹 จุดสะสมตามกฎ ({score}/5) (ไม่ผ่าน backtest)"
                    signals.append({
                        "time": times[confirm_idx],
                        "price": round(c_close, 2),
                        "action": act_txt,
                        "type": sig_type,
                        "score": score,
                        "score_text": f"{score}/5 สัญญาณคอนฟลูเอนซ์ (ไม่ผ่าน backtest)",
                        "badge": badge_txt,
                        "summary": f"{act_txt}ยืนยันที่ราคา ${c_close:.2f} (ยืนยัน Swing Low ${c_low:.2f} ของวันที่ {times[i]}) สัญญาณคอนฟลูเอนซ์ระดับ {score}/5 (ไม่ผ่าน backtest)",
                        "reasons": reasons,
                        "stop_loss": sl,
                        "target": tp,
                        "rr": f"1:{rr}",
                        "marker_shape": "arrowUp" if is_entry else "circle",
                        "marker_color": "#10b981" if is_entry else "#38bdf8",
                    })

    # 2. Detect Swing Peaks (RULE_TP Signals)
    # A swing peak at bar i is confirmed at bar i + k_window (causal confirmation).
    for i in range(scan_start, n - k_window):
        if all(highs[i] >= highs[i + j] for j in range(-k_window, k_window + 1) if j != 0):
            c_high = highs[i]
            confirm_idx = i + k_window
            c_close = closes[confirm_idx]
            c_rsi = rsi_vals[confirm_idx]
            v_avg = max(1.0, vol20_avg[confirm_idx])

            reasons = []
            score = 0

            # Resistance: ATH / Fibo 0.0% / 23.6%
            ath_p = causal_fibo(confirm_idx)["0.0"]
            if ath_p > 0 and abs(c_high - ath_p) / ath_p <= 0.03:
                score += 1
                reasons.append(f"แนวต้านสำคัญ: ยืนยันจุดสูงสุดรอบ 52 สัปดาห์ (${ath_p:.2f})")

            # Momentum: Overbought
            if c_rsi >= SWING_RSI_OVERBOUGHT:
                score += 1
                reasons.append(f"โมเมนตัมตึงตัว: RSI แตะระดับ Overbought ร้อนแรง ({c_rsi:.1f}) เสี่ยงพักฐาน")

            # Volume Churn / Spike at top
            if volumes[confirm_idx] / v_avg >= SWING_VOL_RATIO_SELL:
                score += 1
                reasons.append("สภาพคล่องเทขาย: วอลุ่มพุ่งสูง สะท้อนการขายทำกำไรของรายใหญ่ (Distribution)")

            if score >= 3:
                sl = round(c_high * SWING_SL_RATIO_SELL, 2)
                tp = round(c_close * SWING_TP_RATIO_SELL, 2)
                signals.append({
                    "time": times[confirm_idx],
                    "price": round(c_close, 2),
                    "action": "จุดขายทำกำไรตามกฎ",
                    "type": "RULE_TP",
                    "score": score,
                    "score_text": f"{score}/5 สัญญาณคอนฟลูเอนซ์ (ไม่ผ่าน backtest)",
                    "badge": f"🎯 จุดขายทำกำไรตามกฎ ({score}/5) (ไม่ผ่าน backtest)",
                    "summary": f"จุดขายทำกำไรยืนยันที่ราคา ${c_close:.2f} (ยืนยัน Swing Peak ${c_high:.2f} ของวันที่ {times[i]}) สัญญาณ Overbought ประสานแนวต้านสำคัญ (ไม่ผ่าน backtest)",
                    "reasons": reasons,
                    "stop_loss": sl,
                    "target": tp,
                    "rr": "1:2.0",
                    "marker_shape": "arrowDown",
                    "marker_color": "#f43f5e",
                })

    # Sort signals chronologically and deduplicate (keep minimum 12 days between same action)
    signals.sort(key=lambda s: s["time"])
    pruned = []
    for s in signals:
        if not pruned:
            pruned.append(s)
            continue
        last_t = datetime.strptime(pruned[-1]["time"], "%Y-%m-%d")
        curr_t = datetime.strptime(s["time"], "%Y-%m-%d")
        if (curr_t - last_t).days >= 12:
            pruned.append(s)
        elif s["score"] > pruned[-1]["score"]:
            pruned[-1] = s

    # Limit historical signals to 4 key turning points
    historical_signals = pruned[-4:] if len(pruned) > 4 else pruned

    # 3. Always Add Current / Latest Status Analysis (Today's Candle)
    curr_reasons = []

    # Fundamental & Timing reasons from unified scoring
    curr_reasons.extend(resolved_stock_score.get("reasons", []))

    # Contextual reasons for unbacked indicators (do NOT add points to score)
    UNBACKED_TAG = "(ไม่ผ่าน backtest ไม่นับคะแนน)"

    if current_st_trend == "BULLISH":
        curr_reasons.append(f"แนวโน้ม SuperTrend: ฝั่งกระทิง (BULLISH) {UNBACKED_TAG}")
    else:
        curr_reasons.append(f"แนวโน้ม SuperTrend: สภาวะปรับฐาน (BEARISH) {UNBACKED_TAG}")

    if current_macd_hist >= 0:
        curr_reasons.append(f"โมเมนตัม MACD: Histogram เป็นบวก (+{current_macd_hist:.2f}) {UNBACKED_TAG}")

    f618 = fibo_levels.get("61.8", 0.0)
    if f618 > 0 and abs(curr_close - f618) / f618 <= 0.045:
        curr_reasons.append(f"โซน Fibonacci: ราคาอยู่ใกล้ Golden Pocket 61.8% (${f618:.2f}) {UNBACKED_TAG}")

    if pattern and pattern.get("target") and pattern.get("upside_pct", 0) > 5:
        curr_reasons.append(f"เป้าหมาย Pattern: โครงสร้าง {pattern['name']} เปิด Upside +{pattern.get('upside_pct', 0)}% {UNBACKED_TAG}")

    if cdc_zone == "green":
        curr_reasons.append(f"สัญญาณ CDC ActionZone: อยู่ใน โซนเขียว (Bullish Trend) {UNBACKED_TAG}")
    elif cdc_zone == "blue":
        curr_reasons.append(f"สัญญาณ CDC ActionZone: โซนฟ้า (Bullish Pullback) {UNBACKED_TAG}")
    elif cdc_zone == "orange":
        curr_reasons.append(f"สัญญาณ CDC ActionZone: โซนส้ม (Bearish Rebound) {UNBACKED_TAG}")
    elif cdc_zone == "red":
        curr_reasons.append(f"สัญญาณ CDC ActionZone: โซนแดง (Bearish Trend) {UNBACKED_TAG}")

    if elliott_wave and elliott_wave.get("detected"):
        ew_type = elliott_wave.get("type", "")
        ew_target = elliott_wave.get("target") or 0.0
        if ew_type in BULLISH_DEVELOPING_WAVE_TYPES:
            curr_reasons.append(f"โครงสร้าง Elliott Wave: เคลื่อนที่ใน {elliott_wave.get('current_wave', 'Impulse Wave')} สู่เป้าหมาย ${ew_target:.2f} {UNBACKED_TAG}")
        else:
            curr_reasons.append(f"คำเตือน Elliott Wave: {elliott_wave.get('current_wave', ew_type)} {UNBACKED_TAG}")

    if pivots:
        p_r1 = pivots.get("r1", 0.0)
        p_s1 = pivots.get("s1", 0.0)
        if p_r1 > 0 and curr_close >= p_r1:
            curr_reasons.append(f"ระดับราคา Pivot: ยืนเหนือแนวต้าน R1 (${p_r1:.2f}) {UNBACKED_TAG}")
        elif p_s1 > 0 and p_s1 <= curr_close <= p_s1 * 1.035:
            curr_reasons.append(f"ระดับราคา Pivot: ดีดตัวทดสอบแนวรับสำคัญ S1 (${p_s1:.2f}) {UNBACKED_TAG}")

    if luxalgo_sr:
        last_sig = luxalgo_sr.get("current_signal")
        if last_sig and last_sig.get("time") == times[-1]:
            stype = last_sig.get("type")
            if stype == "BREAKOUT_VOL":
                curr_reasons.append(f"LuxAlgo S/R: {last_sig.get('desc')} {UNBACKED_TAG}")
            elif stype == "BULL_WICK":
                curr_reasons.append(f"คำเตือน LuxAlgo S/R: {last_sig.get('desc')} {UNBACKED_TAG}")

    if smc:
        fvgs = smc.get("unmitigated_fvgs", [])
        for f in fvgs:
            if f.get("type") == "BULLISH_FVG" and f["bottom"] <= curr_close <= f["top"] * 1.02:
                curr_reasons.append(f"Smart Money (SMC): ราคาลงมาทดสอบ Demand FVG (${f['bottom']:.2f} - ${f['top']:.2f}) {UNBACKED_TAG}")
                break

    if squeeze_mom:
        if squeeze_mom.get("squeeze_fired") and squeeze_mom.get("direction") == "BULLISH":
            curr_reasons.append(f"LazyBear Squeeze: สัญญาณ Squeeze Fired ({squeeze_mom.get('momentum'):.2f}) {UNBACKED_TAG}")
        elif squeeze_mom.get("squeeze_on"):
            curr_reasons.append(f"คำเตือน Squeeze: สภาวะ Squeeze ON ความผันผวนบีบอัดแคบ {UNBACKED_TAG}")

    if chandelier_exit:
        if chandelier_exit.get("direction") == "LONG":
            curr_reasons.append(f"Chandelier Exit: เทรนด์หลักฝั่ง Long เหนือ Trailing Stop (${chandelier_exit.get('long_stop'):.2f}) {UNBACKED_TAG}")
        else:
            curr_reasons.append(f"สถานะ Chandelier Exit: ใต้แนวต้าน Stop (${chandelier_exit.get('short_stop'):.2f}) {UNBACKED_TAG}")

    # Determine Action, Type, Badge, and Markers from unified score
    score_total = resolved_stock_score.get("total")
    score_label = f"{score_total:.0f}/100" if score_total is not None else f"{curr_score}/5"
    has_entry_signal = bool(timing_score.get("entry_signal")) or (
        isinstance(resolved_stock_score.get("timing"), dict) and bool(resolved_stock_score["timing"].get("entry_signal"))
    )

    if is_guard and days_to_earnings is not None:
        d_val = int(round(days_to_earnings))
        if d_val <= 0:
            act = "พักสัญญาณ (งบออกวันนี้)"
            b_type = "EARNINGS_GUARD"
            badge = "🟠 พักสัญญาณ (งบออกวันนี้)"
            summary_txt = f"สถานะราคา ${curr_close:.2f} อยู่ในช่วงงบออกวันนี้ (Earnings Guard) พักสัญญาณซื้อเพื่อควบคุมความเสี่ยง"
        else:
            act = f"พักสัญญาณ (งบออกใน {d_val} วัน)"
            b_type = "EARNINGS_GUARD"
            badge = f"🟠 พักสัญญาณ (งบออกใน {d_val} วัน)"
            summary_txt = f"สถานะราคา ${curr_close:.2f} อยู่ในช่วงงบออกใน {d_val} วัน (Earnings Guard) พักสัญญาณซื้อเพื่อควบคุมความเสี่ยง"
        m_shape = "circle"
        m_col = "#fb923c"
    elif grade == "F":
        act = "เลี่ยง"
        b_type = "AVOID"
        badge = "⚠️ เลี่ยง (เกรด F)"
        m_shape = "arrowDown"
        m_col = "#f43f5e"
        extra_rsi = f" (RSI {current_rsi:.1f} อยู่ในโซนสูง)" if current_rsi > RSI_OVERBOUGHT_THRESHOLD else ""
        summary_txt = f"สถานะราคา ${curr_close:.2f} อยู่ในเกรด F พื้นฐานหรือเทรนด์มีความเสี่ยงสูง ควรเลี่ยงหรือวางแผนบริหารความเสี่ยง{extra_rsi}"
    elif grade == "C":
        act = "รอ"
        b_type = "WAIT"
        badge = "⏳ รอ (เกรด C)"
        m_shape = "circle"
        m_col = "#94a3b8"
        extra_rsi = f" (RSI {current_rsi:.1f} อยู่ในโซนสูง)" if current_rsi > RSI_OVERBOUGHT_THRESHOLD else ""
        summary_txt = f"สถานะราคา ${curr_close:.2f} อยู่ในเกรด C สภาวะเฝ้าระวัง ควรรอสัญญาณกลับตัวและงบไตรมาสถัดไป{extra_rsi}"
    elif current_rsi > RSI_OVERBOUGHT_THRESHOLD:
        act = "แบ่งทำกำไร / รอ"
        b_type = "TRIM"
        badge = f"🎯 แบ่งทำกำไร / รอ ({curr_score}/5)"
        m_shape = "arrowDown"
        m_col = "#f43f5e"
        summary_txt = f"สถานะราคา ${curr_close:.2f} เข้าเขต Overbought (RSI {current_rsi:.1f}) แนะนำแบ่งทำกำไรหรือเลื่อน Trailing Stop"
    elif grade == "B":
        act = "รอ"
        b_type = "HOLD"
        badge = "⚖️ รอจังหวะ (เกรด B)"
        m_shape = "circle"
        m_col = "#94a3b8"
        summary_txt = f"สถานะราคา ${curr_close:.2f} อยู่ในเกรด B คุณภาพปานกลาง ถือครองเดิมและรอจังหวะสะสมใหม่"
    elif grade in ("A+", "A", "ETF"):
        if has_entry_signal:
            act = "เข้าเงื่อนไขจุดเข้า"
            b_type = "ENTRY"
            badge = f"💎 เข้าเงื่อนไขจุดเข้า ({grade})"
            m_shape = "arrowUp"
            m_col = "#10b981"
            summary_txt = f"สถานะราคา ${curr_close:.2f} เข้าเงื่อนไขจุดเข้า สัญญาณ RSI Hook หนุนรอบฟื้นตัวในหุ้นคุณภาพเกรด {grade}"
        else:
            act = "รอ"
            b_type = "HOLD"
            badge = f"⚖️ ถือ / รอจุดเข้า ({grade})"
            m_shape = "circle"
            m_col = "#38bdf8"
            summary_txt = f"สถานะราคา ${curr_close:.2f} หุ้นคุณภาพเกรด {grade} อยู่ในเกณฑ์ถือครอง ติดตามจังหวะย่อเพื่อหาจุดเข้า"
    else:
        act = "รอ"
        b_type = "WAIT"
        badge = f"⚖️ รอ ({grade})"
        m_shape = "circle"
        m_col = "#94a3b8"
        summary_txt = f"สถานะราคา ${curr_close:.2f} ข้อมูลไม่เพียงพอสำหรับประเมินเกรด ควรรอข้อมูลเพิ่มเติม"

    current_signal = {
        "time": times[-1],
        "price": round(curr_close, 2),
        "action": act,
        "type": b_type,
        "score": curr_score,
        "score_text": f"{curr_score}/5 ดาว (เกรด {grade} · {score_label})",
        "badge": badge,
        "summary": summary_txt,
        "reasons": curr_reasons,
        "stop_loss": round(curr_close - 1.5 * atr_val, 2) if b_type != "TRIM" and b_type != "AVOID" else round(curr_close + 1.5 * atr_val, 2),
        "target": round(curr_close + 2.5 * atr_val, 2) if b_type != "TRIM" and b_type != "AVOID" else round(curr_close - 2.0 * atr_val, 2),
        "rr": "1:2.5" if b_type != "TRIM" and b_type != "AVOID" else "1:2.0",
        "marker_shape": m_shape,
        "marker_color": m_col,
        "is_latest": True,
        "earnings_guard": is_guard,
        "guard_days": int(round(days_to_earnings)) if is_guard and days_to_earnings is not None else None,
        "guard_days_threshold": int(round(EARNINGS_GUARD_DAYS)),
        "levels_informational": (b_type in ("AVOID", "EARNINGS_GUARD")),
        "grade": grade,
        "stock_score": resolved_stock_score,
    }

    # If the latest bar already has a signal, update it or append
    if historical_signals and historical_signals[-1]["time"] == times[-1]:
        historical_signals[-1] = current_signal
    else:
        historical_signals.append(current_signal)

    return historical_signals


def _previous_month_hlc(candles: List[Dict[str, Any]]) -> tuple:
    y, m = int(candles[-1]["time"][:4]), int(candles[-1]["time"][5:7])
    prev_key = f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"
    month = [c for c in candles if c["time"][:7] == prev_key]
    if not month:
        cur_key = candles[-1]["time"][:7]
        earlier = [c for c in candles if c["time"][:7] < cur_key]
        if earlier:
            last_key = earlier[-1]["time"][:7]
            month = [c for c in earlier if c["time"][:7] == last_key]
        else:
            month = candles
    return max(c["high"] for c in month), min(c["low"] for c in month), month[-1]["close"]


def compute_fibo_and_indicators(
    candles: List[Dict[str, Any]],
    days_to_earnings: Optional[float] = None,
    is_etf: bool = False,
    ticker: Optional[str] = None,
    stock_score: Optional[Dict[str, Any]] = None,
    fundamental: Optional[FundamentalScore] = None,
) -> Dict[str, Any]:
    """
    Compute Inception High/Low (ATH/ATL), Fibonacci retracements (52W cycle and 2Y macro),
    VWAP and Volume Profile POC anchored to the last ANCHOR_BARS daily bars, Moving Averages,
    SuperTrend, Parabolic SAR, Golden/Death cross, Oscillators, and Classical Chart Patterns.
    """
    if not candles or len(candles) < 5:
        return {
            "candles": candles,
            "inception_date": "-",
            "total_bars": 0,
            "ath": {"price": 0.0, "time": ""},
            "atl": {"price": 0.0, "time": ""},
            "swing_high": {"price": 0.0, "time": ""},
            "swing_low": {"price": 0.0, "time": ""},
            "fibo": {},
            "volume_profile": {"poc": 0.0},
            "pattern": None
        }

    # Sanitize input candles to enforce OHLC invariant: high >= max(open, close), low <= min(open, close)
    for c in candles:
        o = c.get("open", c["high"])
        cl = c["close"]
        if c["high"] < max(o, cl):
            c["high"] = max(c["high"], o, cl)
        if c["low"] > min(o, cl):
            c["low"] = min(c["low"], o, cl)

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]
    n = len(candles)

    # 1. Inception All-Time High (ATH) and All-Time Low (ATL)
    ath_val = max(highs)
    atl_val = min(lows)
    ath_idx = highs.index(ath_val)
    atl_idx = lows.index(atl_val)
    ath_time = candles[ath_idx]["time"]
    atl_time = candles[atl_idx]["time"]

    # 2. 2Y Macro & 52-Week Cycle Fibonacci Retracements
    a0 = max(0, n - ANCHOR_BARS)
    macro_hi = max(highs[a0:])
    macro_lo = min(lows[a0:])
    diff_macro = macro_hi - macro_lo
    fibo_macro = {
        "0.0": round(macro_hi, 2),
        "23.6": round(macro_hi - 0.236 * diff_macro, 2),
        "38.2": round(macro_hi - 0.382 * diff_macro, 2),
        "50.0": round(macro_hi - 0.500 * diff_macro, 2),
        "61.8": round(macro_hi - 0.618 * diff_macro, 2),
        "78.6": round(macro_hi - 0.786 * diff_macro, 2),
        "100.0": round(macro_lo, 2)
    }

    recent_252_highs = highs[-252:] if len(highs) >= 252 else highs
    recent_252_lows = lows[-252:] if len(lows) >= 252 else lows
    w52_hi = max(recent_252_highs)
    w52_lo = min(recent_252_lows)
    diff_52w = max(1e-6, w52_hi - w52_lo)
    fibo_cycle = {
        "0.0": round(w52_hi, 2),
        "23.6": round(w52_hi - 0.236 * diff_52w, 2),
        "38.2": round(w52_hi - 0.382 * diff_52w, 2),
        "50.0": round(w52_hi - 0.500 * diff_52w, 2),
        "61.8": round(w52_hi - 0.618 * diff_52w, 2),
        "78.6": round(w52_hi - 0.786 * diff_52w, 2),
        "100.0": round(w52_lo, 2)
    }
    # fibo_levels defaults to active swing cycle for high relevance to current price
    fibo_levels = fibo_cycle

    # 3. SuperTrend (10, 3) with Wilder RMA ATR, matching TradingView ta.supertrend
    tr_list = []
    for i in range(n):
        if i == 0:
            tr_list.append(highs[i] - lows[i])
        else:
            tr_list.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    st_period = min(10, n)
    atr10: List[Optional[float]] = [None] * n
    atr10[st_period - 1] = sum(tr_list[:st_period]) / st_period
    for i in range(st_period, n):
        atr10[i] = (atr10[i - 1] * (st_period - 1) + tr_list[i]) / st_period

    upper_band = 0.0
    lower_band = 0.0
    in_uptrend = False
    for i in range(st_period - 1, n):
        hl2 = (highs[i] + lows[i]) / 2.0
        basic_upper = hl2 + 3.0 * atr10[i]
        basic_lower = hl2 - 3.0 * atr10[i]
        if i == st_period - 1:
            upper_band, lower_band = basic_upper, basic_lower
            in_uptrend = False
            continue
        prev_upper, prev_lower = upper_band, lower_band
        lower_band = basic_lower if (basic_lower > prev_lower or closes[i - 1] < prev_lower) else prev_lower
        upper_band = basic_upper if (basic_upper < prev_upper or closes[i - 1] > prev_upper) else prev_upper
        if in_uptrend:
            in_uptrend = closes[i] >= lower_band
        else:
            in_uptrend = closes[i] > upper_band
    last_st_val = lower_band if in_uptrend else upper_band

    # 4. VWAP anchored to the last ANCHOR_BARS daily bars
    cum_vol = 0
    cum_tp_vol = 0
    vwap_val = closes[-1]
    for i in range(a0, n):
        tp = (highs[i] + lows[i] + closes[i]) / 3.0
        v = volumes[i]
        cum_vol += v
        cum_tp_vol += tp * v
    if cum_vol > 0:
        vwap_val = cum_tp_vol / cum_vol

    # 5. Volume Profile POC over the last ANCHOR_BARS daily bars
    p_min = macro_lo
    p_max = macro_hi
    buckets = 50
    bucket_size = (p_max - p_min) / buckets if p_max > p_min else 1.0
    vol_bins = [0] * buckets
    for i in range(a0, n):
        b_idx = min(buckets - 1, max(0, int((closes[i] - p_min) / max(1e-6, bucket_size))))
        vol_bins[b_idx] += volumes[i]
    poc_idx = vol_bins.index(max(vol_bins))
    poc_price = round(p_min + (poc_idx + 0.5) * bucket_size, 2)

    # 6. MACD (12, 26, 9) from inception
    k12 = 2.0 / 13.0
    k26 = 2.0 / 27.0
    k9 = 2.0 / 10.0
    ema12, ema26 = closes[0], closes[0]
    macd_line = []
    for i in range(n):
        ema12 = (closes[i] * k12) + (ema12 * (1.0 - k12))
        ema26 = (closes[i] * k26) + (ema26 * (1.0 - k26))
        macd_line.append(ema12 - ema26)

    signal_line = []
    sig = macd_line[0]
    for i in range(n):
        sig = (macd_line[i] * k9) + (sig * (1.0 - k9))
        signal_line.append(sig)
    hist = macd_line[-1] - signal_line[-1]
    macd_status = "Bullish Cross 🟢" if hist >= 0 else "Bearish Cross 🔴"

    # 7. Stochastic (14, 3, 3) from inception
    fast_k = []
    for i in range(13, n):
        l14 = min(lows[i - 13 : i + 1])
        h14 = max(highs[i - 13 : i + 1])
        fk = ((closes[i] - l14) / max(1e-6, (h14 - l14))) * 100.0
        fast_k.append(fk)
    slow_k = [sum(fast_k[i - 2 : i + 1]) / 3.0 for i in range(2, len(fast_k))] if len(fast_k) >= 3 else [50.0]
    stoch_d = [sum(slow_k[i - 2 : i + 1]) / 3.0 for i in range(2, len(slow_k))] if len(slow_k) >= 3 else [50.0]
    stoch_k_val = round(slow_k[-1], 1)
    stoch_d_val = round(stoch_d[-1], 1)
    stoch_status = "Oversold Hook 🟢" if stoch_k_val <= 25 and stoch_k_val > stoch_d_val else ("Overbought 🔴" if stoch_k_val >= 80 else "Neutral ⚖️")

    # 8. RSI (14) from inception
    gains, losses = [], []
    for i in range(1, n):
        d = closes[i] - closes[i - 1]
        gains.append(max(0.0, d))
        losses.append(max(0.0, -d))
    rsi_val = 50.0
    if len(gains) >= 14:
        avg_g = sum(gains[:14]) / 14.0
        avg_l = sum(losses[:14]) / 14.0
        rsi_val = _rsi_value(avg_g, avg_l)
        for i in range(14, len(gains)):
            avg_g = (avg_g * 13.0 + gains[i]) / 14.0
            avg_l = (avg_l * 13.0 + losses[i]) / 14.0
            rsi_val = _rsi_value(avg_g, avg_l)

    # 9. 52-Week High & Low
    w52_high = round(max(highs[-252:]), 2)
    w52_low = round(min(lows[-252:]), 2)

    # 10. Classic Pivot Points from the previous completed calendar month's H/L/C
    m_high, m_low, m_close = _previous_month_hlc(candles)
    p_raw = (m_high + m_low + m_close) / 3.0
    p_pivot = round(p_raw, 2)
    r1 = round(2.0 * p_raw - m_low, 2)
    s1 = round(2.0 * p_raw - m_high, 2)
    r2 = round(p_raw + (m_high - m_low), 2)
    s2 = round(p_raw - (m_high - m_low), 2)

    # 11. Golden / Death Cross
    sma50_last = sum(closes[-50:]) / 50.0 if len(closes) >= 50 else closes[-1]
    sma200_last = sum(closes[-200:]) / 200.0 if len(closes) >= 200 else closes[-1]
    ma_cross = "Golden Cross 🌟" if sma50_last >= sma200_last else "Death Cross ⚠️"

    # 12. Parabolic SAR (Step 0.02, Max 0.20) from inception
    sar_status = "-"
    last_sar_val = closes[-1]
    if n >= 5:
        af = 0.02
        af_step = 0.02
        af_max = 0.20
        is_long = True
        ep = highs[0]
        sar_val = lows[0]
        for i in range(1, n):
            prev_sar = sar_val
            if is_long:
                sar_val = prev_sar + af * (ep - prev_sar)
                sar_val = min(sar_val, lows[i - 1], lows[i - 2] if i >= 2 else lows[i - 1])
                if lows[i] < sar_val:
                    is_long = False
                    sar_val = ep
                    ep = lows[i]
                    af = af_step
                else:
                    if highs[i] > ep:
                        ep = highs[i]
                        af = min(af + af_step, af_max)
            else:
                sar_val = prev_sar - af * (prev_sar - ep)
                sar_val = max(sar_val, highs[i - 1], highs[i - 2] if i >= 2 else highs[i - 1])
                if highs[i] > sar_val:
                    is_long = True
                    sar_val = ep
                    ep = highs[i]
                    af = af_step
                else:
                    if lows[i] < ep:
                        ep = lows[i]
                        af = min(af + af_step, af_max)
        last_sar_val = sar_val
        sar_status = f"{'BULLISH 🟢' if is_long else 'BEARISH 🔴'} (${last_sar_val:.2f})"

    # 13. ATR (14) Volatility
    atr14_val = round(atr10[-1], 2)
    if n >= 14:
        atr14 = sum(tr_list[:14]) / 14.0
        for tr in tr_list[14:]:
            atr14 = (atr14 * 13.0 + tr) / 14.0
        atr14_val = round(atr14, 2)
    atr14_pct = round((atr14_val / closes[-1]) * 100.0, 1) if closes[-1] > 0 else 0.0

    # 14. Volume 20D Average & Surge Ratio
    vol20_avg = sum(volumes[-20:]) / 20.0 if len(volumes) >= 20 else volumes[-1]
    vol_surge_ratio = round(volumes[-1] / max(1.0, vol20_avg), 2)

    # 15. Classical Chart Patterns detection
    pattern = detect_chart_patterns(candles)

    # 16. Elliott Wave Impulse Detection (Intermediate Cycle & All-Time Macro)
    elliott_wave = detect_elliott_wave(candles, is_macro=False)
    elliott_wave_macro = detect_elliott_wave(candles, is_macro=True)

    # 17. CDC ActionZone V3 2020 (Uncle Chaloke)
    cdc_actionzone = compute_cdc_actionzone(candles)

    # 18. LuxAlgo Support and Resistance Levels with Breaks
    luxalgo_sr = compute_luxalgo_support_resistance(candles)

    # 19. Smart Money Concepts (SMC) - FVG and Order Blocks
    smc = compute_smart_money_concepts(candles)

    # 20. Squeeze Momentum Indicator [LazyBear]
    squeeze_mom = compute_squeeze_momentum(candles)

    # 21. Chandelier Exit [everget]
    chandelier_exit = compute_chandelier_exit(candles)

    # 22. Multi-Technical Confluence Decision Engine
    ai_signals = compute_ai_confluence_signals(
        candles=candles,
        fibo_levels=fibo_levels,
        pattern=pattern,
        poc_price=poc_price,
        current_st_trend="BULLISH" if in_uptrend else "BEARISH",
        current_rsi=round(rsi_val, 1),
        current_macd_hist=round(hist, 2),
        atr_val=atr14_val,
        cdc_zone=cdc_actionzone["zone"],
        elliott_wave=elliott_wave,
        pivots={"pivot": p_pivot, "r1": r1, "s1": s1, "r2": r2, "s2": s2},
        luxalgo_sr=luxalgo_sr,
        smc=smc,
        squeeze_mom=squeeze_mom,
        chandelier_exit=chandelier_exit,
        ticker=ticker,
        days_to_earnings=days_to_earnings,
        is_etf=is_etf,
        stock_score=stock_score,
        fundamental=fundamental,
    )

    return {
        "candles": candles,
        "inception_date": candles[0]["time"],
        "total_bars": n,
        "ath": {"price": round(ath_val, 2), "time": ath_time},
        "atl": {"price": round(atl_val, 2), "time": atl_time},
        "swing_high": {"price": round(ath_val, 2), "time": ath_time},
        "swing_low": {"price": round(atl_val, 2), "time": atl_time},
        "fibo": fibo_levels,
        "fibo_cycle": fibo_cycle,
        "fibo_macro": fibo_macro,
        "volume_profile": {
            "poc": poc_price
        },
        "anchor_2y": {"time": candles[a0]["time"], "bars": n - a0},
        "supertrend": {
            "trend": "BULLISH" if in_uptrend else "BEARISH",
            "last_value": round(last_st_val, 2)
        },
        "vwap": round(vwap_val, 2),
        "sar": {
            "status": sar_status,
            "last_value": round(last_sar_val, 2)
        },
        "ma_cross": {
            "status": ma_cross,
            "sma50": round(sma50_last, 2),
            "sma200": round(sma200_last, 2)
        },
        "macd": {
            "line": round(macd_line[-1], 2),
            "signal": round(signal_line[-1], 2),
            "hist": round(hist, 2),
            "status": macd_status
        },
        "stochastic": {
            "k": stoch_k_val,
            "d": stoch_d_val,
            "status": stoch_status
        },
        "w52": {
            "high": w52_high,
            "low": w52_low
        },
        "pivots": {
            "pivot": p_pivot,
            "r1": r1,
            "s1": s1,
            "r2": r2,
            "s2": s2
        },
        "atr14": {
            "value": atr14_val,
            "pct": atr14_pct
        },
        "vol_surge": {
            "ratio": vol_surge_ratio,
            "avg20": int(vol20_avg)
        },
        "latest_rsi": round(rsi_val, 1),
        "pattern": pattern,
        "elliott_wave": elliott_wave,
        "elliott_wave_macro": elliott_wave_macro,
        "ai_signals": ai_signals,
        "earnings_history": detect_earnings_history(candles, ticker=ticker, days_to_earnings=days_to_earnings, is_etf=is_etf),
        "cdc_actionzone": cdc_actionzone,
        "luxalgo_sr": luxalgo_sr,
        "smc": smc,
        "squeeze_momentum": squeeze_mom,
        "chandelier_exit": chandelier_exit,
        "earnings_hash": EARNINGS_CALENDAR_HASH,
        "schema_version": INDICATOR_SCHEMA_VERSION
    }


def load_candles_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _strip_candle_colors(entry: Dict[str, Any]) -> Dict[str, Any]:
    cdc = entry.get("cdc_actionzone")
    if isinstance(cdc, dict) and "candle_colors" in cdc:
        entry = {**entry, "cdc_actionzone": {k: v for k, v in cdc.items() if k != "candle_colors"}}
    return entry


def save_candles_cache(cache: Dict[str, Any]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    slim = {t: _strip_candle_colors(e) if isinstance(e, dict) else e for t, e in cache.items()}
    fd, tmp = tempfile.mkstemp(dir=CACHE_PATH.parent, prefix=CACHE_PATH.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(slim, f, ensure_ascii=False)
        os.replace(tmp, CACHE_PATH)
    except BaseException:
        os.unlink(tmp)
        raise


def get_all_charts_payload(tickers: List[str], force_refresh: bool = False) -> Dict[str, Any]:
    """
    Load or fetch chart payloads for all given tickers.
    Returns a dictionary keyed by ticker.
    """
    cache = load_candles_cache()
    now_ts = time.time()

    tickers_to_fetch = []
    for t in set(tickers):
        entry = cache.get(t)
        if (
            force_refresh
            or not entry
            or (now_ts - entry.get("timestamp", 0) > CACHE_TTL_SECONDS)
            or not entry.get("candles")
            or not entry.get("full_history")
            or entry.get("schema_version") != INDICATOR_SCHEMA_VERSION
            or entry.get("earnings_hash") != EARNINGS_CALENDAR_HASH
        ):
            tickers_to_fetch.append(t)

    if tickers_to_fetch:
        def _fetch_and_process(t):
            try:
                entry = cache.get(t)
                if (
                    not force_refresh
                    and entry
                    and entry.get("full_history")
                    and len(entry.get("candles") or []) > 30
                    and (now_ts - entry.get("timestamp", 0) <= CACHE_TTL_SECONDS)
                ):
                    candles = entry["candles"]
                    fetched_ts = entry["timestamp"]
                else:
                    candles = fetch_ticker_candles(t)
                    fetched_ts = now_ts
                if not candles:
                    raise ValueError("no candles returned")
                chart_data = compute_fibo_and_indicators(candles, ticker=t, is_etf=(t in ETF_TICKERS))
                chart_data["timestamp"] = fetched_ts
                chart_data["full_history"] = True
                chart_data["schema_version"] = INDICATOR_SCHEMA_VERSION
                chart_data["earnings_hash"] = EARNINGS_CALENDAR_HASH
                return t, chart_data
            except Exception as e:
                print(f"[chart_data] {t}: refresh failed, keeping cached data: {type(e).__name__}: {e}", file=sys.stderr)
                return t, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(_fetch_and_process, tickers_to_fetch))

        for t, data in results:
            if data and data.get("candles"):
                cache[t] = data
            elif cache.get(t):
                cache[t] = {**cache[t], "stale": True}

        save_candles_cache(cache)

    output = {}
    for t in tickers:
        if t in cache:
            output[t] = cache[t]
    return output


PAGE_DAILY_BARS = 1260


def compact_charts_for_page(cache: Dict[str, Any], tickers: Iterable[str]) -> Dict[str, Any]:
    """
    Indicators in each entry were computed from full history. For the chart page,
    keep the last PAGE_DAILY_BARS daily candles (5Y button) and collapse older history
    into monthly bars so the 1M view, ALL view and client-side EMA/VWAP still span inception.
    """
    wanted = set(tickers)
    out = {}
    for t, entry in cache.items():
        candles = entry.get("candles") or []
        if t not in wanted or not entry.get("full_history") or not candles:
            continue
        cut = max(0, len(candles) - PAGE_DAILY_BARS)
        month = candles[cut]["time"][:7]
        while cut > 0 and candles[cut - 1]["time"][:7] == month:
            cut -= 1
        monthly = []
        for c in candles[:cut]:
            if monthly and monthly[-1]["time"][:7] == c["time"][:7]:
                m = monthly[-1]
                m["time"] = c["time"]
                m["high"] = max(m["high"], c["high"])
                m["low"] = min(m["low"], c["low"])
                m["close"] = c["close"]
                m["volume"] += c["volume"]
            else:
                monthly.append(dict(c))
        entry_copy = _strip_candle_colors(entry)
        out[t] = {**entry_copy, "candles": monthly + candles[cut:]}
    return out


def remove_from_candles_cache(tickers: Iterable[str]) -> List[str]:
    """Remove tickers from data/candles_cache.json if present and persist atomically."""
    cache = load_candles_cache()
    removed = []
    for t in tickers:
        t_up = str(t).upper().strip()
        if t_up in cache:
            del cache[t_up]
            removed.append(t_up)
    if removed:
        save_candles_cache(cache)
    return removed
