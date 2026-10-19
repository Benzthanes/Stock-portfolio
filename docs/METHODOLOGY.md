# คู่มือวิธีทำงานกับระบบคะแนน, backtest และข่าว AI

เอกสารนี้เขียนให้ AI agent (Gemini, Claude หรือตัวอื่น) อ่านก่อนแก้ระบบคะแนน รัน backtest หรือวิเคราะห์ข่าว.
กฎสรุปที่ต้องอ่านก่อนทุกงานอยู่ใน `AGENTS.md`. เอกสารนี้คือรายละเอียดทีละขั้น.
ทำตามขั้นตอนตามลำดับ. ทุกขั้นมีคำสั่งตรวจสอบกำกับไว้.
เหตุผลเบื้องหลังและผลการตัดสินใจอยู่ใน `docs/UNIFIED_SCORING_PLAN.md`.

## กฎหลัก 6 ข้อ

1. **คะแนนมีแหล่งเดียว.** ทุกหน้าอ่านคะแนนจาก `src/scoring.py`. ห้ามเขียนเกณฑ์ตัวเลข (เช่น `rev_growth >= 15`) ในไฟล์อื่น.
2. **กฎเป็นตาราง.** เพิ่มหรือแก้เกณฑ์ที่ `FUNDAMENTAL_RULES` หรือ `TIMING_RULES`. ห้ามเพิ่ม if/else ทีละเงื่อนไข.
3. **ไม่มีหลักฐาน ไม่มีคะแนน.** อินดิเคเตอร์เทคนิคจะได้คะแนนเมื่อผ่าน `scripts/backtest_scoring.py` แล้วเท่านั้น.
4. **ลบของเก่าในรอบเดียวกัน.** ถ้าย้ายสูตรเข้า `src/scoring.py` ให้ลบสูตรเดิมทันที. ห้ามเก็บสองชุดไว้คู่กัน.
5. **ห้ามให้คะแนนจากข้อมูลสมมติ.** ตัวอย่างคือ `get_super_investors()` ซึ่งเป็นข้อมูลรวบรวมเอง ไม่ใช่ SEC 13F จริง.
6. **พิสูจน์ด้วยของจริง.** เทสต์ผ่านอย่างเดียวยังไม่พอ. ต้องสร้างหน้า HTML ใหม่แล้วเปิดดูด้วย Chrome ทุกครั้ง.

---

## 1. แผนที่ระบบคะแนน

### 1.1 ไฟล์และหน้าที่

| ไฟล์ | หน้าที่ |
| :--- | :--- |
| `src/scoring.py` | ตารางกฎ, ค่าคงที่ และฟังก์ชันให้คะแนนทั้งหมด |
| `src/screener.py` `evaluate_stock()` | อ่านข้อมูล TradingView แล้วคืน `fundamental` และ `stock_score` |
| `src/portfolio.py` | `compute_stock_rating()` (ดาว) และ `compute_financial_health()` (badge พื้นฐาน) |
| `recovery.py` | `evaluate_fundamental_health()` และกฎ DCA ใน `analyze_recovery()` |
| `src/html_report.py` `score_badge_html()` | badge เกรดพร้อม tooltip เหตุผล ใช้ร่วมกันทุกหน้า |
| `src/chart_page.py` `attach_scores()` | ใส่ `score` ให้หุ้นทุกตัวในหน้า Chart |
| `src/templates/chart.js` `updateScoreSidebar()` | การ์ด "คะแนนรวม" ในหน้า Chart |
| `scripts/backtest_scoring.py` | เครื่องมือ walk-forward backtest |
| `tests/test_scoring.py` | เทสต์ของตารางกฎและฟังก์ชันให้คะแนน |

### 1.2 ค่าคงที่ใน `src/scoring.py`

