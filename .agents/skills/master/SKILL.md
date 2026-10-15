---
name: master
description: Unified Master Wealth & Portfolio Dashboard. Aggregates KKP Statement deposits, live TradingView stock holdings, closed trades realized P&L, dividend stream, and total net worth (NAV). Trigger on "/master", "master", "/ledger", "ledger", "สรุปบัญชี", "สรุปพอร์ต", "ภาพรวมพอร์ต", "สรุปทั้งหมด", or requests for all-in-one portfolio ledger.
---

# Unified Master Wealth & Portfolio Dashboard (`/master`)

Use this skill to view the complete 360-degree all-in-one wealth and portfolio summary in one single report.
This skill automatically synthesizes:
1. Official Bank Statement Deposits & Withdrawals (from KKP Dime! Save Statement).
2. Live Active Holdings Valuation (from TradingView Scanner API).
3. Complete Buy Orders Ledger (all 55 buy orders parsed from Dime! order confirmation slips).
4. Closed Realized Trades Ledger & Win Rate (from `data/trades.json` - 7 winning sales).
5. Total Dividends Received (13 payments from historical corporate actions).
6. Dime! Save Cash Movement & Deposit Ledger (54 transactions including PromptPay deposits, stock deductions, and interest).
7. Current Cash Reserves (Dime! Save THB and Dime! USD cash).

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
   - 💰 **เงินต้นทุนเติมสุทธิ (Net Injected Capital):** อ้างอิงจาก KKP Statement ทางการ (1,245,000.00 บาท).
   - 🚀 **กำไรรวมสุทธิของพอร์ต (All-Time Net Profit):** NAV ลบเงินต้นสุทธิ พร้อมคำนวณ All-Time ROI %.
   - 💵 **เงินสดพร้อมใช้รวม (Total Idle Cash):** Dime! Save (THB) และ Dime! USD Cash.
   - 🛒 **ประวัติคำสั่งซื้อหุ้นทั้งหมด (Buy Orders History):** 55 ไม้พร้อมจำนวนหุ้น ราคาที่ได้จริง ยอดเงิน และช่องทางชำระเงิน.
   - 🏆 **กำไรที่ปิดทำกำไรจริง (Realized P&L):** กำไรสะสมจากการขายหุ้นจริง (7 ไม้ Win Rate 100%).
   - 💸 **เงินปันผลรับสะสม (Dividends):** ยอดรับปันผลสุทธิทั้งหมด (13 ครั้ง).
   - 🏦 **ประวัติการเติมเงินและเงินสด (Cash Flow & Deposits):** รายการเดินบัญชี Dime! Save 54 รายการ.
   - 📈 **สถานะหุ้นปัจจุบันในพอร์ต (Active Holdings):** ราคาตลาดสด กำไร Unrealized P/L รายตัว.
4. **แนบลิงก์คลิกเปิดรายงานหน้าเว็บสวยงาม:**
   - `reports/portfolio_master.html`

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
ตัวเลขสรุปในไฟล์นี้ (จำนวนไม้ จำนวนครั้ง และเงินต้น) อัปเดตอัตโนมัติทุกครั้งที่รัน `/master` หรือ `/all` ผ่าน `scripts/sync_skill_numbers.py`.

---

## 📂 Source Code Architecture

- Master Report Generator: `scripts/generate_master_report.py`
- Master HTML Dashboard: `reports/portfolio_master.html`
- Aggregated Account Data JSON: `data/account_summary.json`
- Closed Trades Database: `data/trades.json`
- Active Holdings Data: `data/portfolio.json`
- Cash, Deposits & Dividends Ledger: `data/ledger.json`
- Official KKP Statement PDF: `data/KKP_STATEMENT_20261007.pdf`
