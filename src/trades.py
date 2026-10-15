"""
Trade Ledger & Realized P&L Tracker Module
Tracks closed trades, computes realized profit/loss in USD and THB,
and updates active holdings in portfolio.json.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.html_report import get_chart_modal_component
from src.nav import nav_bar_html

DEFAULT_PORTFOLIO_PATH = Path("data/portfolio.json")
DEFAULT_TRADES_PATH = Path("data/trades.json")
DEFAULT_LEDGER_PATH = Path("data/ledger.json")
THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def resolve_slip_relative_path(filename: Optional[str], from_reports_dir: bool = True) -> str:
    if not filename or filename in ("-", "CLI"):
        return ""
    fn = filename.strip()
    prefix = "../" if from_reports_dir else ""
    for folder in ["data/screenshots", "data/set-screenshot", "src/port"]:
        if (Path(folder) / fn).exists():
            return f"{prefix}{folder}/{fn}"
    return f"{prefix}data/screenshots/{fn}"


def get_slip_modal_component() -> str:
    return """
<!-- Order Slip Viewer Modal Component -->
<div id="slipModal" class="slip-modal" onclick="onSlipModalBackdrop(event)" style="display: none;">
    <div class="slip-modal-dialog">
        <div class="slip-modal-header">
            <div class="slip-modal-title-wrap">
                <span style="font-size: 1.3rem;">🧾</span>
                <div>
                    <h3 id="slipModalTitle" class="slip-modal-title">สลิปคำสั่งซื้อ</h3>
                    <div id="slipModalSub" class="slip-modal-sub">รายละเอียดคำสั่งซื้อ</div>
                </div>
            </div>
            <div class="slip-modal-actions">
                <a id="slipModalExternalLink" href="#" target="_blank" rel="noopener noreferrer" class="slip-modal-btn slip-modal-btn-ext" title="เปิดดูภาพขนาดเต็มในแท็บใหม่">
                    ↗️ เปิดแท็บใหม่
                </a>
                <button type="button" class="slip-modal-btn slip-modal-btn-close" onclick="closeSlipModal()" title="ปิด (Esc)">
                    ✕ ปิด
                </button>
            </div>
        </div>
        <div class="slip-modal-body">
            <div id="slipModalLoading" class="slip-modal-loading" style="display: none;">กำลังโหลดรูปภาพสลิป...</div>
            <img id="slipModalImg" src="" alt="สลิปคำสั่งซื้อ" class="slip-modal-img" onload="onSlipImageLoaded()" onerror="onSlipImageError()">
            <div id="slipModalError" class="slip-modal-error" style="display: none;">
                ⚠️ ไม่พบไฟล์สลิปหรือโหลดรูปภาพไม่สำเร็จ
            </div>
        </div>
        <div class="slip-modal-footer">
            <span id="slipModalFilename" class="slip-modal-fn">filename.webp</span>
            <span style="color: var(--text-muted); font-size: 0.78rem;">กด Esc หรือคลิกพื้นหลังเพื่อปิด</span>
        </div>
    </div>
</div>

<style>
.slip-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(3, 7, 18, 0.82);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    box-sizing: border-box;
    opacity: 0;
    transition: opacity 0.2s ease;
}
.slip-modal.show {
    opacity: 1;
}
.slip-modal-dialog {
    background: #0b1120;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    max-width: 560px;
    width: 100%;
    max-height: 92vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 30px rgba(56, 189, 248, 0.15);
    overflow: hidden;
    transform: scale(0.96);
    transition: transform 0.2s ease;
}
.slip-modal.show .slip-modal-dialog {
    transform: scale(1);
}
.slip-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.slip-modal-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}
.slip-modal-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
}
.slip-modal-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 2px;
}
.slip-modal-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}
.slip-modal-btn {
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    font-family: inherit;
}
.slip-modal-btn-ext {
    background: rgba(56, 189, 248, 0.12);
    border-color: rgba(56, 189, 248, 0.3);
    color: #38bdf8;
}
.slip-modal-btn-ext:hover {
    background: rgba(56, 189, 248, 0.25);
    color: #fff;
}
.slip-modal-btn-close {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.15);
    color: #94a3b8;
}
.slip-modal-btn-close:hover {
    background: rgba(244, 63, 94, 0.2);
    border-color: rgba(244, 63, 94, 0.4);
    color: #f43f5e;
}
.slip-modal-body {
    padding: 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 280px;
    max-height: calc(92vh - 120px);
    overflow: auto;
    background: #060913;
    position: relative;
}
.slip-modal-img {
    max-width: 100%;
    max-height: calc(88vh - 130px);
    height: auto;
    object-fit: contain;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
}
.slip-modal-loading {
    color: #94a3b8;
    font-size: 0.9rem;
}
.slip-modal-error {
    color: #f43f5e;
    background: rgba(244, 63, 94, 0.1);
    border: 1px solid rgba(244, 63, 94, 0.3);
    padding: 14px 20px;
    border-radius: 8px;
    font-size: 0.9rem;
    text-align: center;
}
.slip-modal-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    background: rgba(255, 255, 255, 0.02);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.slip-modal-fn {
    font-family: 'Inter', monospace;
    font-size: 0.78rem;
    color: #60a5fa;
    background: rgba(59, 130, 246, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
}
.slip-badge-btn {
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.78rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s ease;
}
.slip-badge-btn:hover {
    background: rgba(56, 189, 248, 0.25);
    border-color: #38bdf8;
    color: #fff;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25);
}
</style>

<script>
function openSlipModal(imagePath, filename, ticker, dateStr, extraInfo) {
    const modal = document.getElementById('slipModal');
    const title = document.getElementById('slipModalTitle');
    const sub = document.getElementById('slipModalSub');
    const fnEl = document.getElementById('slipModalFilename');
    const img = document.getElementById('slipModalImg');
    const extLink = document.getElementById('slipModalExternalLink');
    const loading = document.getElementById('slipModalLoading');
    const errorEl = document.getElementById('slipModalError');

    if (!modal || !img) return;

    title.innerText = ticker ? ('สลิปคำสั่งซื้อ: ' + ticker) : 'สลิปคำสั่งซื้อ';
    sub.innerText = (dateStr || '') + (extraInfo ? (' • ' + extraInfo) : '');
    fnEl.innerText = filename || 'slip.webp';
    extLink.href = imagePath;

    img.style.display = 'none';
    if (errorEl) errorEl.style.display = 'none';
    if (loading) loading.style.display = 'block';

    img.src = imagePath;

    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('show'), 10);
    document.body.style.overflow = 'hidden';
}