| ชื่อ | ค่า | ความหมาย |
| :--- | :--- | :--- |
| `EARNINGS_GUARD_DAYS` | `14.0` | งบออกภายในกี่วันจึงห้ามถัว |
| `ETF_TICKERS` | VOO, SPY, QQQ, QQQI | ETF ที่ไม่ประเมินพื้นฐาน. SPCX คือหุ้น SpaceX ไม่ใช่ ETF |
| `SECTOR_SKIPPED_METRICS` | Finance ข้าม D/E | หนี้สินเป็นธรรมชาติของธนาคาร |
| `GRADE_BANDS` | A+ ≥ 85, A ≥ 70, B ≥ 55, C ≥ 40, F < 40 | เกรดจากคะแนน 0 ถึง 100 |
| `MIN_COVERAGE_FOR_TOP_GRADE` | `0.7` | ข้อมูลครบไม่ถึง 70% ได้เกรดสูงสุดแค่ B |
| `PILLAR_WEIGHTS` | fundamental 0.6, timing 0.4 | น้ำหนักคะแนนรวม |
| `ETF_STARS` | `4` | ดาวคงที่ของ ETF |

### 1.3 รูปแบบข้อมูล

* `Band(lo, hi, points, label)` หมายถึงช่วง `lo ≤ ค่า < hi`. ใช้ `None` แทนอนันต์. `label` ใส่ `{v}` เพื่อแทรกค่าจริงได้.
* `score_fundamentals(...)` คืน `FundamentalScore` ซึ่งมี `applicable`, `points`, `max_points`, `pct`, `coverage`, `grade`, `metrics` และ `reasons`.
* `score_timing(dist_ema200_pct, rsi, rsi_prev)` คืน `TimingScore`. ค่า `entry_signal` เป็น True เมื่อ RSI ยกหัวและค่าใดค่าหนึ่งต่ำกว่า 40.
* `score_stock(fundamental, timing, days_to_earnings)` คืน `StockScore` ซึ่งมี `total`, `grade`, `stars`, `pillars`, `coverage`, `earnings_guard`, `reasons`, `fundamental` และ `timing`.
* คะแนนคิดเป็นสัดส่วนของส่วนที่มีข้อมูล. ถ้าข้อมูลขาด ห้ามเกลี่ยน้ำหนักไปให้ตัวอื่น. ให้ `coverage` ลดลงแทน.

### 1.4 กฎ DCA ในหน้า Recovery

ลำดับการตัดสินใน `analyze_recovery()` เป็นดังนี้:
1. งบออกภายใน 14 วัน ให้ Freeze DCA.
2. พื้นฐานได้ A+ หรือ A, ราคาไม่ต่ำกว่า EMA200 เกิน 10% และ RSI ≤ 35 หรือมี `entry_signal` ให้ Smart DCA.
3. ต้นทุนต่ำกว่า SMA20 ให้ Rebound Exit.
4. พื้นฐานได้ C หรือ F ให้ Capital Rotation.
5. กรณีอื่นให้ Hold & Guard.

---

## 2. วิธีแก้หรือเพิ่มกฎคะแนน

1. แก้ตารางใน `src/scoring.py` เท่านั้น.
2. ถ้าเป็นกฎเทคนิค ให้รัน backtest ตามหัวข้อ 3 ก่อน. ใส่กฎได้เฉพาะเมื่อผลเป็น `edge+` หรือ `edge-` ใน horizon ที่เกี่ยวข้อง.
3. เขียน comment เหนือตารางว่าตัวเลขมาจากผล backtest ไหน (จำนวนหุ้น, ช่วงปี, ค่า diff และ t).
4. เพิ่มเทสต์ใน `tests/test_scoring.py` ที่ assert ค่าตัวเลขจริง เช่น `self.assertEqual(s["total"], 60.8)`. ห้ามเขียนเทสต์ที่ยังผ่านได้แม้ฟังก์ชันคืน `None`.
5. รันเทสต์.
   ```bash
   /usr/bin/python3 -m unittest discover -s tests
   ```
   ต้องผ่านครบ. เทสต์ `test_every_band_table_covers_real_line_without_overlap` จะ fail ถ้าตารางมีช่องว่างหรือช่วงทับกัน.
6. ทดลองทำให้โค้ดผิดโดยตั้งใจ 1 จุด เช่นเลื่อนขอบ band. เทสต์ต้อง fail. จากนั้นแก้คืน.
7. สร้างหน้า HTML ใหม่และตรวจตามหัวข้อ 5.

