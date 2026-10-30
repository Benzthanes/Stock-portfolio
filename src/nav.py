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
    ("watchlist", "watchlist.html", "หุ้นที่สนใจ"),
    ("advisor", "advisor.html", "คำแนะนำ"),
)

ALIASES = {
    "set_review": "review",
    "set_recovery": "recovery",
}

_STYLE = """<style>
.rnav { display: flex; flex-direction: column; gap: 10px; box-sizing: border-box; width: 100%; max-width: 100%;
  padding: 10px 14px; margin: 0 0 16px 0; background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
  font-family: 'Prompt', 'Inter', -apple-system, sans-serif; font-size: 0.86rem; }
.rnav-top-row { display: flex; align-items: center; justify-content: space-between; gap: 8px 16px; width: 100%; flex-wrap: wrap; }
.rnav-links { display: flex; gap: 6px; min-width: 0; flex: 1 1 auto; overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.rnav-links::-webkit-scrollbar { display: none; }
.rnav-link { flex: 0 0 auto; white-space: nowrap; padding: 6px 12px; border-radius: 8px; text-decoration: none; color: #94a3b8;
  border: 1px solid transparent; transition: color 0.15s, background 0.15s; }
.rnav-link:hover { color: #f8fafc; background: rgba(255,255,255,0.06); }
.rnav-link.active { color: #60a5fa; background: rgba(59,130,246,0.15); border-color: #3b82f6; font-weight: 600; }
.rnav-time { white-space: nowrap; color: #64748b; font-size: 0.78rem; }

/* GLOBAL LIVE CONTROLS BAR */
.rnav-live-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
  padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.82rem; }
.rnav-live-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rnav-live-right { display: flex; align-items: center; gap: 10px; margin-left: auto; flex-wrap: wrap; }
.rnav-refresh-btn { display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, rgba(59, 130, 246, 0.22) 0%, rgba(37, 99, 235, 0.32) 100%);
  border: 1px solid rgba(59, 130, 246, 0.45); color: #93c5fd; padding: 5px 12px; border-radius: 8px; font-size: 0.82rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease; font-family: inherit; }
.rnav-refresh-btn:hover { background: linear-gradient(135deg, rgba(59, 130, 246, 0.35) 0%, rgba(37, 99, 235, 0.45) 100%); border-color: #60a5fa; color: #ffffff; }
.rnav-live-badge { font-size: 0.66rem; background: rgba(59, 130, 246, 0.25); border: 1px solid rgba(59, 130, 246, 0.4); padding: 1px 5px; border-radius: 4px; color: #93c5fd; font-weight: 700; }
.rnav-int-group { display: inline-flex; align-items: center; gap: 3px; background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 2px 4px; }
.rnav-int-label { font-size: 0.76rem; color: #94a3b8; font-weight: 600; padding-left: 4px; }
.rnav-int-btn { padding: 3px 8px; border-radius: 5px; border: 1px solid transparent; background: transparent; color: #94a3b8; font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.15s ease; font-family: inherit; }
.rnav-int-btn:hover { color: #f8fafc; background: rgba(255, 255, 255, 0.08); }
.rnav-int-btn.active { background: rgba(59, 130, 246, 0.3); border-color: #3b82f6; color: #60a5fa; font-weight: 700; }
.rnav-status { font-size: 0.78rem; color: #94a3b8; white-space: nowrap; }

@media (max-width: 640px) {
  .rnav { padding: 8px 10px; gap: 8px; }
  .rnav-top-row { gap: 6px; }
  .rnav-live-bar { flex-direction: column; align-items: stretch; gap: 8px; padding-top: 6px; }
  .rnav-live-left { justify-content: space-between; width: 100%; }
  .rnav-live-right { width: 100%; justify-content: space-between; margin-left: 0; }
  .rnav-time { font-size: 0.72rem; }
  .rnav-status { font-size: 0.74rem; }
  /* Every tab visible at once: wrap instead of scrolling sideways. */
  .rnav-links { flex-wrap: wrap; overflow: visible; gap: 4px; }
  .rnav-link { padding: 6px 9px; font-size: 0.80rem; }
  /* Live bar: refresh and interval on one row, status underneath. */
  .rnav-live-left { flex-wrap: nowrap; gap: 6px; }
  .rnav-refresh-btn { padding: 5px 9px; }
  .rnav-live-badge { display: none; }
  .rnav-int-word { display: none; }
  .rnav-int-btn { padding: 3px 6px; }
}
</style>"""

