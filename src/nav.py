"""Shared top navigation bar linking the generated reports in reports/."""

from datetime import datetime
from typing import Optional

PAGES = (
    ("master", "portfolio_master.html", "ภาพรวม"),
    ("review", "portfolio_review.html", "สุขภาพพอร์ต"),
    ("recovery", "portfolio_recovery.html", "แก้ดอย"),
    ("dip_sim", "portfolio_dip_sim.html", "Dip จำลอง"),
    ("ledger", "trades_ledger.html", "รายการซื้อขายทั้งหมด"),
    ("chart", "stock_chart.html", "กราฟ"),
    ("set_review", "portfolio_set_review.html", "หุ้นไทย สุขภาพพอร์ต"),
    ("set_recovery", "portfolio_set_recovery.html", "หุ้นไทย แก้ดอย"),
)

_STYLE = """<style>
.rnav { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; box-sizing: border-box; width: 100%; max-width: 100%;
  padding: 10px 16px; margin: 0 0 16px 0; background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
  font-family: 'Prompt', 'Inter', -apple-system, sans-serif; font-size: 0.86rem; }
.rnav-links { display: flex; gap: 6px; min-width: 0; flex: 1 1 auto; overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.rnav-links::-webkit-scrollbar { display: none; }
.rnav-link { flex: 0 0 auto; white-space: nowrap; padding: 6px 12px; border-radius: 8px; text-decoration: none; color: #94a3b8;
  border: 1px solid transparent; transition: color 0.15s, background 0.15s; }
.rnav-link:hover { color: #f8fafc; background: rgba(255,255,255,0.06); }
.rnav-link.active { color: #60a5fa; background: rgba(59,130,246,0.15); border-color: #3b82f6; font-weight: 600; }
.rnav-time { margin-left: auto; white-space: nowrap; color: #64748b; font-size: 0.8rem; }
</style>"""


def nav_bar_html(active: str, now: Optional[datetime] = None) -> str:
    """Return the nav bar (with its scoped <style>) marking the page whose key is `active`."""
    if active not in {key for key, _, _ in PAGES}:
        raise ValueError(f"unknown nav page: {active!r}")
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M")
    links = "".join(
        f'<a href="{href}" class="rnav-link active" aria-current="page">{label}</a>' if key == active
        else f'<a href="{href}" class="rnav-link">{label}</a>'
        for key, href, label in PAGES
    )
    return (
        f'{_STYLE}\n<nav class="rnav" aria-label="รายงาน"><div class="rnav-links">{links}</div>'
        f'<span class="rnav-time">อัปเดต: {stamp}</span></nav>'
        '<script>(function(){var a=document.querySelector(".rnav-link.active");'
        'if(a){var b=a.parentNode;b.scrollLeft=a.offsetLeft-b.offsetLeft-16;}})();</script>'
    )