---

## 3. วิธีรัน backtest

### 3.1 คำสั่ง

```bash
/usr/bin/python3 scripts/backtest_scoring.py            # ใช้แท่งเทียนจาก cache ถ้ายังไม่เกิน 7 วัน
/usr/bin/python3 scripts/backtest_scoring.py --refresh  # ดึงแท่งเทียนใหม่ทั้งหมด
/usr/bin/python3 scripts/backtest_scoring.py --limit 3  # ทดสอบเร็วกับหุ้น 3 ตัว
```

* ผลลัพธ์เขียนลง `data/backtest_scoring.json`.
* แท่งเทียนเก็บใน `data/.backtest_candles.json` ซึ่งอยู่ใน `.gitignore`.
* รันเต็มใช้เวลาราว 6 ถึง 7 นาที. ให้รันแบบ background แล้วรอให้จบ.

### 3.2 วิธีทำงานของสคริปต์

1. **Universe.** ใช้ `get_universe("all")` (S&P 100 รวม Nasdaq 100) บวกหุ้นใน `data/portfolio.json` แต่ไม่รวม VOO. รอบล่าสุดได้ 173 ตัว.
2. **ข้อมูล.** ดึงแท่งเทียนรายวันย้อนหลัง 6 ปีจาก Yahoo ด้วย `range=6y&interval=1d`.
3. **Walk-forward.** ทุก `STEP = 5` แท่ง ใช้หน้าต่าง `WINDOW = 450` แท่งที่จบ ณ จุดนั้น. คำนวณอินดิเคเตอร์จากข้อมูลถึงจุดนั้นเท่านั้น จึงไม่มี look-ahead. ย้อนหลังสุด `LOOKBACK_BARS = 900` แท่ง.
4. **สถานะ.** `sample_states()` แปลงผลอินดิเคเตอร์จาก `src/chart_data.py` เป็นสถานะแบบ string เช่น `vfi = "DISTRIBUTION"` หรือ `ema200_dist = "0..5%"`.
5. **ผลลัพธ์ที่วัด.** `fwd20` และ `fwd60` คือผลตอบแทน 20 และ 60 วันข้างหน้า. `mdd60` คือ drawdown ลึกสุดใน 60 วันข้างหน้า วัดจากราคา low.
6. **บริบท dip.** จุดที่ราคาห่าง EMA200 ระหว่าง -3% ถึง +8% และ RSI ต่ำสุดใน 5 แท่งน้อยกว่า 40. ในบริบทนี้ วัดตัวกรองมีดตก `dip_knife_vfi`, `dip_knife_chandelier` และ `dip_knife_any` เพิ่มด้วย.

### 3.3 สถิติที่ใช้ตัดสิน

`compare()` เทียบค่าเฉลี่ยของแต่ละสถานะกับค่าเฉลี่ยของสถานะอื่นทั้งหมดใน population เดียวกัน.

* **diff_vs_rest.** ค่าเฉลี่ยของสถานะนี้ ลบค่าเฉลี่ยของที่เหลือ.
* **t ที่ปรับการซ้อนทับ.** จุดที่ห่างกัน 5 แท่งแต่วัดผล 60 วัน มีข้อมูลซ้อนกันอยู่. สคริปต์จึงหารจำนวนตัวอย่างด้วย `horizon / STEP` ก่อนคำนวณ standard error. ห้ามใช้ t แบบไม่ปรับ เพราะจะสูงเกินจริงราว 3.5 เท่า.
* **ความคงที่.** แบ่งข้อมูลตามวันที่เป็นครึ่งแรกและครึ่งหลัง แล้วดู `half_diffs` ทั้งสองครึ่ง. ถ้าทิศทางไม่ตรงกันจะได้ verdict `unstable`.
* **Verdict.** ถ้าคงที่และ t ≥ 2 ได้ `edge+`. ถ้าคงที่และ t ≤ -2 ได้ `edge-`. นอกนั้นได้ `none`.
* ถ้าสถานะไหนมีตัวอย่างน้อยกว่า 20 จะไม่รายงาน.

