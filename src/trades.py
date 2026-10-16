"""
Trade Ledger & Realized P&L Tracker Module
Tracks closed trades, computes realized profit/loss in USD and THB,
and updates active holdings in portfolio.json.
"""

import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from src.fx import FALLBACK_USDTHB, resolve_usdthb

DEFAULT_PORTFOLIO_PATH = Path("data/portfolio.json")
DEFAULT_TRADES_PATH = Path("data/trades.json")
DEFAULT_LEDGER_PATH = Path("data/ledger.json")
THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
_THAI_MONTH_RE = re.compile("|".join(re.escape(m) for m in sorted(THAI_MONTHS, key=len, reverse=True)))


def _to_ce_year(year: int) -> int:
    if year < 100:
        year += 2500
    return year - 543 if year > 2400 else year


def parse_trade_date(value: Optional[str]) -> Optional[date]:
    """Parse ISO, dd/mm/yyyy, or Thai Buddhist-era dates ("12 มิ.ย. 69 - 22:46 น.", "1 มิ.ย. - 15 ก.ค. 69"). Ranges give the start date."""
    if not value:
        return None
    text = re.sub(r"\(\s*\d+\s*ไม้\s*\)", "", str(value))
    text = re.sub(r"\d{1,2}:\d{2}(\s*น\.?)?", "", text).strip(" -")
    iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso:
        return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
    dmy = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if dmy:
        return date(_to_ce_year(int(dmy.group(3))), int(dmy.group(2)), int(dmy.group(1)))
    day = re.match(r"^(\d{1,2})\b", text)
    months = list(_THAI_MONTH_RE.finditer(text))
    if not day or not months:
        return None
    first = months[0]
    year_after_first = re.match(r"\s*(\d{2}|\d{4})\b", text[first.end():])
    month_idx = THAI_MONTHS.index(first.group(0)) + 1
    if year_after_first:
        year = _to_ce_year(int(year_after_first.group(1)))
    else:
        years = re.findall(r"(?<![\d:])(\d{2}|\d{4})\s*$", text)
        if not years:
            return None
        year = _to_ce_year(int(years[-1]))
        if THAI_MONTHS.index(months[-1].group(0)) + 1 < month_idx:
            year -= 1
    try:
        return date(year, month_idx, int(day.group(1)))
    except ValueError:
        return None


def _atomic_write_many(files: Sequence[Tuple[Path, str]]) -> None:
    """Write every file to a temp sibling first, then os.replace them all, so a crash never leaves a half-written set."""
    staged: List[Tuple[str, Path]] = []
    try:
        for path, text in files:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
            staged.append((tmp, path))
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
        for tmp, path in staged:
            os.replace(tmp, path)
    finally:
        for tmp, _ in staged:
            if os.path.exists(tmp):
                os.unlink(tmp)


def _json_text(data: Dict[str, Any], trailing_newline: bool = False) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + ("\n" if trailing_newline else "")


def _validate_trade(shares: Optional[float], price: float, fees: float) -> None:
    if shares is not None and not shares > 0:
        raise ValueError(f"จำนวนหุ้นต้องมากกว่า 0 / Shares must be greater than 0 (got {shares}).")
    if not price > 0:
        raise ValueError(f"ราคาต้องมากกว่า 0 / Price must be greater than 0 (got {price}).")
    if not fees >= 0:
        raise ValueError(f"ค่าธรรมเนียมต้องไม่ติดลบ / Fees must be 0 or more (got {fees}).")


def _run_fx(portfolio_data: Dict[str, Any], fx_rate: Optional[float]) -> float:
    if fx_rate is not None:
        if not fx_rate > 0:
            raise ValueError(f"อัตราแลกเปลี่ยนต้องมากกว่า 0 / FX rate must be greater than 0 (got {fx_rate}).")
        return float(fx_rate)
    rate = resolve_usdthb(portfolio_data.get("fx_rate_usd_thb"))
    portfolio_data["fx_rate_usd_thb"] = rate
    return rate


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
            "default_fx_rate": FALLBACK_USDTHB,
            "trades": []
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trades(trades_data: Dict[str, Any], filepath: Optional[str] = None) -> None:
    _atomic_write_many([(Path(filepath) if filepath else DEFAULT_TRADES_PATH, _json_text(trades_data))])


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
    _atomic_write_many([(Path(filepath) if filepath else DEFAULT_LEDGER_PATH, _json_text(ledger, trailing_newline=True))])


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
    stored = json.loads(p_path.read_text(encoding="utf-8")).get("fx_rate_usd_thb") if p_path.exists() else None
    return resolve_usdthb(stored)


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
    fees: float = 0.0,
    pay: str = "thb",
    trade_date: Optional[str] = None,
    exchange: Optional[str] = None,
    portfolio_path: Optional[str] = None,
    ledger_path: Optional[str] = None,
    dry_run: bool = False,
    exchange_resolver=resolve_exchange,
) -> Dict[str, Any]:
    _validate_trade(shares, price_usd, fees)
    if pay not in ("thb", "usd"):
        raise ValueError(f"--pay must be thb or usd (got {pay}).")

    p_path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_PATH
    if not p_path.exists():
        raise FileNotFoundError(f"Portfolio file not found at {p_path}")
    portfolio_data = json.loads(p_path.read_text(encoding="utf-8"))
    holdings: List[Dict[str, Any]] = portfolio_data.setdefault("holdings", [])
    target_ticker = ticker.strip().upper()
    current_fx = _run_fx(portfolio_data, fx_rate)
    when = _when(trade_date)
    exec_date = when.strftime("%Y-%m-%d")

    add_usd = shares * price_usd + fees
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
            "avg_cost_usd": round(add_usd / shares, 4),
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
    if fees:
        buy_order["fees_usd"] = float(fees)
    ledger["buy_orders"].append(buy_order)
    if pay == "thb":
        _move_save_cash(ledger, -amt_thb, f"ชำระค่าซื้อหุ้น {target_ticker}", "Dime! Save", when, trade_date, "trades.py buy")
    else:
        ledger["cash"]["dime_usd"] = round(ledger["cash"]["dime_usd"] - amt_usd, 2)

    if not dry_run:
        _atomic_write_many([
            (p_path, _json_text(portfolio_data)),
            (Path(ledger_path) if ledger_path else DEFAULT_LEDGER_PATH, _json_text(ledger, trailing_newline=True)),
        ])

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


