---
name: all
description: All-in-One Automated Wealth & Portfolio Update Engine. Updates all 6 HTML reports in one shot (Master Wealth Dashboard, Health Review, Recovery Strategy, Dip Simulation, Trades Ledger, and Stock Chart page). Trigger on "/all", "all", "อัปเดตทั้งหมด", "ทำทุกอย่าง", "รันทั้งหมด", "อัปเดตทุกตัว", or requests to refresh all portfolio dashboards.
---

# All-in-One Wealth & Portfolio Engine (`/all`)

Use this skill whenever the user wants to refresh and regenerate all portfolio reports at once.

## ⚡ Execution Protocol (Dual-Mode: AGY AI vs GitHub Actions)

### 1. In AGY (Interactive Mode with AI Assistant)
When triggered in AGY by user, execute the AI Intelligence pipeline:
1. **Inspect Pending News:** Check for unanalyzed news headlines using:
   ```bash
   python3 -m src.ai_news --pending
   ```
2. **AI News & Market Synthesis:**
   AI analyzes pending articles:
   - แปลหัวข้อข่าวภาษาไทยด้วยศัพท์การเงินที่ถูกต้องและเป็นธรรมชาติ (เช่น หลีกเลี่ยงการแปลชื่อบริษัทตรงตัวอย่าง Alphabet เป็น "ตัวอักษร").
   - วิเคราะห์สรุปประเด็นสำคัญ (`summary_th`) เชื่อมโยงกับธุรกิจจริง.
   - ประเมินผลกระทบต่อราคาหุ้นและปัจจัยพื้นฐาน (`impact_th`).
   - วางแผนกลยุทธ์การเทรด (`action_th`) และกำหนด Sentiment แท้จริง ("bullish", "bearish", "mixed", "neutral").
   - บันทึกลงใน `data/ai_news_cache.json` ผ่านฟังก์ชันใน `src/ai_news.py`.
3. **Regenerate All Dashboards:**
   ```bash
   python3 portfolio.py --all
   ```

### 2. In GitHub Actions Workflow (Automated Background Run)
- รัน `python3 portfolio.py --all` อัตโนมัติ.
- ระบบจะดึงบทวิเคราะห์ของ AI จาก `data/ai_news_cache.json` มาใช้เป็นลำดับแรกเสมอ ไม่ทับของเดิม.
- หากมีข่าวใหม่ที่ AI ยังไม่ได้วิเคราะห์ใน AGY ระบบจะใช้ Heuristic Programmatic Fallback ชั่วคราว เพื่อให้ Workflow ดำเนินการต่อได้โดยไม่หยุดชะงัก.

## 📋 What Gets Updated:
1. **Master Wealth Dashboard:** `reports/portfolio_master.html`
2. **Portfolio Health Review:** `reports/portfolio_review.html`
3. **Portfolio Drawdown Recovery:** `reports/portfolio_recovery.html`
4. **Dip Buying Simulation:** `reports/portfolio_dip_sim.html`
5. **Realized Trades Ledger:** `reports/trades_ledger.html`
6. **Stock Chart & AI Page:** `reports/stock_chart.html`

ทุกรายงานมีแถบเมนูด้านบนสำหรับสลับไปหน้าอื่น และแสดงเวลาอัปเดตล่าสุด.

