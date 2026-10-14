---
name: all
description: All-in-One Automated Wealth & Portfolio Update Engine. Updates all 5 HTML reports in one shot (Master Wealth Dashboard, Health Review, Recovery Strategy, Dip Simulation, and Trades Ledger). Trigger on "/all", "all", "อัปเดตทั้งหมด", "ทำทุกอย่าง", "รันทั้งหมด", "อัปเดตทุกตัว", or requests to refresh all portfolio dashboards.
---

# All-in-One Wealth & Portfolio Engine (`/all`)

Use this skill whenever the user wants to refresh and regenerate all portfolio reports at once.

## ⚡ Execution

When triggered, run:
```bash
python3 portfolio.py --all
```

## 📋 What Gets Updated:
1. **Master Wealth Dashboard:** [portfolio_master.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports/portfolio_master.html)
2. **Portfolio Health Review:** [portfolio_review.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports/portfolio_review.html)
3. **Portfolio Drawdown Recovery:** [portfolio_recovery.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports/portfolio_recovery.html)
4. **Dip Buying Simulation:** [portfolio_dip_sim.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports/portfolio_dip_sim.html)
5. **Realized Trades Ledger:** [trades_ledger.html](file:///Users/thanessriamornruttanakul/Documents/filter-stock/reports/trades_ledger.html)
