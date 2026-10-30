---
name: all
description: Refreshes all 7 HTML reports in one run (Master Dashboard, Health Review, Recovery, Dip Simulation, Trades Ledger, Stock Chart, Watchlist), including AI Thai news translation and analysis, then verifies every page renders. Trigger on "/all", "all", "อัปเดตทั้งหมด", "ทำทุกอย่าง", "รันทั้งหมด", "อัปเดตทุกตัว", or requests to refresh all portfolio dashboards.
---

# All-in-One Refresh (`/all`)

อัปเดตรายงานทั้ง 7 หน้าในรอบเดียว พร้อมวิเคราะห์ข่าวใหม่ด้วย AI.
รายละเอียดทุกขั้นอยู่ใน `docs/METHODOLOGY.md` หัวข้อ 4 และ 5.

## ก่อนเริ่ม

อ่าน `AGENTS.md` ที่ root ของโปรเจกต์ให้จบก่อน. จุดที่ต้องระวังเฉพาะ skill นี้มีดังนี้:
* ห้ามแก้ `data/portfolio.json`, `data/trades.json` และ `data/ledger.json` ในงานนี้. ไฟล์ที่ `/all` เขียนได้มีแค่ `data/ai_news_cache.json`, `data/account_summary.json`, `data/candles_cache.json` และ `reports/`.
* **วันประกาศงบย้อนหลัง.** รายงานใช้ข้อมูลที่ยืนยันแล้วใน `src/earnings_calendar.py` เท่านั้น ห้ามเดาจากโวลุ่ม. ตอนรันในเครื่องใช้ Tavily ค้นวันงบที่ยังไม่มีได้ แต่ต้องยืนยันจากแหล่งทางการก่อนเพิ่มลงไฟล์ (หัวข้อ 3.1 ของ `AGENTS.md`). GitHub Actions ไม่ค้นภายนอก.
* ก่อนเขียนบทวิเคราะห์ข่าว ให้ยืนยันว่า ticker คือบริษัทอะไร (หัวข้อ 4 ของ `AGENTS.md`). SPCX คือหุ้น SpaceX.
* ถ้า `portfolio.py --all` แจ้งว่ามีขั้นตอนที่อัปเดตไม่สำเร็จ หน้านั้นยังเป็นข้อมูลเก่า. ให้บอกผู้ใช้ตรงๆ ว่าหน้าไหนไม่ได้อัปเดต.

## ขั้นตอนเมื่อรันกับ AI แบบ interactive

1. **ดึงข่าวที่ยังไม่ได้วิเคราะห์.**
   ```bash
   python3 -m src.ai_news --pending > /tmp/pending_news.json
   ```
2. **ยืนยันว่าแต่ละ ticker คือบริษัทอะไร** ก่อนเขียนบทวิเคราะห์. ดูจากตารางชื่อใน `src/chart_page.py`, ไฟล์ `data/trades.json` และวันแรกของแท่งเทียน. ตัวอย่างคือ SPCX ซึ่งเป็นหุ้น SpaceX ไม่ใช่ ETF.
3. **เขียนบทวิเคราะห์** ลงไฟล์ `/tmp/ai_news_analysis.json`. รูปแบบเป็น `{"TICKER": [article, ...]}`. คัดลอก field เดิมมาโดยไม่แก้ แล้วเพิ่ม field ต่อไปนี้:
   * `title_th` คือหัวข่าวภาษาไทยที่ใช้ศัพท์การเงิน. ชื่อบริษัทให้คงเป็นภาษาอังกฤษ.
   * `summary_th` คือ 2 ถึง 3 บรรทัดที่ขึ้นต้นด้วย `• `. ห้ามแต่งตัวเลขที่หัวข่าวไม่มี.
   * `impact_th` คือผลกระทบต่อราคาและพื้นฐาน.
   * `action_th` คือคำแนะนำสั้น 1 ประโยค.
   * `sentiment` เป็นได้แค่ `bullish`, `bearish`, `mixed` หรือ `neutral`.
   * `topic` คือหัวข้อภาษาไทย ตามด้วยภาษาอังกฤษในวงเล็บ.
   * หน้าราคาหุ้นทั่วไปให้ใส่ `sentiment = neutral` และ `topic = หน้าข้อมูลราคา (Quote Page)`.
   * ใช้ Tavily ค้นเพิ่มเมื่อหัวข่าวคลุมเครือหรือขัดกับข้อมูลอื่น เช่น บอกว่างบออกแล้วแต่ปฏิทินบอกว่ายัง. ใส่สิ่งที่ยืนยันได้และแหล่งที่มาลงใน `summary_th` หรือ `impact_th`. ถ้ายืนยันไม่ได้ให้เขียนว่ายังไม่ยืนยัน.
   * ก่อนสร้างรายงาน ใช้ Tavily เช็กหุ้นที่งบใกล้ออกหรือเลยวันงบล่าสุดในปฏิทิน ว่ามีวันงบใหม่หรือผลงบล่าสุดที่ควรรู้หรือไม่.