_SCRIPT = """<script>
(function() {
  var activeLink = document.querySelector(".rnav-link.active");
  if (activeLink && activeLink.parentNode) {
    activeLink.parentNode.scrollLeft = activeLink.offsetLeft - activeLink.parentNode.offsetLeft - 16;
  }

  var globalIntervalSec = 0;
  var globalCountdownSec = 0;
  var globalCountdownTimer = null;
  var globalLastSyncTime = '';

  window.triggerGlobalRefresh = async function() {
    var btn = document.getElementById('rnav-btn-refresh');
    var icon = document.getElementById('rnav-refresh-icon');
    var text = document.getElementById('rnav-refresh-text');
    var statusEl = document.getElementById('rnav-live-status');

    if (btn) { btn.disabled = true; btn.style.opacity = '0.7'; }
    if (icon) icon.style.transform = 'rotate(360deg)';
    if (text) text.textContent = 'กำลังดึง...';

    try {
      if (typeof window.refreshLiveQuotes === 'function') {
        await window.refreshLiveQuotes();
      } else if (typeof window.fetchChartLiveQuotes === 'function') {
        await window.fetchChartLiveQuotes();
      } else {
        await fetchGenericLiveQuotes();
      }
      var now = new Date();
      globalLastSyncTime = now.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      updateGlobalStatusUI();
    } catch (e) {
      console.warn('Global refresh error:', e);
      if (statusEl) statusEl.textContent = '⚠️ รีเฟรชไม่สำเร็จ';
    } finally {
      if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
      if (icon) icon.style.transform = 'none';
      if (text) text.textContent = 'รีเฟรชราคา';
    }
  };

  window.setGlobalLiveInterval = function(sec) {
    globalIntervalSec = parseInt(sec, 10) || 0;
    try {
      localStorage.setItem('portfolio_live_interval', globalIntervalSec);
    } catch (e) {}

    [0, 5, 15, 30, 60].forEach(function(s) {
      var b = document.getElementById('rnav-live-' + s);
      if (b) b.classList.toggle('active', s === globalIntervalSec);
    });

    if (globalCountdownTimer) {
      clearInterval(globalCountdownTimer);
      globalCountdownTimer = null;
    }

    if (typeof window.setLiveInterval === 'function') {
      window.setLiveInterval(globalIntervalSec);
    }
    if (typeof window.setChartLiveInterval === 'function') {
      window.setChartLiveInterval(globalIntervalSec);
    }

    if (globalIntervalSec <= 0) {
      updateGlobalStatusUI();
      return;
    }

    globalCountdownSec = globalIntervalSec;
    updateGlobalStatusUI();

    if (typeof window.setLiveInterval !== 'function' && typeof window.setChartLiveInterval !== 'function') {
      window.triggerGlobalRefresh();
      globalCountdownTimer = setInterval(function() {
        if (document.hidden) return;
        globalCountdownSec--;
        if (globalCountdownSec <= 0) {
          globalCountdownSec = globalIntervalSec;
          window.triggerGlobalRefresh();
        }
        updateGlobalStatusUI();
      }, 1000);
    }
  };

  function updateGlobalStatusUI() {
    var statusEl = document.getElementById('rnav-live-status');
    if (!statusEl) return;
    if (globalIntervalSec <= 0) {
      statusEl.innerHTML = globalLastSyncTime 
        ? '🟢 ซิงค์ล่าสุด: <strong style="color:#60a5fa;">' + globalLastSyncTime + ' น.</strong>'
        : '⚪ อัปเดตด้วยตนเอง';
    } else {
      var dot = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 6px #10b981;margin-right:4px;"></span>';
      statusEl.innerHTML = dot + 'Live (' + globalIntervalSec + 's): <strong style="color:#10b981;">' + globalCountdownSec + 's</strong>' +
        (globalLastSyncTime ? ' | <strong style="color:#60a5fa;">' + globalLastSyncTime + ' น.</strong>' : '');
    }
  }

  async function fetchGenericLiveQuotes() {
    var res = await fetch('https://scanner.tradingview.com/america/scan', {
      method: 'POST',
      mode: 'cors',
      body: JSON.stringify({
        symbols: { tickers: ["NASDAQ:NVDA","NASDAQ:AAPL","NASDAQ:MSFT","NASDAQ:GOOGL","NASDAQ:AMZN","NYSE:LLY","NASDAQ:TSLA","NASDAQ:AVGO","AMEX:VOO","NASDAQ:QQQI"] },
        columns: ['close', 'change', 'premarket_close', 'premarket_change', 'postmarket_close', 'postmarket_change']
      })
    });
    if (!res.ok) return;
    var data = await res.json();
    var quotes = {};
    (data.data || []).forEach(function(item) {
      var parts = (item.s || '').split(':');
      var tk = parts.length > 1 ? parts[1] : parts[0];
      quotes[tk] = {
        close: item.d[0],
        change: item.d[1],
        premarket_close: item.d[2],
        premarket_change: item.d[3],
        postmarket_close: item.d[4],
        postmarket_change: item.d[5]
      };
    });
    var now = new Date();
    var timeStr = now.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    var payload = { quotes: quotes, timeStr: timeStr, timestamp: Date.now() };
    try { localStorage.setItem('portfolio_live_bus', JSON.stringify(payload)); } catch(e) {}
    try {
      if (!window.__LIVE_BC__) window.__LIVE_BC__ = new BroadcastChannel('stock_portfolio_live_channel');
      window.__LIVE_BC__.postMessage(payload);
    } catch(e) {}
  }

  window.addEventListener('DOMContentLoaded', function() {
    try {
      var saved = parseInt(localStorage.getItem('portfolio_live_interval') || '0', 10);
      if (saved > 0) {
        setGlobalLiveInterval(saved);
      }
    } catch (e) {}
  });

  try {
    if (!window.__LIVE_BC__) window.__LIVE_BC__ = new BroadcastChannel('stock_portfolio_live_channel');
    window.__LIVE_BC__.onmessage = function(ev) {
      if (ev.data && ev.data.timeStr) {
        globalLastSyncTime = ev.data.timeStr;
        updateGlobalStatusUI();
      }
    };
  } catch(e) {}
})();
</script>"""


