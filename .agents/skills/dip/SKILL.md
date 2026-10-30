---
name: dip
description: Scans US Top 100 stocks (S&P 100 + Nasdaq 100) for pullback-in-uptrend dip buys and manages the simulated dip portfolio. Shows the unified grade (fundamentals + EMA200 price zone) with ATR stop-loss, R:R, earnings guard and news. Trigger on "/dip", "dip", "หุ้นย่อ", "ช้อนซื้อ", "ซื้อ ... ในพอร์ตจำลอง", or requests to scan US stocks on dip.
---

# US Stock Dip Screener (`/dip`)

สแกนหุ้นใหญ่สหรัฐฯ ที่ย่อตัวในเทรนด์ขาขึ้น แล้วสรุปเป็นภาษาคนพร้อมจุดซื้อ จุดตัดขาดทุน และจุดทำกำไร.
ถ้าจะแก้ logic การให้คะแนน ให้อ่าน `docs/METHODOLOGY.md` ก่อน.

## ก่อนเริ่ม

อ่าน `AGENTS.md` ที่ root ของโปรเจกต์ให้จบก่อน. จุดที่ต้องระวังเฉพาะ skill นี้มีดังนี้:
* พอร์ตจำลองเก็บใน `data/portfolio_dip_sim.json` ซึ่งแยกจากพอร์ตจริง. ห้ามสลับไปเขียน `data/portfolio.json`.
* เกรดที่แสดงมาจาก `src/scoring.py`. ตัวกรอง Stoch, MACD, MFI และ ADX ยังไม่ผ่าน backtest ห้ามอ้างว่าพิสูจน์แล้ว.
* ถ้าหุ้นที่ผู้ใช้ระบุหาไม่เจอ ให้ลองตลาด AMEX ด้วย. VOO และ SPY อยู่ที่ AMEX.
* **ค้นข้อมูลด้วย Tavily (รันในเครื่องเท่านั้น).** ใช้เครื่องมือ Tavily MCP ถ้ามี หรือรัน `/usr/bin/python3 -m src.tavily "<คำค้น>"` (ต้องมี `TAVILY_API_KEY` ใน environment). ทุกข้อเท็จจริงต้องบอกแหล่งที่มา และถ้ายืนยันไม่ได้ให้บอกว่ายังไม่ยืนยัน (หัวข้อ 3.1 ของ `AGENTS.md`). สำหรับ skill นี้ ใช้ Tavily หาสาเหตุที่ราคาย่อ (ข้อ 4) และข่าวของตัวที่น่าสนใจที่สุด (ข้อ 5). ถ้าระบบแจ้งว่างบใกล้ออกหรือไม่มีวันงบ ให้ค้นวันงบที่บริษัทประกาศจริง.

## ตัวเลือกคำสั่ง

ถ้าผู้ใช้พิมพ์ `/dip` เฉยๆ ให้รันตัวเลือก (Recommended) ทันทีโดยไม่ถามก่อน.
เมื่อแสดงผลเสร็จ ให้ปิดท้ายด้วยรายการตัวเลือกอื่นบรรทัดละ 1 ตัวเลือก.

| ผู้ใช้พิมพ์ | คำสั่งที่รัน |
| :--- | :--- |
| `(Recommended) /dip` | `python3 screener.py --auto-fallback` |
| `/dip actionable` | `python3 screener.py --auto-fallback --actionable` |
| `/dip best` หรือ `/dip rr` | `python3 screener.py --auto-fallback --min-rr 2.0` |
| `/dip growth` หรือ `/dip quality` | `python3 screener.py --auto-fallback --require-growth` |
| `/dip tech` | `python3 screener.py --auto-fallback --sector Technology` |
| `/dip finance` | `python3 screener.py --auto-fallback --sector Finance` |
| `/dip 40` | `python3 screener.py --rsi-max 40` |
| `/dip AAPL NVDA` | `python3 screener.py -t AAPL NVDA --rsi-max 100` |
| `/dip port` | `python3 portfolio.py` |

## พอร์ตจำลอง (Paper Trading)

