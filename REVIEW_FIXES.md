# รายการที่ควรแก้จาก Code Review (uncommitted changes)

สถานะ test ตอนรีวิว: `python3 -m unittest discover -s tests` ผ่าน 50/50
ไฟล์ที่รีวิว: `src/chart_data.py`, `src/chart_page.py`, `src/news.py`, `tests/test_screener_chart.py`, `.github/workflows/update_portfolio.yml`

---

## 🔴 P1 บั๊กที่ควรแก้ก่อน commit

### 1. Weekly chart เรียงเวลาผิดใน timezone ติดลบ
- ไฟล์: `src/chart_page.py:2431` (`getWeekIdentifier`)
- ปัญหา: อ่านด้วย `getUTCDate()/getUTCDay()` แต่ตั้งค่าด้วย `d.setDate(diff)` ซึ่งเป็น local time
- ผลกระทบ: ผู้ใช้ฝั่งอเมริกากดปุ่ม W แล้วได้ bucket ที่เวลาไม่เรียงลำดับ ตัว lightweight-charts v4 throw ตอน `candleSeries.setData` ทำให้กราฟพัง
- หลักฐาน: รันด้วย `TZ=America/New_York` เจอ 22 จุดไม่เรียงลำดับต่อ ticker (JPM ได้ 800 bucket เทียบกับ 762 ที่ Asia/Bangkok)
- วิธีแก้: เปลี่ยน `d.setDate(diff)` เป็น `d.setUTCDate(diff)`
- Test: ใช้ node รัน `aggregateCandles('W')` ด้วย `TZ=America/New_York` แล้ว assert ว่าเวลาเรียงจากน้อยไปมาก

### 2. ค่า RSI ตอน hover ไม่อัปเดต
- ไฟล์: `src/chart_page.py:4021`
- ปัญหา: เรียก `param.seriesData.get(activeRsiSeries)` ใน `subscribeCrosshairMove` ของกราฟหลัก แต่ RSI series อยู่อีกกราฟหนึ่ง จึงไม่มีอยู่ใน `seriesData` นี้
- ผลกระทบ: ค่า RSI ค้างอยู่ที่ค่าล่าสุดตลอด
- วิธีแก้: สร้าง map จาก time ไปเป็นค่า RSI ตอน `setData` แล้วหาค่าจาก `param.time` แทน

### 3. RSI pane เลื่อนจากแท่งเทียน 14 แท่ง
- ไฟล์: `src/chart_page.py:4003-4013` และ `calcRSI` ที่บรรทัด 3989
- ปัญหา: sync สองกราฟด้วย logical range แต่ RSI ไม่มีข้อมูล 14 แท่งแรก index 0 ของ RSI จึงตรงกับแท่งที่ 14
- วิธีแก้: เติม whitespace point `{ time }` ให้ 14 แท่งแรก หรือเปลี่ยนไป sync ด้วย time range

### 4. XSS จากข้อมูลข่าว
- ไฟล์: `src/chart_page.py:3425` (`displayTitle` ลง innerHTML), `:3431` (`enLink` ลง `href`), `:2349` (`summary_th/summary`), `:3358` (whale `name/summary`)
- ปัญหา: ข้อความจาก RSS ถูกใส่ลง HTML โดยไม่ escape ทั้งใน `src/news.py` และ `src/chart_data.py`
- ผลกระทบ: หัวข่าวที่มี `<img onerror=...>` หรือลิงก์ `javascript:` จะรันในหน้าเพจได้
- วิธีแก้:
  - เพิ่ม helper `escapeHtml()` ฝั่ง JS แล้วครอบทุกค่าที่ใส่ลง template string
  - ตรวจ `enLink` ว่าขึ้นต้นด้วย `http://` หรือ `https://` เท่านั้น ไม่งั้นใช้ `#`
  - หรือใช้ `textContent` เหมือนที่ news modal ทำอยู่แล้ว