# Phones: a table wider than the screen becomes one card per row, each cell a
# "label: value" line taken from its column header. Only tables that actually
# overflow are converted, so narrow tables keep their layout. A table can opt
# out with class "no-cards" (the chart page's statement table has its own view).
_MOBILE_TABLES = """<style>
@media (max-width: 640px) {
  .rc-wrap { overflow: visible !important; border: none !important; background: transparent !important; box-shadow: none !important; }
  table.rc-cards { display: block; width: 100% !important; min-width: 0 !important; border: none !important; background: transparent !important; }
  table.rc-cards thead { display: none; }
  table.rc-cards tbody, table.rc-cards tfoot { display: block; }
  table.rc-cards tr { display: block; margin: 0 0 10px 0; padding: 10px 12px; border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px; background: rgba(15,23,42,0.75); }
  table.rc-cards td { display: flow-root; padding: 7px 0 !important; border: none !important;
    border-bottom: 1px dashed rgba(255,255,255,0.06) !important; text-align: right !important; white-space: normal !important;
    min-width: 0 !important; max-width: none !important; width: auto !important; position: static !important;
    box-shadow: none !important; background: transparent !important; }
  table.rc-cards td:last-child { border-bottom: none !important; }
  table.rc-cards td[data-label]::before { content: attr(data-label); float: left; width: 40%; margin-right: 10px; text-align: left;
    color: #94a3b8; font-size: 0.74rem; font-weight: 600; line-height: 1.5; }
  table.rc-cards td.rc-head { font-size: 1.02rem; padding-bottom: 8px !important;
    border-bottom: 1px solid rgba(255,255,255,0.10) !important; text-align: left !important; }
  table.rc-cards td.rc-head::before { display: none; }
  table.rc-cards td.rc-empty { display: none; }
}
</style>
<script>
(function () {
  var PHONE = 640, timer = null;
  function headers(table) {
    var row = table.tHead && table.tHead.rows[table.tHead.rows.length - 1];
    if (!row) return [];
    var out = [];
    for (var i = 0; i < row.cells.length; i++) {
      var c = row.cells[i], tmp = document.createElement('div');
      tmp.innerHTML = c.innerHTML.replace(/<br\\s*\\/?>/gi, ' ');
      var text = (tmp.textContent || '').replace(/\\s+/g, ' ').trim();
      for (var k = 0; k < (c.colSpan || 1); k++) out.push(text);
    }
    return out;
  }
  function label(table) {
    var hs = headers(table);
    for (var b = 0; b < table.tBodies.length; b++) {
      var rows = table.tBodies[b].rows;
      for (var r = 0; r < rows.length; r++) {
        var col = 0, cells = rows[r].cells;
        for (var i = 0; i < cells.length; i++) {
          var td = cells[i], h = hs[col] || '';
          col += td.colSpan || 1;
          if (i === 0 && cells.length > 1) { td.classList.add('rc-head'); continue; }
          if (cells.length === 1) continue;
          if (h) td.setAttribute('data-label', h);
          var txt = (td.textContent || '').trim();
          td.classList.toggle('rc-empty', !txt || txt === '-');
        }
      }
    }
  }
  function apply() {
    var phone = window.innerWidth <= PHONE;
    var tables = document.querySelectorAll('table:not(.no-cards):not(.fin-table)');
    for (var t = 0; t < tables.length; t++) {
      var table = tables[t], wrap = table.parentElement;
      if (!phone) {
        if (table.classList.contains('rc-cards')) { table.classList.remove('rc-cards'); if (wrap) wrap.classList.remove('rc-wrap'); }
        continue;
      }
      if (!table.tHead || table.closest('.rc-skip')) continue;
      if (!table.classList.contains('rc-cards')) {
        var avail = wrap ? wrap.clientWidth : window.innerWidth;
        if (table.scrollWidth <= avail + 4) continue;
        table.classList.add('rc-cards');
        if (wrap) wrap.classList.add('rc-wrap');
      }
      label(table);
    }
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(apply, 120); }
  document.addEventListener('DOMContentLoaded', function () {
    apply();
    window.addEventListener('resize', schedule);
    // Live price refreshes rewrite rows; relabel them.
    try { new MutationObserver(function (ms) {
      for (var i = 0; i < ms.length; i++) { if (ms[i].target.closest && ms[i].target.closest('table')) { schedule(); return; } }
      schedule();
    }).observe(document.body, { childList: true, subtree: true }); } catch (e) {}
  });
})();
</script>"""


