"""
Chart Data & Technical Analysis Engine
Fetches 6-month daily OHLCV candles, computes Swing High/Low,
Fibonacci Retracements (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%),
SMA 50, SMA 200, and Volume profiles for automated programmatic charting.
"""

import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "candles_cache.json"
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours


def _round_price(x: float) -> float:
    x = float(x)
    return round(x, 4) if abs(x) < 10 else round(x, 2)


def fetch_ticker_candles(ticker: str) -> List[Dict[str, Any]]:
    """
    Fetch all daily OHLCV candles since entering the market (inception/IPO) from Yahoo Finance v8 API.
    """
    clean_ticker = ticker.replace(".", "-").upper().strip()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_ticker}?period1=0&period2=9999999999&interval=1d"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
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
            candles.append({
                "time": t_str,
                "open": _round_price(o),
                "high": _round_price(h),
                "low": _round_price(l),
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
    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]
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
                if inter_troughs:
                    neck_val = min(t["price"] for t in inter_troughs)
                    head_h = p2["price"] - neck_val
                    target = round(neck_val - head_h, 2)
                    t_left = [t for t in inter_troughs if p1["idx"] < t["idx"] < p2["idx"]]
                    t_right = [t for t in inter_troughs if p2["idx"] < t["idx"] < p3["idx"]]
                    tl = min(t_left, key=lambda x: x["price"]) if t_left else inter_troughs[0]
                    tr = min(t_right, key=lambda x: x["price"]) if t_right else inter_troughs[-1]
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
                        "win_rate": "71% (Bulkowski Classical Chart Pattern Database)",
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
                if inter_peaks:
                    neck_val = max(p["price"] for p in inter_peaks)
                    head_h = neck_val - t2["price"]
                    target = round(neck_val + head_h, 2)
                    p_left = [p for p in inter_peaks if t1["idx"] < p["idx"] < t2["idx"]]
                    p_right = [p for p in inter_peaks if t2["idx"] < p["idx"] < t3["idx"]]
                    pl = max(p_left, key=lambda x: x["price"]) if p_left else inter_peaks[0]
                    pr = max(p_right, key=lambda x: x["price"]) if p_right else inter_peaks[-1]
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
                        "win_rate": "78% (หนึ่งในรูปแบบกลับตัวเป็นกระทิงที่แม่นยำที่สุดในตลาดหุ้น)",
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
            if mid_peaks:
                neck_p = max(p["price"] for p in mid_peaks)
                avg_bottom = (t1["price"] + t2["price"] + t3["price"]) / 3.0
                target = round(neck_p + (neck_p - avg_bottom), 2)
                p_mid1 = [p for p in mid_peaks if t1["idx"] < p["idx"] < t2["idx"]]
                p_mid2 = [p for p in mid_peaks if t2["idx"] < p["idx"] < t3["idx"]]
                pm1 = max(p_mid1, key=lambda x: x["price"]) if p_mid1 else mid_peaks[0]
                pm2 = max(p_mid2, key=lambda x: x["price"]) if p_mid2 else mid_peaks[-1]
                detected = {
                    "name": "Bullish Triple Bottom (สามฐานแข็งแกร่ง)",
                    "type": "Bullish Reversal",
                    "badge": "🟢 สามฐานกระทิง (Triple Bottom)",
                    "summary": f"ทดสอบแนวรับ 3 ครั้งไม่หลุดใกล้ ${avg_bottom:.2f} โซนดูดซับแรงขายสมบูรณ์แบบ",
                    "neckline": round(neck_p, 2),
                    "breakout": round(neck_p, 2),
                    "target": target,
                    "upside_pct": round((target - current_price) / current_price * 100, 1),
                    "psychology": "ราคาทดสอบแนวรับเดิมถึง 3 ครั้ง แต่ไม่มีแรงขายใดสามารถกดให้หลุดลงไปได้ แสดงถึงแนวรับหินผา (Institutional Strong Floor) ที่สถาบันตั้งรับซื้อไม่อั้นจนอุปทานหมดตลาด",
                    "structure": f"ฐานแนวรับ 3 ครั้งเฉลี่ย ${avg_bottom:.2f} • Neckline แนวต้านเบรกเอาท์ ${neck_p:.2f}",
                    "action_plan": f"ซื้อสะสมใกล้โซนฐาน ${avg_bottom:.2f} หรือ Follow Buy เมื่อปิดเบรก Neckline ${neck_p:.2f} เป้าหมาย ${target:.2f}",
                    "invalidation": f"Stop Loss ทันทีหากราคาปิดหลุดฐานต่ำสุด ${min(t1['price'], t2['price'], t3['price']):.2f}",
                    "win_rate": "74% (Thomas Bulkowski)",
                    "target_calc": f"วัดความสูงจากฐาน ${avg_bottom:.2f} ถึงยอด Neckline ${neck_p:.2f} แล้วนำไปบวกเพิ่มจากยอด Neckline",
                    "key_points": [
                        {"name": "Bottom 1", "time": t1["time"], "price": t1["price"], "role": "start"},
                        {"name": "Neckline Peak 1", "time": pm1["time"], "price": pm1["price"]},
                        {"name": "Bottom 2", "time": t2["time"], "price": t2["price"]},
                        {"name": "Neckline Peak 2", "time": pm2["time"], "price": pm2["price"]},
                        {"name": "Bottom 3", "time": t3["time"], "price": t3["price"]},
                    ],
                    "lines": [
                        {"name": "Triple Support Floor", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": avg_bottom}, {"time": times[-1], "value": avg_bottom}]},
                        {"name": "Neckline Breakout", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": neck_p}, {"time": times[-1], "value": neck_p}]}
                    ]
                }

    # 4. Double Bottom (W-Shape)
    if not detected and len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        mid_peaks = [p for p in peaks if t1["idx"] < p["idx"] < t2["idx"]]
        if mid_peaks:
            neck_p = max(mid_peaks, key=lambda x: x["price"])
            price_diff = abs(t1["price"] - t2["price"]) / t1["price"]
            bounce = (neck_p["price"] - min(t1["price"], t2["price"])) / min(t1["price"], t2["price"])
            if price_diff <= 0.045 and bounce >= 0.035:
                target = round(neck_p["price"] + (neck_p["price"] - min(t1["price"], t2["price"])), 2)
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
                    "structure": f"ฐานแรก (${t1['price']:.2f}) • ยอดกลาง Neckline (${neck_p['price']:.2f}) • ฐานที่สอง (${t2['price']:.2f})",
                    "action_plan": f"เข้าซื้อเมื่อแท่งเทียนปิดทะลุ Neckline ${neck_p['price']:.2f} ด้วย Volume หนาแน่น เป้าหมาย ${target:.2f}",
                    "invalidation": f"รูปแบบจะล้มเหลวหากราคาปิดหลุดต่ำกว่าฐานที่ 2 (${t2['price']:.2f})",
                    "win_rate": "72% (รูปแบบยอดนิยมความแม่นยำสูง)",
                    "target_calc": f"วัดส่วนสูงฐานคู่ถึงยอดกลาง (${neck_p['price'] - min(t1['price'], t2['price']):.2f}) บวกเพิ่มจากยอด Neckline",
                    "key_points": [
                        {"name": "Bottom 1", "time": t1["time"], "price": t1["price"], "role": "start"},
                        {"name": "Neckline Peak", "time": neck_p["time"], "price": neck_p["price"]},
                        {"name": "Bottom 2", "time": t2["time"], "price": t2["price"]},
                    ],
                    "lines": [
                        {"name": "Double Bottom Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": t2["time"], "value": t2["price"]}]},
                        {"name": "Neckline Breakout", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": neck_p["price"]}, {"time": times[-1], "value": neck_p["price"]}]}
                    ]
                }

    # 5. Double Top (M-Shape)
    if not detected and len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        mid_troughs = [t for t in troughs if p1["idx"] < t["idx"] < p2["idx"]]
        if mid_troughs:
            neck_t = min(mid_troughs, key=lambda x: x["price"])
            price_diff = abs(p1["price"] - p2["price"]) / p1["price"]
            drop = (max(p1["price"], p2["price"]) - neck_t["price"]) / max(p1["price"], p2["price"])
            if price_diff <= 0.045 and drop >= 0.035:
                target = round(neck_t["price"] - (max(p1["price"], p2["price"]) - neck_t["price"]), 2)
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
                    "structure": f"ยอดแรก (${p1['price']:.2f}) • ฐานรับกลาง Neckline (${neck_t['price']:.2f}) • ยอดที่สอง (${p2['price']:.2f})",
                    "action_plan": f"ขายทำกำไร (Trim/TP) หรือตั้ง Stop Loss เมื่อราคาหลุด Neckline ${neck_t['price']:.2f} เป้าหมายขาลง ${target:.2f}",
                    "invalidation": f"รูปแบบล้มเหลวหากราคาเบรกทะลุยอดสูงสุด ${max(p1['price'], p2['price']):.2f}",
                    "win_rate": "69% (Thomas Bulkowski)",
                    "target_calc": f"วัดส่วนสูงของยอดคู่แล้วหักลบออกจาก Neckline ${neck_t['price']:.2f}",
                    "key_points": [
                        {"name": "Peak 1", "time": p1["time"], "price": p1["price"], "role": "start"},
                        {"name": "Neckline Trough", "time": neck_t["time"], "price": neck_t["price"]},
                        {"name": "Peak 2", "time": p2["time"], "price": p2["price"]},
                    ],
                    "lines": [
                        {"name": "Resistance Ceiling", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": p2["time"], "value": p2["price"]}]},
                        {"name": "Neckline Support", "color": "#38bdf8", "style": 2, "points": [{"time": p1["time"], "value": neck_t["price"]}, {"time": times[-1], "value": neck_t["price"]}]}
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
                    "win_rate": "70% (Bullish Continuation Pattern)",
                    "target_calc": f"วัดความสูงของเสาธง ({pole_peak - pole_base:.2f}) แล้วนำไปทาบต่อจากจุดเบรกเอาท์ของกรอบธง",
                    "key_points": kp,
                    "lines": [
                        {"name": "Flagpole", "color": "#facc15", "style": 0, "points": [{"time": times[base_real_idx], "value": pole_base}, {"time": times[peak_real_idx], "value": pole_peak}]},
                        {"name": "Flag Resistance", "color": "#10b981", "style": 2, "points": [{"time": times[-8], "value": flag_high}, {"time": times[-1], "value": flag_high}]},
                        {"name": "Flag Support", "color": "#38bdf8", "style": 2, "points": [{"time": times[-8], "value": flag_low}, {"time": times[-1], "value": flag_low}]}
                    ]
                }

    # 7. Triangles, Wedges, Expanding Triangles, Channels
    if not detected and len(peaks) >= 2 and len(troughs) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        t1, t2 = troughs[-2], troughs[-1]
        peak_slope = (p2["price"] - p1["price"]) / max(1, (p2["idx"] - p1["idx"]))
        trough_slope = (t2["price"] - t1["price"]) / max(1, (t2["idx"] - t1["idx"]))

        # Ascending Triangle: Flat Resistance (p1 ~= p2), Rising Support (t2 > t1)
        if abs(p2["price"] - p1["price"]) / p1["price"] <= 0.025 and t2["price"] > t1["price"] * 1.015:
            target = round(p2["price"] + (p2["price"] - t1["price"]), 2)
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
                "summary": f"แนวต้านคงที่ ${p2['price']:.2f} ขณะที่แนวรับยกฐานสูงขึ้นเรื่อยๆ รอจังหวะเบรกเอาท์",
                "neckline": round(p2["price"], 2),
                "breakout": round(p2["price"], 2),
                "target": target,
                "upside_pct": round((target - current_price) / current_price * 100, 1),
                "psychology": "แม้จะมีแรงขายกั้นไว้ที่แนวต้านแนวนอน แต่ผู้ซื้อยินดีซื้อในราคาที่แพงขึ้นเรื่อยๆ ทำให้จุดต่ำสุดยกตัวสูงขึ้นอย่างต่อเนื่อง (Higher Lows) บ่งบอกว่าแรงขายที่แนวต้านกำลังจะถูกดูดซับจนหมดสิ้น",
                "structure": f"แนวต้านแนวนอน (${p2['price']:.2f}) • แนวรับเฉียงขึ้นยกฐานจาก ${t1['price']:.2f} มาที่ ${t2['price']:.2f}",
                "action_plan": f"ดักซื้อสะสมเมื่อราคาลงแตะแนวรับเฉียงขึ้น หรือเคาะซื้อ Follow Buy เมื่อปิดเหนือ ${p2['price']:.2f} เป้าหมาย ${target:.2f}",
                "invalidation": f"รูปแบบเสียทรงหากราคาหลุดแนวรับเฉียงขึ้น",
                "win_rate": "73% (มีโอกาสเบรกขึ้นสูงกว่าลง 3 ต่อ 1)",
                "target_calc": f"วัดความกว้างของสามเหลี่ยมที่ฐานแรก (${p2['price'] - t1['price']:.2f}) บวกเพิ่มจากจุดต้าน ${p2['price']:.2f}",
                "key_points": kp,
                "lines": [
                    {"name": "Flat Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": p2["price"]}]},
                    {"name": "Ascending Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Descending Triangle: Falling Resistance (p2 < p1), Flat Support (t1 ~= t2)
        elif abs(t2["price"] - t1["price"]) / t1["price"] <= 0.025 and p2["price"] < p1["price"] * 0.985:
            target = round(t2["price"] - (p1["price"] - t2["price"]), 2)
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
                "summary": f"แนวรับคงที่ ${t2['price']:.2f} ขณะที่จุดสูงสุดถูกกดต่ำลง บ่งชี้แรงขายสะสมต่อเนื่อง",
                "neckline": round(t2["price"], 2),
                "breakout": round(t2["price"], 2),
                "target": target,
                "upside_pct": round((target - current_price) / current_price * 100, 1),
                "psychology": "ผู้ขายกดราคาลงมาต่อเนื่องจนทำ Lower Highs ขณะที่แนวรับเดิมเริ่มเปราะบาง สะท้อนแรงขายกดดันสะสมจากสถาบัน",
                "structure": f"แนวรับแบนราบ (${t2['price']:.2f}) • แนวต้านเฉียงกดต่ำลงต่อเนื่อง",
                "action_plan": f"ระมัดระวังแรงเทขาย หากหลุดแนวรับ ${t2['price']:.2f} ให้ขายตัดขาดทุนทันที เป้าหมายขาลง ${target:.2f}",
                "invalidation": f"รูปแบบล้มเหลวหากเบรกทะลุเส้นแนวต้านเฉียงกดขึ้นไปได้",
                "win_rate": "68% (Bearish Continuation Pattern)",
                "target_calc": f"วัดความสูงสามเหลี่ยมแล้วหักลบออกจากแนวรับ ${t2['price']:.2f}",
                "key_points": kp,
                "lines": [
                    {"name": "Descending Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Flat Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": t2["price"]}]}
                ]
            }
        # Symmetrical Expanding Triangle (Megaphone / Broadening)
        elif p2["price"] > p1["price"] * 1.02 and t2["price"] < t1["price"] * 0.98:
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
                "win_rate": "55% (ความผันผวนสูง ควรรอการยืนยัน)",
                "target_calc": f"เป้าหมายสวิงที่ ${target:.2f}",
                "key_points": kp,
                "lines": [
                    {"name": "Diverging Resistance", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Diverging Support", "color": "#f43f5e", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Symmetrical Triangle
        elif p2["price"] < p1["price"] * 0.985 and t2["price"] > t1["price"] * 1.015:
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
                "win_rate": "65% (เตรียมระเบิดเทรนด์ตามทิศทางเบรก)",
                "target_calc": f"วัดความกว้างสูงสุดของสามเหลี่ยม ({p1['price'] - t1['price']:.2f}) นำไปทาบจากจุดเบรก",
                "key_points": kp,
                "lines": [
                    {"name": "Upper Resistance Line", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Lower Support Line", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Falling Wedge (Bullish Reversal)
        elif p2["price"] < p1["price"] and t2["price"] < t1["price"]:
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
                "win_rate": "74% (หนึ่งในรูปแบบกลับตัวยอดเยี่ยมของสถาบัน)",
                "target_calc": f"เป้าหมายเชิงเทคนิคคือจุดเริ่มต้นของลิ่มที่ ${p1['price']:.2f}",
                "key_points": kp,
                "lines": [
                    {"name": "Upper Wedge Resistance", "color": "#38bdf8", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Lower Wedge Support", "color": "#10b981", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Channel Up / Rising Trend
        elif p2["price"] > p1["price"] and t2["price"] > t1["price"]:
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
                "win_rate": "76% (Trend Following Setup)",
                "target_calc": f"เป้าหมายแนวต้านกรอบบนคำนวณที่ ${target:.2f}",
                "key_points": kp,
                "lines": [
                    {"name": "Upper Channel Line", "color": "#10b981", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2['idx']), 2)}]},
                    {"name": "Lower Channel Support", "color": "#38bdf8", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2['idx']), 2)}]}
                ]
            }

    # Fallback: Range Consolidation Box
    if not detected:
        recent_high = max(highs[-30:])
        recent_low = min(lows[-30:])
        target = round(recent_high + (recent_high - recent_low) * 0.5, 2)
        h_sub = highs[-30:].index(recent_high)
        l_sub = lows[-30:].index(recent_low)
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
            "target": target,
            "upside_pct": round((target - current_price) / current_price * 100, 1),
            "psychology": "ราคาพักตัวรอปัจจัยหนุนใหม่ มีการสะสมหุ้นในกรอบระหว่างผู้ซื้อที่ตั้งรับด้านล่างและผู้ขายที่ขายทำกำไรด้านบน",
            "structure": f"กรอบแนวรับ ${recent_low:.2f} และแนวต้าน ${recent_high:.2f}",
            "action_plan": f"ตั้งรับใกล้แนวรับ ${recent_low:.2f} หรือ Follow Buy เมื่อเบรกทะลุกรอบบน ${recent_high:.2f} เป้าหมาย ${target:.2f}",
            "invalidation": f"Stop Loss หากราคาปิดหลุดแนวรับ ${recent_low:.2f}",
            "win_rate": "60% (Range Trading Strategy)",
            "target_calc": f"ความสูงของกรอบบวกเพิ่มจากแนวต้านเป้าหมาย ${target:.2f}",
            "key_points": kp,
            "lines": [
                {"name": "Box Resistance", "color": "#f43f5e", "style": 2, "points": [{"time": times[-30], "value": recent_high}, {"time": times[-1], "value": recent_high}]},
                {"name": "Box Support", "color": "#10b981", "style": 2, "points": [{"time": times[-30], "value": recent_low}, {"time": times[-1], "value": recent_low}]}
            ]
        }

    return detected


