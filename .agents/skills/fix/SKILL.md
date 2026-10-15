---
name: fix
description: Quantitative Portfolio Drawdown Recovery & Breakeven Strategy Analyzer (เทคนิคแก้หลุดดอย 360 องศา). Analyzes underwater holdings with forward fundamentals (Revenue/Net Income YoY, PEG), Earnings Calendar Shock Guards, Live News Catalysts, Smart DCA triggers, and Capital Rotation recovery simulations. Trigger on "/fix", "fix", "/rescue", "rescue", "แก้ดอย", "แก้ติดลบ", "กู้พอร์ต", or requests to recover underwater positions.
---

# Portfolio Drawdown Recovery & Breakeven Strategy (`/fix`)

Use this skill to diagnose and recover underwater stock positions in your portfolio. It evaluates whether an underwater holding is a salvageable growth dip or a fundamental value trap by analyzing:
1. **Forward Fundamentals:** Revenue YoY %, Net Income YoY %, PEG, P/E, and Wall Street consensus ratings.
2. **Earnings Calendar Shock Guard:** Locks and warns against DCA within 14 days of an earnings release.
3. **Live News & Catalysts:** Real-time headlines and drivers explaining why the stock fell.
4. **Actionable Recovery Playbooks:** Rebound Exit, Smart DCA with confirmation triggers, Capital Rotation simulations, and ATR Cut Loss guards.

---

## 💡 ตัวเลือกฟังก์ชันต่อท้าย (Sub-Functions)

เมื่อผู้ใช้พิมพ์คำสั่งสั้นๆ เพียง `/fix` ให้รันตัวเลือก (Recommended) ทันทีโดยไม่ต้องถามก่อน.
เมื่อแสดงผลเสร็จ ให้ปิดท้ายด้วยตัวเลือกอื่นด้านล่างแบบสั้นๆ:
1. `(Recommended) /fix`: รันแผนกู้พอร์ต 360 องศา สรุปภาพรวมหุ้นติดลบทุกตัวในพอร์ตทันที.
2. `/fix [TICKER]`: เจาะลึกแผนแก้ดอยหุ้นรายตัว (เช่น `/fix APP`, `/fix NOK`, `/fix BAC`).
3. `/fix [TICKER] --shares [N] --cost [PRICE]`: วิเคราะห์หุ้นนอกพอร์ตพร้อมระบุจำนวนและต้นทุน.

---

## ⚡ Fast Chat Commands

1. **Scan All Underwater Holdings (Dashboard)**:
   - User types: `/fix` or `/fix all` or `แก้ติดลบ`
   - Agent runs: `python3 recovery.py`
   - Generates the 360-degree recovery dashboard ranking positions by drawdown, loss amounts, breakeven gaps, earnings calendar, fundamentals, and latest news:
     - 🚨 **ระดับความเร่งด่วนในการแก้ดอย (Emergency Triage: 🟢/🟡/🔴)** แยกตามความเสี่ยงวันงบออกและพื้นฐาน.
     - 🎯 **ระบุระดับราคาแนวรับสำคัญและแนวต้านสำคัญ (Key Support & Key Resistance)** พร้อมชื่ออินดิเคเตอร์กำกับชัดเจน.
     - 📊 **ตารางเปรียบเทียบ 3 ทางเลือกแบบฟันธง (3-Option Comparison Matrix)**: ถือรอเฉยๆ (Hold) vs Smart DCA (ระบุราคาแนวรับที่ควรตั้งซื้อชัดเจน) vs สลับตัว (Capital Rotation) พร้อมคำแนะนำที่เหมาะสมที่สุดสำหรับมือใหม่.
     - 🎯 **การเปรียบเทียบต้นทุนของคุณกับราคาเป้าหมายสถาบัน** ยืนยันโอกาสหลุดดอยตามหลักสถิติวอลล์สตรีท.
     - 📱 **คู่มือการเปิดแอปไปตั้งคำสั่งจริง (Broker App Execution Guide)** แนะนำวิธีตั้ง Limit Order และ Stop Loss ในแอป Dime/InnovestX/IBKR.
     - 📖 **พจนานุกรมแปลศัพท์สำหรับคนติดดอยฉบับ 1 บรรทัด (Underwater Beginner Glossary)**.

