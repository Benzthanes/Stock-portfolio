# Project Review: filter-stock (ข้อเสนอแนะทั้งโปรเจกต์)

รีวิวเมื่อ 2026-10-17 ตรวจซ้ำเมื่อ 2026-10-22 แบบ read-only แบ่งเป็น 4 ส่วน (เงินและพอร์ต, HTML report, data/chart pipeline, repo/CI/tests)
ทุกข้อติดป้าย **[ยืนยัน]** (รันหรือ trace โค้ดแล้ว) หรือ **[ยังไม่ยืนยัน]** / **[น่าจะใช่]**

## ภาพรวมตัวเลข (วัดจริง)
- Test ผ่าน 207/207 ใน 30.3 วินาที (Python 3.11) ไม่มี linter, formatter หรือ type checker
- ไม่มี dependency ภายนอก ใช้ stdlib ทั้งหมด
- `data/candles_cache.json` ขนาด 38 MB สำหรับ 27 ticker โดย 18.3 MB เป็น `candle_colors` ของ CDC ที่หน้าเพจไม่ได้ใช้
- `reports/chart_data.js` ขนาด 4.2 MB (gzip 0.91 MB) ผู้ใช้โหลดทุก ticker ทุกครั้งที่เปิดหน้า
- `compute_fibo_and_indicators` ใช้ 11 ถึง 71 ms ต่อ ticker ไม่ใช่คอขวด
- 24 จาก 27 commit แตะ `reports/` และ bot commit แต่ละครั้งเขียนใหม่ราว 550 ถึง 940 บรรทัด

---

## 🔴 P1 ตัวเลขเงินผิด (กระทบการตัดสินใจลงทุนโดยตรง)

### 7. ใช้ต้นทุนผิดสกุลเงิน [ยืนยันจาก trace ยังไม่เกิดจริง]
- `recovery.py:98` และ `:345` ใช้ `avg_cost_thb or avg_cost_usd` โดยไม่ดู `base_currency`
- `src/portfolio.py:361` มีปัญหากลับด้านสำหรับพอร์ต THB
- แก้: ใช้ accessor เดียว `cost_basis(holding, base_currency)`

---

## 🟠 P2 ข้อมูลที่ดูเหมือนข้อเท็จจริงแต่ไม่ใช่

### 8. Sentiment และสรุปข่าว [ยังไม่ยืนยัน]
- พาดหัวที่มีคำว่า AI แต่ไม่มี keyword ลบ จะถูกบังคับเป็น bullish (`src/news.py:132`) เช่น "AI bubble fears hit chip stocks" ได้ bullish
- "SEC charges executive" ได้ neutral
- สรุป ผลกระทบ และกลยุทธ์เป็น template ตาม sentiment ตอนนี้มีป้ายเตือนใน modal แล้ว แต่ใน card ยังไม่มี
- แก้: เลิกให้ AI เป็น bullish โดยอัตโนมัติ เพิ่ม keyword ลบอย่าง "fears", "charges", "bubble" และติดป้ายบน card ว่าเป็น heuristic

### 9. ข้อมูลขาดถูกแปลงเป็นข้อความมั่นใจ [ยืนยัน]
- `src/screener.py:595` ถ้าไม่มีข่าวลบ (รวมถึงตอนดึงข่าวล้มเหลวแล้วได้ `[]`) จะพิมพ์ว่า "การย่อเป็นแค่ market correction"
- `src/screener.py:614` ถ้า revenue growth เป็น None จะพิมพ์ว่า "ธุรกิจมั่นคงมาก"
- `src/outlook.py:268-271` เปลี่ยนค่าที่หายเป็น `0.0` แล้วแสดงเป็น "+0.0% YoY" หรือ "PEG 0.00"
- แก้: แยกสถานะ "ดึงข้อมูลไม่ได้" ออกจาก "ไม่มีข้อมูล" แล้วแสดง "-"

### 10. ข้อมูลเขียนตายตัว [ยืนยัน]
- Pattern win rate เช่น "71% Bulkowski" (`src/chart_data.py:134-594`) แต่ detector เป็น swing heuristic ไม่ใช่นิยามของ Bulkowski
- Thesis ของ 9 บริษัทใน `src/outlook.py:54-263` เช่น NVDA "Gross Margin 73-75%" และจำนวนโบรกเกอร์อย่าง "50+" หรือ "28 แห่ง" ทั้งที่มี `rec_buy/hold/sell` จริงให้ใช้อยู่แล้ว
- "🤖 AI Confluence" จริงๆ คือ rule-based scoring
- แก้: ตัด % ที่อ้างแหล่งไม่ได้ทิ้ง ใส่วันที่กำกับข้อความที่ curate เอง สร้างจำนวนโบรกเกอร์จากข้อมูลสด และเปลี่ยนชื่อเป็น "Rule-based Confluence"

### 11. Indicator ที่ anchor ตั้งแต่ IPO ใช้งานไม่ได้ [ยังไม่ยืนยัน]
- Volume POC ของ JNJ อยู่ที่ $3.58 ขณะที่ราคาปิดคือ $255.52
- VWAP ตั้งแต่ IPO ของ JNJ คือ $66.88
- `fibo_macro` anchor ที่ low ปี 1970 ราคา $0.78
- แก้: anchor ย้อนหลัง 1 ถึง 2 ปี หรือที่ swing ที่เลือกไว้