### 3.4 วิธีอ่านผล

```bash
/usr/bin/python3 -c "
import json;r=json.load(open('data/backtest_scoring.json'))
for m in ['fwd60','fwd20','mdd60']:
  for k,v in r[m].items():
    for s,x in v.get('states',{}).items():
      if abs(x['t'])>=1.2: print(m,k,s,x['n'],x['diff_vs_rest'],x['t'],x['half_diffs'],x['verdict'])"
```

* ดูทั้งผลตอบแทนและ drawdown. ตัวชี้วัดที่ลดความเสี่ยงได้แต่ไม่เพิ่มผลตอบแทน ให้ใช้เป็นคะแนนความเสี่ยง (แบบโซน EMA200).
* ตัวชี้วัดที่ช่วยเฉพาะ 20 วัน ให้ใช้เป็นสัญญาณเข้าซื้อ ไม่ใช่คะแนนสุขภาพ (แบบ RSI hook).
* ถ้าผลสวนกับความเชื่อ ให้เชื่อข้อมูล. ตัวอย่างคือ VFI `DISTRIBUTION` ที่ให้ผลตอบแทน 20 วันดีกว่าสถานะอื่น จึงห้ามใช้บล็อกการถัว.

### 3.5 วิธีเพิ่มอินดิเคเตอร์เข้า backtest

1. เรียกฟังก์ชันจาก `src/chart_data.py` ใน `sample_states()`.
2. แปลงผลเป็น string ที่มีจำนวนสถานะน้อย (ไม่เกินราว 6 ค่า). ถ้าเป็นค่าต่อเนื่อง ให้ใช้ `band()` แบ่งช่วง.
3. รัน `--limit 3` เพื่อตรวจว่าไม่มี error.
4. รันเต็มแบบ background.

### 3.6 ผลล่าสุด (2026-10-19, 173 หุ้น, 30,845 จุด, ปี 2023 ถึง 2026)

| ตัวชี้วัด | ผล | ใช้อย่างไรในระบบ |
| :--- | :--- | :--- |
| EMA200 0..5% และ 5..10% | mdd60 ตื้นกว่า +1.68 (t 4.0) และ +1.58 (t 3.7) | ได้ 6 จาก 6 คะแนน |
| EMA200 < -10% | mdd60 ลึกกว่า -2.72 (t -4.3). fwd60 +3.10 (t 2.2) แต่เสี่ยงสูง | ได้ 0 คะแนน และห้าม Smart DCA |
| EMA200 > 10% | mdd60 ลึกกว่า -1.31 (t -3.3) | ได้ 3 คะแนน |
| RSI hook | fwd20 +0.79 (t 2.1) | เป็น `entry_signal` |
| VFI DISTRIBUTION | fwd20 +0.65 (t 2.1) | ไม่ใช้บล็อก |
| VFI, WAE, Squeeze, UT Bot, Chandelier, WaveTrend, Lorentzian, SMC | ไม่มี edge ที่คงที่ | ไม่นับคะแนน |
| ตัวกรองมีดตกในบริบท dip | ไม่มีนัยสำคัญ | ไม่ใช้บล็อก |

### 3.7 ข้อจำกัดที่ต้องบอกผู้ใช้ทุกครั้ง

* Universe เป็นหุ้นใหญ่ที่ยังอยู่ในดัชนีวันนี้ จึงมี survivorship bias.
* ช่วงเวลาส่วนใหญ่เป็นตลาดขาขึ้น.
* ทดสอบคะแนนพื้นฐานไม่ได้ เพราะ TradingView ให้แต่ค่าปัจจุบัน ไม่มีงบย้อนหลัง.
* ผลนี้ใช้ตัดอินดิเคเตอร์ที่ไม่ช่วยออกได้ แต่ยังไม่พอใช้ปรับน้ำหนักละเอียด.

---

## 4. วิธีวิเคราะห์และแปลข่าวด้วย AI

### 4.1 ขั้นตอน

