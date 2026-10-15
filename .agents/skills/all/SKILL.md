---
name: all
description: All-in-One Automated Wealth & Portfolio Update Engine. Updates all 6 HTML reports in one shot (Master Wealth Dashboard, Health Review, Recovery Strategy, Dip Simulation, Trades Ledger, and Stock Chart page). Trigger on "/all", "all", "อัปเดตทั้งหมด", "ทำทุกอย่าง", "รันทั้งหมด", "อัปเดตทุกตัว", or requests to refresh all portfolio dashboards.
---

# All-in-One Wealth & Portfolio Engine (`/all`)

Use this skill whenever the user wants to refresh and regenerate all portfolio reports at once.

## ⚡ Execution

When triggered, run:
```bash
python3 portfolio.py --all
```

## 📋 What Gets Updated:
1. **Master Wealth Dashboard:** `reports/portfolio_master.html`
2. **Portfolio Health Review:** `reports/portfolio_review.html`
3. **Portfolio Drawdown Recovery:** `reports/portfolio_recovery.html`
4. **Dip Buying Simulation:** `reports/portfolio_dip_sim.html`
5. **Realized Trades Ledger:** `reports/trades_ledger.html`
6. **Stock Chart & AI Page:** `reports/stock_chart.html`

ทุกรายงานมีแถบเมนูด้านบนสำหรับสลับไปหน้าอื่น และแสดงเวลาอัปเดตล่าสุด.