### 12. สูตร Indicator ไม่ตรง TradingView [ยืนยัน ผลกระทบต่ำ]
- Supertrend (`src/chart_data.py:1980`) ใช้ ATR แบบ SMA แต่ TradingView ใช้ RMA เช่น VRT ได้ 242.33 เทียบกับ 243.52 แต่ทิศทางยังตรงกัน
- Pivot (`:2088`) ใช้ high/low 22 แท่งที่รวมวันนี้ แต่ Classic pivot ใช้ HLC ของเดือนก่อนหน้า
- ส่วนที่ถูกต้องแล้วคือ RSI Wilder, ATR14, MACD, Stochastic, SAR และสูตร Fibonacci

---

## 🟠 P2 การแสดงผลผิดและความปลอดภัยของ HTML

### 15. Escape ไม่ครบ [ยังไม่ยืนยัน]
- ชื่อบริษัทและ sector จาก TradingView ไม่ถูก escape ใน master, ledger, dip sim และ `outlook.py:274-283`
- onclick ของ dip sim (`scripts/generate_dip_sim_report.py:26-38`) escape แค่ `'` ถ้าชื่อมี `"` attribute จะพัง
- `openSlipModal('...')` ใน ledger ใส่ชื่อไฟล์ OCR ตรงๆ
- แก้ระยะสั้น: ใช้ `_make_chart_onclick` ของ `html_report.py` (ใช้ `json.dumps` บวก `escape`) ที่เดียว
- แก้ระยะยาว: ใช้ Jinja2 ที่เปิด autoescape (ดูข้อ S2)

---

## 🟡 P3 ความทนทานของระบบและ CI

### 17. Skills ของ Claude Code ไม่ไปกับ repo [ยืนยัน]
- `.gitignore:10` ignore `.claude/` อยู่ ส่วน `.claude/skills` เป็น symlink ไปที่ `.agents/skills`
- clone ใหม่จะใช้ `/all /dip /fix /master /port` ไม่ได้
- แก้: เพิ่ม `!.claude/skills` แล้ว commit symlink

### 18. CI ทิ้งการแก้ SKILL.md [ยืนยัน]
- `portfolio.py:50-51` เรียก `sync_skill_numbers` ซึ่งเขียน `.agents/skills/master/SKILL.md` ใหม่ แต่ workflow รันแค่ `git add reports/ data/`
- แก้: หยุดแก้ไฟล์เอกสารที่ track อยู่ทุกครั้งที่รัน หรือเพิ่ม path นี้ใน `git add`

### 19. Error ถูกกลืนทิ้งเงียบๆ [ยืนยัน]
- `portfolio.py:41` และ `src/chart_data.py:2310` (`_fetch_and_process` ที่ใช้ 10 worker) กลืน exception ทิ้ง cache เก่าจึงถูก commit ราวกับเป็นข้อมูลใหม่
- `src/trades.py:810` ถ้า master ledger พังจะเงียบแล้ว render HTML แบบเก่าราว 300 บรรทัดแทน
- เรียก API ที่ไม่เป็นทางการทั้งหมดโดยไม่มี retry หรือ backoff ได้แก่ Yahoo v8, TradingView scanner, Google News RSS และ Translate `gtx`
- แก้: ทำ `src/http.py` ตัวเดียวที่มี timeout, retry, backoff และคืนค่าเป็น `{ok, data, error}` แล้วแสดงป้าย "ข้อมูลเก่า" บนหน้าเพจ

---

## 🔵 โครงสร้าง (คนดูแลโค้ดต่อจะได้ประโยชน์ที่สุด)

### S1. แยก source ออกจาก output
- Deploy `reports/` ผ่าน `actions/upload-pages-artifact` แทนการ commit ลง main แล้ว gitignore `reports/` กับ `data/account_summary.json`
- ได้ผลพร้อมกัน 3 อย่าง: เลิก bot commit churn, เลิก push race และหยุดให้ history โตขึ้นเรื่อยๆ (ตอนนี้ pack 11 MB และ `chart_data.js` ถูก commit แล้ว 17 รอบ)

### S2. Template แยกจาก Python
- `src/chart_page.py` มี f-string เดียวยาว 4,731 บรรทัด (CSS 1,207, HTML 533, JS 2,972) โดยมีจุด interpolate จริงแค่ 5 จุด
- Report อื่นมี f-string ยาว 400 ถึง 1,190 บรรทัด
- `:root` CSS ซ้ำกัน 6 ชุดรวมราว 1,133 บรรทัด และเริ่มไม่ตรงกันแล้ว
- Google Fonts ซ้ำ 12 จุด และ onclick builder ซ้ำ 3 ตัว
- แผน: ทำ `templates/base.html` แล้วให้แต่ละหน้าเป็น child template บน Jinja2 ที่เปิด autoescape แยก `assets/app.css` และ `app.js` ออกมา ส่วนหน้ากราฟย้าย JS ไปเป็น `chart.js` แล้ว lint และ test ได้
- วิธีพิสูจน์: diff HTML ที่ render ได้กับ output ปัจจุบัน (ประเมินว่าหน้ากราฟใช้เวลาราวครึ่งวัน)