1. ดึงข่าวที่ยังไม่ได้วิเคราะห์ไปเก็บในไฟล์ชั่วคราว.
   ```bash
   /usr/bin/python3 -m src.ai_news --pending > /tmp/pending_news.json
   ```
2. ก่อนวิเคราะห์ ให้ยืนยันว่าแต่ละ ticker คือบริษัทอะไร. ดูจาก `src/chart_page.py` (ตาราง `name, sector`), `data/trades.json` และวันแรกของแท่งเทียนใน `data/candles_cache.json`. ตัวอย่างคือ SPCX ที่เข้าตลาดวันที่ 2026-06-12 ซึ่งเป็นหุ้น SpaceX ไม่ใช่ SPAC ETF.
3. เขียนไฟล์ผลลัพธ์ที่มีรูปแบบ `{"TICKER": [article, ...]}`. เรียงลำดับเหมือน input. คัดลอก `title`, `source`, `link`, `published` และ `raw_date` มาโดยไม่แก้. เพิ่ม field ต่อไปนี้:
   * `title_th` คือหัวข่าวภาษาไทยที่ใช้ศัพท์การเงินถูกต้อง. ชื่อบริษัทและสินค้าให้คงเป็นภาษาอังกฤษ ห้ามแปล Alphabet เป็น "ตัวอักษร".
   * `summary_th` คือ 2 ถึง 3 บรรทัด. แต่ละบรรทัดขึ้นต้นด้วย `• ` และคั่นด้วย `\n`. เขียนเฉพาะสิ่งที่หัวข่าวรองรับ บวกบริบทธุรกิจที่รู้กันทั่วไป. ห้ามแต่งตัวเลขที่หัวข่าวไม่มี.
   * `impact_th` คือผลกระทบต่อราคาและพื้นฐาน 1 ถึง 2 ประโยค.
   * `action_th` คือคำแนะนำสั้น 1 ประโยค ห้ามรับประกันผล.
   * `sentiment` เป็นได้แค่ `bullish`, `bearish`, `mixed` หรือ `neutral`. ตัดสินจากหัวข่าวเอง ไม่ใช่จาก `current_sentiment`.
   * `topic` คือหัวข้อภาษาไทย ตามด้วยภาษาอังกฤษในวงเล็บ เช่น `ผลประกอบการ (Earnings)`.
4. หน้าราคาหุ้นทั่วไป (เช่น "XYZ Stock Quote Price and Forecast") ไม่นับเป็นข่าว. ให้ใส่ `sentiment = neutral` และ `topic = หน้าข้อมูลราคา (Quote Page)`.
5. ตรวจไฟล์ด้วย Python ก่อนรวม. ticker และจำนวนข่าวต้องตรงกับ input. ทุกข่าวต้องมี field ใหม่ครบ 6 ตัวและไม่ว่าง. sentiment ต้องอยู่ในชุดที่อนุญาต.
6. สุ่มอ่านเองอย่างน้อย 5 ข่าวจากหลาย ticker.
7. สำรอง cache เดิมก่อน แล้วรวมข่าวเข้า cache.
   ```bash
   cp data/ai_news_cache.json /tmp/ai_news_cache.before.json
   /usr/bin/python3 -m src.ai_news --save /tmp/ai_news_analysis.json
   /usr/bin/python3 -m src.ai_news --status
   ```

### 4.2 ตัวอย่าง output ที่ถูกต้อง

```json
{
  "title": "JPMorgan posts rare profit miss as dealmaking, bond trading lose momentum",
  "title_th": "JPMorgan รายงานกำไรต่ำกว่าคาดซึ่งเกิดขึ้นได้ยาก หลังธุรกิจดีลและการเทรดตราสารหนี้ชะลอตัว",
  "summary_th": "• JPMorgan ประกาศกำไรต่ำกว่าที่ตลาดคาด ซึ่งไม่ค่อยเกิดขึ้นกับธนาคารรายนี้\n• สาเหตุหลักมาจากรายได้วาณิชธนกิจและการเทรดตราสารหนี้ที่อ่อนแรงลง",
  "impact_th": "กดดันราคาหุ้นระยะสั้นและอาจทำให้นักวิเคราะห์ปรับลดประมาณการกำไร แต่ฐานธุรกิจหลักยังแข็งแรง",
  "action_th": "ถือต่อและติดตามแนวโน้มรายได้ดีลในไตรมาสถัดไป",
  "sentiment": "bearish",
  "topic": "ผลประกอบการ (Earnings)"
}
```