def format_profit_factor(value: Optional[float]) -> str:
    return "∞" if value is None else f"{value:.2f}"


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
            "profit_factor_display": format_profit_factor(0.0),
            "best_trade": None,
            "worst_trade": None,
        }

    winning_trades = [t for t in trades if t.get("realized_pl_usd", 0) > 0]
    losing_trades = [t for t in trades if t.get("realized_pl_usd", 0) < 0]
    breakeven_trades = [t for t in trades if t.get("realized_pl_usd", 0) == 0]

    decided = len(winning_trades) + len(losing_trades)
    win_rate = (len(winning_trades) / decided * 100.0) if decided else 0.0

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
    if gross_loss > 0:
        profit_factor = round(gross_profit / gross_loss, 2)
    else:
        # None (not inf) when there are no losses: the summary is json.dumps'd into data/account_summary.json and the browser rejects Infinity.
        profit_factor = None if gross_profit > 0 else 0.0

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
        "profit_factor": profit_factor,
        "profit_factor_display": format_profit_factor(profit_factor),
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

    _validate_trade(shares, sell_price, fees)
    if shares is None:
        sell_shares = current_shares
    elif shares > current_shares:
        raise ValueError(f"ขายเกินจำนวนที่ถือ / Cannot sell {shares} shares of {target_ticker}: only {current_shares} held.")
    else:
        sell_shares = float(shares)

    current_fx = _run_fx(portfolio_data, fx_rate)
    if trade_date:
        parsed_exec = parse_trade_date(trade_date)
        if parsed_exec is None:
            raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง / Unrecognised trade date: {trade_date!r}.")
        exec_date = parsed_exec.isoformat()
    else:
        exec_date = datetime.now().strftime("%Y-%m-%d")

    cost_usd = round(sell_shares * avg_cost, 2)
    old_cost_thb = holding_match.get("cost_thb")
    if old_cost_thb is None:
        old_cost_thb = round(current_shares * avg_cost * current_fx, 2)
    old_cost_thb = float(old_cost_thb)
    cost_thb = round(old_cost_thb * sell_shares / current_shares, 2) if current_shares > 0 else 0.0

    gross_rev_usd = round(sell_shares * sell_price, 2)
    net_rev_usd = round(gross_rev_usd - fees, 2)
    rev_thb = round(net_rev_usd * current_fx, 2)

    realized_pl_usd = round(net_rev_usd - cost_usd, 2)
    realized_pl_thb = round(rev_thb - cost_thb, 2)
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
        bought = parse_trade_date(buy_date)
        trade_entry["holding_days"] = (date.fromisoformat(exec_date) - bought).days if bought else None

    # Update holdings
    remaining_shares = current_shares - sell_shares
    if remaining_shares <= 0.000001:
        status_action = f"Closed position completely (sold all {sell_shares} shares)."
        if not dry_run:
            holdings.pop(holding_idx)
    else:
        new_total_cost = round(remaining_shares * avg_cost, 2)
        new_cost_thb = round(old_cost_thb - cost_thb, 2)
        status_action = f"Partial sell: {sell_shares} sold, {remaining_shares:.4f} remaining."
        if not dry_run:
            holding_match["shares"] = round(remaining_shares, 7)
            holding_match["total_cost_usd"] = new_total_cost
            holding_match["cost_thb"] = new_cost_thb

    ledger = load_ledger(ledger_path)
    ledger["cash"]["dime_usd"] = round(ledger["cash"]["dime_usd"] + net_rev_usd, 2)
    if not dry_run:
        trades_data["trades"].append(trade_entry)
        _atomic_write_many([
            (p_path, _json_text(portfolio_data)),
            (Path(trades_path) if trades_path else DEFAULT_TRADES_PATH, _json_text(trades_data)),
            (Path(ledger_path) if ledger_path else DEFAULT_LEDGER_PATH, _json_text(ledger, trailing_newline=True)),
        ])

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
    lines.append(f"- **Profit Factor:** `{summary['profit_factor_display']}`")
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
    from scripts.generate_master_report import generate_master_dashboard_data, generate_master_ledger_html
    return generate_master_ledger_html(generate_master_dashboard_data())