function closeSlipModal() {
    const modal = document.getElementById('slipModal');
    if (!modal) return;
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
        const img = document.getElementById('slipModalImg');
        if (img) img.src = '';
    }, 200);
    document.body.style.overflow = '';
}

function onSlipImageLoaded() {
    const img = document.getElementById('slipModalImg');
    const loading = document.getElementById('slipModalLoading');
    const errorEl = document.getElementById('slipModalError');
    if (loading) loading.style.display = 'none';
    if (errorEl) errorEl.style.display = 'none';
    if (img) img.style.display = 'block';
}

function onSlipImageError() {
    const img = document.getElementById('slipModalImg');
    const loading = document.getElementById('slipModalLoading');
    const errorEl = document.getElementById('slipModalError');
    if (loading) loading.style.display = 'none';
    if (img) img.style.display = 'none';
    if (errorEl) errorEl.style.display = 'block';
}

function onSlipModalBackdrop(event) {
    if (event.target && event.target.id === 'slipModal') {
        closeSlipModal();
    }
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
        closeSlipModal();
    }
});
</script>
"""


def load_trades(filepath: Optional[str] = None) -> Dict[str, Any]:
    path = Path(filepath) if filepath else DEFAULT_TRADES_PATH
    if not path.exists():
        return {
            "portfolio_name": "ไม่รวยก็ซวยอ่ะค้าบ",
            "broker": "InnovestX",
            "base_currency": "USD",
            "default_fx_rate": 33.62,
            "trades": []
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trades(trades_data: Dict[str, Any], filepath: Optional[str] = None) -> None:
    path = Path(filepath) if filepath else DEFAULT_TRADES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(trades_data, f, indent=2, ensure_ascii=False)


def load_ledger(filepath: Optional[str] = None) -> Dict[str, Any]:
    path = Path(filepath) if filepath else DEFAULT_LEDGER_PATH
    if not path.exists():
        return {
            "cash": {"dime_save_thb": 0.0, "dime_usd": 0.0},
            "net_injected_capital_thb": 0.0,
            "gross_deposits_thb": 0.0,
            "transfer_out_thb": 0.0,
            "dime_save_interest_thb": 0.0,
            "cash_movements": [],
            "dividends": [],
            "buy_orders": [],
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ledger(ledger: Dict[str, Any], filepath: Optional[str] = None) -> None:
    path = Path(filepath) if filepath else DEFAULT_LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _when(trade_date: Optional[str]) -> datetime:
    if trade_date is None:
        return datetime.now().replace(second=0, microsecond=0)
    return datetime.strptime(trade_date, "%Y-%m-%d").replace(hour=12)


def _cash_date_str(when: datetime, trade_date: Optional[str]) -> str:
    return when.strftime("%d/%m/%Y") if trade_date else when.strftime("%d/%m/%Y %H:%M น.")


def _thai_date_str(when: datetime) -> str:
    return f"{when.day} {THAI_MONTHS[when.month - 1]} {(when.year + 543) % 100:02d}"


def _portfolio_fx(portfolio_path: Optional[str]) -> float:
    p_path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_PATH
    if not p_path.exists():
        return 33.62
    return float(json.loads(p_path.read_text(encoding="utf-8")).get("fx_rate_usd_thb", 33.62))


def _move_save_cash(ledger: Dict[str, Any], amount_thb: float, movement_type: str, channel: str,
                    when: datetime, trade_date: Optional[str], ref: str) -> Dict[str, Any]:
    balance = round(ledger["cash"]["dime_save_thb"] + amount_thb, 2)
    ledger["cash"]["dime_save_thb"] = balance
    movement = {
        "date_str": _cash_date_str(when, trade_date),
        "type": movement_type,
        "amount_thb": round(amount_thb, 2),
        "balance_thb": balance,
        "channel": channel,
        "ref": ref,
    }
    ledger["cash_movements"].append(movement)
    return movement


def _cash_warnings(ledger: Dict[str, Any]) -> List[str]:
    warnings = []
    if ledger["cash"]["dime_save_thb"] < 0:
        warnings.append(f"Dime! Save cash is negative: ฿{ledger['cash']['dime_save_thb']:,.2f}")
    if ledger["cash"]["dime_usd"] < 0:
        warnings.append(f"Dime! USD cash is negative: ${ledger['cash']['dime_usd']:,.2f}")
    return warnings


def resolve_exchange(ticker: str) -> tuple:
    from src.universe import resolve_custom_tickers
    from src.tradingview import fetch_screener_data

    candidates = resolve_custom_tickers([ticker])
    try:
        rows = fetch_screener_data(candidates)
    except Exception:
        rows = []
    if rows:
        return rows[0]["exchange"], rows[0].get("description") or ticker
    if len(candidates) == 1:
        return candidates[0].split(":", 1)[0], ticker
    raise ValueError(f"Cannot resolve exchange for {ticker}. Pass --exchange NASDAQ|NYSE|AMEX.")


def record_buy(
    ticker: str,
    shares: float,
    price_usd: float,
    fx_rate: Optional[float] = None,
    pay: str = "thb",
    trade_date: Optional[str] = None,
    exchange: Optional[str] = None,
    portfolio_path: Optional[str] = None,
    ledger_path: Optional[str] = None,
    dry_run: bool = False,
    exchange_resolver=resolve_exchange,
) -> Dict[str, Any]:
    if shares <= 0:
        raise ValueError(f"Shares to buy must be greater than 0 (got {shares}).")
    if price_usd <= 0:
        raise ValueError(f"Price must be greater than 0 (got {price_usd}).")
    if pay not in ("thb", "usd"):
        raise ValueError(f"--pay must be thb or usd (got {pay}).")

    p_path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_PATH
    if not p_path.exists():
        raise FileNotFoundError(f"Portfolio file not found at {p_path}")
    portfolio_data = json.loads(p_path.read_text(encoding="utf-8"))
    holdings: List[Dict[str, Any]] = portfolio_data.setdefault("holdings", [])
    target_ticker = ticker.strip().upper()
    current_fx = fx_rate if fx_rate is not None else float(portfolio_data.get("fx_rate_usd_thb", 33.62))
    when = _when(trade_date)
    exec_date = when.strftime("%Y-%m-%d")

    add_usd = shares * price_usd
    amt_usd = round(add_usd, 2)
    amt_thb = round(add_usd * current_fx, 2)

    holding = next((h for h in holdings if h.get("ticker", "").upper() == target_ticker), None)
    if holding:
        old_shares = float(holding.get("shares", 0.0))
        old_total = float(holding.get("total_cost_usd", old_shares * float(holding.get("avg_cost_usd", 0.0))))
        old_cost_thb = float(holding.get("cost_thb", old_total * current_fx))
        new_shares = old_shares + shares
        holding.update({
            "shares": round(new_shares, 7),
            "avg_cost_usd": round((old_total + add_usd) / new_shares, 4),
            "total_cost_usd": round(old_total + add_usd, 2),
            "cost_thb": round(old_cost_thb + amt_thb, 2),
        })
        status_action = f"Added {shares} shares to existing {target_ticker} position ({new_shares:.4f} total)."
    else:
        if exchange:
            exch, name = exchange.upper(), target_ticker
        else:
            exch, name = exchange_resolver(target_ticker)
        holding = {
            "ticker": target_ticker,
            "exchange": exch,
            "name": name,
            "shares": round(float(shares), 7),
            "avg_cost_usd": round(float(price_usd), 4),
            "total_cost_usd": amt_usd,
            "cost_thb": amt_thb,
            "buy_date": exec_date,
        }
        holdings.append(holding)
        status_action = f"Opened new {target_ticker} position on {holding['exchange']}."

    ledger = load_ledger(ledger_path)
    buy_order = {
        "fn": "CLI",
        "ticker": target_ticker,
        "shares": float(shares),
        "price_usd": float(price_usd),
        "amt_usd": amt_usd,
        "amt_thb": amt_thb if pay == "thb" else 0.0,
        "fx_rate": current_fx,
        "date": f"{_thai_date_str(when)} - {when.strftime('%H:%M')} น.",
        "order_type": "Market",
        "account": "Dime! Save (THB)" if pay == "thb" else "Dime! USD",
    }
    ledger["buy_orders"].append(buy_order)
    if pay == "thb":
        _move_save_cash(ledger, -amt_thb, f"ชำระค่าซื้อหุ้น {target_ticker}", "Dime! Save", when, trade_date, "trades.py buy")
    else:
        ledger["cash"]["dime_usd"] = round(ledger["cash"]["dime_usd"] - amt_usd, 2)

    if not dry_run:
        p_path.write_text(json.dumps(portfolio_data, indent=2, ensure_ascii=False), encoding="utf-8")
        save_ledger(ledger, ledger_path)

    return {
        "holding": holding,
        "buy_order": buy_order,
        "cash": dict(ledger["cash"]),
        "status_action": status_action,
        "warnings": _cash_warnings(ledger),
        "dry_run": dry_run,
    }


def record_deposit(amount_thb: float, channel: str = "PROMPTPAY", trade_date: Optional[str] = None,
                   ledger_path: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    if amount_thb <= 0:
        raise ValueError(f"Deposit amount must be greater than 0 (got {amount_thb}).")
    ledger = load_ledger(ledger_path)
    when = _when(trade_date)
    movement = _move_save_cash(ledger, amount_thb, "ฝากเงิน (โอนเข้า Dime! Save)", channel, when, trade_date, "trades.py deposit")
    ledger["net_injected_capital_thb"] = round(ledger["net_injected_capital_thb"] + amount_thb, 2)
    ledger["gross_deposits_thb"] = round(ledger["gross_deposits_thb"] + amount_thb, 2)
    if not dry_run:
        save_ledger(ledger, ledger_path)
    return {"movement": movement, "cash": dict(ledger["cash"]), "net_injected_capital_thb": ledger["net_injected_capital_thb"],
            "warnings": _cash_warnings(ledger), "dry_run": dry_run}


def record_withdraw(amount_thb: float, trade_date: Optional[str] = None,
                    ledger_path: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    if amount_thb <= 0:
        raise ValueError(f"Withdraw amount must be greater than 0 (got {amount_thb}).")
    ledger = load_ledger(ledger_path)
    when = _when(trade_date)
    movement = _move_save_cash(ledger, -amount_thb, "โอนเงินออกไปต่างธนาคาร", "Dime! Save", when, trade_date, "trades.py withdraw")
    ledger["net_injected_capital_thb"] = round(ledger["net_injected_capital_thb"] - amount_thb, 2)
    ledger["transfer_out_thb"] = round(ledger["transfer_out_thb"] + amount_thb, 2)
    if not dry_run:
        save_ledger(ledger, ledger_path)
    return {"movement": movement, "cash": dict(ledger["cash"]), "net_injected_capital_thb": ledger["net_injected_capital_thb"],
            "warnings": _cash_warnings(ledger), "dry_run": dry_run}


def record_dividend(ticker: str, amount_usd: float, fx_rate: Optional[float] = None, rate: str = "-",
                    trade_date: Optional[str] = None, portfolio_path: Optional[str] = None,
                    ledger_path: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    if amount_usd <= 0:
        raise ValueError(f"Dividend amount must be greater than 0 (got {amount_usd}).")
    current_fx = fx_rate if fx_rate is not None else _portfolio_fx(portfolio_path)
    ledger = load_ledger(ledger_path)
    entry = {
        "date": _thai_date_str(_when(trade_date)),
        "ticker": ticker.strip().upper(),
        "amount_usd": round(float(amount_usd), 2),
        "rate": rate,
        "amount_thb": round(amount_usd * current_fx, 2),
        "fx_rate": current_fx,
    }
    ledger["dividends"].insert(0, entry)
    ledger["cash"]["dime_usd"] = round(ledger["cash"]["dime_usd"] + amount_usd, 2)
    if not dry_run:
        save_ledger(ledger, ledger_path)
    return {"dividend": entry, "cash": dict(ledger["cash"]), "dry_run": dry_run}


def calculate_trades_summary(trades_data: Dict[str, Any]) -> Dict[str, Any]:
    trades: List[Dict[str, Any]] = trades_data.get("trades", [])
    total_trades = len(trades)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate_pct": 0.0,
            "total_cost_usd": 0.0,
            "total_cost_thb": 0.0,
            "total_revenue_usd": 0.0,
            "total_revenue_thb": 0.0,
            "total_realized_pl_usd": 0.0,
            "total_realized_pl_thb": 0.0,
            "total_fees_usd": 0.0,
            "roi_pct": 0.0,
            "profit_factor": 0.0,
            "best_trade": None,
            "worst_trade": None,
        }

    winning_trades = [t for t in trades if t.get("realized_pl_usd", 0) > 0]
    losing_trades = [t for t in trades if t.get("realized_pl_usd", 0) < 0]
    breakeven_trades = [t for t in trades if t.get("realized_pl_usd", 0) == 0]

    win_rate = (len(winning_trades) / total_trades) * 100.0

    total_cost_usd = sum(t.get("total_cost_usd", 0) for t in trades)
    total_cost_thb = sum(t.get("cost_thb", 0) for t in trades)
    total_rev_usd = sum(t.get("net_revenue_usd", 0) for t in trades)
    total_rev_thb = sum(t.get("revenue_thb", 0) for t in trades)
    total_pl_usd = sum(t.get("realized_pl_usd", 0) for t in trades)
    total_pl_thb = sum(t.get("realized_pl_thb", 0) for t in trades)
    total_fees_usd = sum(t.get("fees_usd", 0) for t in trades)

    roi_pct = (total_pl_usd / total_cost_usd * 100.0) if total_cost_usd > 0 else 0.0

    gross_profit = sum(t.get("realized_pl_usd", 0) for t in winning_trades)
    gross_loss = abs(sum(t.get("realized_pl_usd", 0) for t in losing_trades))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    best_trade = max(trades, key=lambda t: t.get("realized_pl_usd", 0)) if trades else None
    worst_trade = min(trades, key=lambda t: t.get("realized_pl_usd", 0)) if trades else None

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "breakeven_trades": len(breakeven_trades),
        "win_rate_pct": round(win_rate, 1),
        "total_cost_usd": round(total_cost_usd, 2),
        "total_cost_thb": round(total_cost_thb, 2),
        "total_revenue_usd": round(total_rev_usd, 2),
        "total_revenue_thb": round(total_rev_thb, 2),
        "total_realized_pl_usd": round(total_pl_usd, 2),
        "total_realized_pl_thb": round(total_pl_thb, 2),
        "total_fees_usd": round(total_fees_usd, 2),
        "roi_pct": round(roi_pct, 2),
        "profit_factor": round(profit_factor, 2),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def record_sell(
    ticker: str,
    sell_price: float,
    shares: Optional[float] = None,
    fees: float = 0.0,
    fx_rate: Optional[float] = None,
    trade_date: Optional[str] = None,
    notes: str = "",
    portfolio_path: Optional[str] = None,
    trades_path: Optional[str] = None,
    dry_run: bool = False,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    p_path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_PATH
    if not p_path.exists():
        raise FileNotFoundError(f"Portfolio file not found at {p_path}")

    with open(p_path, "r", encoding="utf-8") as f:
        portfolio_data = json.load(f)

    holdings: List[Dict[str, Any]] = portfolio_data.get("holdings", [])
    target_ticker = ticker.strip().upper()

    holding_match = None
    holding_idx = -1
    for i, h in enumerate(holdings):
        if h.get("ticker", "").upper() == target_ticker:
            holding_match = h
            holding_idx = i
            break

    if not holding_match:
        raise ValueError(f"Ticker '{target_ticker}' not found in active holdings.")

    current_shares = float(holding_match.get("shares", 0.0))
    avg_cost = float(holding_match.get("avg_cost_usd", 0.0))

    if shares is None:
        sell_shares = current_shares
    elif shares <= 0:
        raise ValueError(f"Shares to sell must be greater than 0 (got {shares}).")
    elif shares > current_shares:
        raise ValueError(f"Cannot sell {shares} shares of {target_ticker}: only {current_shares} held.")
    else:
        sell_shares = float(shares)

    current_fx = fx_rate if fx_rate is not None else float(portfolio_data.get("fx_rate_usd_thb", 33.62))
    exec_date = trade_date or datetime.now().strftime("%Y-%m-%d")

    cost_usd = round(sell_shares * avg_cost, 2)
    cost_thb = round(cost_usd * current_fx, 2)

    gross_rev_usd = round(sell_shares * sell_price, 2)
    net_rev_usd = round(gross_rev_usd - fees, 2)
    rev_thb = round(net_rev_usd * current_fx, 2)

    realized_pl_usd = round(net_rev_usd - cost_usd, 2)
    realized_pl_thb = round(realized_pl_usd * current_fx, 2)
    realized_pl_pct = round((realized_pl_usd / cost_usd * 100.0) if cost_usd > 0 else 0.0, 2)

    trades_data = load_trades(trades_path)
    trade_id = f"TRD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{target_ticker}"

    trade_entry = {
        "id": trade_id,
        "ticker": target_ticker,
        "exchange": holding_match.get("exchange", "NASDAQ"),
        "name": holding_match.get("name", target_ticker),
        "action": "SELL",
        "date": exec_date,
        "shares": sell_shares,
        "buy_price_usd": avg_cost,
        "sell_price_usd": float(sell_price),
        "total_cost_usd": cost_usd,
        "cost_thb": cost_thb,
        "gross_revenue_usd": gross_rev_usd,
        "fees_usd": float(fees),
        "net_revenue_usd": net_rev_usd,
        "revenue_thb": rev_thb,
        "realized_pl_usd": realized_pl_usd,
        "realized_pl_thb": realized_pl_thb,
        "realized_pl_pct": realized_pl_pct,
        "fx_rate": current_fx,
        "notes": notes,
        "remaining_shares": round(current_shares - sell_shares, 7),
    }

    buy_date = holding_match.get("buy_date")
    if buy_date:
        trade_entry["buy_date"] = buy_date
        try:
            trade_entry["holding_days"] = (datetime.strptime(exec_date, "%Y-%m-%d") - datetime.strptime(buy_date, "%Y-%m-%d")).days
        except ValueError:
            pass

    # Update holdings
    remaining_shares = current_shares - sell_shares
    if remaining_shares <= 0.000001:
        status_action = f"Closed position completely (sold all {sell_shares} shares)."
        if not dry_run:
            holdings.pop(holding_idx)
    else:
        new_total_cost = round(remaining_shares * avg_cost, 2)
        old_cost_thb = holding_match.get("cost_thb")
        if old_cost_thb is None:
            new_cost_thb = round(new_total_cost * current_fx, 2)
        else:
            new_cost_thb = round(float(old_cost_thb) * remaining_shares / current_shares, 2)
        status_action = f"Partial sell: {sell_shares} sold, {remaining_shares:.4f} remaining."
        if not dry_run:
            holding_match["shares"] = round(remaining_shares, 7)
            holding_match["total_cost_usd"] = new_total_cost
            holding_match["cost_thb"] = new_cost_thb

    if not dry_run:
        with open(p_path, "w", encoding="utf-8") as f:
            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)

        trades_data["trades"].append(trade_entry)
        save_trades(trades_data, trades_path)

    ledger = load_ledger(ledger_path)
    ledger["cash"]["dime_usd"] = round(ledger["cash"]["dime_usd"] + net_rev_usd, 2)
    if not dry_run:
        save_ledger(ledger, ledger_path)

    return {
        "trade": trade_entry,
        "status_action": status_action,
        "dry_run": dry_run,
        "cash": dict(ledger["cash"]),
        "updated_summary": calculate_trades_summary(trades_data if not dry_run else {"trades": trades_data.get("trades", []) + [trade_entry]}),
    }


def generate_trades_markdown(trades_data: Dict[str, Any]) -> str:
    summary = calculate_trades_summary(trades_data)
    trades = trades_data.get("trades", [])

    lines = []
    lines.append("# 📈 บัญชีกำไรขาดทุนจากการซื้อขาย (Realized Trade Ledger)")
    lines.append(f"**พอร์ตโฟลิโอ:** {trades_data.get('portfolio_name', 'My Portfolio')} | **โบรกเกอร์:** {trades_data.get('broker', 'InnovestX')}\n")

    lines.append("## 📊 ภาพรวมกำไรขาดทุนสะสม (Realized Performance)")
    pl_sign = "+" if summary["total_realized_pl_usd"] >= 0 else ""
    lines.append(f"- **กำไรขาดทุนสุทธิ (Net Realized P&L):** `{pl_sign}${summary['total_realized_pl_usd']:,.2f}` (`{pl_sign}฿{summary['total_realized_pl_thb']:,.2f}`)")
    lines.append(f"- **ผลตอบแทนเฉลี่ย (Overall ROI):** `{pl_sign}{summary['roi_pct']:.2f}%`")
    lines.append(f"- **อัตราการเทรดชนะ (Win Rate):** `{summary['win_rate_pct']:.1f}%` ({summary['winning_trades']} ชนะ / {summary['losing_trades']} แพ้ จาก {summary['total_trades']} รายการ)")
    lines.append(f"- **Profit Factor:** `{summary['profit_factor']:.2f}`")
    lines.append(f"- **ต้นทุนที่ปิดการขายไป:** `${summary['total_cost_usd']:,.2f}` | **เงินรับสุทธิ (Proceeds):** `${summary['total_revenue_usd']:,.2f}`\n")

    lines.append("## 📝 รายการปิดการขาย (Closed Trades History)")
    if not trades:
        lines.append("*ยังไม่มีรายการปิดสถานะซื้อขายในประวัติ.*")
    else:
        lines.append("| วันที่ซื้อ | วันที่ขาย | ระยะถือ | หุ้น | หุ้นที่ขาย | ทุนเฉลี่ย | ราคาขาย | ต้นทุน ($) | เงินรับ ($) | กำไร/ขาดทุน ($) | กำไร/ขาดทุน (฿) | % ROI |")
        lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        for t in reversed(trades):
            pl_usd = t.get("realized_pl_usd", 0)
            pl_thb = t.get("realized_pl_thb", 0)
            pl_pct = t.get("realized_pl_pct", 0)
            sign = "+" if pl_usd >= 0 else ""
            b_date = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
            h_days = f"{t.get('holding_days')} วัน" if t.get('holding_days') is not None else "-"
            lines.append(
                f"| {b_date} | {t.get('date', '-')} | {h_days} | **{t.get('ticker')}** | {t.get('shares'):.4f} | "
                f"${t.get('buy_price_usd'):.2f} | ${t.get('sell_price_usd'):.2f} | "
                f"${t.get('total_cost_usd'):,.2f} | ${t.get('net_revenue_usd'):,.2f} | "
                f"`{sign}${pl_usd:,.2f}` | `{sign}฿{pl_thb:,.2f}` | `{sign}{pl_pct:.2f}%` |"
            )

    return "\n".join(lines)


def generate_trades_html(trades_data: Dict[str, Any]) -> str:
    try:
        from scripts.generate_master_report import generate_master_dashboard_data, generate_master_ledger_html
        return generate_master_ledger_html(generate_master_dashboard_data())
    except Exception:
        pass
    summary = calculate_trades_summary(trades_data)
    trades = trades_data.get("trades", [])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pl_val = summary["total_realized_pl_usd"]
    pl_color = "#10b981" if pl_val >= 0 else "#f43f5e"
    pl_sign = "+" if pl_val >= 0 else ""

    rows_html = ""
    for idx, t in enumerate(reversed(trades)):
        t_pl = t.get("realized_pl_usd", 0)
        t_thb = t.get("realized_pl_thb", 0)
        t_pct = t.get("realized_pl_pct", 0)
        t_color = "#10b981" if t_pl >= 0 else "#f43f5e"
        t_sign = "+" if t_pl >= 0 else ""
        tranches = t.get("buy_tranches", [])
        tranche_count = len(tranches)
        trade_id = t.get("id", f"trade_{idx}").replace("-", "_")

        buy_date_str = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
        days = t.get("holding_days", "-")
        days_str = f"{days} วัน" if isinstance(days, (int, float)) else str(days)

        if tranche_count > 1:
            tranche_btn = f'<button onclick="toggleTranche(\'{trade_id}\')" style="background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 6px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">สะสม {tranche_count} ไม้ <span id="icon-{trade_id}">▼</span></button>'
        else:
            single_fn = tranches[0].get('file') if tranches else None
            single_path = resolve_slip_relative_path(single_fn) if single_fn else ""
            if single_path:
                t_tk = t.get("ticker", "")
                t_sh = t.get("shares", 0.0)
                t_pr = t.get("buy_price_usd", 0.0)
                t_info = f"{t_sh:.4f} หุ้น @ ${t_pr:.2f}"
                tranche_btn = f'<span style="background: rgba(255, 255, 255, 0.08); color: #94a3b8; padding: 2px 8px; border-radius: 6px; font-size: 0.76rem;">1 ไม้</span> <button type="button" onclick="openSlipModal(\'{single_path}\', \'{single_fn}\', \'{t_tk}\', \'{buy_date_str}\', \'{t_info}\')" class="slip-badge-btn" style="padding: 2px 7px; font-size: 0.74rem;" title="คลิกดูภาพสลิปคำสั่งซื้อ">🧾 สลิป</button>'
            else:
                tranche_btn = '<span style="background: rgba(255, 255, 255, 0.08); color: #94a3b8; padding: 2px 8px; border-radius: 6px; font-size: 0.76rem;">1 ไม้</span>'

        t_ticker = t.get('ticker', '')
        t_name = (t.get('name') or t_ticker).replace("'", "\\'")
        t_click_js = f"openChartModal('{t_ticker}', '{t.get('exchange', 'NASDAQ')}', '{t_name}', 'Closed Trade', {t.get('buy_price_usd', 0)}, {t.get('sell_price_usd', 0)}, 0, 0, 0, {t.get('sell_price_usd', 0)}, 0)"

        rows_html += f"""
        <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="white-space: nowrap; font-size: 0.85rem; color: #60a5fa; font-weight: 500;">{buy_date_str}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary); text-align: center;">{t.get('date', '-')}</td>
            <td style="text-align: center; font-size: 0.82rem; color: var(--text-muted); white-space: nowrap;">{days_str}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; font-size: 1.05rem; color: #fff;">
                <span class="clickable-ticker" onclick="{t_click_js}" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="คลิกเปิดดูกราฟเทคนิคัล">{t.get('ticker')} 📈</span>
            </td>
            <td>
                <div>{t.get('name', '-')}</div>
                <div style="margin-top: 4px;">{tranche_btn}</div>
            </td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{t.get('shares', 0):.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('buy_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('sell_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('total_cost_usd', 0):,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('net_revenue_usd', 0):,.2f}</td>
            <td style="text-align: right; font-weight: 700; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}${t_pl:,.2f}</td>
            <td style="text-align: right; font-weight: 600; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}฿{t_thb:,.2f}</td>
            <td style="text-align: right; font-weight: 700; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}{t_pct:.2f}%</td>
        </tr>
        """

        if tranches:
            tranche_subrows = ""
            for tr in tranches:
                t_thb_str = f"฿{tr.get('amt_thb', 0):,.2f}" if tr.get('amt_thb', 0) > 0 else "-"
                tr_fn = tr.get('file', '')
                tr_path = resolve_slip_relative_path(tr_fn)
                if tr_path:
                    tr_tk = t.get("ticker", "")
                    tr_dt = tr.get("date", "-")
                    tr_num = tr.get("tranche", 1)
                    tr_sh = tr.get("shares", 0.0)
                    tr_pr = tr.get("price_usd", 0.0)
                    tr_info = f"ไม้ที่ {tr_num} • {tr_sh:.4f} หุ้น @ ${tr_pr:.2f}"
                    slip_col = f'<button type="button" onclick="openSlipModal(\'{tr_path}\', \'{tr_fn}\', \'{tr_tk}\', \'{tr_dt}\', \'{tr_info}\')" class="slip-badge-btn" title="คลิกดูภาพสลิปคำสั่งซื้อ">🧾 {tr_fn}</button>'
                else:
                    slip_col = f'<span style="color: var(--text-muted); font-size: 0.78rem;">{tr_fn or "-"}</span>'

                tranche_subrows += f"""
                <tr style="background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.82rem;">
                    <td style="text-align: center; color: #c084fc; font-weight: 700;">ไม้ที่ {tr.get('tranche')}</td>
                    <td style="color: #60a5fa; font-family: 'Inter', sans-serif;">{tr.get('date')}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">{tr.get('shares'):.4f} หุ้น</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">${tr.get('price_usd'):.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${tr.get('amt_usd'):,.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{t_thb_str}</td>
                    <td style="color: var(--text-secondary);">{tr.get('note', '-')}</td>
                    <td style="text-align: center;">{slip_col}</td>
                </tr>
                """

            rows_html += f"""
            <tr id="details-{trade_id}" class="tranche-detail-row" style="display: none; background: rgba(139, 92, 246, 0.05);">
                <td colspan="13" style="padding: 12px 18px;">
                    <div style="background: #090e1a; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 14px 18px;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #c084fc; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                            <span>🔍</span> รายละเอียดการเข้าซื้อทีละไม้ของ {t.get('ticker')} (ทั้งหมด {tranche_count} ไม้ | ต้นทุนเฉลี่ย ${t.get('buy_price_usd', 0):.2f}):
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem; color: var(--text-secondary);">
                                    <th style="text-align: center; width: 65px; background: transparent;">ไม้ที่</th>
                                    <th style="background: transparent;">วัน-เวลาที่เข้าซื้อ (Buy Date & Time)</th>
                                    <th style="text-align: right; background: transparent;">จำนวนหุ้น</th>
                                    <th style="text-align: right; background: transparent;">ราคาที่ซื้อ ($)</th>
                                    <th style="text-align: right; background: transparent;">ยอดลงทุน ($)</th>
                                    <th style="text-align: right; background: transparent;">ยอดเงินบาท (THB)</th>
                                    <th style="background: transparent;">หมายเหตุ / กลยุทธ์</th>
                                    <th style="text-align: center; background: transparent;">สลิปอ้างอิง</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tranche_subrows}
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
            """

    if not trades:
        rows_html = '<tr><td colspan="11" style="text-align: center; padding: 28px; color: var(--text-muted);">ยังไม่มีรายการปิดสถานะซื้อขายในประวัติ</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Realized Trade Ledger - {trades_data.get('portfolio_name', 'Portfolio')}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #080d1a;
            --bg-card: #0f172a;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.05);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --rose: #f43f5e;
            --blue: #3b82f6;
            --amber: #f59e0b;
            --radius-sm: 8px;
            --radius-md: 14px;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Prompt', 'Inter', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            padding: 24px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .meta-pill {{
            background: var(--bg-card); padding: 6px 14px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-color); font-size: 0.9rem; color: var(--text-secondary);
        }}
        .grid-4-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .card {{
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: var(--radius-md); padding: 22px;
        }}
        .kpi-label {{ font-size: 0.82rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 1.85rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .kpi-subtext {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; }}
        table {{
            width: 100%; border-collapse: collapse; font-size: 0.92rem;
        }}
        th {{
            background: rgba(255, 255, 255, 0.03); color: var(--text-secondary);
            padding: 12px 14px; text-align: left; font-weight: 600;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 14px; border-bottom: 1px solid var(--border-subtle);
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
    </style>
</head>
<body>
    <div class="container">
        {nav_bar_html('ledger')}
        <div class="header">
            <div>
                <h1 style="font-size: 1.85rem; font-weight: 700;">📈 บัญชีกำไรขาดทุนจากการซื้อขาย (Realized Trade Ledger)</h1>
                <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">
                    พอร์ต: <strong>{trades_data.get('portfolio_name')}</strong> | โบรกเกอร์: {trades_data.get('broker')}
                </p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button onclick="toggleAllTranches()" style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); color: #c084fc; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                    <span>🔍</span> <span id="toggleAllBtnText">คลี่ดูรายละเอียดทุกไม้ (Expand All)</span>
                </button>
                <span class="meta-pill">🕒 ข้อมูล ณ: {now_str}</span>
            </div>
        </div>

        <div class="grid-4-cols">
            <div class="card">
                <div class="kpi-label">กำไรขาดทุนสะสม (Net Realized P&L)</div>
                <div class="kpi-value" style="color: {pl_color};">{pl_sign}${summary['total_realized_pl_usd']:,.2f}</div>
                <div class="kpi-subtext" style="color: {pl_color}; font-weight: 600;">{pl_sign}฿{summary['total_realized_pl_thb']:,.2f}</div>
            </div>
            <div class="card">
                <div class="kpi-label">อัตราเทรดชนะ (Win Rate)</div>
                <div class="kpi-value">{summary['win_rate_pct']:.1f}%</div>
                <div class="kpi-subtext">{summary['winning_trades']} ชนะ / {summary['losing_trades']} แพ้ (รวม {summary['total_trades']} ไม้)</div>
            </div>
            <div class="card">
                <div class="kpi-label">ผลตอบแทนเฉลี่ย (Overall ROI)</div>
                <div class="kpi-value" style="color: {pl_color};">{pl_sign}{summary['roi_pct']:.2f}%</div>
                <div class="kpi-subtext">Profit Factor: {summary['profit_factor']:.2f}</div>
            </div>
            <div class="card">
                <div class="kpi-label">เงินรับรวมสุทธิ (Net Proceeds)</div>
                <div class="kpi-value">${summary['total_revenue_usd']:,.2f}</div>
                <div class="kpi-subtext">จากต้นทุนปิดสัญญา ${summary['total_cost_usd']:,.2f}</div>
            </div>
        </div>

        <div class="card" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>วันที่ซื้อ (Buy Date)</th>
                        <th style="text-align: center;">วันที่ขาย</th>
                        <th style="text-align: center;">ระยะถือ</th>
                        <th>หุ้น</th>
                        <th>ชื่อบริษัท / ไม้สะสม</th>
                        <th style="text-align: right;">จำนวนหุ้น</th>
                        <th style="text-align: right;">ราคาซื้อเฉลี่ย</th>
                        <th style="text-align: right;">ราคาขายจริง</th>
                        <th style="text-align: right;">ต้นทุนรวม ($)</th>
                        <th style="text-align: right;">เงินรับสุทธิ ($)</th>
                        <th style="text-align: right;">กำไร ($)</th>
                        <th style="text-align: right;">กำไร (฿)</th>
                        <th style="text-align: right;">% ผลตอบแทน</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    function toggleTranche(id) {{
        var row = document.getElementById('details-' + id);
        var icon = document.getElementById('icon-' + id);
        if (!row) return;
        if (row.style.display === 'none' || row.style.display === '') {{
            row.style.display = 'table-row';
            if (icon) icon.innerHTML = '▲';
        }} else {{
            row.style.display = 'none';
            if (icon) icon.innerHTML = '▼';
        }}
    }}

    var allExpanded = false;
    function toggleAllTranches() {{
        var rows = document.querySelectorAll('.tranche-detail-row');
        var btnText = document.getElementById('toggleAllBtnText');
        allExpanded = !allExpanded;
        rows.forEach(function(row) {{
            row.style.display = allExpanded ? 'table-row' : 'none';
            var id = row.id.replace('details-', '');
            var icon = document.getElementById('icon-' + id);
            if (icon) icon.innerHTML = allExpanded ? '▲' : '▼';
        }});
        if (btnText) {{
            btnText.innerText = allExpanded ? 'หุบรายละเอียดทุกไม้ (Collapse All)' : 'คลี่ดูรายละเอียดทุกไม้ (Expand All)';
        }}
    }}
    </script>
    {get_chart_modal_component()}
    {get_slip_modal_component()}
</body>
</html>
"""
    return html
