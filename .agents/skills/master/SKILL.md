---
name: master
description: Unified Master Wealth & Portfolio Dashboard. Aggregates KKP Statement deposits, live TradingView stock holdings, closed trades realized P&L, dividend stream, and total net worth (NAV). Trigger on "/master", "master", "/ledger", "ledger", "สรุปบัญชี", "สรุปพอร์ต", "ภาพรวมพอร์ต", "สรุปทั้งหมด", or requests for all-in-one portfolio ledger.
---

# Unified Master Wealth & Portfolio Dashboard (`/master`)

Use this skill to view the complete 360-degree all-in-one wealth and portfolio summary in one single report.
This skill automatically synthesizes:
1. Official Bank Statement Deposits & Withdrawals (from KKP Dime! Save Statement).
2. Live Active Holdings Valuation (from TradingView Scanner API).
3. Complete Buy Orders Ledger (every buy order parsed from Dime! order confirmation slips).
4. Closed Realized Trades Ledger & Win Rate (from `data/trades.json`).
5. Total Dividends Received (from historical corporate actions).
6. Dime! Save Cash Movement & Deposit Ledger (including PromptPay deposits, stock deductions, and interest).
7. Current Cash Reserves (Dime! Save THB and Dime! USD cash).

## ก่อนเริ่ม

อ่าน `AGENTS.md` ที่ root ของโปรเจกต์ให้จบก่อน. จุดที่ต้องระวังเฉพาะ skill นี้มีดังนี้:
* ตัวเลขเงินบาทของต้นทุนหุ้นที่ซื้อด้วย Dime! USD ยังคิดที่ 33.62 THB/USD. ส่วนที่จ่ายจาก Dime! Save (THB) ปรับตาม slip ได้ด้วย `python3 scripts/reconcile_cost_thb.py` (dry-run ก่อนเสมอ).
* LLY มีจำนวนหุ้นใน slip ไม่ตรงกับพอร์ต (27.7467 กับ 27.6477631). ถ้าผู้ใช้ถามเรื่องต้นทุน LLY ให้แจ้งเรื่องนี้ด้วย.
* คำสั่ง `trades.py` ทุกคำสั่งต้องรันด้วย `--dry-run` ก่อน แล้วให้ผู้ใช้ยืนยันก่อนรันจริง.

---

## ⚡ Fast Chat Execution Protocol (Autonomous Execution)

เมื่อผู้ใช้พิมพ์คำสั่ง `/master`, `master`, `/ledger`, `ledger`, หรือขอ "สรุปบัญชี", "สรุปพอร์ต", "ภาพรวมพอร์ต", "สรุปทั้งหมด":

1. **ห้ามตอบโดยสั่งให้ผู้ใช้ไปพิมพ์คำสั่ง Terminal เองเด็ดขาด.**
2. **AI Agent ต้องรันสคริปต์ประมวลผลให้ผู้ใช้โดยอัตโนมัติทันที:**
   ```bash
   python3 scripts/generate_master_report.py
   ```
3. **อ่านข้อมูลผลลัพธ์จาก `data/account_summary.json` และรายงานผลลัพธ์ลงในแชททันที:**
   - 🌟 **มูลค่าพอร์ตรวมสุทธิ (Total Net Worth / NAV):** ยอดหุ้นสด + เงินสดคงเหลือ ทั้ง $ และ ฿.
   - 💰 **เงินต้นทุนเติมสุทธิ (Net Injected Capital):** อ้างอิงจาก KKP Statement ทางการ (`net_injected_capital_thb`).
   - 🚀 **กำไรรวมสุทธิของพอร์ต (All-Time Net Profit):** NAV ลบเงินต้นสุทธิ พร้อมคำนวณ All-Time ROI %.
   - 💵 **เงินสดพร้อมใช้รวม (Total Idle Cash):** Dime! Save (THB) และ Dime! USD Cash.
   - 🛒 **ประวัติคำสั่งซื้อหุ้นทั้งหมด (Buy Orders History):** จำนวนไม้ (`len(buy_orders)`) พร้อมจำนวนหุ้น ราคาที่ได้จริง ยอดเงิน และช่องทางชำระเงิน.
   - 🏆 **กำไรที่ปิดทำกำไรจริง (Realized P&L):** กำไรสะสมจากการขายหุ้นจริง (`trades_summary.total_trades` ไม้ และ `trades_summary.win_rate_pct`).
   - 💸 **เงินปันผลรับสะสม (Dividends):** ยอดรับปันผลสุทธิทั้งหมด (`total_dividends_thb` และจำนวนครั้ง `len(dividends_list)`).
   - 🏦 **ประวัติการเติมเงินและเงินสด (Cash Flow & Deposits):** รายการเดินบัญชี Dime! Save (`len(cash_movements)` รายการ).
   - 📈 **สถานะหุ้นปัจจุบันในพอร์ต (Active Holdings):** ราคาตลาดสด กำไร Unrealized P/L รายตัว.
4. **แนบลิงก์คลิกเปิดรายงานหน้าเว็บสวยงาม:**
   - `reports/portfolio_master.html`
5. **ห้ามคำนวณตัวเลขเอง.** ให้อ่านค่าจาก `data/account_summary.json` เท่านั้น. ถ้าสคริปต์ล้มเหลว ให้แจ้ง error ตามจริงและห้ามใช้ตัวเลขจากรอบก่อนโดยไม่บอกผู้ใช้.
6. **ถ้าผู้ใช้ถามว่าหุ้นตัวไหนดี** ให้ส่งต่อไปที่ `/port`. คะแนนและเกรดหุ้นรายตัวอยู่ใน `src/scoring.py` ไม่ได้อยู่ในรายงาน master.

---

## ✍️ บันทึกรายการใหม่ (ไม่ต้องแก้โค้ด)

เมื่อผู้ใช้บอกว่าซื้อหุ้น ฝากเงิน ถอนเงิน หรือได้ปันผล ให้รันคำสั่งที่ตรงกันแล้วรัน `/master` ใหม่:
- ซื้อหุ้น: `python3 trades.py buy -t TICKER -s SHARES -p PRICE_USD [--fx RATE] [--pay thb|usd]`.
- ขายหุ้น: `python3 trades.py sell -t TICKER -p PRICE_USD [-s SHARES]`.
- ฝากเงิน: `python3 trades.py deposit --amount THB`.
- ถอนเงิน: `python3 trades.py withdraw --amount THB`.
- รับปันผล: `python3 trades.py dividend -t TICKER --usd AMOUNT`.

ทุกคำสั่งรองรับ `--dry-run` และ `--date YYYY-MM-DD`.
ข้อมูลเงินสด เงินต้น รายการเดินบัญชี และปันผล เก็บอยู่ใน `data/ledger.json`.
ไฟล์นี้ไม่เก็บตัวเลขสด.
ให้อ่านตัวเลขล่าสุด (จำนวนไม้ จำนวนครั้ง และเงินต้น) จาก `data/account_summary.json` ทุกครั้งที่ใช้งาน.
ชื่อ field ในวงเล็บด้านบนคือ key ในไฟล์นั้น.

---

## 📂 Source Code Architecture

- Master Report Generator: `scripts/generate_master_report.py`
- Master HTML Dashboard: `reports/portfolio_master.html`
- Aggregated Account Data JSON: `data/account_summary.json`
- Closed Trades Database: `data/trades.json`
- Active Holdings Data: `data/portfolio.json`
- Cash, Deposits & Dividends Ledger: `data/ledger.json`
- Official KKP Statement PDF: `data/KKP_STATEMENT_20261007.pdf`
