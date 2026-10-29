# รายการงานค้างและแผนการปรับปรุงระบบ (Pending Work & Roadmap)

* วันที่บันทึกข้อมูล 2026-10-29.
* อ้างอิง Git Commit ฐาน 4c4162d.
* สถานะการทำงาน สรุปหลังเสร็จสิ้นงานปรับปรุงของ W1 ถึง W6 (วัดจริง).

---

## สรุปภาพรวม 5 บรรทัด
1. โปรเจกต์ผ่านการปรับปรุงระบบครั้งใหญ่ มีไฟล์ที่แก้ไขค้างใน Working Directory รวม 31 ไฟล์ และไฟล์ใหม่ 12 ไฟล์ (วัดจริง).
2. ชุดทดสอบทั้งระบบ 320 รายการผ่านครบ 100% โดยใช้เวลา 24.1 วินาที (วัดจริง) และข้อมูลบัญชีจริงในไดเรกทอรี data ไม่ถูกแตะต้อง.
3. งานที่เสร็จแล้วเมื่อ 2026-10-29 ได้แก่ การลบอินดิเคเตอร์ 6 ตัวที่ไม่ผ่าน backtest, การล็อกยอดหุ้น LLY, การเพิ่มป้าย FX ทั่วไป, การเปลี่ยนชื่อไฟล์เทสต์ 4 ไฟล์ และการเติมปฏิทินวันงบ 3 ปี.
4. เรื่องเงินสด 0.01 บาท และ Dime! USD 295.59 ดอลลาร์ ได้รับการตรวจสอบสลิปและแอปจริงแล้ว ขณะนี้กำลังเขียน ledger โดย W3 ตามที่ผู้ใช้อนุมัติ.
5. งานค้างที่เหลืออยู่คือการแก้ Hardcoded Path ไดเรกทอรี data, การแยกไฟล์กราฟ chart_data.js เป็นราย Ticker, การสร้างรายงาน HTML ใหม่ และการขออนุมัติ commit โค้ด.

---

## ตารางสรุปรายการงานค้างทั้งหมด

