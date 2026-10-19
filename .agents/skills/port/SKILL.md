---
name: port
description: Live US stock portfolio health check with 1-5 star ratings from the unified grade (fundamentals + EMA200 zone), concentration risk (HHI), 14-day earnings guard, fresh-cash top picks, forbidden buys and news. Triggers on "/port", "port", "analytic port", "วิเคราะห์พอร์ต", "ตรวจสุขภาพพอร์ต", or requests to review portfolio holdings.
---

# Portfolio Health Check (`/port`)

ตรวจสุขภาพพอร์ตหุ้นจริงทั้งหมดในคำสั่งเดียว แล้วสรุปเป็นภาษาคน.
ถ้าจะแก้ logic การให้คะแนน ให้อ่าน `docs/METHODOLOGY.md` ก่อน.

## ก่อนเริ่ม

อ่าน `AGENTS.md` ที่ root ของโปรเจกต์ให้จบก่อน. จุดที่ต้องระวังเฉพาะ skill นี้มีดังนี้:
* ใน `src/portfolio.py` key `score` คือแต้มของ screener. ดาวและเกรดรวมอยู่ที่ `stock_score` และ `rating`.
* คำสั่ง `trades.py` ทุกคำสั่งต้องรันด้วย `--dry-run` ก่อน แล้วให้ผู้ใช้ยืนยันก่อนรันจริง.
* ถ้าเกรดของหุ้นตัวเดียวกันไม่ตรงกันในแต่ละหน้า แปลว่ามีบั๊ก. ให้แจ้งผู้ใช้และดูหัวข้อ 3 ของ `AGENTS.md`.

## วิธีรัน

เมื่อผู้ใช้พิมพ์ `/port` ให้รันทันทีโดยไม่ถามตัวเลือก.

```bash
python3 portfolio.py                                            # รายงาน Markdown ในแชท
python3 portfolio.py --save-report reports/portfolio_review.html  # สร้างหน้า HTML
```

## สิ่งที่ต้องสรุปให้ผู้ใช้

1. เกรดพอร์ต กำไรขาดทุนรวมทั้ง $ และ ฿ หุ้นที่ทำเงินที่สุด และหุ้นที่ฉุดพอร์ตที่สุด.
2. ความเสี่ยงการกระจุกตัว (HHI) และสัดส่วนตามกลุ่มธุรกิจ.
3. ดาวและเกรดรวมของหุ้นทุกตัว เช่น `⭐⭐⭐⭐ เกรด A · 75/100` พร้อมจุดเด่นและข้อควรระวัง.
4. หุ้นที่งบจะออกภายใน 14 วัน และคำเตือนว่าห้ามซื้อเพิ่มก่อนงบ.
5. ถ้ามีเงินใหม่ ควรซื้อตัวไหน (อันดับ 1 ถึง 3) พร้อมราคาแนวรับ แนวต้าน และ SL.
6. หุ้นที่ห้ามซื้อเพิ่ม และเหตุผล.
7. ข่าวดีและข่าวร้าย พร้อมราคาเป้าหมายจากนักวิเคราะห์.
8. เช็กลิสต์ 3 ข้อที่ควรทำวันนี้.

## ระบบดาวและเกรด (จาก `src/scoring.py`)

คะแนนรวมคิดจากพื้นฐาน 60% และโซนราคาเทียบ EMA200 40%.

| เกรด | คะแนนรวม | ดาว |
| :--- | :--- | :--- |
| A+ | ≥ 85 | ⭐⭐⭐⭐⭐ |
| A | 70 ถึง 84 | ⭐⭐⭐⭐ |
| B | 55 ถึง 69 | ⭐⭐⭐ |
| C | 40 ถึง 54 | ⭐⭐ |
| F | < 40 | ⭐ |
| ETF | ไม่ประเมินพื้นฐาน | ⭐⭐⭐⭐ คงที่ |

* ถ้าข้อมูลครบไม่ถึง 70% เกรดสูงสุดคือ B.
* คะแนนพื้นฐานใช้ Revenue YoY, Net Income YoY, ROE, PEG, D/E และ FCF. หุ้นกลุ่ม Finance ไม่ใช้ D/E.
* โซนราคา 0 ถึง 10% เหนือ EMA200 ได้คะแนนเต็ม. ต่ำกว่าเส้นเกิน 10% ได้ 0.
* สัดส่วนในพอร์ตและกำไรขาดทุนของผู้ใช้ไม่มีผลต่อดาว. ทั้งสองอย่างแสดงเป็นข้อควรระวังแทน.

## เงื่อนไขห้ามซื้อเพิ่ม (`analyze_portfolio()`)

ห้ามซื้อเพิ่มเมื่อเข้าข้อใดข้อหนึ่ง ตามลำดับนี้:
1. สัดส่วนในพอร์ต ≥ 25%.
2. งบออกภายใน 14 วัน.
3. วันนี้เป็น Plunge Day.
4. พื้นฐานได้เกรด F.

## บันทึกรายการซื้อขาย

```bash
python3 trades.py buy -t BAC -s 2 -p 48.10          # ทุกคำสั่งใส่ --dry-run เพื่อดูผลก่อนได้
python3 trades.py sell --ticker VST --price 160.50
python3 trades.py deposit --amount 20000
python3 trades.py withdraw --amount 5000
python3 trades.py dividend -t LLY --usd 3.50
python3 trades.py list                              # ดูกำไรขาดทุนและ Win Rate
```

## ไฟล์ที่เกี่ยวข้อง

* `portfolio.py` คือ CLI. `src/portfolio.py` คือ logic.
* `src/scoring.py` คือคะแนนและเกรด.
* `data/portfolio.json` คือหุ้นที่ถือ. `data/trades.json` คือเทรดที่ปิดแล้ว.