### 5. Elliott Wave ขาลงกลับไปเพิ่มคะแนน BUY
- ไฟล์: `src/chart_data.py:1303`
- ปัญหา: ทุก wave ที่ `detected=True` ได้ `curr_score += 1` รวมถึง `Corrective Wave (A-B-C)` (กำลังลง) และ `Bullish Impulse Completed` (จบรอบขาขึ้น)
- ผลกระทบ: หุ้นที่กำลังปรับฐานได้คะแนนสูงขึ้นจนใกล้เกณฑ์ STRONG BUY (≥4 ที่ `:1837`)
- วิธีแก้: ให้ +1 เฉพาะ `type` ที่ขึ้นต้นด้วย `Bullish Impulse (` หรือ `Emerging Bullish Impulse` ส่วน Corrective ให้ใส่แค่ reason เตือน ไม่บวกคะแนน และส่วน Completed ไม่บวกคะแนน
- Test: ส่ง `elliott_wave={"detected": True, "type": "Corrective Wave (A-B-C)", ...}` เข้า `compute_ai_confluence_signals` แล้ว assert ว่าคะแนนไม่เพิ่ม

### 6. Pivot S1 ให้ +1 แม้ราคาหลุดแนวรับแล้ว
- ไฟล์: `src/chart_data.py:1313`
- ปัญหา: `abs(curr_close - p_s1) / p_s1 <= 0.035` นับทั้งกรณีอยู่เหนือและอยู่ใต้ S1
- วิธีแก้: เปลี่ยนเป็น `p_s1 <= curr_close <= p_s1 * 1.035`
- Test: ราคาต่ำกว่า S1 อยู่ 2% ต้องไม่ได้คะแนน Pivot

---

## 🟠 P2 ปัญหาความแม่นของ logic

### 7. หมวดข่าวจับ keyword แบบ substring
- ไฟล์: `src/news.py` (`synthesize_news_summary`)
- ปัญหา: `"ai"` ไปเจอใน "said" และ "retail", `"sec"` ไปเจอใน "sector", `"fund"` ไปเจอใน "fundamental"
- หลักฐาน: "Analysts said retail demand steady" ถูกจัดเป็นหมวด AI
- วิธีแก้: ทำ keyword ของแต่ละหมวดเป็น regex `\b...\b` แบบเดียวกับ `_BEAR_REGEX/_BULL_REGEX` แล้วเก็บเป็นตาราง `(regex, topic, context)` เพื่อตัดสาย if/elif
- Test: "Analysts said retail demand steady" ต้องได้หมวด default

### 8. keyword `"lower"` ทำให้ข่าวถูกจัดเป็น bearish ผิด
- ไฟล์: `src/news.py:44` (`BEARISH_KEYWORDS`)
- หลักฐาน: "Apple to lower iPhone prices in China" ได้ bearish ส่วน "Fed expected to lower rates, stocks rally" ได้ mixed
- วิธีแก้: ลบ `"lower"` แล้วใช้ phrase ที่เจาะจงกว่า เช่น `"shares lower"`, `"trades lower"`, `"moves lower"`, `"closes lower"`
- Test: ใส่สองหัวข้อข้างบนเป็น regression test

### 9. สรุปข่าวภาษาไทยเป็น template
- ไฟล์: `src/news.py` (`synthesize_news_summary`)
- ปัญหา: summary, impact และ action เป็นข้อความสำเร็จรูปตาม sentiment ไม่ได้มาจากเนื้อข่าว
- วิธีแก้ (เลือกอย่างใดอย่างหนึ่ง):
  - ติด label ใน UI ว่า "แนวทางทั่วไปตาม sentiment ไม่ใช่สรุปเนื้อข่าว"
  - หรือเปลี่ยนไปสรุปจากเนื้อข่าวจริง

### 10. ข้อมูล Super Investors เขียนตายตัว
- ไฟล์: `src/chart_data.py` (`SUPER_INVESTORS_DATA`)
- ปัญหา: ไม่มีวันที่และแหล่งที่มา บางรายการน่าจะเก่าแล้ว เช่น Druckenmiller กับ NVDA (ข้อนี้มาจากความจำ ยังไม่ได้เช็คกับ 13F)
- วิธีแก้: เพิ่ม field `as_of` (ไตรมาส 13F) และ `source` แล้วแสดงใน UI หรือดึงจาก 13F จริง