| # | รายการงาน | ความสำคัญ | ไฟล์และตำแหน่งบรรทัด | ประเมินขนาดงาน | ต้องให้ผู้ใช้ตัดสินใจ |
| :-: | :--- | :-: | :--- | :-: | :-: |
| 1 | ขอคำสั่งจากผู้ใช้เพื่อ Commit ไฟล์ที่แก้ไข 31 ไฟล์และไฟล์ใหม่ 12 ไฟล์ | สูง | 31 ไฟล์ที่แก้ไข และ 12 ไฟล์ใหม่ใน git status | เล็ก (ขนาด S ใช้เวลาราว 15 นาที) | ใช่ |
| 2 | รันสร้างรายงาน HTML ทั้ง 6 หน้าใหม่ให้เป็นปัจจุบัน | สูง | [reports/](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports), [portfolio.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/portfolio.py) | เล็ก (ขนาด S ใช้เวลาราว 10 นาที) | ไม่ต้อง |
| 3 | แก้ไข Hardcoded Path ของไดเรกทอรี data ให้รองรับ FILTER_STOCK_DATA_DIR | สูง | 9 ไฟล์ใน src/, scripts/ และ portfolio.py | กลาง (ขนาด M ใช้เวลาราว 2 ชั่วโมง) | ไม่ต้อง |
| 4 | แยกไฟล์ชุดข้อมูลกราฟ chart_data.js เป็นราย Ticker ลดขนาดจาก 2.71 MB เพื่อเปิดแบบ Local file:// | กลาง | [src/chart_page.py:366](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_page.py#L366), [src/templates/chart.js:1](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.js#L1) | กลาง (ขนาด M ใช้เวลาราว 3 ชั่วโมง) | ไม่ต้อง |
| 5 | ปรับปรุงรายการเดินบัญชีเงินสด data/ledger.json (กำลังเขียน) | สูง | [data/ledger.json:4](file:///Users/thanessriamornruttanakul/Documents/filter-stock/data/ledger.json#L4), [data/screenshots/IMG_5871.png](file:///Users/thanessriamornruttanakul/Documents/filter-stock/data/screenshots/IMG_5871.png) | เล็ก (ขนาด S ใช้เวลาราว 15 นาที) | ใช่ |
| 6 | แยก Template ของรายงานอีก 5 หน้าออกจากโค้ด Python (สถาปัตยกรรม S2) | กลาง | [src/html_report.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/html_report.py), [scripts/generate_master_report.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_master_report.py) | ใหญ่ (ขนาด L ใช้เวลาราว 2 ถึง 3 วัน) | ไม่ต้อง |
| 7 | สร้าง Dataclass โมเดลข้อมูลธุรกรรม และแยก Source ออกจาก Output (S1, S3, S5) | ต่ำ | [src/trades.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/trades.py), [src/portfolio.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/portfolio.py), [.github/workflows/](file:///Users/thanessriamornruttanakul/Documents/filter-stock/.github/workflows) | ใหญ่ (ขนาด L ใช้เวลาราว 3 ถึง 5 วัน) | ไม่ต้อง |

---

## รายละเอียดงานค้างรายข้อ

### ข้อ 1 การขอคำสั่งจากผู้ใช้เพื่อ Commit ไฟล์ทั้งหมดเข้าสู่ Git Repository
* ปัญหาที่พบคือ ปัจจุบันมีการแก้ไขค้างอยู่ใน Working Directory รวม 31 ไฟล์ และมีไฟล์ใหม่ 12 ไฟล์ (วัดจริง). ตามกฎเหล็ก ห้าม AI ทำการ commit โดยไม่ได้รับคำสั่งจากผู้ใช้โดยเด็ดขาด.
* หลักฐานยืนยันมีดังนี้:
  * การรัน git status short รายงาน 31 ไฟล์ที่มีสถานะ Modified และ 12 ไฟล์ Untracked (วัดจริง).
  * ไฟล์เทสต์เดิมทั้งหมดได้รับการเปลี่ยนชื่อให้สื่อความหมายตามพฤติกรรมเรียบร้อยแล้ว.
* วิธีแก้ที่เสนอคือ รอรับคำสั่งอนุมัติจากผู้ใช้เพื่อดำเนินการ git add และ git commit รวบยอด.
* ไฟล์ที่ต้องแตะ ได้แก่ ไฟล์ทั้งหมดใน Working Directory.
* วิธีพิสูจน์ว่าเสร็จคือ git status สะอาดและโค้ดทั้งหมดถูกบันทึกใน Git.

---

### ข้อ 2 การสร้างรายงาน HTML ทั้ง 6 หน้าใหม่ (Regenerate Reports)
* ปัญหาที่พบคือ ไฟล์ HTML รายงานในไดเรกทอรี reports/ ยังคงเป็นผลลัพธ์จากการรันในอดีต (ตั้งแต่คอมมิต 4c4162d เมื่อวันที่ 2026-10-28 21:56 น.). โค้ดคำนวณคะแนนใหม่ ตรรกะเรขาคณิตแพทเทิร์นใหม่ การตัด 6 อินดิเคเตอร์ออก และป้าย FX ใหม่ยังไม่ถูกนำไปเรนเดอร์ลงในหน้าเว็บจริง.
* หลักฐานยืนยันมีดังนี้:
  * เวลาแก้ไขของ reports/stock_chart.html คือ 2026-10-28 21:56 น. ก่อนเริ่มการแก้ไขรอบที่ 1 ถึง 6 (วัดจริง).
  * กฎร่วมข้อ 3 และ 4 ใน COMMON.md สั่งห้ามไม่ให้ Worker รันสคริปต์เขียนทับ reports/ ระหว่างที่งานยังไม่รวม.
* วิธีแก้ที่เสนอมีดังนี้:
  * หลังทำการ commit การแก้ไขโค้ดทั้งหมดแล้ว ให้ผู้ใช้สั่งรัน /usr/bin/python3 portfolio.py --all หรือผลักดันโค้ดขึ้น GitHub เพื่อให้ GitHub Actions รันสร้างรายงานใหม่อัตโนมัติ.
  * ตรวจสอบว่ารายงานทั้ง 6 หน้าจบด้วย Exit Code 0 และเปิดดูด้วย Headless Chrome ไม่พบข้อผิดพลาด Uncaught Exception.
* ไฟล์ที่ต้องแตะ ได้แก่ ไดเรกทอรี [reports/](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports).
* วิธีพิสูจน์ว่าเสร็จคือ portfolio.py --all ขึ้นข้อความอัปเดตรายงานครบ 6 รายการสมบูรณ์ และไฟล์ใน reports/ มี Timestamp ใหม่ล่าสุด.

---

### ข้อ 3 การแก้ไข Hardcoded Path ของไดเรกทอรี data ให้รองรับ FILTER_STOCK_DATA_DIR
* ปัญหาที่พบคือ มีไฟล์โค้ดภาษา Python 9 จุดที่กำหนด path ไปยังโฟลเดอร์ data/ โดยตรงแบบ Hardcode โดยไม่ได้อ่านค่าจากตัวแปรสภาพแวดล้อม FILTER_STOCK_DATA_DIR. ส่งผลให้เมื่อรันสคริปต์หรือเทสต์ที่ไม่ระบุ path จะไปอ่านหรือเขียนทับไฟล์ข้อมูลจริงในไดเรกทอรี data/.
* หลักฐานตำแหน่งบรรทัดในโค้ดจริงที่ตรวจสอบใหม่มีดังนี้:
  1. [src/news.py:24](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/news.py#L24) กำหนด CACHE_FILE ไปยัง data/.news_cache.json ตรงๆ.
  2. [src/ai_news.py:15-17](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/ai_news.py#L15-L17) กำหนด DATA_DIR ไปยัง data/ ตรงๆ.
  3. [src/chart_data.py:40](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_data.py#L40) กำหนด CACHE_PATH ไปยัง data/candles_cache.json ตรงๆ.
  4. [src/chart_page.py:82, 113, 145, 177](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_page.py#L82) เรียกใช้ Path("data/portfolio.json") และไฟล์อื่นโดยตรง.
  5. [portfolio.py:31-33, 50](file:///Users/thanessriamornruttanakul/Documents/filter-stock/portfolio.py#L31) เรียกใช้ Path("data/portfolio.json") และเขียนไฟล์ account_summary.json ลง data/ ตรงๆ.
  6. [scripts/generate_master_report.py:81, 194, 2697](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_master_report.py#L81) เรียกใช้ Path("data/.ocr_extracted.json"), Path("data/.statement_text.txt") และ Path("data/account_summary.json").
  7. [scripts/generate_dip_sim_report.py:49](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_dip_sim_report.py#L49) กำหนด DATA_PATH ระดับโมดูลไปยัง data/portfolio_dip_sim.json.
  8. [scripts/backtest_scoring.py:32, 33, 195](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/backtest_scoring.py#L32) กำหนด CANDLES_PATH, RESULT_PATH และอ่าน portfolio.json จาก data/ ตรงๆ.
  9. [src/trades.py:152](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/trades.py#L152) กำหนดโฟลเดอร์รูปภาพ data/screenshots และ data/set-screenshot ตรงๆ.
* วิธีแก้ที่เสนอมีดังนี้:
  * ใช้ฟังก์ชันกลาง data_path(filename) จาก [src/trades.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/trades.py) หรือสร้างฟังก์ชัน get_data_dir() ที่ตรวจสอบ os.environ.get("FILTER_STOCK_DATA_DIR") เสมอในทุกโมดูล.
  * กำหนดค่าคงที่ระดับโมดูลให้เรียกใช้ผ่านฟังก์ชัน เพื่อให้สอดรับกับการตั้งค่าตัวแปรสภาพแวดล้อมในขณะรันการทดสอบ.
* ไฟล์ที่ต้องแตะ ได้แก่ src/news.py, src/ai_news.py, src/chart_data.py, src/chart_page.py, portfolio.py, scripts/generate_master_report.py, scripts/generate_dip_sim_report.py, scripts/backtest_scoring.py, src/trades.py.
* วิธีพิสูจน์ว่าเสร็จคือ ตั้งค่า FILTER_STOCK_DATA_DIR ไปยังไดเรกทอรีชั่วคราว แล้วสั่งรันสคริปต์ทั้งหมด. ตรวจสอบว่าไม่มีไฟล์ใดถูกสร้างหรือแก้ไขในไดเรกทอรี data/ จริง.

---

### ข้อ 4 การแยกไฟล์ชุดข้อมูลกราฟ chart_data.js เป็นราย Ticker
* ปัญหาที่พบคือ ไฟล์ reports/chart_data.js ใน Git repository มีขนาด 3,473,918 ไบต์ (3.47 MB วัดจริง). เมื่อทดลอง build ในไดเรกทอรีสำเนาหลัง W5 ลบ 6 อินดิเคเตอร์ออก ขนาดลดลงเหลือ 2,713,453 ไบต์ (2.71 MB วัดจาก build ในสำเนา). ปัจจุบันยังรวมข้อมูลหุ้นทุกตัวไว้ในไฟล์เดียว ทำให้เบราว์เซอร์ต้องประมวลผลข้อมูลทั้งหมดตั้งแต่เริ่มเปิดหน้าเว็บ.
* ข้อจำกัดทางเทคนิคสำคัญคือ การแยกไฟล์เป็น JSON แล้วโหลดด้วย fetch('./charts/' + ticker + '.json') ไม่สามารถใช้งานได้เมื่อเปิดไฟล์ผ่านโปรโตคอล file:// บนเครื่อง Local เพราะ Chrome จะบล็อกคำสั่ง fetch ด้วยนโยบาย CORS.
* หลักฐานยืนยันมีดังนี้:
  * ขนาดไฟล์ reports/chart_data.js ใน repository เท่ากับ 3,473,918 ไบต์ (วัดจริง).
  * ขนาดไฟล์ที่สร้างขึ้นใหม่ในไดเรกทอรีสำเนาหลังตัด 6 อินดิเคเตอร์เท่ากับ 2,713,453 ไบต์ (วัดจาก build ในสำเนา).
  * ใน [src/chart_page.py:366-377](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_page.py#L366-L377) มีการรวมข้อมูลหุ้นทั้งหมดเป็น JSON ก้อนเดียวใน window.CHARTS_DATA.
* วิธีแก้ที่เสนอมีดังนี้:
  1. แยกข้อมูลออกเป็น 2 ส่วน:
     * ส่วนที่ 1 เป็น reports/charts_meta.js (ขนาดประมาณ 60 ถึง 90 KB ค่าประเมิน) บรรจุ window.STOCKS_META โหลดผ่านแท็ก script src="charts_meta.js" ตั้งแต่เริ่มต้นเพื่อเรนเดอร์ Sidebar และแถบ HUD ทันที.
     * ส่วนที่ 2 เป็น ไดเรกทอรี reports/chart_data/<TICKER>.js (ขนาดเฉลี่ยประมาณ 100 KB ต่อหุ้น ค่าประเมิน) แต่ละไฟล์จะเรียกฟังก์ชัน window.registerChart('<TICKER>', { ... }) เพื่อลงทะเบียนข้อมูลเข้า window.CHARTS_DATA['<TICKER>'].
  2. ปรับปรุงตัวโหลดข้อมูลใน [src/templates/chart.js](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.js):
     * เมื่อผู้ใช้คลิกเลือกหุ้นที่ยังไม่มีข้อมูลในแคช ให้แทรกแท็กสคริปต์แบบพลวัต document.createElement('script') ชี้ไปยัง chart_data/<TICKER>.js.
     * การโหลดผ่านแท็ก script ทำงานได้ราบรื่น 100% ทั้งบน Local file:// และบน Web Server โดยไม่ถูกบล็อก CORS.
     * เมื่อสคริปต์โหลดเสร็จและเรียก window.registerChart ระบบจะสั่งเรนเดอร์กราฟทันที พร้อมซ่อนสถานะ Loading.
* ผลลัพธ์ที่คาดหวังคือ ปริมาณข้อมูลที่ต้องโหลดตอนเปิดหน้าเว็บครั้งแรกจะลดลงเหลือประมาณ 200 KB (ลดลงราว 92% ค่าอนุมาน) และเปิดดูไฟล์แบบ Local file:// ได้อย่างสมบูรณ์.
* ไฟล์ที่ต้องแตะ ได้แก่ [src/chart_page.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_page.py), [src/templates/chart.js](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.js), [src/templates/chart.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.html).
* วิธีพิสูจน์ว่าเสร็จคือ หน้าเว็บเปิดผ่านโปรโตคอล file:// ในเบราว์เซอร์ Chrome ได้อย่างถูกต้องโดยไม่มีข้อผิดพลาด CORS ในคอนโซล.

---

### ข้อ 5 ปรับปรุงรายการเดินบัญชีเงินสด data/ledger.json (กำลังเขียน)
* ปัญหาที่พบคือ รายการเดินบัญชีใน data/ledger.json บรรทัด 4 มีตัวเลขเงินสดไม่ตรงกับแอป Dime! ได้แก่ เศษเงินสด 0.01 บาท และยอดเงินคงค้างในกระเป๋า Dime! USD.
* หลักฐานและการตรวจสอบโดย W3 (วัดจริง) มีดังนี้:
  1. เงิน 9,999.81 บาท เมื่อวันที่ 23 ต.ค. 69 ไม่ได้ซื้อหุ้น เพราะคำสั่งซื้อ NOK หมดอายุ ทำให้เงินบาทถูกแลกเป็น USD ค้างอยู่ใน Dime! USD จำนวน 295.59 USD ที่อัตราแลกเปลี่ยน 33.83 THB/USD (วัดจริงจากภาพ IMG_5871.png และ IMG_5872.png).
  2. รายการเวลา 21:49 น. วันที่ 22 ต.ค. 69 ใน ledger ระบุชำระค่าซื้อหุ้น VRT แท้จริงคือคำสั่ง NOK ยอด 19,999.80 บาทที่ถูกยกเลิก แล้วนำเงิน USD ไปซื้อ VRT 591.36 USD ในเวลา 22:10 น. ที่อัตราแลกเปลี่ยน 33.82 THB/USD.
  3. ยอดเงินสดในแอป Dime! Save ณ วันที่ 29 ต.ค. 69 แสดง 0.59 บาท ตรงกับการคำนวณฐานเดิม 0.40 บาท (0.40 + 10,000.00 - 9,999.81 = 0.59 บาท) พิสูจน์ว่าฐานเดิมคือ 0.40 บาท ไม่ใช่ 0.41 บาท หรือ 0.42 บาท.
  4. ดอกเบี้ยสะสม 14.98 บาทในแอปเป็นดอกเบี้ยค้างรับ ยังไม่ถึงรอบจ่ายจริง ณ สิ้นเดือน ธ.ค. 2569 จึงยังไม่นับเป็นเงินสด.
* สถานะปัจจุบัน กำลังเขียน ledger โดย W3 ตามที่ผู้ใช้อนุมัติเมื่อ 2026-10-29.
* ไฟล์ที่ต้องแตะ ได้แก่ [data/ledger.json](file:///Users/thanessriamornruttanakul/Documents/filter-stock/data/ledger.json).
* วิธีพิสูจน์ว่าเสร็จคือ ยอดเงินสด dime_save_thb เท่ากับ 0.59 บาท และ dime_usd เท่ากับ 295.59 ดอลลาร์ ตรงกับหน้าแอป 100%.

---

### ข้อ 6 การแยก Template ของรายงานอีก 5 หน้าออกจากโค้ด Python (สถาปัตยกรรม S2)
* ปัญหาที่พบคือ เทมเพลตของหน้ารายงานกราฟแยกออกเป็น chart.html, chart.css, chart.js เรียบร้อยแล้ว แต่รายงานอีก 5 หน้ายังคงเป็นโค้ด HTML และ CSS ฝังอยู่ในสตริง f-string ภายในไฟล์ Python:
  * [src/html_report.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/html_report.py) มีฟังก์ชันสร้างหน้า Portfolio Review และ Recovery รวมกว่า 2,000 บรรทัด.
  * [scripts/generate_master_report.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_master_report.py) มีฟังก์ชันสร้าง Master Dashboard และ Trades Ledger รวมกว่า 2,700 บรรทัด.
  * [scripts/generate_dip_sim_report.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_dip_sim_report.py) มีโค้ด HTML ของหน้า Dip Simulation รวมกว่า 500 บรรทัด.
* วิธีแก้ที่เสนอมีดังนี้:
  * สร้างไดเรกทอรี src/templates/ สำหรับรายงานแต่ละหน้า ได้แก่ master.html, review.html, recovery.html, dip.html, ledger.html.
  * สร้างไฟล์ src/templates/common.css รวบรวม Design Tokens, สไตล์การ์ด, ป้าย Badge และชุดสี เพื่อใช้ร่วมกันทุกหน้า.
* ไฟล์ที่ต้องแตะ ได้แก่ src/html_report.py, scripts/generate_master_report.py, scripts/generate_dip_sim_report.py, src/templates/.
* วิธีพิสูจน์ว่าเสร็จคือ ไฟล์ผลลัพธ์ HTML ทั้ง 6 หน้ามีหน้าตาและการทำงานเหมือนเดิมทุกประการ พิสูจน์ด้วย Headless Chrome.

---

### ข้อ 7 การสร้างโมเดลข้อมูลที่มี Type ชัดเจนและการแยก Source ออกจาก Output (S1, S3, S5)
* ปัญหาที่พบมีดังนี้:
  1. สถาปัตยกรรมข้อมูล (S3). ปัจจุบันข้อมูลพอร์ต รายการเทรด และรายการเดินบัญชี ยังคงถูกส่งผ่านในรูปแบบ Dictionary ไร้โครงสร้าง ทำให้ไม่มีการตรวจสอบความถูกต้องอัตโนมัติ.
  2. การปะปนระหว่าง Source Code และ Output (S1). ไดเรกทอรี reports/ และไฟล์ data/account_summary.json ซึ่งเป็นผลลัพธ์ ยังคงถูก Track และ Commit ลงใน Git Repository ทำให้ประวัติของ Git มีขนาดใหญ่ขึ้นเรื่อยๆ.
  3. ขาดระบบ Page Registry กลาง (S5). การระบุรายชื่อหน้ารายงานทั้ง 6 หน้ายังคงเขียนกระจายซ้ำซ้อนอยู่ในหลายไฟล์ เช่น portfolio.py, src/nav.py, README.md และเอกสารสคิลล์.
* วิธีแก้ที่เสนอมีดังนี้:
  * สร้าง Dataclass ที่มี Type Annotations สำหรับ Holding, Trade, LedgerMovement และ PortfolioSummary.
  * ปรับปรุง CI Workflow ให้ Deploy หน้าเว็บผ่าน GitHub Pages Artifact แทนการ Commit ไฟล์ HTML ผลลัพธ์กลับเข้าสู่กิ่งหลัก.
  * รวมศูนย์รายชื่อและตัวจัดการรายงานไว้ใน [src/nav.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/nav.py) ให้เป็น Single Source of Truth เดียวของระบบเพจทั้งหมด.
* ไฟล์ที่ต้องแตะ ได้แก่ src/portfolio.py, src/trades.py, src/nav.py, .github/workflows/update_portfolio.yml.
* วิธีพิสูจน์ว่าเสร็จคือ รันการตรวจสอบประเภทข้อมูลด้วย mypy หรือชุดเทสต์ทดสอบ Dataclass.

---

## ประเด็นที่ต้องให้ผู้ใช้ตัดสินใจ (User Decisions Required)

1. **การอนุมัติ Commit โค้ดทั้งหมดเข้าสู่ Git Repository**
   * สรุปการเปลี่ยนแปลงคือ มี 31 ไฟล์ที่แก้ไข และ 12 ไฟล์ใหม่ (วัดจริง).
   * ข้อเสนอแนะคือ อนุมัติให้ทำ Commit รวบยอด เพื่อให้สถานะของโปรเจกต์สะอาดและปลอดภัย.
2. **การอนุมัติเขียนรายการเดินบัญชีเงินสดจริงใน data/ledger.json (กำลังเขียน)**
   * ข้อเท็จจริงที่พิสูจน์แล้วคือ ยอดเงินสดในแอป Dime! Save คือ 0.59 บาท และ Dime! USD คือ 295.59 ดอลลาร์.
   * ขณะนี้ W3 กำลังดำเนินการเขียนข้อมูลลงใน data/ledger.json ตามที่ได้รับอนุมัติในแชท.

---

## สรุปงานที่ปิดสมบูรณ์แล้ว (Closed Tasks)

### ปิดสมบูรณ์เมื่อวันที่ 2026-10-29

* **ลบอินดิเคเตอร์ที่ไม่ผ่าน Backtest 6 ตัว (W5)**
  * ลบฟังก์ชันคำนวณของ WAE, VFI, WaveTrend, UT Bot, Hull Suite และ Lorentzian Classification ออกจาก [src/chart_data.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/chart_data.py).
  * ลบปุ่มเปิดปิด เส้นกราฟ มาร์กเกอร์ และหน้าต่างย่อยออกจาก [src/templates/chart.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.html) และ [src/templates/chart.js](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/templates/chart.js).
  * ปรับปรุง INDICATOR_SCHEMA_VERSION เป็น 16.
  * ลดขนาดไฟล์ reports/chart_data.js ลง 781,340 ไบต์ หรือ 22.36% (วัดจาก build ในสำเนา จาก 3.49 MB เหลือ 2.71 MB ขณะที่ไฟล์ใน repository ยังคงเป็น 3,473,918 ไบต์เนื่องจากยังไม่ regenerate).
  * สร้างชุดทดสอบใหม่ [tests/test_removed_indicators.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_removed_indicators.py) ผ่านครบ 6 เทสต์.
* **ล็อกจำนวนหุ้น LLY ตามการตัดสินใจของผู้ใช้ (W4)**
  * อัปเดตข้อเท็จจริงใน [AGENTS.md](file:///Users/thanessriamornruttanakul/Documents/filter-stock/AGENTS.md#L46) ให้ยึด 27.6477631 หุ้นตามพอร์ต และห้ามใช้ --force กับ LLY.
  * เพิ่มค่าคงที่ LOCKED_PORTFOLIO_TICKERS เป็น frozenset({"LLY"}) ใน [scripts/reconcile_cost_thb.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/reconcile_cost_thb.py#L33) ป้องกันการเขียนทับยอด LLY ทุกกรณี.
  * สร้างชุดทดสอบใหม่ [tests/test_reconcile_lly.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_reconcile_lly.py) ผ่านครบ 6 เทสต์ (วัดจริง).
* **ปรับปรุงฟังก์ชันสร้างป้าย FX ทั่วไปเมื่อไม่ใช่เรทสด (W6)**
  * ปรับปรุง _format_fx_badge ใน [src/html_report.py:21-29](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/html_report.py#L21-L29) ให้รองรับกรณี fx_source มีค่าและไม่ใช่ live ให้แสดงป้าย FX ไม่ใช่เรทสด สี amber แบบเดียวกับ stored.
  * ประสานการเรียกใช้ _format_fx_badge ใน [scripts/generate_master_report.py:1501, 2094](file:///Users/thanessriamornruttanakul/Documents/filter-stock/scripts/generate_master_report.py#L1501).
  * เพิ่มยูนิตเทสต์ assert ครบทั้ง 4 กรณี ใน [tests/test_recovery_financials.py:816, 844](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_recovery_financials.py#L816) (test_format_fx_badge_all_four_cases บรรทัด 816 และ test_fx_stored_vs_fallback_badges บรรทัด 844).
* **เปลี่ยนชื่อไฟล์เทสต์และคลาสเทสต์ตามพฤติกรรม (W6)**
  * เปลี่ยนชื่อไฟล์เทสต์ 4 ไฟล์ด้วยคำสั่ง mv:
    * tests/test_w1_r3.py เปลี่ยนเป็น [tests/test_dip_tier.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_dip_tier.py) (22 เทสต์).
    * tests/test_w1_r4.py เปลี่ยนเป็น [tests/test_portfolio_rebalance.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_portfolio_rebalance.py) (6 เทสต์).
    * tests/test_w1_r5.py เปลี่ยนเป็น [tests/test_dip_actionable.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_dip_actionable.py) (2 เทสต์).
    * tests/test_w3_recovery_financials.py เปลี่ยนเป็น [tests/test_recovery_financials.py](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_recovery_financials.py) (26 เทสต์).
  * เปลี่ยนชื่อคลาสเทสต์ทั้งหมดที่ขึ้นต้นด้วย TestW1, TestW3 และ Round เป็นชื่อตามพฤติกรรม.
* **เติมข้อมูลปฏิทินวันประกาศงบย้อนหลัง 3 ปีและเวลาประกาศงบ BMO/AMC (W1)**
  * เติมวันประกาศงบย้อนหลัง 3 ปีที่ขาด 1 ไตรมาสครบ 10 ตัว (VRT, LLY, BAC, NOW, APP, SKHY, GOOGL, ABNB, MNST, NVDA) และเพิ่มงบหลัง IPO ของ SPCX ใน [src/earnings_calendar.py:18-119](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/earnings_calendar.py#L18-L119).
  * เติมเวลาประกาศงบ BMO/AMC ใน CONFIRMED_EARNINGS_TIMING ครบทุกตัว (SKHY, AAPL, MSFT, AMZN, JPM, SPCX) ใน [src/earnings_calendar.py:124-143](file:///Users/thanessriamornruttanakul/Documents/filter-stock/src/earnings_calendar.py#L124-L143).
  * เพิ่มชุดทดสอบยืนยัน 12 ไตรมาสและ timing ทุกตัวใน [tests/test_screener_chart.py:180-264](file:///Users/thanessriamornruttanakul/Documents/filter-stock/tests/test_screener_chart.py#L180-L264).

### ปิดสมบูรณ์ในรอบที่ 1 ถึง 5 เดิม

* **รอบที่ 1** รวบรวม Unified Scoring เป็นแหล่งเดียวใน src/scoring.py (พื้นฐาน 60% และ EMA200 40%), ตัดการให้คะแนนจากอินดิเคเตอร์ที่ไม่ผ่าน backtest, จัดการ Single-source SL/TP บนหน้ากราฟ.
* **รอบที่ 2** สร้างปฏิทินวันงบย้อนหลัง 3 ปีใน src/earnings_calendar.py, แก้ไขการแสดงผลบนจอมือถือ Responsive Layout, ปรับปรุงการคำนวณขาดทุนบาทใน Recovery Plan จาก cost_thb จริง.
* **รอบที่ 3** เชื่อมโยงระดับคะแนนพอร์ตกับ Unified Scoring Bands (85/70/55/40), แก้ไขข้อผิดพลาด JavaScript Blocker ในหน้ากราฟ, กำหนดเพดานกรอบ Consolidation Box ไม่เกิน 15%.
* **รอบที่ 4** ปรับปรุง Dip Opportunities ใน Screener ให้อิงตามเกรดและ entry signal เท่านั้น, ลดระยะเวลาการรันเทสต์ทั้งระบบลงเหลือ 17 วินาทีด้วย TTL Cache เมื่อต่อเน็ตไม่ได้, เพิ่มป้าย FX สำรองและ FX บันทึกไว้.
* **รอบที่ 5** ลบโค้ดส่วนเกิน has_reversal_confirmation, กำหนด TTL 10 นาทีสำหรับ Fallback FX ใน src/fx.py, แก้ไขการ mock แคชใน tests/test_screener_chart.py ป้องกันการแตะต้อง data/candles_cache.json.

---

## บทเรียนจากรอบนี้ (Process Lessons Learned)

* **แคชถูกเขียนทับ 2 ครั้ง.** data/candles_cache.json ถูกเขียนเมื่อ 2026-10-28 เวลา 23:24 และ 23:52 น. (วัดจริงจาก mtime). ต้นเหตุเกิดจากเทสต์ใน tests/test_screener_chart.py เรียกฟังก์ชันสร้างหน้ากราฟที่เข้าถึงแคชจริง. แก้ไขแล้วในรอบที่ 5 โดยการ patch CACHE_PATH ไปไดเรกทอรีชั่วคราว. ไฟล์เงินจริงทั้ง 3 ไฟล์ไม่ได้รับผลกระทบใดๆ (วัดจริงผ่าน md5).
* **ตัวเฝ้าไฟล์ช่วยได้.** การตรวจสอบค่า md5 และ mtime ทุก 15 วินาทีระหว่างที่ Worker ทำงาน ทำให้ตรวจพบการเขียนทับได้ทันที.
* **โควตาโมเดลมีจำกัด.** โควตา Gemini เคยหมดลงกลางรอบที่ 3 ส่งผลให้งานหยุดชะงักราว 1 ชั่วโมง. ควรแบ่งงานแต่ละชิ้นให้มีขนาดกะทัดรัดและจบได้ในรอบเดียว.
* **การระบุ Absolute Path.** ต้องระบุพาธแบบสมบูรณ์ของไฟล์รายงานเสมอ เพื่อป้องกันการบันทึกรายงานผิดตำแหน่ง.
* **การตั้งค่า Model Alias.** ใน ~/.claude/settings.json ต้องตรวจสอบให้ alias ชี้ไปยังโมเดลที่ถูกต้องและใช้งานได้จริง.
* **การแยกคำของตัวแปรใน Shell.** ใน zsh คำสั่ง set -- $var ไม่แยกคำ ต้องส่งอาร์กิวเมนต์ผ่านฟังก์ชันเพื่อความแม่นยำ.
* **การจัดคิวงานแก้ไขไฟล์ร่วม.** ไฟล์ที่มี Worker หลายตัวต้องแก้ไข ต้องจัดลำดับการทำงานทีละตัวเพื่อป้องกันการแก้ไขชนกัน.

---

## ลำดับการดำเนินงานที่แนะนำ (Recommended Execution Order)

1. **ระยะเร่งด่วน (ทันที):**
   * ขออนุมัติจากผู้ใช้เพื่อ Commit ไฟล์ทั้งหมด 31 ไฟล์และไฟล์ใหม่ 12 ไฟล์เข้าสู่ Git Repository.
   * รอ W3 เขียนข้อมูลเงินสดจริงใน data/ledger.json ให้เสร็จสิ้น (Dime! Save 0.59 บาท และ Dime! USD 295.59 ดอลลาร์).
   * รันคำสั่ง portfolio.py --all เพื่อสร้างไฟล์รายงาน HTML ใน reports/ ทั้ง 6 หน้าใหม่ให้เป็นปัจจุบัน.
2. **ระยะสั้น (1 ถึง 2 วัน):**
   * แก้ไข Hardcoded Path ของไดเรกทอรี data/ ทั้ง 9 จุดให้รองรับ FILTER_STOCK_DATA_DIR อย่างสมบูรณ์.
3. **ระยะกลาง (1 สัปดาห์):**
   * แยกไฟล์ชุดข้อมูลกราฟ chart_data.js ขนาด 2.71 MB ให้เป็นราย Ticker เพื่อเพิ่มความเร็วในการโหลดหน้าเว็บแบบ Local file://.
4. **ระยะยาว (ปรับปรุงโครงสร้างสถาปัตยกรรม):**
   * แยก Template HTML และ CSS ของรายงานอีก 5 หน้าออกจากโค้ดภาษา Python (สถาปัตยกรรม S2).
   * สร้าง Dataclass และนำ Type Annotations มาใช้กับโมเดลธุรกรรมทางการเงินทั้งหมด (สถาปัตยกรรม S3).
   * ปรับปรุง CI Workflow ให้ Deploy ผ่าน Pages Artifact เพื่อแยก Source Code ออกจาก Output อย่างแท้จริง (สถาปัตยกรรม S1).

---

## ข้อจำกัดของ Backtest ที่ต้องระบุทุกครั้ง
ในการอ้างอิงผลลัพธ์หรือสัญญาณจากการทดสอบย้อนหลัง (Backtest) ผู้ใช้งานต้องตระหนักถึงข้อจำกัด 3 ประการเสมอ:
1. Survivorship Bias (อคติจากการคัดรอด). รายชื่อหุ้นที่นำมาทดสอบเป็นหุ้นที่อยู่ในดัชนีชั้นนำปัจจุบัน หุ้นที่ถูกถอดออกหรือปิดตัวลงในอดีตไม่ได้ถูกนำมารวมในการคำนวณ.
2. Bull Market Regime (สภาวะตลาดขาขึ้น). ช่วงเวลาที่ใช้ทดสอบ (ปี 2024 ถึง 2026) เป็นตลาดขาขึ้นของหุ้นกลุ่มเทคโนโลยีและปัญญาประดิษฐ์ ผลตอบแทนจากกลยุทธ์ซื้อตอนย่อจึงอาจสูงกว่าค่าเฉลี่ยในสภาวะตลาดปกติ.
3. Lack of Point-in-Time Fundamentals (การขาดข้อมูลงบการเงินตามเวลาจริง). การทดสอบใช้ข้อมูลงบการเงินของรอบล่าสุดแทนที่จะเป็นตัวเลขงบที่ประกาศจริง ณ วันเทรดนั้นๆ ทำให้มีแต้มต่อของข้อมูลในอนาคตเล็กน้อย.
