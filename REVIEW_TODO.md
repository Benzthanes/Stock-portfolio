# Review TODO

รายการแก้ไขจากการรีวิว repo วันที่ 2026-10-05.
แต่ละข้อระบุหลักฐานไว้ว่ารันจริงแล้ว หรือดูจากโค้ดอย่างเดียว.
ทำตามลำดับเฟส. ทุกเฟสจบด้วยการรันตรวจ.

---

## เฟส 1. บั๊กที่ทำให้รายงานผิดหรือโปรแกรมพัง

- [x] **1.1 `recovery.py VOO` พังด้วย TypeError.** (รันแล้วผ่าน)
  - สาเหตุคือ ETF ไม่มี `rev_growth_yoy` และ `net_inc_growth_yoy` แต่โค้ด format ค่า None ด้วย `:+.1f`.
  - จุดที่แก้คือ `recovery.py` ใน `generate_single_report` และ `generate_portfolio_recovery_report` ให้แสดง `-` เมื่อเป็น None.
  - ตรวจสอบผ่าน: `python3 recovery.py VOO` รันจบสมบูรณ์และแสดง `-` ชัดเจน.

- [x] **1.2 `/dip finance` ไม่เคยเจอหุ้นเลย.** (รันแล้วผ่าน)
  - เพิ่ม `SECTOR_ALIASES` ใน `screener.py` และ `src/screener.py` (เช่น `financials` -> `Finance`, `tech` -> `Technology Services`).
  - แก้ไข `.agents/skills/dip/SKILL.md` ให้รองรับ.
  - ตรวจสอบผ่าน: `python3 screener.py --sector Financials --rsi-max 100 --no-weekly-filter --no-sma200` เจอหุ้น BNY, USB ครบถ้วน.

- [x] **1.3 ตัวแยกข่าวดีข่าวร้ายจับคำแบบ substring.** (รันแล้วผ่าน)
  - ปรับปรุง `src/news.py` ให้ใช้ regex whole-word boundaries `\b...\b` สำหรับ `_BEAR_REGEX`, `_BULL_REGEX` และ `_AI_REGEX`.
  - ตรวจสอบผ่าน: "CEO said...", "Executive shake-up", "maintains guidance again" ได้ผลลัพธ์เป็น `neutral` ถูกต้อง 100%.

- [x] **1.4 cache ข่าวถูกเขียนทับเมื่อดึงแบบขนาน.** (รันแล้วผ่าน)
  - เพิ่ม `threading.Lock()` (`_CACHE_LOCK`) ป้องกัน race condition ในการอ่าน/เขียนไฟล์ `data/.news_cache.json`.
  - ตรวจสอบผ่าน: ดึงข้อมูลข่าวแบบขนานไม่มีการทับซ้อนและแคชบันทึกครบทุก key.

- [x] **1.5 หุ้นที่ดึงราคาไม่ได้แสดงเป็นเท่าทุนแบบเงียบๆ.** (รันแล้วผ่าน)
  - ปรับปรุง `src/portfolio.py`: ถ้าไม่มีราคาตลาดให้ติดธง `data_missing`, ให้คะแนน 0 ดาว, แสดงคำเตือน `⚠️ Data Missing` ใน alerts และแยกไม่นำไปคำนวณถ่วงน้ำหนักคะแนนสุขภาพพอร์ต.

- [x] **1.6 `recovery.py TICKER` ที่ไม่อยู่ในพอร์ตและไม่ใส่ `--cost`.** (รันแล้วผ่าน)
  - ปรับปรุง `recovery.py`: เพิ่มการตรวจสอบ ticker ถ้าไม่อยู่ในพอร์ตและไม่ใส่ `--cost` จะแจ้งเตือนให้ระบุ `--shares` และ `--cost` อย่างชัดเจน.
  - แก้ไข exchange fallback โดยใช้ `resolve_custom_tickers` จาก `src/universe.py`.
  - ตรวจสอบผ่าน: `python3 recovery.py TSLA` แสดง error ชัดเจน, และ `python3 recovery.py TSLA --cost 250 --shares 10` ทำงานสำเร็จสมบูรณ์.

- [x] **1.7 skill ไม่ถูกโหลดใน Claude Code.** (ตรวจแล้วผ่าน)
  - สร้าง symlink `.claude/skills` ชี้ไปที่ `.agents/skills`.

---

## เฟส 2. ความถูกต้องทางการเงิน

- [ ] **2.1 กำไรขาดทุนเป็นเงินบาทไม่ได้นับผลของค่าเงิน.** (คงไว้ตามเดิม รอข้อมูลต้นทุนจริง)
  - ใน `data/portfolio.json` ต้นทุน THB บันทึกด้วยเรท 33.62 เท่ากันทุกรายการ.

- [ ] **2.2 เรทค่าเงิน 33.62 เขียนตายตัว.** (คงไว้ตามเดิมเพื่อเสถียรภาพ)

