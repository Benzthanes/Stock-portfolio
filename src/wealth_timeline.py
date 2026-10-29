"""
Daily Wealth & Net Asset Value (NAV) Timeline Engine.
Reconstructs day-by-day total portfolio net worth (Stock Equity + Cash)
and net deposited capital from the very first deposit date (2026-02-02) to present.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.fx import FALLBACK_USDTHB

MONTH_MAP = {
    "มค": 1, "กพ": 2, "มีค": 3, "เมย": 4, "พค": 5, "มิย": 6,
    "กค": 7, "สค": 8, "กย": 9, "ตค": 10, "พย": 11, "ธค": 12
}


def parse_wealth_datetime(date_val: Any) -> Tuple[int, int, int, int, int, int]:
    """
    Parse various datetime formats found in statement, OCR slips, and ledger.
    Supports:
    - Slash: 'DD/MM/YYYY' or 'DD/MM/YYYY HH:MM'
    - Thai: '14 ต.ค. 69 - 21:03 น.' or '17 มิ.ย. 69'
    - ISO: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
    Returns (year, month, day, hour, minute, second).
    """
    if not date_val:
        return (0, 0, 0, 0, 0, 0)
    s = str(date_val).strip()

    # ISO format YYYY-MM-DD
    m_iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?", s)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        hr = int(m_iso.group(4)) if m_iso.group(4) else 12
        mn = int(m_iso.group(5)) if m_iso.group(5) else 0
        sc = int(m_iso.group(6)) if m_iso.group(6) else 0
        return (y, m, d, hr, mn, sc)

    # DD/MM/YYYY
    m_slash = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m_slash:
        d, m, y = int(m_slash.group(1)), int(m_slash.group(2)), int(m_slash.group(3))
        tm = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
        hr = int(tm.group(1)) if tm else 12
        mn = int(tm.group(2)) if tm else 0
        sc = int(tm.group(3)) if tm and tm.group(3) else 0
        return (y, m, d, hr, mn, sc)

    # Thai string: e.g. '14 ต.ค. 69' or '3 ก.พ. 69 - 21:30 น.'
    m_th = re.search(r"(\d{1,2})\s+([^\s]+)\s+(\d{2,4})", s)
    if m_th:
        d = int(m_th.group(1))
        m_str = re.sub(r"[\.\s]", "", m_th.group(2))
        m = MONTH_MAP.get(m_str, 0)
        y = int(m_th.group(3))
        if y < 100:
            y += 2000 - 43
        elif y > 2500:
            y -= 543
        tm = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
        hr = int(tm.group(1)) if tm else 12
        mn = int(tm.group(2)) if tm else 0
        sc = int(tm.group(3)) if tm and tm.group(3) else 0
        return (y, m, d, hr, mn, sc)

    return (0, 0, 0, 0, 0, 0)


def dt_tuple_to_ymd(tup: Tuple[int, int, int, int, int, int]) -> str:
    """Format (y, m, d, ...) tuple to YYYY-MM-DD."""
    return f"{tup[0]:04d}-{tup[1]:02d}-{tup[2]:02d}"


def calculate_daily_wealth_timeline(
    summary_data: Dict[str, Any],
    candles_cache: Optional[Dict[str, Any]] = None,
    live_override: bool = True
) -> Dict[str, Any]:
    """
    Compute daily wealth time series starting from the first deposit date up to present.
    """
    if candles_cache is None:
        data_dir = Path(os.environ.get("FILTER_STOCK_DATA_DIR") or (Path(__file__).resolve().parent.parent / "data"))
        candles_path = data_dir / "candles_cache.json"
        if candles_path.exists():
            with open(candles_path, "r", encoding="utf-8") as f:
                candles_cache = json.load(f)
        else:
            candles_cache = {}

    buys = summary_data.get("buy_orders", [])
    trades = summary_data.get("closed_trades", [])
    cash_mov = summary_data.get("cash_movements", [])
    divs = summary_data.get("dividends_list", [])
    fx_rate = float(summary_data.get("fx_rate", FALLBACK_USDTHB) or FALLBACK_USDTHB)

    # 1. Price lookup map: prices[ticker][YYYY-MM-DD] = close_price
    prices: Dict[str, Dict[str, float]] = defaultdict(dict)
    for ticker, c_data in (candles_cache or {}).items():
        if isinstance(c_data, dict) and "candles" in c_data:
            for bar in c_data["candles"]:
                b_time = bar.get("time")
                b_close = bar.get("close")
                if b_time and b_close is not None:
                    prices[ticker][b_time] = float(b_close)

    # 2. Chronological cash movements
    chron_movs = sorted(cash_mov, key=lambda c: parse_wealth_datetime(c.get("date_str", "")))
    daily_save_bal: Dict[str, float] = {}
    deposit_events: Dict[str, float] = defaultdict(float)

    first_deposit_ymd = None
    for c in chron_movs:
        c_dt = parse_wealth_datetime(c.get("date_str", ""))
        if c_dt[0] == 0:
            continue
        d_str = dt_tuple_to_ymd(c_dt)
        daily_save_bal[d_str] = float(c.get("balance_thb", 0.0))

        c_type = c.get("type", "")
        amt = float(c.get("amount_thb", 0.0))
        if "ฝากเงิน" in c_type:
            deposit_events[d_str] += amt
            if first_deposit_ymd is None:
                first_deposit_ymd = d_str
        elif "โอนเงินออกไปต่างธนาคาร" in c_type:
            deposit_events[d_str] += amt

    if not first_deposit_ymd:
        first_deposit_ymd = "2026-02-02"

    # 3. Buy orders chronologically
    buy_by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for b in sorted(buys, key=lambda x: parse_wealth_datetime(x.get("date", ""))):
        b_dt = parse_wealth_datetime(b.get("date", ""))
        if b_dt[0] > 0:
            buy_by_date[dt_tuple_to_ymd(b_dt)].append(b)

    # 4. Closed trades chronologically
    sell_by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tr in sorted(trades, key=lambda x: parse_wealth_datetime(x.get("date", ""))):
        tr_dt = parse_wealth_datetime(tr.get("date", ""))
        if tr_dt[0] > 0:
            sell_by_date[dt_tuple_to_ymd(tr_dt)].append(tr)

    # 5. Dividends chronologically
    div_by_date: Dict[str, float] = defaultdict(float)
    for dv in divs:
        dv_dt = parse_wealth_datetime(dv.get("date", ""))
        if dv_dt[0] > 0:
            div_by_date[dt_tuple_to_ymd(dv_dt)] += float(dv.get("amount_usd", 0.0))

    # 6. Determine date bounds
    start_y, start_m, start_d = [int(x) for x in first_deposit_ymd.split("-")]
    start_dt = datetime(start_y, start_m, start_d)

    now_dt = datetime.now()
    end_dt = datetime(now_dt.year, now_dt.month, now_dt.day)
    if end_dt < start_dt:
        end_dt = start_dt

    # 7. Day-by-day simulation
    curr = start_dt
    shares_held: Dict[str, float] = defaultdict(float)
    last_price: Dict[str, float] = {}
    current_save_bal = 0.0
    current_usd_cash = 0.0
    cumulative_capital = 0.0

    points: List[Dict[str, Any]] = []
    ath_nav_thb = 0.0
    ath_date = first_deposit_ymd

    while curr <= end_dt:
        d_str = curr.strftime("%Y-%m-%d")

        # Capital updates
        if d_str in deposit_events:
            cumulative_capital += deposit_events[d_str]

        # Dime! Save balance update
        if d_str in daily_save_bal:
            current_save_bal = daily_save_bal[d_str]

        # Sales proceeds
        for tr in sell_by_date[d_str]:
            shares_held[tr["ticker"]] -= float(tr.get("shares", 0.0))
            current_usd_cash += float(tr.get("net_revenue_usd", 0.0))

        # Dividends
        if d_str in div_by_date:
            current_usd_cash += div_by_date[d_str]

        # Buys
        for b in buy_by_date[d_str]:
            shares_held[b["ticker"]] += float(b.get("shares", 0.0))
            if "USD" in str(b.get("account", "")):
                current_usd_cash = max(0.0, current_usd_cash - float(b.get("amt_usd", 0.0)))

        # Value stocks
        stock_val_usd = 0.0
        for t, sh in list(shares_held.items()):
            if sh > 0.000001:
                if d_str in prices[t]:
                    last_price[t] = prices[t][d_str]
                p = last_price.get(t, 0.0)
                stock_val_usd += sh * p

        stock_val_thb = stock_val_usd * fx_rate
        usd_cash_thb = current_usd_cash * fx_rate
        total_cash_thb = current_save_bal + usd_cash_thb
        nav_thb = stock_val_thb + total_cash_thb
        nav_usd = stock_val_usd + current_usd_cash + (current_save_bal / fx_rate)

        profit_thb = nav_thb - cumulative_capital
        profit_usd = nav_usd - (cumulative_capital / fx_rate)
        roi_pct = (profit_thb / cumulative_capital * 100.0) if cumulative_capital > 0 else 0.0

        if nav_thb > ath_nav_thb:
            ath_nav_thb = nav_thb
            ath_date = d_str

        points.append({
            "time": d_str,
            "nav_thb": round(nav_thb, 2),
            "nav_usd": round(nav_usd, 2),
            "capital_thb": round(cumulative_capital, 2),
            "capital_usd": round(cumulative_capital / fx_rate, 2),
            "stock_thb": round(stock_val_thb, 2),
            "stock_usd": round(stock_val_usd, 2),
            "cash_thb": round(total_cash_thb, 2),
            "cash_usd": round(current_usd_cash + (current_save_bal / fx_rate), 2),
            "profit_thb": round(profit_thb, 2),
            "profit_usd": round(profit_usd, 2),
            "roi_pct": round(roi_pct, 2)
        })

        curr += timedelta(days=1)

    # Live override on the final point to match live hero KPI exactly
    if live_override and points and summary_data.get("total_net_worth_thb"):
        live_net_thb = float(summary_data["total_net_worth_thb"])
        live_net_usd = float(summary_data.get("total_net_worth_usd", round(live_net_thb / fx_rate, 2)))
        live_cap_thb = float(summary_data.get("net_injected_capital_thb", cumulative_capital))
        live_stock_thb = float(summary_data.get("stock_market_val_thb", 0.0))
        live_stock_usd = float(summary_data.get("stock_market_val_usd", 0.0))
        live_cash_thb = float(summary_data.get("total_cash_thb", 0.0))
        live_profit_thb = float(summary_data.get("all_time_profit_thb", live_net_thb - live_cap_thb))
        live_roi_pct = float(summary_data.get("all_time_roi_pct", (live_profit_thb / live_cap_thb * 100.0) if live_cap_thb > 0 else 0.0))

        last_pt = points[-1]
        last_pt["nav_thb"] = round(live_net_thb, 2)
        last_pt["nav_usd"] = round(live_net_usd, 2)
        last_pt["capital_thb"] = round(live_cap_thb, 2)
        last_pt["capital_usd"] = round(live_cap_thb / fx_rate, 2)
        last_pt["stock_thb"] = round(live_stock_thb, 2)
        last_pt["stock_usd"] = round(live_stock_usd, 2)
        last_pt["cash_thb"] = round(live_cash_thb, 2)
        last_pt["cash_usd"] = round(live_cash_thb / fx_rate, 2)
        last_pt["profit_thb"] = round(live_profit_thb, 2)
        last_pt["profit_usd"] = round(live_profit_thb / fx_rate, 2)
        last_pt["roi_pct"] = round(live_roi_pct, 2)

        if live_net_thb > ath_nav_thb:
            ath_nav_thb = live_net_thb
            ath_date = last_pt["time"]

    latest_pt = points[-1] if points else {}

    return {
        "timeline": points,
        "summary": {
            "start_date": first_deposit_ymd,
            "end_date": latest_pt.get("time", ""),
            "total_days": len(points),
            "ath_nav_thb": round(ath_nav_thb, 2),
            "ath_date": ath_date,
            "current_nav_thb": latest_pt.get("nav_thb", 0.0),
            "current_nav_usd": latest_pt.get("nav_usd", 0.0),
            "current_capital_thb": latest_pt.get("capital_thb", 0.0),
            "current_profit_thb": latest_pt.get("profit_thb", 0.0),
            "current_roi_pct": latest_pt.get("roi_pct", 0.0),
        }
    }