BULLISH_DEVELOPING_WAVE_TYPES = {"Bullish Impulse (1-2-3-4-5)", "Emerging Bullish Impulse (1-2-3)"}


def detect_elliott_wave(candles: List[Dict[str, Any]], is_macro: bool = False) -> Optional[Dict[str, Any]]:
    """
    Detects Elliott Wave structures (Impulse 1-2-3-4-5, Emerging 1-2-3, or Corrective A-B-C)
    using strict academic Elliott Wave rules (Cardinal Rules 1-3, consecutive swings, and floor integrity).
    Returns detected: False when the stock is in consolidation or has an invalidated wave.
    """
    if not candles or len(candles) < 20:
        return {
            "detected": False,
            "type": "Insufficient Data",
            "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
            "current_wave": "ข้อมูลแท่งเทียนไม่เพียงพอ",
            "current_wave_badge": "N/A",
            "summary": "ข้อมูลแท่งเทียนไม่เพียงพอต่อการวิเคราะห์โครงสร้างคลื่น",
            "points": [],
            "lines": [],
            "target": None,
            "invalidation": None
        }

    recent = candles if is_macro else (candles[-252:] if len(candles) >= 252 else candles)
    current_c = recent[-1]
    current_p = round(float(current_c["close"]), 2)
    current_t = current_c["time"]

    # Volatility for adaptive threshold
    sample = recent[-60:] if len(recent) >= 60 else recent
    diffs = [abs(sample[i]["close"] - sample[i - 1]["close"]) / max(1e-4, sample[i - 1]["close"]) for i in range(1, len(sample))]
    avg_vol = sum(diffs) / len(diffs) if diffs else 0.015
    base_thresh = max(0.025, min(0.10, avg_vol * (4.0 if is_macro else 3.0)))

    # Find best swings with index tracking
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
            "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
            "current_wave": "ไม่มีโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์",
            "current_wave_badge": "Consolidation",
            "summary": "ไม่พบโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์ (ราคาอยู่ในสภาวะพักฐาน ปรับฐาน หรือสะสมพลังไซด์เวย์ แนะนำอ้างอิง Classical Chart Pattern หรือแนวรับต้าน EMA)",
            "points": [],
            "lines": [],
            "target": None,
            "invalidation": None
        }

    n_sw = len(best_swings)

    # 1. Active Bullish Impulse (0)-(1)-(2)-(3)-(4) -> developing Wave (5)
    for k in range(max(0, n_sw - 6), n_sw - 4):
        s0, s1, s2, s3, s4 = best_swings[k:k + 5]
        if s0["type"] == "low" and s1["type"] == "high" and s2["type"] == "low" and s3["type"] == "high" and s4["type"] == "low":
            len1 = s1["price"] - s0["price"]
            len3 = s3["price"] - s2["price"]

            # Cardinal Rules: W2 > W0, W3 > W1 and strong, W4 > W1 (no overlap)
            if s2["price"] > s0["price"] and s3["price"] > s1["price"] and len3 >= len1 * 0.8 and s4["price"] > s1["price"]:
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
                    clean_pts = []
                    seen_t = set()
                    for p in pts:
                        if p["time"] not in seen_t:
                            seen_t.add(p["time"])
                            clean_pts.append(p)
                        else:
                            clean_pts[-1] = p

                    lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                    return {
                        "detected": True,
                        "type": "Bullish Impulse (1-2-3-4-5)",
                        "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
                        "current_wave": curr_w_str,
                        "current_wave_badge": curr_badge,
                        "summary": f"เกิดโครงสร้างคลื่นขาขึ้น Bullish Impulse (1-2-3-4-5) โดย Wave (3) อยู่ที่ ${s3['price']:.2f} และ Wave (4) ฐานรับที่ ${s4['price']:.2f}",
                        "points": clean_pts,
                        "lines": lns,
                        "target": target5,
                        "invalidation": inval
                    }

    # 2. Completed Bullish Impulse (0)-(1)-(2)-(3)-(4)-(5)
    if n_sw >= 6:
        s0, s1, s2, s3, s4, s5 = best_swings[-6:]
        if s0["type"] == "low" and s1["type"] == "high" and s2["type"] == "low" and s3["type"] == "high" and s4["type"] == "low" and s5["type"] == "high":
            len1 = s1["price"] - s0["price"]
            len3 = s3["price"] - s2["price"]
            if s2["price"] > s0["price"] and s3["price"] > s1["price"] and s4["price"] > s1["price"] and s5["price"] > s3["price"] and len3 >= len1 * 0.8:
                pts = [
                    {"wave": "(0)", "time": s0["time"], "price": s0["price"], "label": "Start Wave (0)"},
                    {"wave": "(1)", "time": s1["time"], "price": s1["price"], "label": "Wave (1) Impulse"},
                    {"wave": "(2)", "time": s2["time"], "price": s2["price"], "label": "Wave (2) Retrace"},
                    {"wave": "(3)", "time": s3["time"], "price": s3["price"], "label": "Wave (3) Expansion"},
                    {"wave": "(4)", "time": s4["time"], "price": s4["price"], "label": "Wave (4) Base Floor"},
                    {"wave": "(5)", "time": s5["time"], "price": s5["price"], "label": "Wave (5) Peak"},
                ]
                lns = [{"time": p["time"], "value": p["price"]} for p in pts]
                return {
                    "detected": True,
                    "type": "Bullish Impulse Completed (1-2-3-4-5)",
                    "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
                    "current_wave": "Wave (5) Peak จบรอบคลื่นสมบูรณ์",
                    "current_wave_badge": "Wave (5) Peak",
                    "summary": f"คลื่นขาขึ้น Bullish Impulse (1-2-3-4-5) จบรอบสมบูรณ์ที่ยอดคลื่น (5) ระดับ ${s5['price']:.2f} กำลังเข้าสู่ช่วงพักฐาน Corrective Phase",
                    "points": pts,
                    "lines": lns,
                    "target": round(s5["price"], 2),
                    "invalidation": round(s4["price"], 2)
                }

    # 3. Emerging Bullish Impulse (0)-(1)-(2) -> developing Wave (3)
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
                        clean_pts = []
                        seen_t = set()
                        for p in pts:
                            if p["time"] not in seen_t:
                                seen_t.add(p["time"])
                                clean_pts.append(p)
                            else:
                                clean_pts[-1] = p

                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        return {
                            "detected": True,
                            "type": "Emerging Bullish Impulse (1-2-3)",
                            "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
                            "current_wave": "Wave (3) Impulse กำลังดีดตัวขยายตัว",
                            "current_wave_badge": "Wave (3)",
                            "summary": f"เกิดโครงสร้างต้นรอบคลื่น Wave (1-2-3) โดย Wave (2) ยกฐานรับที่ ${s2['price']:.2f} และกำลังวิ่งขึ้นทดสอบเป้าหมาย Wave (3)",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target3,
                            "invalidation": inval
                        }

    # 4. Clean Corrective Wave (A-B-C)
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
                        clean_pts = []
                        seen_t = set()
                        for p in pts:
                            if p["time"] not in seen_t:
                                seen_t.add(p["time"])
                                clean_pts.append(p)
                            else:
                                clean_pts[-1] = p

                        lns = [{"time": p["time"], "value": p["price"]} for p in clean_pts]
                        return {
                            "detected": True,
                            "type": "Corrective Wave (A-B-C)",
                            "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
                            "current_wave": "Corrective Wave (C) กำลังปรับฐานหาจุดสมดุล",
                            "current_wave_badge": "Wave (C)",
                            "summary": f"โครงสร้างคลื่นปรับฐาน Corrective (A-B-C) หลังยอดดอย ${s_top['price']:.2f} โดยมีรีบาวด์ Wave (B) ที่ ${sb['price']:.2f}",
                            "points": clean_pts,
                            "lines": lns,
                            "target": target_c,
                            "invalidation": inval
                        }

    # 5. Consolidation / Sideway (No valid unbroken wave)
    return {
        "detected": False,
        "type": "No Clear Wave / Consolidation",
        "degree": "All-Time Supercycle" if is_macro else "Intermediate Cycle (52W)",
        "current_wave": "ไม่มีโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์",
        "current_wave_badge": "Consolidation",
        "summary": "ไม่พบโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์ (ราคาอยู่ในสภาวะพักฐาน ปรับฐาน หรือสะสมพลังไซด์เวย์ แนะนำอ้างอิง Classical Chart Pattern หรือแนวรับต้าน EMA)",
        "points": [],
        "lines": [],
        "target": None,
        "invalidation": None
    }