| ผู้ใช้พิมพ์ | คำสั่งที่รัน |
| :--- | :--- |
| `ซื้อ BNY ในพอร์ตจำลอง` หรือ `ช้อน JPM 20000 ใน sim` | `python3 -m scripts.generate_dip_sim_report --buy TICKER [--capital THB]` |
| `ขาย TICKER ในพอร์ตจำลอง` | `python3 -m scripts.generate_dip_sim_report --sell TICKER` |
| `ล้างพอร์ตจำลอง` | `python3 -m scripts.generate_dip_sim_report --reset` |
| `ดูพอร์ตจำลอง` | `python3 -m scripts.generate_dip_sim_report` |
| `ปิดไม้ที่ถึง TP/SL` | `python3 -m scripts.generate_dip_sim_report --close-triggers` |

การซื้อจำลองใช้ราคาตลาด. SL อยู่ที่ 1.5 ATR. TP อยู่ที่เส้น 50 วัน. ทุกคำสั่งอัปเดต `reports/portfolio_dip_sim.html`.

## สิ่งที่ต้องสรุปให้ผู้ใช้

1. หุ้นที่ผ่านเกณฑ์ พร้อม `tier` และเกรดรวม เช่น `เกรด A · 78/100`. ถ้ามี `⤴` แปลว่า RSI ยกหัวจากต่ำกว่า 40.
2. ราคาแนวรับ แนวต้าน SL และ R:R ของแต่ละตัว.
3. คำเตือนวันงบออก. ถ้างบออกภายใน 14 วัน ให้บอกว่าห้ามซื้อก่อนงบ.
4. สรุปภาษาคน 1 ถึง 2 ประโยคต่อตัว ว่าบริษัททำอะไรและทำไมราคาย่อ. สาเหตุที่ราคาย่อต้องมาจากข่าวที่ค้นด้วย Tavily พร้อมแหล่งที่มา ห้ามเดา.
5. ข่าวดีและข่าวร้ายของตัวที่น่าสนใจที่สุด.

## เกณฑ์คัดกรองและความหมาย

ส่วนที่ผ่าน backtest (`data/backtest_scoring.json`, 173 หุ้น, ปี 2023 ถึง 2026):
* **โซนราคาเทียบ EMA200.** ราคาเหนือเส้น 0 ถึง 10% มี drawdown 60 วันตื้นที่สุด. ราคาต่ำกว่าเส้นเกิน 10% เสี่ยงที่สุด.
* **RSI Hook.** RSI ยกหัวจากต่ำกว่า 40 ให้ผลตอบแทน 20 วันดีขึ้นเล็กน้อย.

ส่วนที่เป็นตัวกรองตามกลยุทธ์ แต่ยังไม่ผ่าน backtest:
* RSI รายวัน ≤ 35, RSI รายสัปดาห์ ≥ 45, Stoch RSI cross, MACD tick up, MFI และ ADX (เก็บเป็น tag ข้อมูลประกอบ ไม่คิดคะแนนและไม่ตัดสิทธิ์หุ้น).
* Plunge Guard ป้องกันมีดหล่น (ตัดหุ้นวันทิ้งตัว change ≤ -3.0% หรือแท่งแดง change ≤ -1.5%) และ Earnings Guard 14 วัน.
* ถ้าผู้ใช้ถามว่าตัวไหนแม่น ให้ตอบตามผล backtest. ห้ามอ้างว่าตัวกรองเหล่านี้พิสูจน์แล้ว.

คะแนนพื้นฐานมาจาก `score_fundamentals()` ใน `src/scoring.py` ตัวเดียวกับทุกหน้า.

## ไฟล์ที่เกี่ยวข้อง

* `screener.py` คือ CLI. `src/screener.py` `evaluate_stock()` คือ logic การคัดกรอง.
* `src/scoring.py` คือคะแนนรวม.
* `src/universe.py` คือรายชื่อหุ้น. `src/tradingview.py` คือ client ของ TradingView.
* `scripts/generate_dip_sim_report.py` คือพอร์ตจำลอง.
