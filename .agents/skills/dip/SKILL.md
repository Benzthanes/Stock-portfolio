---
name: dip
description: Screens US Top 100 stocks (S&P 100 + Nasdaq 100) for high-probability dip buying setups using TradingView Screener API. Features EMA200/SMA200 Value Zone, RSI Hook, Fresh Stoch Cross, MACD Histogram, MFI Capitulation, ATR Dynamic Stop-Loss, Risk-to-Reward (R:R) targets, Forward Fundamentals (Rev YoY, PEG), and Live News Catalysts. Trigger on "/dip", "dip", or requests to scan US stocks on dip.
---

# US Stock Dip Screener (`/dip`)

Use this skill to scan and filter top US mega/large cap stocks (S&P 100 and Nasdaq 100) for **"Super Pullback in Uptrend"** dip-buying opportunities, combining technical momentum setups, fundamental growth quality, and live news catalyst monitoring.

---

## 💡 ตัวเลือกฟังก์ชันต่อท้าย (Sub-Functions)

เมื่อผู้ใช้พิมพ์คำสั่งสั้นๆ เพียง `/dip` ให้รันตัวเลือก (Recommended) ทันทีโดยไม่ต้องถามก่อน.
เมื่อแสดงผลเสร็จ ให้ปิดท้ายด้วยตัวเลือกอื่นด้านล่างแบบสั้นๆ:
1. `(Recommended) /dip`: สแกนหาหุ้นย่อตัวชั้นนำที่ดีที่สุดประจำวัน.
2. `/dip best`: กรองเฉพาะหุ้นที่มี Reward-to-Risk คุ้มค่าตั้งแต่ 2.0 เท่าขึ้นไป.
3. `/dip growth`: กรองเฉพาะหุ้นที่รายได้เติบโตเป็นบวก (Quality Growth).
4. `/dip tech`: สแกนหาหุ้นย่อตัวเฉพาะกลุ่มเทคโนโลยี.
5. `/dip finance`: สแกนหาหุ้นย่อตัวเฉพาะกลุ่มสถาบันการเงินและธนาคาร.
6. `/dip [TICKER]`: ระบุชื่อหุ้นที่สนใจตรวจสอบรายตัว.

---

## ⚡ Fast Chat Commands

1. **Daily Auto-Scan (Best Dip Buys)**:
   - User types: `/dip`
   - Agent runs: `python3 screener.py --auto-fallback`
   - Generates complete dip scan with beginner protections:
     - 🟢 **ป้ายระดับความเหมาะสมสำหรับมือใหม่ (Beginner Suitability Badge: 🟢/🟡/🔴)**.
     - 🎯 **ราคาเป้าหมายเฉลี่ยสถาบันและ Upside %** พร้อมมติสถาบัน (ซื้อ/ถือ/ขาย).
     - 🛡️ **ระบุระดับราคาแนวรับสำคัญและแนวต้านสำคัญ (Key Support & Key Resistance)** พร้อมจุดตัดขาดทุน (SL).
     - 👶 **สรุปภาษาคน สำหรับมือใหม่** อธิบายว่าบริษัททำอะไร กราฟอยู่ตรงไหน ตั้งจุดยอมแพ้และจุดทำกำไรตรงไหน.
     - 🗡️ **เช็กลิสต์ 3 ข้อ ป้องกันการรับมีดหล่น (Falling Knife Protection Checklist)**.
     - 🪜 **สูตรแบ่ง 3 ไม้ช้อนซื้อ สำหรับมือใหม่ (3-Step Dip Money Management)**.
     - 📖 **พจนานุกรมแปลศัพท์ฉบับ 1 บรรทัด สำหรับคนอยากช้อนซื้อ (Dip Buying Glossary)**.

2. **High Conviction Dip Buys (R:R ≥ 2.0x)**:
   - User types: `/dip best` or `/dip rr`
   - Agent runs: `python3 screener.py --auto-fallback --min-rr 2.0`

3. **Quality Growth Dips (Positive Revenue Growth Only)**:
   - User types: `/dip growth` or `/dip quality`
   - Agent runs: `python3 screener.py --auto-fallback --require-growth`

4. **Scan Specific Stocks (with News & Fundamentals)**:
   - User types: `/dip AAPL NVDA TSLA BNY JPM`
   - Agent runs: `python3 screener.py -t AAPL NVDA TSLA BNY JPM --rsi-max 100`

5. **Sector Scan**:
   - User types: `/dip tech` or `/dip finance`
   - Agent runs: `python3 screener.py --sector Technology --auto-fallback` (or `--sector Finance`)

6. **Broader Pullback Watchlist**:
   - User types: `/dip 40`
   - Agent runs: `python3 screener.py --rsi-max 40`

7. **Portfolio Tracking & Health Scan**:
   - User types: `/dip port` or `/dip portfolio`
   - Agent runs: `python3 portfolio.py`

