---
name: fix
description: Drawdown recovery and breakeven planner for underwater holdings (เทคนิคแก้หลุดดอย 360 องศา). Picks Freeze DCA, Smart DCA, Rebound Exit, Capital Rotation or Hold & Guard from the unified grade, EMA200 zone and the 14-day earnings guard. Trigger on "/fix", "fix", "/rescue", "rescue", "แก้ดอย", "แก้ติดลบ", "กู้พอร์ต", or requests to recover underwater positions.
---

# Portfolio Drawdown Recovery (`/fix`)

วิเคราะห์หุ้นที่ติดลบว่าควรถัว ควรรอเด้งออก หรือควรโยกเงิน แล้วสรุปเป็นภาษาคน.
ถ้าจะแก้กฎการตัดสินใจ ให้อ่าน `docs/METHODOLOGY.md` หัวข้อ 1.4 ก่อน.

## ก่อนเริ่ม

อ่าน `AGENTS.md` ที่ root ของโปรเจกต์ให้จบก่อน. จุดที่ต้องระวังเฉพาะ skill นี้มีดังนี้:
* ถ้าไม่มีค่า RSI หรือ EMA200 (เช่นหุ้น IPO ใหม่) ระบบจะไม่แนะนำ Smart DCA. นี่คือพฤติกรรมที่ตั้งใจไว้ ไม่ใช่บั๊ก.
* หุ้นที่ไม่มีข้อมูลงบ (เกรด N/A) จะไม่ถูกแนะนำ Capital Rotation. ให้บอกผู้ใช้ว่าข้อมูลไม่พอประเมิน.
* `recovery.py TICKER` เขียนไฟล์ `reports/recovery_TICKER.md`. ถ้ารันเพื่อทดสอบ ให้ลบไฟล์นี้ทิ้งหลังใช้.
* **ค้นข้อมูลด้วย Tavily (รันในเครื่องเท่านั้น).** ใช้เครื่องมือ Tavily MCP ถ้ามี หรือรัน `/usr/bin/python3 -m src.tavily "<คำค้น>"` (ต้องมี `TAVILY_API_KEY` ใน environment). ทุกข้อเท็จจริงต้องบอกแหล่งที่มา และถ้ายืนยันไม่ได้ให้บอกว่ายังไม่ยืนยัน (หัวข้อ 3.1 ของ `AGENTS.md`). สำหรับ skill นี้ ใช้ Tavily หาว่าราคาลงเพราะอะไร (ข้อ 6) และแยกให้ได้ว่าเป็นปัญหาพื้นฐานของบริษัท (เช่น งบแย่ ลด guidance คดีความ) หรือแค่แรงขายทั้งตลาด เพราะผลนี้ช่วยเลือกระหว่าง Smart DCA กับ Capital Rotation.

## ตัวเลือกคำสั่ง

ถ้าผู้ใช้พิมพ์ `/fix` เฉยๆ ให้รันตัวเลือก (Recommended) ทันทีโดยไม่ถามก่อน.
เมื่อแสดงผลเสร็จ ให้ปิดท้ายด้วยรายการตัวเลือกอื่นบรรทัดละ 1 ตัวเลือก.

| ผู้ใช้พิมพ์ | คำสั่งที่รัน |
| :--- | :--- |
| `(Recommended) /fix` หรือ `แก้ติดลบ` | `python3 recovery.py` |
| `/fix APP` | `python3 recovery.py APP` |
| `/fix TSLA --shares 10 --cost 250` | `python3 recovery.py TSLA --shares 10 --cost 250` |
| บันทึกเป็นไฟล์ | `python3 recovery.py [TICKER] --save-report reports/xxx.md` |

## ลำดับการตัดสินใจ (ตรงกับ `analyze_recovery()` ใน `recovery.py`)

1. **🟠 Freeze DCA.** งบออกภายใน 14 วัน (`EARNINGS_GUARD_DAYS`). ห้ามถัวจนกว่างบออก.
2. **🟢 Smart DCA.** พื้นฐานได้เกรด A+ หรือ A, ราคาไม่ต่ำกว่า EMA200 เกิน 10% และ RSI ≤ 35 หรือมี RSI Hook (`entry_signal`). ให้รอแท่งเทียนเขียวที่แนวรับก่อนซื้อ.
3. **🎯 Rebound Exit.** ต้นทุนเฉลี่ยต่ำกว่า SMA20. ไม่ต้องเติมเงิน รอเด้งคืนทุนแล้วขาย.
4. **🔄 Capital Rotation.** พื้นฐานได้เกรด C หรือ F. ตัดขาดทุนแล้วโยกเงินไปหุ้นที่ผ่านเกณฑ์ `/dip`.
5. **🛡️ Hold & Guard.** กรณีอื่น. ถือต่อและเฝ้าแนวรับ. จุดตัดขาดทุนอยู่ที่ราคาปิดลบ 1.5 ATR.

เหตุผลของกฎข้อ 2 มาจาก backtest. ราคาที่ต่ำกว่า EMA200 เกิน 10% มี drawdown 60 วันลึกที่สุด. ตัวกรองมีดตกจาก VFI หรือ Chandelier ไม่ช่วยอย่างมีนัยสำคัญ จึงไม่ใช้.
ETF (VOO, QQQI) ไม่ได้รับคำแนะนำ Capital Rotation.

## สิ่งที่ต้องสรุปให้ผู้ใช้

1. ตารางหุ้นติดลบ เรียงตามความรุนแรง พร้อมต้นทุน ราคาปัจจุบัน และ % ที่ต้องเด้งเพื่อคืนทุน.
2. คำตัดสิน (`action_verdict`) ของแต่ละตัว และเหตุผลตามลำดับการตัดสินใจด้านบน.
3. เกรดรวม เช่น `เกรด C · 48/100` พร้อมเหตุผลหลัก 2 ถึง 3 ข้อ.
4. ถ้าแนะนำ Smart DCA ให้บอกราคาแนวรับที่ควรตั้งซื้อ และต้นทุนเฉลี่ยใหม่ถ้าซื้อเพิ่ม 50% หรือ 100%.
5. ถ้าแนะนำ Capital Rotation ให้บอกว่าหุ้นใหม่ต้องได้กำไรกี่ % จึงจะชดเชยส่วนที่ขาดทุนได้ (`gain_pct_needed_on_rotation`).
6. ข่าวที่อธิบายว่าทำไมราคาลง ค้นด้วย Tavily พร้อมแหล่งที่มา. บอกว่าเป็นปัญหาเฉพาะบริษัทหรือแรงขายทั้งตลาด.

## ไฟล์ที่เกี่ยวข้อง

* `recovery.py` คือ CLI และ logic การตัดสินใจ.
* `src/scoring.py` คือเกรดพื้นฐานและเกรดรวม.
* `src/html_report.py` `generate_recovery_html()` คือหน้า `reports/portfolio_recovery.html`.
* `data/portfolio.json` คือหุ้นที่ถืออยู่.