---

## 5. วิธีสร้างหน้า HTML ใหม่และตรวจผล

1. รันเทสต์ให้ผ่านก่อน.
   ```bash
   /usr/bin/python3 -m unittest discover -s tests
   ```
2. สร้างรายงานทั้ง 6 หน้า. ต้องจบด้วย exit 0 และขึ้นข้อความ "อัปเดตรายงานทั้งหมด 6 รายการเรียบร้อยสมบูรณ์".
   ```bash
   /usr/bin/python3 portfolio.py --all
   ```
3. ถ้าแก้แค่หน้า Chart ให้สร้างเฉพาะหน้านั้น.
   ```bash
   /usr/bin/python3 -c "import sys;sys.path.insert(0,'.');from pathlib import Path;import portfolio as p;p._chart_page(Path('reports'))"
   ```
4. เปิดทุกหน้าด้วย Chrome แบบ headless เพื่อถ่าย screenshot และเก็บ console log.
   ```bash
   C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
   for f in portfolio_master portfolio_review portfolio_recovery portfolio_dip_sim trades_ledger stock_chart; do
     "$C" --headless=new --disable-gpu --enable-logging=stderr --v=0 --virtual-time-budget=8000 \
       --window-size=1440,2400 --screenshot=/tmp/$f.png "file://$PWD/reports/$f.html" 2>/tmp/$f.console.log >/dev/null
     echo "$f js_errors=$(grep -c 'Uncaught' /tmp/$f.console.log)"
   done
   ```
   * `js_errors` ต้องเป็น 0 ทุกหน้า.
   * บรรทัด `CVDisplayLinkCreateWithCGDisplay failed` เป็น noise ของ Chrome บน macOS ไม่ใช่ error ของหน้าเว็บ.
5. เปิดดู screenshot เอง. หน้า Review ต้องมี badge "เกรด X · N/100" ใต้ดาว. หน้า Chart ต้องมีการ์ด "คะแนนรวม (Unified Score)".
6. ตรวจว่าเกรดออกมาครบด้วย grep.
   ```bash
   grep -o "เกรด [A-F+]* · [0-9]*/100" reports/portfolio_review.html | sort | uniq -c
   ```
7. ถ้าหน้า Dip Sim ไม่มี badge ให้ดูก่อนว่า `data/portfolio_dip_sim.json` มีหุ้นถืออยู่หรือไม่. ถ้าไม่มีหุ้น การไม่มี badge ถือว่าถูกต้อง.

---

## 6. จุดที่ผิดพลาดง่าย