8. **Simulated Paper Trading (ช้อนซื้อในพอร์ตจำลองตามคำสั่งผู้ใช้)**:
   - User types: `ซื้อ [TICKER] ในพอร์ตจำลอง` หรือ `ช้อน [TICKER] ใน sim` (เช่น `ซื้อ BNY ในพอร์ตจำลอง`, `ช้อน JPM 20000 ในพอร์ตจำลอง`)
   - Agent runs: `python3 scripts/generate_dip_sim_report.py --buy [TICKER] [--capital [THB]]`
   - ระบบจะเข้าซื้อจำลองที่ราคาตลาด คำนวณจุดตัดขาดทุน (SL 1.5 ATR) และเป้าหมายทำกำไร (TP 50D Mean Reversion) ให้ทันที พร้อมอัปเดต `reports/portfolio_dip_sim.html`.
   - คำสั่งขาย/ลบ: `ขาย [TICKER] ในพอร์ตจำลอง` หรือ `ลบ [TICKER] ออกจากพอร์ตจำลอง` -> `python3 scripts/generate_dip_sim_report.py --sell [TICKER]`
   - คำสั่งล้างพอร์ตจำลอง: `ล้างพอร์ตจำลอง` -> `python3 scripts/generate_dip_sim_report.py --reset`
   - คำสั่งดูสรุปพอร์ตจำลอง: `ดูพอร์ตจำลอง` หรือ `สรุปพอร์ตจำลอง` -> `python3 scripts/generate_dip_sim_report.py`

---

## 🎯 Quantitative Strategy: Super Pullback in Uptrend

1. **Daily RSI (14) ≤ 35**: Oversold pullbacks in the daily timeframe.
2. **200-Day Macro Trend (SMA 200 & EMA 200)**:
   - Price must trade above SMA 200 (or EMA 200) to confirm a long-term bull market structure.
   - **Institutional Value Zone (💎):** Stocks within 0% to +5% above their 200-day trend lines offer maximum Margin of Safety.
3. **Weekly RSI ≥ 45**: Multi-timeframe confirmation that the macro bull cycle remains intact.
4. **Triple Confluence Reversal**:
   - **RSI Hook Up (⤴):** Daily RSI ticks higher than previous day (ΔRSI > 0).
   - **Fresh Stoch Cross (✂🟢):** Stochastic RSI %K crosses above %D from oversold territory on the current bar.
   - **MACD Histogram Tick Up (📈):** MACD histogram turns upward, confirming selling pressure exhaustion.
5. **Money Flow Capitulation (🌊)**: MFI (volume-weighted RSI) ≤ 20-30, confirming institutional wash-out.
6. **Falling Knife Filter (ADX Guard)**: Excludes stocks plunging with severe downward trend momentum (ADX > 35).
7. **Execution Plan & Risk-to-Reward (R:R)**:
   - **Stop-Loss (SL):** Placed at 1.5 × ATR below close to absorb market noise.
   - **Take-Profit (TP):** Target set at 50-day Mean Reversion (SMA 50 / EMA 50).
   - **R:R Filter:** Prioritizes setups offering ≥ 2.0x reward-to-risk.
8. **Forward Fundamental Quality**:
   - Displays Revenue YoY Growth and PEG ratio in scan table.
   - Optional `--require-growth` prevents entering value traps.
9. **Business Profiles (ทำอะไร คร่าวๆ)**:
   - Displays concise Thai business profile under each ticker name in the table and in a dedicated section.
10. **⚖️ Catalyst & News Balance (ข่าวดี vs ข่าวร้าย)**:
   - Categorizes live RSS news into Bullish Catalysts vs Bearish Downside Risks for top candidates.
11. **👶 Beginner Layman Verdict (สรุปภาษาคน สำหรับมือใหม่)**:
   - Explains why the stock is pulling back and gives concrete Stop-Loss and Take-Profit instructions.
12. **Earnings Risk Shield**: Flags ⚠️ if an earnings announcement is due within 14 days.

---

## 🛠️ Direct Terminal CLI Reference

```bash
# Standard scan with auto-fallback
python3 screener.py --auto-fallback

# Filter high reward-to-risk setups only (R:R >= 2.0x)
python3 screener.py --min-rr 2.0

# Enforce Quality Growth (Revenue YoY > 0%)
python3 screener.py --require-growth

# Scan specific custom tickers with news and fundamentals
python3 screener.py -t AAPL NVDA JPM WMT BNY

# Save formatted report to a Markdown file
python3 screener.py --save-report reports/daily_scan.md

# Live Portfolio Tracking & Health Scan
python3 portfolio.py
```

---

## 📂 Source Code Architecture

- Screener Entrypoint CLI: `screener.py`
- Financial News Engine: `src/news.py`
- Portfolio Entrypoint CLI: `portfolio.py`
- Portfolio Holdings Data: `data/portfolio.json`
- Portfolio Analyzer Engine: `src/portfolio.py`
- Stock Universe & Ticker Resolver: `src/universe.py`
- TradingView Screener API Client: `src/tradingview.py`
- Indicator Evaluation & Scoring Engine: `src/screener.py`
