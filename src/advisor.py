"""Advisor page (reports/advisor.html): the portfolio advice from a consultation, kept as data.

The advice text is dated and does not change by itself. What stays live is the trigger table:
each row is a price level, and the page marks whether today's price has reached it. Prices are
fetched from TradingView when the page is built, and again in the browser on refresh.

Add a new consultation by editing CONSULT_DATE, the card lists and TRIGGERS below.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.nav import nav_bar_html
from src.trades import data_path

CONSULT_DATE = "30 ต.ค. 2569"

SYMBOLS = {
    "LLY": "NYSE:LLY",
    "SMH": "NASDAQ:SMH",
    "GPIQ": "NASDAQ:GPIQ",
    "AEHR": "NASDAQ:AEHR",
    "CHPY": "AMEX:CHPY",
}

# What the consultation concluded, three lines a reader can act on.
HEADLINES = [
    ("⚖️", "ลด LLY จาก 78% ให้เหลือราว 50%", "แบ่งขาย 3 ไม้ แล้วเอาเงินไปทำพอร์ตแกน VOO"),
    ("🧹", "ขาย NOK กับ BAC ที่ได้เกรด F", "รอวันที่ราคาเด้งก่อน ไม่ขายวันที่ร่วงแรง"),
    ("🔌", "อยากได้หุ้นชิป เลือก SMH ไม่ใช่ CHPY", "รอแท่งกลับตัวเหนือ EMA200 แล้วค่อยซื้อไม้แรก"),
]

# Portfolio plan, in priority order. tone: go | wait | stop
PLAN = [
    {"tone": "go", "title": "1. ลด LLY ลงทีละขั้น",
     "lines": ["LLY คิดเป็น 78% ของพอร์ต ถ้าลง 25% พอร์ตจะหายราว 330,000 บาท.",
               "ราคายืดเหนือ EMA200 ไป 29% และราคาเป้านักวิเคราะห์สูงกว่าแค่ 1.3%.",
               "ขาย 3 ไม้ ไม้ละราว 3 หุ้น ห่างกัน 1 ถึง 2 สัปดาห์. ถ้าหลุด 1,364 ให้ขายไม้ที่เหลือเลย."]},
    {"tone": "go", "title": "2. ขาย NOK และ BAC",
     "lines": ["ทั้งสองตัวได้เกรด F. NOK กำไรหด 6.7% ส่วน BAC ยอดขายลด 1%.",
               "รวมกันราว 3,177 USD. ย้ายไปหุ้นเกรด A ดีกว่ารอกลับมาเท่าทุน."]},
    {"tone": "go", "title": "3. สร้างพอร์ตแกนด้วย VOO",
     "lines": ["ตอนนี้ VOO มีแค่ 0.7% ของพอร์ต.",
               "เป้าคือราว 18 ถึง 20%. ซื้อตามรอบที่ขาย LLY."]},
    {"tone": "wait", "title": "4. เติม VRT เมื่อมีแท่งกลับตัว",
     "lines": ["คะแนนพื้นฐานเต็ม 100% และราคาเป้าสูงกว่า 42.6%.",
               "วันที่ปรึกษาเป็นวันร่วงแรง จึงรอแท่งกลับตัวก่อน. งบรอบหน้าอีก 117 วัน."]},
    {"tone": "wait", "title": "5. MNST, ABNB, APP รอหลังงบ",
     "lines": ["APP งบ 4 พ.ย. ABNB และ MNST งบ 5 พ.ย. ห้ามซื้อเพิ่มก่อนงบ.",
               "MNST เกรด A+ ดีที่สุดในพอร์ต ถ้างบผ่านค่อยเติม."]},
    {"tone": "wait", "title": "6. GOOGL ค่อยๆ ซื้อ",
     "lines": ["พื้นฐานเต็ม 100% และ P/E 14.7 แต่ราคาต่ำกว่า EMA200 14.5%.",
               "ซื้อไม้เล็กเมื่อ RSI กลับตัวขึ้น. หยุดซื้อถ้าหลุด 266."]},
]

# Target mix after the plan, percent of the portfolio.
TARGET_MIX = [
    ("LLY", 50, "#a78bfa"), ("VOO", 19, "#3b82f6"), ("GOOGL", 10, "#22d3ee"), ("VRT", 7, "#10b981"),
    ("MNST", 5, "#f59e0b"), ("ABNB + APP", 6, "#f472b6"), ("เงินสด", 3, "#64748b"),
]

# Funds and stocks the user asked about. verdict tone: go | wait | stop
ASKED = [
    {"ticker": "SMH", "name": "VanEck Semiconductor ETF", "tone": "go", "verdict": "น่าซื้อที่สุดในกลุ่มชิป",
     "lines": ["ปีนี้ได้ +45.5% ใกล้ CHPY แต่ร่วงน้อยกว่าและไม่ต้องเสียภาษีปันผลบ่อย.",
               "ราคาแตะ EMA200 พอดี แต่วันที่ปรึกษาลง 6.7% จึงรอแท่งกลับตัว.",
               "ขนาด 5 ถึง 8% ของพอร์ต แบ่ง 3 ไม้ตามตารางจุดซื้อด้านล่าง."]},
    {"ticker": "GPIQ", "name": "Goldman Sachs Nasdaq-100 Premium Income", "tone": "go", "verdict": "ซื้อได้ถ้าอยากได้ปันผล",
     "lines": ["ปันผลรายเดือนราว 10% ต่อปี ค่าธรรมเนียม 0.35%.",
               "ปีนี้ได้ +12.4% ใกล้ QQQ แต่ร่วงน้อยกว่า.",
               "ถ้าเน้นให้พอร์ตโต VOO หรือ QQQ ดีกว่า."]},
    {"ticker": "AEHR", "name": "Aehr Test Systems", "tone": "wait", "verdict": "หุ้นเก็งกำไร รอหลังงบ 2 พ.ย.",
     "lines": ["เกรด F (8.6). ยอดขายลด 15% กำไรลด 82% และกระแสเงินสดติดลบ.",
               "จุดแข็งคือไม่มีหนี้ และนักวิเคราะห์ 5 คนให้ซื้อ ราคาเป้า 141.75.",
               "ถ้าซื้อ ไม่เกิน 2% ของพอร์ต และเตรียมใจว่าอาจหายครึ่ง."]},
    {"ticker": "CHPY", "name": "YieldMax Semiconductor Option Income", "tone": "stop", "verdict": "ไม่แนะนำสำหรับพอร์ตนี้",
     "lines": ["ปันผลราว 43% ต่อปี แต่ราคาแทบไม่โต เพราะจ่ายกำไรออกมาหมด.",
               "ร่วงหนักสุด 27.6% มากกว่า SMH ที่ได้ผลตอบแทนพอๆ กัน.",
               "ถ้าหุ้นชิปไม่ขึ้น ปันผลจะมาจากเงินต้นของเราเอง."]},
]

# Measured 2025-12-31 to 2026-10-30 from Yahoo Finance daily data, dividends reinvested.
BACKTEST_YTD = {
    "period": "31 ธ.ค. 68 ถึง 30 ต.ค. 69",
    "rows": [
        ("CHPY", 1.8, 42.8, 44.8, -27.6),
        ("SMH", 45.5, 0.0, 45.5, -24.6),
        ("QQQ", 12.8, 0.4, 13.2, -11.7),
        ("GPIQ", 3.0, 9.1, 12.4, -9.5),
        ("VOO", 11.0, 0.9, 12.0, -8.9),
    ],
}

# Price levels to watch. kind "above": reached when price >= level. kind "below": price <= level.
TRIGGERS = [
    {"ticker": "SMH", "kind": "above", "level": 519.0, "action": "ซื้อไม้ 1", "note": "ปิดเหนือ EMA200 และมีแท่งกลับตัว"},
    {"ticker": "SMH", "kind": "below", "level": 505.0, "action": "ซื้อไม้ 2", "note": "ย่อถึงขอบล่าง Bollinger แถว 500"},
    {"ticker": "SMH", "kind": "above", "level": 570.6, "action": "ซื้อไม้ 3", "note": "ยืนเหนือ EMA50 ได้ แปลว่าขาลงจบ"},
    {"ticker": "SMH", "kind": "below", "level": 467.0, "action": "หยุดซื้อ", "note": "ต่ำกว่า EMA200 เกิน 10%"},
    {"ticker": "GPIQ", "kind": "below", "level": 55.5, "action": "ซื้อไม้ 1", "note": "ราคาแถว EMA200"},
    {"ticker": "GPIQ", "kind": "above", "level": 56.8, "action": "ซื้อไม้ 2", "note": "ยืนเหนือ EMA50"},
    {"ticker": "AEHR", "kind": "above", "level": 57.0, "action": "ซื้อครึ่งแรก", "note": "หลังงบ 2 พ.ย. และยืนเหนือแนวรับ Fibo"},
    {"ticker": "AEHR", "kind": "below", "level": 43.0, "action": "รอดูแท่งกลับตัว", "note": "ขอบล่าง Bollinger ถ้างบแย่"},
    {"ticker": "LLY", "kind": "below", "level": 1364.0, "action": "ขายไม้ที่เหลือ", "note": "หลุด stop ของระบบ (ATR)"},
]

RULES = [
    "หุ้นตัวเดียวห้ามเกิน 35% ของพอร์ต. ส่วนที่เกินให้ขายออก.",
    "ถือไม่เกิน 8 ถึง 10 ตัว. ตัวที่ได้เกรด F ติดกันเกิน 1 ไตรมาสให้ขาย.",
    "เงินฝากใหม่แบ่ง 50% เข้า VOO และ 50% ให้หุ้นเกรด A ที่อยู่ในโซนเหนือ EMA200 0 ถึง 10%.",
    "ไม่ซื้อเพิ่มภายใน 14 วันก่อนงบ และไม่ซื้อวันที่ราคาร่วงแรง.",
]

LIMITS = [
    "โซน EMA200 มาจาก backtest ที่มี survivorship bias, ทดสอบช่วงตลาดขาขึ้น และไม่มีงบย้อนหลัง.",
    "ผลตอบแทนปี 2569 ยาวแค่ 10 เดือน ยังไม่หักภาษีปันผลและค่าธรรมเนียม.",
    "ภาษีปันผลกองทุนสหรัฐและภาษีเงินนำเข้าไทย ยังไม่ได้ยืนยันกับผู้เชี่ยวชาญ.",
    "นี่เป็นความเห็นจากข้อมูลในระบบ ไม่ใช่คำแนะนำการลงทุนที่รับรองผล.",
]


def trigger_status(kind: str, level: float, price: Optional[float]) -> Dict[str, Any]:
    """Whether `price` has reached `level`. gap_pct is how far price still has to move (0 once reached)."""
    if price is None or price <= 0:
        return {"hit": None, "gap_pct": None}
    hit = price >= level if kind == "above" else price <= level
    gap = 0.0 if hit else round((level / price - 1) * 100, 1)
    return {"hit": hit, "gap_pct": gap}


def fetch_prices(timeout: int = 15) -> Dict[str, float]:
    """Latest close per ticker from TradingView. Empty on network failure."""
    try:
        from src.tradingview import fetch_screener_data
        rows = fetch_screener_data(list(SYMBOLS.values()), timeout=timeout)
    except Exception:
        return {}
    return {r["ticker"]: r["close"] for r in rows if r.get("close")}


def lly_weight_pct() -> Optional[float]:
    """LLY share of the stock portfolio from data/account_summary.json, or None."""
    try:
        summary = json.loads(Path(data_path("account_summary.json")).read_text(encoding="utf-8"))
        total = summary["stock_market_val_usd"]
        lly = next(p for p in summary["positions"] if p["ticker"] == "LLY")
        return round(lly["current_val_usd"] / total * 100, 1)
    except Exception:
        return None


def _status_cell(t: Dict[str, Any], price: Optional[float]) -> str:
    s = trigger_status(t["kind"], t["level"], price)
    if s["hit"] is None:
        return '<span class="st st-na">ไม่มีราคา</span>'
    if s["hit"]:
        return '<span class="st st-hit">✅ ถึงแล้ว</span>'
    return f'<span class="st st-wait">⏳ อีก {s["gap_pct"]:+.1f}%</span>'


def _fmt_price(p: Optional[float]) -> str:
    return "-" if p is None else f"{p:,.2f}"


def generate_advisor_html(prices: Dict[str, float], lly_weight: Optional[float], now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    tone_label = {"go": "ทำได้", "wait": "รอจังหวะ", "stop": "ไม่แนะนำ"}

    headlines = "".join(
        f'<div class="hl"><div class="hl-ico">{ico}</div><div><div class="hl-t">{t}</div><div class="hl-s">{s}</div></div></div>'
        for ico, t, s in HEADLINES
    )

    lly_now = lly_weight if lly_weight is not None else 78.0
    lly_bar = (
        f'<div class="prog"><div class="prog-head"><span>สัดส่วน LLY ตอนนี้ <b>{lly_now:.1f}%</b></span>'
        f'<span class="muted">เป้าแรก 50% · ระยะยาว 30 ถึง 35%</span></div>'
        f'<div class="prog-bar"><div class="prog-fill" style="width:{min(lly_now, 100):.1f}%"></div>'
        f'<div class="prog-mark" style="left:50%" title="เป้าแรก 50%"></div>'
        f'<div class="prog-mark prog-mark2" style="left:35%" title="เพดานระยะยาว 35%"></div></div></div>'
    )

    plan = "".join(
        f'<div class="card tone-{p["tone"]}"><div class="card-top"><div class="card-t">{p["title"]}</div>'
        f'<span class="pill pill-{p["tone"]}">{tone_label[p["tone"]]}</span></div>'
        f'<ul>{"".join(f"<li>{x}</li>" for x in p["lines"])}</ul></div>'
        for p in PLAN
    )

    mix_bar = "".join(
        f'<div class="mix-seg" style="width:{pct}%;background:{color}" title="{name} {pct}%"></div>'
        for name, pct, color in TARGET_MIX
    )
    mix_legend = "".join(
        f'<span class="mix-key"><i style="background:{color}"></i>{name} <b>{pct}%</b></span>'
        for name, pct, color in TARGET_MIX
    )

    asked = "".join(
        f'<div class="card tone-{a["tone"]}"><div class="card-top"><div>'
        f'<div class="tk">{a["ticker"]}</div><div class="muted small">{a["name"]}</div></div>'
        f'<span class="pill pill-{a["tone"]}">{a["verdict"]}</span></div>'
        f'<div class="live-line">ราคาตอนนี้ <b data-price="{a["ticker"]}">{_fmt_price(prices.get(a["ticker"]))}</b> USD</div>'
        f'<ul>{"".join(f"<li>{x}</li>" for x in a["lines"])}</ul></div>'
        for a in ASKED
    )

    best = max(r[3] for r in BACKTEST_YTD["rows"])
    bt_rows = "".join(
        f'<tr><td class="tk-cell">{tk}</td><td>{pr:+.1f}%</td><td>{dv:.1f}%</td>'
        f'<td class="tot">{tot:+.1f}%<div class="bar"><div style="width:{tot / best * 100:.0f}%"></div></div></td>'
        f'<td class="neg">{dd:.1f}%</td></tr>'
        for tk, pr, dv, tot, dd in BACKTEST_YTD["rows"]
    )

    trig_rows = "".join(
        f'<tr data-kind="{t["kind"]}" data-level="{t["level"]}" data-ticker="{t["ticker"]}">'
        f'<td class="tk-cell">{t["ticker"]}</td><td><b>{t["action"]}</b><div class="muted small">{t["note"]}</div></td>'
        f'<td>{"≥" if t["kind"] == "above" else "≤"} {t["level"]:,.2f}</td>'
        f'<td data-price="{t["ticker"]}">{_fmt_price(prices.get(t["ticker"]))}</td>'
        f'<td class="st-cell">{_status_cell(t, prices.get(t["ticker"]))}</td></tr>'
        for t in TRIGGERS
    )

    rules = "".join(f"<li>{r}</li>" for r in RULES)
    limits = "".join(f"<li>{r}</li>" for r in LIMITS)
    no_price = "" if prices else (
        '<div class="alert">⚠️ ดึงราคาจาก TradingView ไม่ได้ตอนสร้างหน้า. กด "รีเฟรชราคา" ด้านบนเพื่อลองใหม่.</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>คำแนะนำพอร์ต - Filter Stock</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#080d1a; --card:#0f172a; --line:rgba(255,255,255,0.08); --text:#f8fafc; --sub:#94a3b8; --muted:#64748b;
  --go:#10b981; --wait:#f59e0b; --stop:#f43f5e; --blue:#3b82f6; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font-family:'Prompt','Inter',-apple-system,sans-serif; line-height:1.6; }}
.wrap {{ max-width:1080px; margin:0 auto; padding:16px; }}
h1 {{ font-size:1.6rem; margin:4px 0 2px; }}
h2 {{ font-size:1.15rem; margin:30px 0 12px; display:flex; align-items:center; gap:8px; }}
.muted {{ color:var(--muted); }} .small {{ font-size:0.8rem; }}
.sub {{ color:var(--sub); margin:0 0 18px; font-size:0.92rem; }}
.alert {{ background:rgba(244,63,94,0.08); border:1px solid rgba(244,63,94,0.3); border-radius:12px; padding:12px 16px; margin-bottom:16px; }}
.hero {{ background:linear-gradient(135deg,rgba(59,130,246,0.18),rgba(167,139,250,0.12)); border:1px solid rgba(96,165,250,0.3);
  border-radius:18px; padding:20px; }}
.hero-date {{ display:inline-block; font-size:0.78rem; color:#93c5fd; background:rgba(59,130,246,0.18); border-radius:999px; padding:2px 10px; }}
.hls {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:16px; }}
.hl {{ display:flex; gap:12px; background:rgba(8,13,26,0.55); border:1px solid var(--line); border-radius:14px; padding:14px; }}
.hl-ico {{ font-size:1.6rem; line-height:1; }}
.hl-t {{ font-weight:600; }} .hl-s {{ color:var(--sub); font-size:0.85rem; }}
.prog {{ margin-top:16px; }}
.prog-head {{ display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; font-size:0.88rem; margin-bottom:6px; }}
.prog-bar {{ position:relative; height:12px; background:rgba(255,255,255,0.08); border-radius:999px; overflow:visible; }}
.prog-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg,#a78bfa,#f43f5e); }}
.prog-mark {{ position:absolute; top:-4px; width:2px; height:20px; background:#f8fafc; }}
.prog-mark2 {{ background:#10b981; }}
.grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--muted); border-radius:14px; padding:14px 16px; }}
.tone-go {{ border-left-color:var(--go); }} .tone-wait {{ border-left-color:var(--wait); }} .tone-stop {{ border-left-color:var(--stop); }}
.card-top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }}
.card-t {{ font-weight:600; }}
.card ul {{ margin:8px 0 0; padding-left:18px; color:#cbd5e1; font-size:0.9rem; }}
.card li {{ margin:3px 0; }}
.pill {{ flex:0 0 auto; font-size:0.76rem; font-weight:600; border-radius:999px; padding:3px 10px; white-space:nowrap; }}
.pill-go {{ color:#6ee7b7; background:rgba(16,185,129,0.15); }}
.pill-wait {{ color:#fcd34d; background:rgba(245,158,11,0.15); }}
.pill-stop {{ color:#fda4af; background:rgba(244,63,94,0.15); }}
.tk {{ font-family:'Inter',sans-serif; font-weight:700; font-size:1.25rem; }}
.live-line {{ margin-top:8px; font-size:0.88rem; color:var(--sub); }}
.live-line b {{ color:var(--text); font-family:'Inter',sans-serif; }}
.mix {{ display:flex; height:22px; border-radius:8px; overflow:hidden; border:1px solid var(--line); }}
.mix-seg {{ height:100%; }}
.mix-legend {{ display:flex; flex-wrap:wrap; gap:6px 14px; margin-top:10px; font-size:0.85rem; color:var(--sub); }}
.mix-key i {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; }}
.tbl-wrap {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
th {{ text-align:left; color:var(--sub); font-weight:500; font-size:0.8rem; padding:10px 12px; border-bottom:1px solid var(--line); }}
td {{ padding:10px 12px; border-bottom:1px solid rgba(255,255,255,0.04); vertical-align:top; font-family:'Inter','Prompt',sans-serif; }}
tr:last-child td {{ border-bottom:none; }}
.tk-cell {{ font-weight:700; }}
.tot {{ font-weight:700; color:#6ee7b7; min-width:110px; }}
.bar {{ height:4px; background:rgba(255,255,255,0.06); border-radius:4px; margin-top:4px; }}
.bar div {{ height:100%; background:var(--go); border-radius:4px; }}
.neg {{ color:#fda4af; }}
.st {{ font-size:0.8rem; font-weight:600; border-radius:999px; padding:3px 9px; white-space:nowrap; }}
.st-hit {{ color:#6ee7b7; background:rgba(16,185,129,0.15); }}
.st-wait {{ color:#cbd5e1; background:rgba(255,255,255,0.06); }}
.st-na {{ color:var(--muted); }}
.note {{ color:var(--sub); font-size:0.82rem; margin-top:8px; }}
.box {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px 18px; }}
.box ol, .box ul {{ margin:0; padding-left:20px; color:#cbd5e1; font-size:0.9rem; }}
.box li {{ margin:4px 0; }}
@media (max-width:720px) {{
  .wrap {{ padding:10px; }}
  h1 {{ font-size:1.3rem; }}
  .hls, .grid {{ grid-template-columns:1fr; }}
  .hero {{ padding:16px; }}
  td, th {{ padding:8px; }}
}}
</style>
</head>
<body>
<div class="wrap">
{nav_bar_html("advisor", now)}
{no_price}
<section class="hero">
  <span class="hero-date">🗓️ ปรึกษาเมื่อ {CONSULT_DATE}</span>
  <h1>คำแนะนำพอร์ต</h1>
  <p class="sub" style="margin:0">สรุปจากการคุยกันว่าถ้าเป็นเจ้าของพอร์ตนี้จะทำอะไรต่อ. ตารางจุดซื้อขายด้านล่างอัปเดตราคาสดได้.</p>
  <div class="hls">{headlines}</div>
  {lly_bar}
</section>

<h2>🧭 แผนจัดพอร์ต</h2>
<div class="grid">{plan}</div>

<h2>🎯 พอร์ตเป้าหมายหลังทำครบ</h2>
<div class="box">
  <div class="mix">{mix_bar}</div>
  <div class="mix-legend">{mix_legend}</div>
  <div class="note">ถ้า LLY ลงแรง ความเสียหายจะเหลือประมาณครึ่งหนึ่งของตอนนี้.</div>
</div>

<h2>💬 หุ้นและกองทุนที่ถามมา</h2>
<div class="grid">{asked}</div>

<h2>📊 ผลตอบแทนปีนี้ (รวมปันผล)</h2>
<div class="tbl-wrap"><table class="no-cards">
<thead><tr><th>กองทุน</th><th>ราคา</th><th>ปันผล</th><th>รวม</th><th>ร่วงหนักสุด</th></tr></thead>
<tbody>{bt_rows}</tbody></table></div>
<div class="note">ช่วง {BACKTEST_YTD["period"]}. ข้อมูลรายวันจาก Yahoo Finance และคิดว่าเอาปันผลไปซื้อเพิ่มทันที.
CHPY ได้ผลตอบแทนพอๆ กับ SMH แต่ราคาแทบไม่โต และร่วงลึกกว่า.</div>

<h2>🚦 จุดซื้อขายที่รอดู</h2>
<div class="tbl-wrap"><table id="trig-table">
<thead><tr><th>หุ้น</th><th>ทำอะไร</th><th>เงื่อนไข</th><th>ราคาตอนนี้</th><th>สถานะ</th></tr></thead>
<tbody>{trig_rows}</tbody></table></div>
<div class="note">"ถึงแล้ว" แปลว่าราคาแตะระดับแล้ว. ยังต้องดูแท่งเทียนกลับตัวและวันงบก่อนกดซื้อจริง.</div>

<h2>📏 กฎประจำพอร์ต</h2>
<div class="box"><ol>{rules}</ol></div>

<h2>⚠️ ข้อจำกัด</h2>
<div class="box"><ul>{limits}</ul></div>
<p class="note" style="text-align:center;margin:24px 0">สร้างหน้าเมื่อ {now.strftime("%Y-%m-%d %H:%M")}</p>
</div>
<script>
(function () {{
  var SYMBOLS = {json.dumps(SYMBOLS)};
  function fmt(p) {{ return p == null ? '-' : p.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}); }}
  function status(kind, level, price) {{
    if (price == null || price <= 0) return '<span class="st st-na">ไม่มีราคา</span>';
    var hit = kind === 'above' ? price >= level : price <= level;
    if (hit) return '<span class="st st-hit">✅ ถึงแล้ว</span>';
    var gap = (level / price - 1) * 100;
    return '<span class="st st-wait">⏳ อีก ' + (gap >= 0 ? '+' : '') + gap.toFixed(1) + '%</span>';
  }}
  function apply(prices) {{
    document.querySelectorAll('[data-price]').forEach(function (el) {{
      var p = prices[el.getAttribute('data-price')];
      if (p != null) el.textContent = fmt(p);
    }});
    document.querySelectorAll('#trig-table tr[data-kind]').forEach(function (tr) {{
      var p = prices[tr.getAttribute('data-ticker')];
      if (p != null) tr.querySelector('.st-cell').innerHTML = status(tr.getAttribute('data-kind'), parseFloat(tr.getAttribute('data-level')), p);
    }});
  }}
  window.refreshLiveQuotes = async function () {{
    var res = await fetch('https://scanner.tradingview.com/america/scan', {{
      method: 'POST', mode: 'cors',
      body: JSON.stringify({{ symbols: {{ tickers: Object.values(SYMBOLS) }}, columns: ['close'] }})
    }});
    if (!res.ok) return;
    var data = await res.json(), prices = {{}};
    (data.data || []).forEach(function (it) {{ prices[(it.s || '').split(':').pop()] = it.d[0]; }});
    apply(prices);
  }};
}})();
</script>
</body>
</html>"""


def generate_advisor_page(reports_dir: Optional[Path] = None, prices: Optional[Dict[str, float]] = None) -> Path:
    """Write reports/advisor.html. Fetches live prices unless `prices` is given."""
    reports_dir = reports_dir or Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    if prices is None:
        prices = fetch_prices()
    out = reports_dir / "advisor.html"
    out.write_text(generate_advisor_html(prices, lly_weight_pct()), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Generated {generate_advisor_page()}")