2. **Deep Dive Single Stock Recovery Plan**:
   - User types: `/fix APP` or `/fix NOK` or `/fix BAC`
   - Agent runs: `python3 recovery.py <TICKER>`
   - Provides full 5-part deep dive: Current Position, Forward Fundamentals, Live News, Support/Resistance Pivots, and 4 Actionable Playbooks.

3. **Custom Position Analysis**:
   - User types: `/fix TSLA --shares 10 --cost 250`
   - Agent runs: `python3 recovery.py TSLA --shares 10 --cost 250`

---

## 🛠️ Direct Terminal CLI Reference

```bash
# Scan and analyze all underwater holdings in data/portfolio.json
python3 recovery.py

# Deep dive into a specific underwater stock
python3 recovery.py APP

# Save full portfolio recovery dashboard to Markdown
python3 recovery.py --save-report reports/portfolio_recovery.md

# Save single stock recovery plan to Markdown
python3 recovery.py APP --save-report reports/app_recovery.md
```

---

## 🧭 The 4 Actionable Recovery Playbooks

1. **🎯 Rebound Exit (เด้งชนแนวต้านเพื่อลดพอร์ต - ไม่เติมเงินใหม่):**
   - ใช้กับหุ้นที่ต้นทุนเฉลี่ยอยู่ต่ำกว่าแนวต้านแรก (SMA 20) หรือหุ้นที่พื้นฐานชะลอตัว.
   - ตั้งคำสั่งขายคืนทุนอัตโนมัติเมื่อเกิด Technical Rebound โดยไม่ต้องเสี่ยงเติมเงินเพิ่ม.

2. **📐 Smart DCA (การถัวเฉลี่ยเชิงกลยุทธ์เมื่อคอนเฟิร์มฐาน):**
   - **กฎเหล็กสิทธิ์การถัว:** อนุญาตเฉพาะหุ้นที่พื้นฐานแข็งแกร่ง (กำไรโต, PEG สมเหตุสมผล) และวันประกาศงบไม่อยู่ใน 14 วันข้างหน้า.
   - **เงื่อนไขจังหวะเข้าซื้อ:** รอแท่งเทียนเขียว Daily ปิดเหนือราคาเปิด และเส้น Stoch RSI %K ตัดขึ้นเหนือ %D ก่อนเสมอ.
   - คำนวณจำนวนหุ้นและเงินทุนที่ต้องใช้ (ซื้อเพิ่ม 50% หรือ 100%) เพื่อดึงต้นทุนเฉลี่ยลงมาให้ต้องการการเด้งเพียง +5% ถึง +7%.

3. **🔄 Capital Rotation (การโยกเงินไปหาหุ้นผู้นำขาขึ้น):**
   - สำหรับหุ้นที่กำไรสุทธิติดลบหนักหรือเป็น Value Trap: ยอมรับการขาดทุนจำนวนจำกัด แล้วโยกเงินสดที่เหลือไปเข้าหุ้น Dip ขาขึ้นที่เข้าเกณฑ์ `/dip` (เช่น BNY, JPM) ซึ่งมี R:R $\ge 2.0x$.
   - ระบบจะคำนวณกำไรเปอร์เซ็นต์ที่หุ้นใหม่ต้องการทำเพื่อกู้เงินต้นที่เสียไปกลับมาทั้งหมด.

4. **🛡️ Cut Loss Guard (จุดตัดขาดทุนรักษาเงินต้น):**
   - กำหนดจุดยอมจำนนเด็ดขาดที่ $Close - (1.5 \times ATR)$ เพื่อป้องกันไม่ให้การติดลบระดับ -10% ลุกลามกลายเป็นวิกฤต -30% ถึง -50%.

---

## 📂 Source Code Architecture

- Recovery CLI Tool: `recovery.py`
- Financial News Engine: `src/news.py`
- Portfolio Holdings Data: `data/portfolio.json`
- TradingView Screener API Client: `src/tradingview.py`
- Portfolio Analytics Engine: `src/portfolio.py`