### S3. โมเดลข้อมูลมีชนิดชัดเจน และให้ transaction เป็นต้นทาง
- ทำ dataclass `Holding`, `Trade` และ `Ledger` ที่มี loader เดียว แทน fallback chain ที่กระจายอยู่ 3 ไฟล์
- รายชื่อ ETF `("VOO","SPY","QQQ")` ซ้ำ 4 จุดและไม่มี QQQI ที่เคยเทรดจริง
- คำนวณ holding, cost basis และ P&L THB จาก log ของ buy, sell, dividend และ FX ที่เก็บ FX ไว้ทุกรายการ แบบนี้ตัวเลขจะ drift ไม่ได้ (แก้ P1 ข้อ 1 ถึง 3 ทั้งกลุ่ม)
- เก็บจำนวนเงินเป็น `Decimal` หรือหน่วยเซ็นต์ และปัดเศษเฉพาะตอนแสดงผล

### S4. เป็น Python package จริง
- เพิ่ม `pyproject.toml` ย้าย `recovery.py` (805 บรรทัด) และ `scripts/generate_*.py` (2,477 บรรทัด ซึ่งจริงๆ เป็น library) เข้า `src/`
- ลบ `sys.path.insert` ทั้ง 16 จุด แล้วรันด้วย `python -m`
- ย้ายรูปใน `src/port/` ไปไว้ที่ `data/screenshots/port/`
- เพิ่ม config ของ ruff

### S5. Page registry
- ขยาย `src/nav.PAGES` ให้แต่ละหน้ามี renderer และ loader ของตัวเอง แล้วให้ `--all`, `index.html`, nav, README และ `all/SKILL.md` สร้างจากรายการนี้รายการเดียว
- ตอนนี้รายชื่อ 6 report ซ้ำอยู่ 3 ที่ และหน้า SET หลุดออกจากรายการไปแล้ว

### S6. แยกข้อเท็จจริงออกจาก heuristic
- ทุกค่าที่แสดงให้มี `source` เป็น `computed`, `heuristic`, `curated:<วันที่>` หรือ `unavailable` แล้ว render ป้ายตามนั้น

### S7. โหลดข้อมูลกราฟทีละ ticker
- แยกเป็น `charts/<T>.json` แล้ว lazy-load ตอนผู้ใช้เลือก จะลดการโหลดครั้งแรกจาก 4.2 MB เหลือราว 170 KB (ค่าประมาณ)

---

## 🧪 Test ที่ควรเพิ่ม
- `analyze_portfolio` ซึ่งเป็นเส้นทางเงินหลักยังไม่มี test เลย
- `calculate_trades_summary`: win rate, profit factor, ขายเท่าทุน และกรณีไม่มีข้อมูล
- ต้นทุน THB ต้องรวมแล้วเท่าเดิมหลังขายบางส่วนที่ FX ต่างจากวันซื้อ
- ค่าธรรมเนียม input ติดลบ และหุ้นที่ไม่ได้ราคา
- Snapshot test ที่ render ทุกหน้าจาก `tests/fixtures/*.json` แบบ offline แล้ว assert ว่าไม่มี `$-`, `+-` และไม่มี `<` ดิบจาก fixture
- Golden test ที่เทียบ Supertrend และ pivot กับค่าจาก TradingView 2 ถึง 3 ticker
- ปิด network ใน test base class: `test_larger_request_not_served_from_smaller_cache` ยังยิงไป `translate.googleapis.com` จริง
- Test ของหน้ากราฟที่ตอนนี้ใช้ `assertIn` หา substring ใน HTML 50 KB ควรเปลี่ยนไป assert ระดับข้อมูลแทน
- ยังไม่มี test เลยสำหรับ `src/tradingview.py`, `src/universe.py`, `src/profiles.py` และ `scripts/generate_dip_sim_report.py`

---

## 📋 ลำดับที่แนะนำ
1. **P1 ข้อ 7.** ตัวเลขเงินผิด แก้ได้ไม่กี่บรรทัด พร้อม test conservation ของต้นทุน
2. **ข้อ 17 ถึง 19.** commit symlink skills, หยุดกลืน error
3. **ข้อ 8 ถึง 10.** ติดป้ายหรือตัดข้อความที่ดูเป็นข้อเท็จจริงแต่ไม่ใช่
4. **S1.** เลิก commit output (ทำก่อน S2 เพราะ diff ของ template จะสะอาดขึ้นมาก)
5. **S3 และ S2.** refactor ใหญ่ ทำทีละหน้าและใช้ HTML diff พิสูจน์ว่าไม่เปลี่ยน behavior

## หมายเหตุ
- `REVIEW_FIXES.md` ถูก commit ไปใน `6f46cc4` แล้ว และทุกข้อในนั้นแก้ครบแล้ว ควรลบทิ้ง