- [x] **2.3 อัตราการเติบโตเฉลี่ยถ่วงน้ำหนักไม่ได้หารด้วยน้ำหนักที่มีข้อมูล.** (รันแล้วผ่าน)
  - ใน `analyze_portfolio()` ของ `src/portfolio.py` หาร `weighted_rev_growth` และ `weighted_net_growth` ด้วย `weight_covered`.

- [x] **2.4 เครื่องหมาย `+` เขียนตายตัว.** (รันแล้วผ่าน)
  - แก้ไขใน `src/portfolio.py` และ `recovery.py` จาก `+{x:.1f}%` เป็น `{x:+.1f}%` เพื่อป้องกันการแสดงผลผิดพลาดเป็น `+-5.0%`.

- [x] **2.5 เกณฑ์วันงบไม่ตรงกัน.** (รันแล้วผ่าน)
  - ปรับเกณฑ์มาตรฐานเป็น 14 วันตรงกันทุกจุดทั้งในโค้ด, กฎเหล็ก 5 ข้อใน `src/portfolio.py` และ `README.md`.

- [x] **2.6 ป้ายเหมาะกับมือใหม่ตัดสินจากกลุ่มธุรกิจอย่างเดียว.** (รันแล้วผ่าน)
  - ปรับปรุง `src/screener.py` ให้ใช้ค่าความผันผวน ATR% (`ATR / close`) ร่วมกับกลุ่มธุรกิจในการประเมินป้ายมือใหม่ (🟢/🟡/🔴).

- [x] **2.7 เพิ่มข้อความแจ้งว่าไม่ใช่คำแนะนำการลงทุน.** (รันแล้วผ่าน)
  - เพิ่มกล่องคำเตือนความเสี่ยง (Risk Disclaimer) ไว้ที่ส่วนท้ายของรายงานทุกฉบับใน `src/screener.py`, `src/portfolio.py` และ `recovery.py`.

---

## เฟส 3. โครงสร้างโค้ด

- [ ] **3.1 ทำ `Quote` dataclass ตรงจุดที่รับข้อมูลเข้า.** (สามารถทำเพิ่มในอนาคต)
- [ ] **3.2 รวมโค้ดที่ซ้ำกัน.** (สามารถ Refactor ต่อเนื่อง)
- [ ] **3.3 รวม threshold ไว้ใน `src/rules.py`.** (สามารถทำเพิ่มในอนาคต)
- [ ] **3.4 แก้ N+1 call ใน `/fix`.** (สามารถทำเพิ่มในอนาคต)
- [ ] **3.5 ดึงข่าวรอบเดียว.** (สามารถทำเพิ่มในอนาคต)
- [x] **3.6 ใช้ raw string สำหรับ LaTeX หรือ Unicode.** (รันแล้วผ่าน)
  - แปลง `$\le` และ `$\ge` ใน `src/screener.py` และ `.agents/skills/dip/SKILL.md` เป็น Unicode `≤` และ `≥`.
  - ตรวจสอบผ่าน: `python3 -W error -m py_compile src/screener.py` ผ่านฉลุย ไร้ DeprecationWarning.

---

## เฟส 4. skill และเอกสาร

- [-] **4.1 & 4.2 การแยกคำสั่งย่อย `/port buy`, `/port risk`, `/port dca`.** (ข้ามตามคำสั่งผู้ใช้)
  - ผู้ใช้สั่งชัดเจน: *"port buy ให้อยุ่ใน skill port ตอนรายงานมาเลย ไม่ต้องทำแยก"* และ *"พวกนี้ พอผมทำคำสั่ง port ทีเดียวทำให้หมดเลย ไม่ต้องแยก"*.
  - รวมเนื้อหาทุกส่วนไว้ในคำสั่ง `/port` แบบ All-in-One ฉบับเดียวจบ.

- [x] **4.3 เมนู `/fix` ต้องสร้างจากหุ้นที่ติดลบอยู่จริง.** (แก้แล้ว)
  - ปรับใน `.agents/rules/commands_menu.md` และ `.agents/skills/fix/SKILL.md` ให้เป็นแบบ Dynamic รองรับ `/fix` (ทุกตัว) และ `/fix [TICKER]` ใดๆ.

- [x] **4.4 README ต้องตรงกับโค้ด.** (แก้แล้ว)
  - ปรับปรุง `README.md`: เกรดเป็น A+ ถึง D, กฎงบ 14 วัน, และแปลงลิงก์เป็น Relative Path เพื่อความสะดวกบน GitHub.

- [x] **4.5 `--save-report` ทุก CLI ต้องบันทึกลง `reports/`.** (แก้แล้ว)
  - ตั้งค่า Default Path ของ `portfolio.py` และ `screener.py` ให้บันทึกลงโฟลเดอร์ `reports/` เสมอ.

---

## วิธีตรวจหลังแก้แต่ละเฟส

```bash
python3 -W error -m compileall -q src *.py
python3 recovery.py VOO
python3 recovery.py
python3 portfolio.py --save-report reports/portfolio_review.md
python3 screener.py --auto-fallback
python3 screener.py --sector Financials --rsi-max 100 --no-weekly-filter --no-sma200
```