def nav_bar_html(active: str, now: Optional[datetime] = None) -> str:
    """Return the nav bar (with its scoped <style>) marking the page whose key is `active`."""
    active = ALIASES.get(active, active)
    if active not in {key for key, _, _ in PAGES}:
        raise ValueError(f"unknown nav page: {active!r}")
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M")
    links = "".join(
        f'<a href="{href}" class="rnav-link active" aria-current="page">{label}</a>' if key == active
        else f'<a href="{href}" class="rnav-link">{label}</a>'
        for key, href, label in PAGES
    )
    return (
        f'{_STYLE}\n<nav class="rnav" aria-label="รายงาน">'
        f'<div class="rnav-top-row"><div class="rnav-links">{links}</div></div>'
        f'<div class="rnav-live-bar">'
        f'<div class="rnav-live-left">'
        f'<button id="rnav-btn-refresh" class="rnav-refresh-btn" onclick="triggerGlobalRefresh()" title="กดเพื่อดึงราคาตลาดสดทันที">'
        f'<span id="rnav-refresh-icon" style="display:inline-block; transition:transform 0.6s ease;">🔄</span> '
        f'<span id="rnav-refresh-text">รีเฟรชราคา</span> '
        f'<span class="rnav-live-badge">Live</span>'
        f'</button>'
        f'<div class="rnav-int-group" title="อัปเดตราคาหุ้นอัตโนมัติ (5วิ - 60วิ)">'
        f'<span class="rnav-int-label">⏱️<span class="rnav-int-word"> อัปเดตสด:</span></span>'
        f'<button id="rnav-live-0" class="rnav-int-btn active" onclick="setGlobalLiveInterval(0)">ปิด</button>'
        f'<button id="rnav-live-5" class="rnav-int-btn" onclick="setGlobalLiveInterval(5)">5s</button>'
        f'<button id="rnav-live-15" class="rnav-int-btn" onclick="setGlobalLiveInterval(15)">15s</button>'
        f'<button id="rnav-live-30" class="rnav-int-btn" onclick="setGlobalLiveInterval(30)">30s</button>'
        f'<button id="rnav-live-60" class="rnav-int-btn" onclick="setGlobalLiveInterval(60)">60s</button>'
        f'</div>'
        f'</div>'
        f'<div class="rnav-live-right">'
        f'<span id="rnav-live-status" class="rnav-status">⚪ อัปเดตด้วยตนเอง</span>'
        f'<span class="rnav-time">อัปเดต: {stamp}</span>'
        f'</div>'
        f'</div>'
        f'</nav>\n{_SCRIPT}\n{_MOBILE_TABLES}'
    )