* ใช้ `/usr/bin/python3` ห้ามใช้ `uv run` เพราะจะสร้างไฟล์ `uv.lock` ที่ไม่ต้องการ. `python3` ใน PATH อาจไม่มี pytest ให้ใช้ `unittest` แทน.
* ใน `src/portfolio.py` key `pos["score"]` คือแต้มของ screener (`score_points`) ไม่ใช่คะแนนรวม. คะแนนรวมอยู่ที่ `pos["stock_score"]`.
* ถ้าแก้ผลลัพธ์ของฟังก์ชันอินดิเคเตอร์ใน `src/chart_data.py` ให้เพิ่มค่า `INDICATOR_SCHEMA_VERSION` ด้วย. ไม่อย่างนั้น cache จะไม่คำนวณใหม่.
* `src/templates/chart.js` อ่าน `smc.structure` ซึ่งมีค่า `BULLISH`, `BEARISH` หรือ `NEUTRAL`. ห้ามเทียบกับ `market_structure` ซึ่งเป็นข้อความยาว.
* Badge สีในหน้ารายงานเลือกจาก `grade_code` ห้ามเลือกจากการหาคำภาษาไทยในข้อความ.
* ถ้า PEG หรือ FCF มีค่าเท่ากับ 0 พอดี จะตกช่วงที่ได้คะแนนบวก. ข้อมูลจริงแทบไม่เกิด จึงยังไม่ทำกรณีพิเศษ.
* `is_etf()` มี fallback คือ sector เป็น "Miscellaneous" หรือ "Other / Diversified" และไม่มีข้อมูลรายได้. หุ้นใหม่ที่ข้อมูลยังไม่ครบอาจถูกนับเป็น ETF. ให้ตรวจผลกับหุ้นที่เพิ่ง IPO.
* เทสต์ที่รัน CLI หรือฟังก์ชันที่เขียนไฟล์ ต้องตั้ง `FILTER_STOCK_DATA_DIR` ให้ชี้ไปที่โฟลเดอร์ชั่วคราว. `src/trades.py` `data_path()` อ่านค่านี้ทุกครั้งที่เรียก. ถ้าไม่ตั้ง เทสต์จะเขียนทับ `data/ledger.json`, `data/portfolio.json` และ `data/trades.json` ของจริง.
* สคริปต์ที่ไม่มี argparse เช่น `scripts/generate_master_report.py` จะรันจริงเมื่อเรียกด้วย `--help` และเขียนทับ `data/account_summary.json` กับ `reports/`. ห้ามเรียก `--help` กับสคริปต์แบบนี้.
* Python ของ macOS เก็บ bytecode ไว้ที่ `~/Library/Caches/com.apple.python/<path>`. ถ้าแก้ไฟล์ชั่วคราวเพื่อทดสอบว่าเทสต์จับ bug ได้ แล้ว copy ไฟล์เดิมกลับมาภายในวินาทีเดียวกันและขนาดเท่าเดิม Python จะใช้ bytecode ของไฟล์ที่ถูกแก้ต่อ. ให้ลบโฟลเดอร์ cache นั้นหลังทดสอบทุกครั้ง.
* การวัดตำแหน่งบนกราฟด้วย headless Chrome ต้องรออย่างน้อย 500 ms หลัง `selectStock()`. `setVisibleLogicalRange` มีผลในเฟรมถัดไป ถ้าวัดทันทีจะเห็นว่า pane ไม่ตรงกันทั้งที่จริงตรงกัน.
* Confluence Engine ในหน้า Chart (`compute_ai_confluence_signals()`) เป็น heuristic ที่ยังไม่ผ่าน backtest. ห้ามนำสัญญาณ STRONG BUY ของมันไปใช้แทนคะแนนรวม.

---

## 7. รายการตรวจก่อนส่งงาน

- [ ] ไม่มีเกณฑ์ตัวเลขของคะแนนอยู่นอก `src/scoring.py`. ตรวจด้วย `grep -rnE "(rev_g|net_g|roe|peg|debt_to_equity)[a-z_]* *(>=|<=|>|<) *-?[0-9]" src recovery.py`. ผลที่ยอมรับได้มีแค่ 3 ที่ ได้แก่ `max_peg` ใน `src/screener.py` (ตัวกรองที่ผู้ใช้ตั้ง), สีของ ROE ใน `src/html_report.py` และ `_peg_verdict()` ใน `src/portfolio.py` (ข้อความแสดงผล ไม่บวกคะแนน).
- [ ] เทสต์ผ่านครบ. `tests/test_skills.py` ตรวจว่าทุกคำสั่ง `python3 <script> --flag` ใน `.agents/skills/*/SKILL.md` มีอยู่จริง. ถ้าแก้ CLI หรือแก้ skill ต้องให้เทสต์นี้ผ่าน.
- [ ] กฎเทคนิคใหม่มีผล backtest อ้างอิงใน comment.
- [ ] `portfolio.py --all` จบด้วย exit 0.
- [ ] js_errors เป็น 0 ทุกหน้า และเปิดดู screenshot แล้ว.
- [ ] สรุปให้ผู้ใช้ว่าตัวเลขไหนวัดจริง ตัวไหนอนุมาน และข้อจำกัดของ backtest มีอะไร.
