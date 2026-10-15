---
name: port
description: Real-time US Stock Portfolio Analytics, Health Check, Star Ratings (1-5 Stars), Forward Fundamentals (Rev/Net Inc Growth, PEG), 30-Day Earnings Radar, and Live News Digest. Triggers on "/port", "analytic port", "วิเคราะห์พอร์ต", or requests to review portfolio holdings.
---

# Portfolio Analytics & Health Check (`/port`)

Use this skill to track live portfolio performance, evaluate each holding with a dynamic 1-5 star rating combining technical trends and business fundamentals, monitor upcoming earnings releases in the next 30 days, digest live news catalysts, and detect concentration and drawdown risks.

---

## ⚡ Fast Chat Commands (All-in-One Execution)

เมื่อผู้ใช้พิมพ์คำสั่ง `/port` หรือ `port` หรือ `วิเคราะห์พอร์ต`:
ระบบจะรันการวิเคราะห์พอร์ตโฟลิโอแบบ All-in-One ทันทีโดยไม่ต้องถามตัวเลือกย่อยซ้ำซ้อน.
รายงานฉบับเดียวจะครอบคลุมครบทุกมิติทันทีในคำสั่งเดียว:
1. 🏥 **สุขภาพพอร์ต เกรดพอร์ต และสรุปภาษาคน (Health Check & Layman Summary):** เกรดพอร์ต กำไรขาดทุนรวมทั้ง $ และ ฿ พร้อมชี้เป้าฮีโร่และตัวฉุด.
2. ⚠️ **ตรวจความเสี่ยงการกระจุกตัวและหุ้นติดลบ (Risk & Concentration):** คำนวณระดับความเสี่ยง HHI, ตารางสัดส่วน Sector Allocation, และปฏิทินวันงบการเงิน 14 วัน.
3. 🎯 **โอกาสช้อนซื้อและสะสม DCA (Value Zone & Technical Dips):** สแกนหุ้นในพอร์ตที่ลงมาในโซนรับสถาบัน (Value Zone), RSI Oversold, และระบุราคาแนวรับ/แนวต้าน (Support & Resistance) ทุกตัว.
4. 💵 **ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม (Top Rebalancing Buys & Forbidden Buys):** จัดอันดับ 1-3 พร้อมระบุราคาแนวรับที่ควรตั้งซื้อ (Limit Order Support), แนวต้านเป้าหมาย (TP Resistance), จุดตัดขาดทุน (SL), หุ้นที่ห้ามซื้อเด็ดขาด, และสูตรแบ่งเงิน 3 ไม้.
5. ⚖️ **ตาชั่งข่าวดี vs ข่าวร้าย (Bullish vs Bearish Catalysts):** รวบรวมข่าวสด ปัจจัยบวก ปัจจัยลบ และราคาเป้าหมายจากสถาบันวอลล์สตรีท.
6. ⭐ **คะแนนดาว 1-5 ดาว (Star Ratings):** ตัดเกรดดาวรายตัว 1 ถึง 5 ดาว พร้อมระบุจุดเด่นและข้อควรระวัง.

---

## 🌟 1-5 Star Rating System (เกณฑ์การให้คะแนนดาว)

- ⭐⭐⭐⭐⭐ **5 ดาว (เกรด A+ ยอดเยี่ยม ปลอดภัยสูง)**:
  - เทรนด์ขาขึ้นแข็งแกร่ง (ยืนเหนือเส้น 200 วัน), อยู่ใน Value Zone หรือเป็นดัชนีหลัก, ธุรกิจกำไรเติบโตเด่น, ปลอดภัยสูง.
- ⭐⭐⭐⭐ **4 ดาว (เกรด A สุขภาพดี แข็งแกร่ง)**:
  - มีกำไรเติบโต, เทรนด์ขาขึ้นชัดเจน, มีสัญญาณกลับตัวหรือโมเมนตัมต่อเนื่อง.
- ⭐⭐⭐ **3 ดาว (เกรด B ปานกลาง / พักฐาน / รอสร้างฐาน)**:
  - กำไรเติบโตดีที่กำลังพักฐานทดสอบแนวรับ, โซน Pullback Oversold ใกล้แนวรับสำคัญ, หรือหุ้นเติบโตสูง (High Growth) ที่หลุดเส้น 200 วันลึกแต่มีพื้นฐานแข็งแกร่งรองรับ.
- ⭐⭐ **2 ดาว (เกรด C เฝ้าระวัง / เสี่ยงสูง)**:
  - ราคาหลุดต่ำกว่าเส้น 200 วันลึกโดยที่พื้นฐานไม่มีการเติบโตรองรับ, กำไรสุทธิหดตัวต่อเนื่อง, หรือไม่มีสัญญาณการสร้างฐานราคา.
- ⭐ **1 ดาว (เกรด D น่าเป็นห่วง / หลุดทรง)**:
  - หลุดแนวรับสำคัญลึก, พื้นฐานชะลอตัวหนัก, เป็น Falling Knife ไร้แรงซื้อหนุน, ควรวางแผนคัทลอส.

---

## 🛠️ Direct Terminal CLI Reference

```bash
# รันวิเคราะห์พอร์ตโฟลิโอและตัดเกรดดาว พร้อมตารางงบ ปฏิทินงบ และฟีดข่าว
python3 portfolio.py

# บันทึกรายการใหม่ (ทุกคำสั่งใส่ --dry-run เพื่อดูผลก่อนได้)
python3 trades.py buy -t BAC -s 2 -p 48.10          # ซื้อหุ้น คำนวณต้นทุนเฉลี่ยใหม่และตัดเงินสดให้อัตโนมัติ
python3 trades.py sell --ticker VST --price 160.50  # ขายหุ้น บันทึกกำไรขาดทุนและเพิ่มเงิน USD
python3 trades.py deposit --amount 20000            # ฝากเงินเข้า Dime! Save
python3 trades.py withdraw --amount 5000            # ถอนเงินออก
python3 trades.py dividend -t LLY --usd 3.50        # รับเงินปันผล

# บันทึกผลลัพธ์เป็นไฟล์รายงาน HTML สวยงาม
python3 portfolio.py --save-report reports/portfolio_review.html

# ดูบัญชีกำไรขาดทุนและอัตรา Win Rate
python3 trades.py list

# รวมศูนย์ข้อมูลพอร์ตทั้งหมดเป็นที่เดียว (Master Dashboard)
python3 scripts/generate_master_report.py
```

---

## 📂 Source Code Architecture

- Portfolio Entrypoint CLI: `portfolio.py`
- Trade Ledger Entrypoint CLI: `trades.py`
- Trade Ledger Engine: `src/trades.py`
- Closed Trades Database: `data/trades.json`
- Financial News Engine: `src/news.py`
- Portfolio Holdings Data: `data/portfolio.json`
- Portfolio Analytics Engine: `src/portfolio.py`
- Screener Entrypoint CLI: `screener.py`
- TradingView Screener API Client: `src/tradingview.py`