def detect_earnings_history(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Approximates quarterly earnings reactions by taking the highest-volume candle
    in each ~62-bar window. These are volume spikes, not confirmed announcement dates.
    """
    if not candles or len(candles) < 2:
        return []

    recent = candles[-750:] if len(candles) >= 750 else candles
    events = []
    q_len = 62 if len(recent) >= 62 else len(recent)
    for start in range(0, len(recent), q_len):
        chunk = recent[start:start + q_len]
        if len(chunk) < min(20, q_len):
            continue
        max_c = max(chunk, key=lambda c: c.get("volume", 0))
        idx = recent.index(max_c)
        if idx > 0:
            avg_vol = sum(c.get("volume", 0) for c in chunk) / len(chunk)
            if max_c.get("volume", 0) >= avg_vol * 1.3:
                prev_c = recent[idx - 1]
                if prev_c.get("close", 0) > 0:
                    pct = round(((max_c["close"] - prev_c["close"]) / prev_c["close"]) * 100, 1)
                    events.append({
                        "time": max_c["time"],
                        "reaction_pct": pct,
                        "text": f"📊 Vol {pct:+.1f}%",
                        "color": "#10b981" if pct >= 0 else "#f43f5e",
                        "position": "belowBar" if pct >= 0 else "aboveBar",
                    })

    events.sort(key=lambda x: x["time"])
    return events


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
    pivots: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    AI Multi-Technical Confluence Decision Engine.
    Evaluates 5 dimensions: Trend, Momentum, Value/Fibo, Volume Flow, and Pattern Geometry.
    Pins actionable BUY, SELL, DCA points directly on the chart with full multi-indicator reasoning.
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
        rs = avg_g / max(1e-6, avg_l)
        rsi_vals[14] = 100.0 - (100.0 / (1.0 + rs))
        for i in range(15, n):
            avg_g = (avg_g * 13.0 + gains[i - 1]) / 14.0
            avg_l = (avg_l * 13.0 + losses[i - 1]) / 14.0
            rs = avg_g / max(1e-6, avg_l)
            rsi_vals[i] = 100.0 - (100.0 / (1.0 + rs))

    signals = []
    scan_start = max(15, n - 220)  # scan past ~10-11 months

    # 1. Detect Swing Troughs (BUY / DCA Signals)
    k_window = 3
    for i in range(scan_start, n - k_window):
        if all(lows[i] <= lows[i + j] for j in range(-k_window, k_window + 1) if j != 0):
            c_low = lows[i]
            c_close = closes[i]
            c_vol = volumes[i]
            c_rsi = rsi_vals[i]
            c_ema50 = ema50_vals[i]
            c_ema200 = ema200_vals[i]
            v_avg = max(1.0, vol20_avg[i])

            reasons = []
            score = 0

            # Factor 1: Value / Fibonacci Golden Pocket / POC
            f618 = fibo_levels.get("61.8", 0.0)
            f500 = fibo_levels.get("50.0", 0.0)
            f786 = fibo_levels.get("78.6", 0.0)
            if f618 > 0 and abs(c_low - f618) / f618 <= 0.035:
                score += 1
                reasons.append(f"โซนราคาคุณค่า: ทดสอบแนวรับ Fibonacci 61.8% Golden Pocket (${f618:.2f}) รับอยู่หมัด")
            elif f500 > 0 and abs(c_low - f500) / f500 <= 0.035:
                score += 1
                reasons.append(f"โซนราคาคุณค่า: เด้งทดสอบแนวรับ Fibonacci 50.0% (${f500:.2f})")
            elif poc_price > 0 and abs(c_low - poc_price) / poc_price <= 0.035:
                score += 1
                reasons.append(f"โซนราคาคุณค่า: ทดสอบ Inception POC โซนสะสมวอลุ่มหนาแน่น (${poc_price:.2f})")

            # Factor 2: Momentum / RSI Hook
            if c_rsi <= 38:
                score += 1
                reasons.append(f"โมเมนตัมกลับตัว: RSI เข้าสู่โซน Oversold ({c_rsi:.1f}) พร้อมส่งสัญญาณ Bullish Hook")
            elif i > 1 and rsi_vals[i] > rsi_vals[i - 1] and rsi_vals[i - 1] <= 42:
                score += 1
                reasons.append(f"โมเมนตัมกลับตัว: RSI ดีดยกฐานกลับตัวจากโซนต่ำ ({c_rsi:.1f})")

            # Factor 3: Volume Confirmation
            vol_ratio = c_vol / v_avg
            if vol_ratio >= 1.15:
                score += 1
                reasons.append(f"สภาพคล่องสถาบัน: ปริมาณการซื้อขายพุ่งสูง {vol_ratio:.1f}x ของค่าเฉลี่ย 20 วัน ยืนยันแรงซื้อดูดซับ")

            # Factor 4: Trend Alignment
            if c_close >= c_ema200:
                score += 1
                reasons.append(f"แนวโน้มระยะยาว: ราคายืนเหนือ EMA 200 (${c_ema200:.2f}) โครงสร้างหลักเป็นขาขึ้น")
            elif c_close >= c_ema50:
                score += 1
                reasons.append(f"แนวโน้มระยะกลาง: ราคายืนเหนือ EMA 50 (${c_ema50:.2f})")

            # Factor 5: Pattern & Support Floor
            if pattern and pattern.get("type") and "bull" in pattern["type"].lower():
                score += 1
                reasons.append(f"โครงสร้างกราฟ: เกิดการกลับตัวตามรูปแบบ {pattern['name']}")

            if score >= 3:
                is_strong = score >= 4
                sl = round(c_low * 0.965, 2)
                tp = round(c_close * 1.12, 2)
                rr = round((tp - c_close) / max(0.01, c_close - sl), 1)
                signals.append({
                    "time": times[i],
                    "price": round(c_close, 2),
                    "action": "BUY" if is_strong else "DCA",
                    "type": "STRONG BUY" if is_strong else "SMART DCA",
                    "score": score,
                    "score_text": f"{score}/5 สัญญาณคอนฟลูเอนซ์",
                    "badge": f"🚀 STRONG BUY ({score}/5)" if is_strong else f"💎 SMART DCA ({score}/5)",
                    "summary": f"จุดเข้าซื้อคอนฟลูเอนซ์ระดับ {score}/5 ที่ราคา ${c_close:.2f} มีการประสานกันของสัญญาณทางเทคนิคถึง {score} ประการ",
                    "reasons": reasons,
                    "stop_loss": sl,
                    "target": tp,
                    "rr": f"1:{rr}",
                    "marker_shape": "arrowUp" if is_strong else "circle",
                    "marker_color": "#10b981" if is_strong else "#38bdf8"
                })

    # 2. Detect Swing Peaks (SELL / TAKE PROFIT Signals)
    for i in range(scan_start, n - k_window):
        if all(highs[i] >= highs[i + j] for j in range(-k_window, k_window + 1) if j != 0):
            c_high = highs[i]
            c_close = closes[i]
            c_vol = volumes[i]
            c_rsi = rsi_vals[i]
            v_avg = max(1.0, vol20_avg[i])

            reasons = []
            score = 0

            # Resistance: ATH / Fibo 0.0% / 23.6%
            ath_p = fibo_levels.get("0.0", 0.0)
            if ath_p > 0 and abs(c_high - ath_p) / ath_p <= 0.03:
                score += 1
                reasons.append(f"แนวต้านสำคัญ: ทดสอบ All-Time High (${ath_p:.2f}) ชนกรอบต้านสูงสุด")

            # Momentum: Overbought
            if c_rsi >= 68:
                score += 1
                reasons.append(f"โมเมนตัมตึงตัว: RSI แตะระดับ Overbought ร้อนแรง ({c_rsi:.1f}) เสี่ยงพักฐาน")

            # Volume Churn / Spike at top
            if c_vol / v_avg >= 1.25:
                score += 1
                reasons.append("สภาพคล่องเทขาย: วอลุ่มพุ่งสูงที่ยอดบน สะท้อนการขายทำกำไรของรายใหญ่ (Distribution)")

            # Pattern Resistance
            if pattern and pattern.get("neckline"):
                score += 1
                reasons.append("โครงสร้างราคา: ทดสอบแนวต้านโครงสร้างหลักและเริ่มมีแรงขายกดดัน")

            if score >= 3:
                sl = round(c_high * 1.025, 2)
                tp = round(c_close * 0.92, 2)
                signals.append({
                    "time": times[i],
                    "price": round(c_close, 2),
                    "action": "SELL",
                    "type": "TAKE PROFIT",
                    "score": score,
                    "score_text": f"{score}/5 สัญญาณคอนฟลูเอนซ์",
                    "badge": f"🎯 TAKE PROFIT ({score}/5)",
                    "summary": f"จุดขายทำกำไร / ลดพอร์ต ที่ราคา ${c_close:.2f} สัญญาณ Overbought ประสานแนวต้านสำคัญ",
                    "reasons": reasons,
                    "stop_loss": sl,
                    "target": tp,
                    "rr": "1:2.0",
                    "marker_shape": "arrowDown",
                    "marker_color": "#f43f5e"
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
    curr_close = closes[-1]
    curr_low = lows[-1]
    curr_high = highs[-1]
    curr_reasons = []
    curr_score = 0

    # Evaluate current conditions
    if current_st_trend == "BULLISH":
        curr_score += 1
        curr_reasons.append("แนวโน้ม SuperTrend: ฝั่งกระทิง (BULLISH) คุมทิศทางราคา")
    else:
        curr_reasons.append("แนวโน้ม SuperTrend: สภาวะปรับฐาน (BEARISH)")

    if current_rsi < 35:
        curr_score += 2
        curr_reasons.append(f"โมเมนตัม RSI: โซน Oversold มีแต้มต่อสูง ({current_rsi:.1f})")
    elif current_rsi < 48:
        curr_score += 1
        curr_reasons.append(f"โมเมนตัม RSI: ปลอดโปร่ง ไม่ร้อนแรง ({current_rsi:.1f})")
    elif current_rsi > 70:
        curr_reasons.append(f"โมเมนตัม RSI: เข้าเขต Overbought ({current_rsi:.1f}) ควรระวังการพักตัว")

    if current_macd_hist >= 0:
        curr_score += 1
        curr_reasons.append(f"โมเมนตัม MACD: Histogram เป็นบวก (+{current_macd_hist:.2f}) มีโมเมนตัมหนุน")

    f618 = fibo_levels.get("61.8", 0.0)
    if f618 > 0 and abs(curr_close - f618) / f618 <= 0.045:
        curr_score += 1
        curr_reasons.append(f"โซน Fibonacci: ราคาอยู่ใกล้ Golden Pocket 61.8% (${f618:.2f})")

    if pattern and pattern.get("target") and pattern.get("upside_pct", 0) > 5:
        curr_score += 1
        curr_reasons.append(f"เป้าหมาย Pattern: โครงสร้าง {pattern['name']} เปิด Upside +{pattern.get('upside_pct', 0)}%")

    if cdc_zone == "green":
        curr_score += 1
        curr_reasons.append("สัญญาณ CDC ActionZone: อยู่ใน โซนเขียว (Bullish Trend / ถือรันเทรนด์ ห้ามขายหมู)")
    elif cdc_zone == "blue":
        curr_score += 1
        curr_reasons.append("สัญญาณ CDC ActionZone: โซนฟ้า (Bullish Pullback ย่อตัวทดสอบแนวรับเพื่อไปต่อ)")
    elif cdc_zone == "orange":
        curr_reasons.append("สัญญาณ CDC ActionZone: โซนส้ม (Bearish Rebound ระวังเด้งเพื่อลงต่อ)")
    elif cdc_zone == "red":
        curr_reasons.append("สัญญาณ CDC ActionZone: โซนแดง (Bearish Trend แนะนำถือเงินสด)")

    if elliott_wave and elliott_wave.get("detected"):
        ew_type = elliott_wave.get("type", "")
        ew_target = elliott_wave.get("target") or 0.0
        if ew_type in BULLISH_DEVELOPING_WAVE_TYPES:
            curr_score += 1
            curr_reasons.append(f"โครงสร้าง Elliott Wave: กำลังเคลื่อนที่ใน {elliott_wave.get('current_wave', 'Impulse Wave')} สู่เป้าหมาย ${ew_target:.2f}")
        else:
            curr_reasons.append(f"คำเตือน Elliott Wave: {elliott_wave.get('current_wave', ew_type)} (ไม่นับเป็นสัญญาณซื้อ)")

    if pivots:
        p_r1 = pivots.get("r1", 0.0)
        p_s1 = pivots.get("s1", 0.0)
        if p_r1 > 0 and curr_close >= p_r1:
            curr_score += 1
            curr_reasons.append(f"ระดับราคา Pivot: ยืนเหนือแนวต้าน R1 (${p_r1:.2f}) เปลี่ยนเป็นแนวรับใหม่")
        elif p_s1 > 0 and p_s1 <= curr_close <= p_s1 * 1.035:
            curr_score += 1
            curr_reasons.append(f"ระดับราคา Pivot: ดีดตัวทดสอบแนวรับสำคัญ S1 (${p_s1:.2f})")

    curr_score = min(5, max(1, curr_score))

    if curr_score >= 4:
        act = "BUY"
        b_type = "STRONG BUY"
        badge = f"🚀 STRONG BUY ({curr_score}/5)"
        m_shape = "arrowUp"
        m_col = "#10b981"
        summary_txt = f"สถานะปัจจุบันราคา ${curr_close:.2f} อยู่ในจุดได้เปรียบสูง สัญญาณคอนฟลูเอนซ์ระดับ {curr_score}/5 พร้อมลุ้นฟื้นตัว"
    elif curr_score == 3:
        act = "DCA"
        b_type = "SMART DCA"
        badge = f"💎 SMART DCA ({curr_score}/5)"
        m_shape = "circle"
        m_col = "#38bdf8"
        summary_txt = f"สถานะปัจจุบันราคา ${curr_close:.2f} เหมาะแก่การทยอยสะสม (DCA) คอนฟลูเอนซ์ระดับ 3/5 ปลอดภัย"
    elif current_rsi > 70:
        act = "SELL"
        b_type = "TRIM"
        badge = f"🎯 TRIM / TAKE PROFIT (4/5)"
        m_shape = "arrowDown"
        m_col = "#f43f5e"
        summary_txt = f"สถานะปัจจุบันราคา ${curr_close:.2f} วิ่งขึ้นมาในโซนตึงตัว แนะนำแบ่งทำกำไรหรือเลื่อน Trailing Stop"
    else:
        act = "HOLD"
        b_type = "HOLD & MONITOR"
        badge = f"⚖️ HOLD & MONITOR ({curr_score}/5)"
        m_shape = "circle"
        m_col = "#94a3b8"
        summary_txt = f"สถานะปัจจุบันราคา ${curr_close:.2f} อยู่ในเกณฑ์ถือครอง (HOLD) ติดตามแนวรับแนวต้านสำคัญ"

    current_signal = {
        "time": times[-1],
        "price": round(curr_close, 2),
        "action": act,
        "type": b_type,
        "score": curr_score,
        "score_text": f"{curr_score}/5 สัญญาณคอนฟลูเอนซ์",
        "badge": badge,
        "summary": summary_txt,
        "reasons": curr_reasons,
        "stop_loss": round(curr_close - 1.5 * atr_val, 2) if act != "SELL" else round(curr_close + 1.5 * atr_val, 2),
        "target": round(curr_close + 2.5 * atr_val, 2) if act != "SELL" else round(curr_close - 2.0 * atr_val, 2),
        "rr": "1:2.5" if act != "SELL" else "1:2.0",
        "marker_shape": m_shape,
        "marker_color": m_col,
        "is_latest": True
    }

    # If the latest bar already has a signal, update it or append
    if historical_signals and historical_signals[-1]["time"] == times[-1]:
        historical_signals[-1] = current_signal
    else:
        historical_signals.append(current_signal)

    return historical_signals


def compute_fibo_and_indicators(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute Inception High/Low (ATH/ATL), Fibonacci retracement levels from inception,
    Inception-anchored VWAP, Volume Profile POC from inception, Moving Averages from inception,
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

    # 2. Inception & 52-Week Cycle Fibonacci Retracements
    diff_all = ath_val - atl_val
    fibo_macro = {
        "0.0": round(ath_val, 2),
        "23.6": round(ath_val - 0.236 * diff_all, 2),
        "38.2": round(ath_val - 0.382 * diff_all, 2),
        "50.0": round(ath_val - 0.500 * diff_all, 2),
        "61.8": round(ath_val - 0.618 * diff_all, 2),
        "78.6": round(ath_val - 0.786 * diff_all, 2),
        "100.0": round(atl_val, 2)
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

    # 3. SuperTrend (10, 3) across all bars from inception
    tr_list = []
    atr10 = []
    for i in range(n):
        if i == 0:
            tr_list.append(highs[i] - lows[i])
        else:
            tr_list.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
        if i >= 9:
            atr10.append(sum(tr_list[i - 9 : i + 1]) / 10.0)
        else:
            atr10.append(tr_list[-1])

    upper_band = 0.0
    lower_band = 0.0
    in_uptrend = True
    last_st_val = closes[-1]
    for i in range(n):
        hl2 = (highs[i] + lows[i]) / 2.0
        basic_upper = hl2 + 3.0 * atr10[i]
        basic_lower = hl2 - 3.0 * atr10[i]
        if i == 0:
            upper_band = basic_upper
            lower_band = basic_lower
        else:
            if basic_lower > lower_band or closes[i - 1] < lower_band:
                lower_band = basic_lower
            if basic_upper < upper_band or closes[i - 1] > upper_band:
                upper_band = basic_upper

        if in_uptrend:
            if closes[i] < lower_band:
                in_uptrend = False
        else:
            if closes[i] > upper_band:
                in_uptrend = True

        last_st_val = lower_band if in_uptrend else upper_band

    # 4. Inception-Anchored VWAP (calculated from day 1 of entering the market)
    cum_vol = 0
    cum_tp_vol = 0
    vwap_val = closes[-1]
    for i in range(n):
        tp = (highs[i] + lows[i] + closes[i]) / 3.0
        v = volumes[i]
        cum_vol += v
        cum_tp_vol += tp * v
    if cum_vol > 0:
        vwap_val = cum_tp_vol / cum_vol

    # 5. Inception Volume Profile POC (calculated across all volume since entering the market)
    p_min = atl_val
    p_max = ath_val
    buckets = 50
    bucket_size = (p_max - p_min) / buckets if p_max > p_min else 1.0
    vol_bins = [0] * buckets
    for i in range(n):
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
        rs = avg_g / max(1e-9, avg_l)
        rsi_val = 100.0 - (100.0 / (1.0 + rs))
        for i in range(14, len(gains)):
            avg_g = (avg_g * 13.0 + gains[i]) / 14.0
            avg_l = (avg_l * 13.0 + losses[i]) / 14.0
            rs = avg_g / max(1e-9, avg_l)
            rsi_val = 100.0 - (100.0 / (1.0 + rs))

    # 9. 52-Week High & Low
    w52_high = round(max(highs[-252:]), 2)
    w52_low = round(min(lows[-252:]), 2)

    # 10. Pivot Points (Classic) from recent 22 bars
    m_high = max(highs[-22:])
    m_low = min(lows[-22:])
    m_close = closes[-1]
    p_pivot = round((m_high + m_low + m_close) / 3.0, 2)
    r1 = round(2.0 * p_pivot - m_low, 2)
    s1 = round(2.0 * p_pivot - m_high, 2)
    r2 = round(p_pivot + (m_high - m_low), 2)
    s2 = round(p_pivot - (m_high - m_low), 2)

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
    atr14_val = atr10[-1] if len(atr10) > 0 else 0.0
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

    # 18. AI Multi-Technical Confluence Decision Engine
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
        pivots={"pivot": p_pivot, "r1": r1, "s1": s1, "r2": r2, "s2": s2}
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
        "earnings_history": detect_earnings_history(candles),
        "cdc_actionzone": cdc_actionzone
    }


def load_candles_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_candles_cache(cache: Dict[str, Any]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


# Bump whenever compute_fibo_and_indicators output changes so cached entries are recomputed from cached candles.
INDICATOR_SCHEMA_VERSION = 2


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
                chart_data = compute_fibo_and_indicators(candles)
                chart_data["timestamp"] = fetched_ts
                chart_data["full_history"] = True
                chart_data["schema_version"] = INDICATOR_SCHEMA_VERSION
                return t, chart_data
            except Exception as e:
                return t, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(_fetch_and_process, tickers_to_fetch))

        for t, data in results:
            if data and data.get("candles"):
                cache[t] = data

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
        entry_copy = dict(entry)
        if "cdc_actionzone" in entry_copy and isinstance(entry_copy["cdc_actionzone"], dict):
            cdc = dict(entry_copy["cdc_actionzone"])
            cdc.pop("candle_colors", None)
            entry_copy["cdc_actionzone"] = cdc
        out[t] = {**entry_copy, "candles": monthly + candles[cut:]}
    return out