4. **ตรวจไฟล์ด้วย Python.** ticker และจำนวนข่าวต้องตรงกับ input. field ใหม่ต้องครบทั้ง 6 ตัว. sentiment ต้องอยู่ในชุดที่อนุญาต. จากนั้นสุ่มอ่านเองอย่างน้อย 5 ข่าว.
5. **สำรอง cache แล้วรวมข่าวเข้า cache.**
   ```bash
   cp data/ai_news_cache.json /tmp/ai_news_cache.before.json
   python3 -m src.ai_news --save /tmp/ai_news_analysis.json
   ```
6. **สร้างรายงานทั้งหมด.** ต้องจบด้วย exit 0 และขึ้นข้อความ "อัปเดตรายงานทั้งหมด 7 รายการเรียบร้อยสมบูรณ์".
   ```bash
   python3 portfolio.py --all
   ```
7. **ตรวจข้อมูลในรายงานด้วยสคริปต์.** ต้องจบด้วย exit 0 และขึ้น `0 problems`. ถ้ามีปัญหาให้หยุด รายงานผู้ใช้ และห้าม commit.
   ```bash
   python3 scripts/check_reports.py
   ```
   สคริปต์เช็กบั๊กที่หน้าเว็บไม่แสดงเป็น error. ได้แก่ stop หรือ target กลับด้าน, earnings guard ที่ไม่มีจำนวนวัน, guard บนกราฟที่ไม่ตรงกับ `days_to_earnings` ใน `data/account_summary.json` และแท่งสุดท้ายที่ตกวันเสาร์อาทิตย์หรือเลยวันปัจจุบันของตลาดสหรัฐฯ.
8. **ตรวจทุกหน้าด้วย Chrome แบบ headless** ตามคำสั่งใน `docs/METHODOLOGY.md` หัวข้อ 5. จำนวน `Uncaught` error ต้องเป็น 0 ทุกหน้า. ให้เปิดดู screenshot ของหน้า Review และหน้า Chart เองด้วย.
9. **สรุปให้ผู้ใช้.** บอก NAV, กำไรสะสม, จำนวนข่าวที่วิเคราะห์ใหม่, หุ้นที่เกรดเปลี่ยน และหุ้นที่งบออกภายใน 14 วัน.

## เมื่อรันใน GitHub Actions

* Workflow `.github/workflows/update_portfolio.yml` รัน `python3 portfolio.py --all`.
* ระบบใช้บทวิเคราะห์จาก `data/ai_news_cache.json` ก่อนเสมอ และไม่เขียนทับของเดิม.
* ข่าวที่ AI ยังไม่ได้วิเคราะห์จะใช้ heuristic แทนชั่วคราว.
* หลังสร้างรายงาน workflow รัน `python3 scripts/check_reports.py`. ถ้าเจอปัญหา workflow ยัง push รายงานใหม่ แต่ job จะ fail และเปิด issue.

## รายงานที่ได้

1. `reports/portfolio_master.html` คือภาพรวมความมั่งคั่ง.
2. `reports/portfolio_review.html` คือสุขภาพพอร์ต ดาว และเกรดรวม.
3. `reports/portfolio_recovery.html` คือแผนแก้ดอย.
4. `reports/portfolio_dip_sim.html` คือพอร์ตจำลองช้อนซื้อ.
5. `reports/trades_ledger.html` คือรายการซื้อขายทั้งหมด.
6. `reports/stock_chart.html` คือกราฟ, การ์ดคะแนนรวม และข่าว.
7. `reports/watchlist.html` คือแนวรับ Fibo และหุ้นที่สนใจ.
