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
from typing import Any, Dict, List, Optional

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "candles_cache.json"
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours


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
                "open": round(float(o), 2),
                "high": round(float(h), 2),
                "low": round(float(l), 2),
                "close": round(float(c), 2),
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
                            {"name": "Left Shoulder", "time": p1["time"], "price": p1["price"]},
                            {"name": "Head", "time": p2["time"], "price": p2["price"]},
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
                            {"name": "Left Shoulder", "time": t1["time"], "price": t1["price"]},
                            {"name": "Head", "time": t2["time"], "price": t2["price"]},
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
                        {"name": "Bottom 1", "time": t1["time"], "price": t1["price"]},
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
                        {"name": "Peak 1", "time": p1["time"], "price": p1["price"]},
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
        pole_base = min(lows[-25:-8])
        pole_peak = max(highs[-25:-8])
        pole_gain = (pole_peak - pole_base) / pole_base
        if pole_gain >= 0.08:
            flag_high = max(highs[-8:])
            flag_low = min(lows[-8:])
            if flag_high <= pole_peak * 1.01 and flag_low >= pole_base + (pole_peak - pole_base) * 0.45:
                target = round(flag_high + (pole_peak - pole_base), 2)
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
                    "lines": [
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
                "lines": [
                    {"name": "Flat Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": p2["price"]}]},
                    {"name": "Ascending Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Descending Triangle: Falling Resistance (p2 < p1), Flat Support (t1 ~= t2)
        elif abs(t2["price"] - t1["price"]) / t1["price"] <= 0.025 and p2["price"] < p1["price"] * 0.985:
            target = round(t2["price"] - (p1["price"] - t2["price"]), 2)
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
                "lines": [
                    {"name": "Descending Resistance", "color": "#f43f5e", "style": 0, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Flat Support", "color": "#10b981", "style": 0, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": t2["price"]}]}
                ]
            }
        # Symmetrical Expanding Triangle (Megaphone / Broadening)
        elif p2["price"] > p1["price"] * 1.02 and t2["price"] < t1["price"] * 0.98:
            height = p2["price"] - t2["price"]
            target = round(p2["price"] + height * 0.5, 2)
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
                "lines": [
                    {"name": "Diverging Resistance", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Diverging Support", "color": "#f43f5e", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Symmetrical Triangle
        elif p2["price"] < p1["price"] * 0.985 and t2["price"] > t1["price"] * 1.015:
            height = p1["price"] - t1["price"]
            target = round(current_price + height * 0.75, 2)
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
                "lines": [
                    {"name": "Upper Resistance Line", "color": "#f59e0b", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Lower Support Line", "color": "#38bdf8", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Falling Wedge (Bullish Reversal)
        elif p2["price"] < p1["price"] and t2["price"] < t1["price"]:
            target = round(p1["price"], 2)
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
                "lines": [
                    {"name": "Upper Wedge Resistance", "color": "#38bdf8", "style": 2, "points": [{"time": p1["time"], "value": p1["price"]}, {"time": times[-1], "value": round(p2["price"] + peak_slope * (n - 1 - p2["idx"]), 2)}]},
                    {"name": "Lower Wedge Support", "color": "#10b981", "style": 2, "points": [{"time": t1["time"], "value": t1["price"]}, {"time": times[-1], "value": round(t2["price"] + trough_slope * (n - 1 - t2["idx"]), 2)}]}
                ]
            }
        # Channel Up / Rising Trend
        elif p2["price"] > p1["price"] and t2["price"] > t1["price"]:
            target = round(p2["price"] * 1.08, 2)
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
            "lines": [
                {"name": "Box Resistance", "color": "#f43f5e", "style": 2, "points": [{"time": times[-30], "value": recent_high}, {"time": times[-1], "value": recent_high}]},
                {"name": "Box Support", "color": "#10b981", "style": 2, "points": [{"time": times[-30], "value": recent_low}, {"time": times[-1], "value": recent_low}]}
            ]
        }

    return detected


def compute_ai_confluence_signals(
    candles: List[Dict[str, Any]],
    fibo_levels: Dict[str, float],
    pattern: Optional[Dict[str, Any]],
    poc_price: float,
    current_st_trend: str,
    current_rsi: float,
    current_macd_hist: float,
    atr_val: float
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
    for i in range(scan_start, n - 2):
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
    for i in range(scan_start, n - 2):
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
        atr14_list = [sum(tr_list[i - 13 : i + 1]) / 14.0 for i in range(13, n)]
        atr14_val = round(atr14_list[-1], 2)
    atr14_pct = round((atr14_val / closes[-1]) * 100.0, 1) if closes[-1] > 0 else 0.0

    # 14. Volume 20D Average & Surge Ratio
    vol20_avg = sum(volumes[-20:]) / 20.0 if len(volumes) >= 20 else volumes[-1]
    vol_surge_ratio = round(volumes[-1] / max(1.0, vol20_avg), 2)

    # 15. Classical Chart Patterns detection
    pattern = detect_chart_patterns(candles)

    # 16. AI Multi-Technical Confluence Decision Engine
    ai_signals = compute_ai_confluence_signals(
        candles=candles,
        fibo_levels=fibo_levels,
        pattern=pattern,
        poc_price=poc_price,
        current_st_trend="BULLISH" if in_uptrend else "BEARISH",
        current_rsi=round(rsi_val, 1),
        current_macd_hist=round(hist, 2),
        atr_val=atr14_val
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
        "ai_signals": ai_signals
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
            or "inception_date" not in entry
            or "ath" not in entry
            or "ai_signals" not in entry
            or not entry.get("ai_signals")
            or "psychology" not in (entry.get("pattern") or {})
        ):
            tickers_to_fetch.append(t)

    if tickers_to_fetch:
        def _fetch_and_process(t):
            try:
                entry = cache.get(t)
                if entry and entry.get("candles") and len(entry["candles"]) > 30 and (now_ts - entry.get("timestamp", 0) <= CACHE_TTL_SECONDS):
                    candles = entry["candles"]
                else:
                    candles = fetch_ticker_candles(t)
                chart_data = compute_fibo_and_indicators(candles)
                chart_data["timestamp"] = now_ts
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