### 11. "🗓️ งบ" ไม่ได้ใช้วันประกาศงบจริง
- ไฟล์: `src/chart_data.py` (`detect_earnings_history`)
- ปัญหา: เลือกแท่งที่ volume สูงสุดในแต่ละช่วง 62 แท่ง ช่วงนับจากต้น array ไม่ได้ตรงกับไตรมาส และช่วงสุดท้ายอาจมีแค่ไม่กี่แท่ง
- วิธีแก้: ใช้วันประกาศงบจริงจาก TradingView หรือ data source ที่ใช้อยู่ ถ้ายังทำไม่ได้ ให้ข้ามช่วงที่สั้นกว่า 20 แท่ง และเปลี่ยน label เป็น "Volume Spike"

---

## 🟡 P3 เรื่องเล็ก

### 12. ข่าวที่แปลเพิ่มใน cache ไม่ถูก save กลับ
- ไฟล์: `src/news.py:272`
- ผลกระทบ: เรียก Google Translate ซ้ำทุกรอบจนกว่า cache จะหมดอายุ
- วิธีแก้: หลัง backfill ให้เรียก `_update_cache(clean_ticker, cached, max_items)`

### 13. การแปลทำทีละข่าวเรียงกัน
- ไฟล์: `src/news.py` (`translate_text_to_thai`)
- ผลกระทบ: ถ้า endpoint `gtx` (ไม่ใช่ API ทางการ) โดนบล็อกใน CI แต่ละ ticker อาจช้าขึ้นราว 14 วินาที (คำนวณจาก timeout 3.5 วินาที × 4 ข่าว ยังไม่ได้วัดจริง)
- วิธีแก้: รวมหัวข่าวด้วย `\n` แล้วแปลครั้งเดียว หรือถ้าครั้งแรกล้มเหลวให้หยุดแปลข่าวที่เหลือ

### 14. Widget ใช้แท่งเทียนของ ticker ก่อนหน้า
- ไฟล์: `src/chart_page.py:4440` เทียบกับ `:4454`
- ปัญหา: `updateSmartDca` และ `updateAiNarrative` ถูกเรียกก่อน `renderLightweightChart` ซึ่งเป็นตัวตั้ง `currentCandles` fallback ที่ `:4100`, `:4152` และ `:4176` จึงอ่านค่าของ ticker เก่า
- ผลกระทบ: ตอนนี้ยังไม่พังเพราะทุก ticker มี `meta.price`
- วิธีแก้: ตั้ง `currentCandles` ก่อนเรียก widget

### 15. เส้น Elliott Wave ในโหมด W/M ไม่ snap กับแท่ง
- ไฟล์: `src/chart_page.py:2753`
- ปัญหา: `s.setData(ew.lines)` ใช้เวลารายวัน จึงเพิ่มจุดเวลาเกินเข้าไปใน time scale (น่าจะเป็นจริง ยังไม่ได้ยืนยัน)
- วิธีแก้: snap เวลาแบบเดียวกับ `interpolatePatternPoints`

### 16. ค่า `reaction_pct` อาจไม่มี
- ไฟล์: `src/chart_page.py` (`updateChartMarkers`)
- ปัญหา: `e.reaction_pct.toFixed(1)` throw ได้ถ้า entry ไม่มีทั้ง `text` และ `reaction_pct` (ความมั่นใจต่ำ)
- วิธีแก้: ใช้ `(e.reaction_pct ?? 0).toFixed(1)` หรือข้าม entry นั้น

### 17. Comment ใน workflow ผิดช่วงฤดูหนาว
- ไฟล์: `.github/workflows/update_portfolio.yml:5`
- ปัญหา: comment บอกว่า 13:39 UTC คือ "หลังเปิดตลาด" แต่ตั้งแต่พฤศจิกายนถึงมีนาคม ตลาดเปิด 14:30 UTC
- วิธีแก้: แก้ comment หรือเลื่อน cron เป็น 14:39 UTC

---

## ลำดับที่แนะนำ
1. P1 ข้อ 1 ถึง 6 (แก้เล็ก ผลกระทบสูง)
2. P2 ข้อ 7 และ 8 (มี regression test ให้เลย)
3. P3 ข้อ 12 และ 14
4. ข้อที่เหลือเป็นเรื่องออกแบบ ต้องตัดสินใจเรื่อง data source ก่อน (ข้อ 9, 10, 11)
