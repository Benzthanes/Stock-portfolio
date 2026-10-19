#!/usr/bin/env python3
"""
Rebuild THB cost basis (cost_thb) from the buy slips.

Holdings in data/portfolio.json and closed trades in data/trades.json were recorded with
cost_thb = USD cost x 33.62. Slips paid from Dime! Save (THB) show the baht actually paid,
so that part is replaced with the slip amount. Slips paid from Dime! USD carry no baht figure,
so that part stays at --usd-fx (default 33.62, the rate the records were made with).

Buys (slips) and sells (data/trades.json) for each ticker are replayed in date order with
average cost: a sell removes the same fraction of the THB-paid and USD-paid parts.

Usage:
    python3 scripts/reconcile_cost_thb.py            # dry run, prints the plan, writes nothing
    python3 scripts/reconcile_cost_thb.py --apply    # writes portfolio.json and trades.json (backup first)
    python3 scripts/reconcile_cost_thb.py --apply --force   # also writes tickers whose slip shares do not match
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate_master_report import load_ocr_buy_orders
from src.fx import FALLBACK_USDTHB
from src.trades import _atomic_write_many, _json_text, data_path, load_ledger, parse_trade_date

SHARE_TOLERANCE = 1e-4


class Position:
    """Shares and cost split by how they were paid, so a sell can remove each part pro rata."""

    def __init__(self) -> None:
        self.shares = 0.0
        self.thb_paid = 0.0
        self.usd_paid = 0.0

    def buy(self, shares: float, amt_usd: float, amt_thb: Optional[float]) -> None:
        self.shares += shares
        if amt_thb:
            self.thb_paid += amt_thb
        else:
            self.usd_paid += amt_usd

    def sell(self, shares: float) -> Tuple[float, float]:
        frac = min(1.0, shares / self.shares) if self.shares > 0 else 0.0
        thb, usd = self.thb_paid * frac, self.usd_paid * frac
        self.shares -= shares
        self.thb_paid -= thb
        self.usd_paid -= usd
        return thb, usd


def cost_thb(thb_paid: float, usd_paid: float, usd_fx: float) -> float:
    return round(thb_paid + usd_paid * usd_fx, 2)


def load_events(trades: List[Dict[str, Any]]) -> Tuple[Dict[str, list], List[str]]:
    slips = load_ocr_buy_orders() + load_ledger(str(data_path("ledger.json")))["buy_orders"]
    events: Dict[str, list] = defaultdict(list)
    problems = []
    for o in slips:
        d = parse_trade_date(o.get("date"))
        if d is None:
            problems.append(f"slip {o.get('fn')} {o.get('ticker')}: unreadable date {o.get('date')!r}")
            continue
        thb = o.get("amt_thb") if "THB" in str(o.get("account", "")) else None
        events[o["ticker"]].append((d, 0, "buy", o))
        if thb is None and not o.get("amt_usd"):
            problems.append(f"slip {o.get('fn')} {o['ticker']}: no USD or THB amount")
        o["_thb"] = thb
    for i, t in enumerate(trades):
        if t.get("action") != "SELL":
            continue
        d = parse_trade_date(t.get("date"))
        if d is None:
            problems.append(f"trade {t.get('id')}: unreadable date {t.get('date')!r}")
            continue
        events[t["ticker"]].append((d, 1, "sell", i))
    for evs in events.values():
        evs.sort(key=lambda e: (e[0], e[1]))
    return events, problems


def plan(usd_fx: float) -> Dict[str, Any]:
    portfolio = json.loads(data_path("portfolio.json").read_text(encoding="utf-8"))
    trades_data = json.loads(data_path("trades.json").read_text(encoding="utf-8"))
    trades = trades_data["trades"]
    events, problems = load_events(trades)

    trade_rows, holding_rows = [], []
    positions: Dict[str, Position] = {}
    for ticker, evs in events.items():
        pos = positions.setdefault(ticker, Position())
        for _, _, kind, item in evs:
            if kind == "buy":
                pos.buy(float(item["shares"]), float(item.get("amt_usd") or 0.0), item["_thb"])
                continue
            t = trades[item]
            held_before = pos.shares
            thb, usd = pos.sell(float(t["shares"]))
            new = cost_thb(thb, usd, usd_fx)
            ok = held_before + SHARE_TOLERANCE >= float(t["shares"])
            trade_rows.append({
                "index": item, "id": t["id"], "ticker": ticker, "shares": t["shares"], "slip_shares": round(held_before, 7),
                "old": t.get("cost_thb"), "new": new, "thb_part": round(thb, 2), "usd_part": round(usd, 2),
                "new_pl": round(float(t.get("revenue_thb", 0.0)) - new, 2), "ok": ok,
            })

    for h in portfolio["holdings"]:
        pos = positions.get(h["ticker"], Position())
        new = cost_thb(pos.thb_paid, pos.usd_paid, usd_fx)
        holding_rows.append({
            "ticker": h["ticker"], "shares": h["shares"], "slip_shares": round(pos.shares, 7),
            "old": h.get("cost_thb"), "new": new, "thb_part": round(pos.thb_paid, 2), "usd_part": round(pos.usd_paid, 2),
            "ok": abs(pos.shares - float(h["shares"])) <= SHARE_TOLERANCE,
        })
    return {"portfolio": portfolio, "trades_data": trades_data, "holdings": holding_rows, "trades": trade_rows, "problems": problems}


def print_plan(p: Dict[str, Any], usd_fx: float) -> None:
    def table(title: str, rows: List[Dict[str, Any]], key: str) -> None:
        print(f"\n{title}")
        print(f"  {'':24} {'shares':>12} {'slip shares':>12} {'THB paid':>11} {'USD paid':>10} {'old cost_thb':>13} {'new cost_thb':>13} {'change':>10}  status")
        for r in rows:
            change = r["new"] - float(r["old"] or 0.0)
            status = "OK" if r["ok"] else "SHARES MISMATCH (skipped unless --force)"
            print(f"  {r[key]:24} {r['shares']:>12.4f} {r['slip_shares']:>12.4f} {r['thb_part']:>11,.2f} {r['usd_part']:>10,.2f} "
                  f"{float(r['old'] or 0):>13,.2f} {r['new']:>13,.2f} {change:>+10,.2f}  {status}")
    print(f"USD-paid slips are valued at {usd_fx} THB/USD.")
    table("Holdings (data/portfolio.json)", p["holdings"], "ticker")
    table("Closed trades (data/trades.json)", p["trades"], "id")
    for r in p["trades"]:
        print(f"  {r['id']}: realized_pl_thb becomes {r['new_pl']:,.2f}")
    for msg in p["problems"]:
        print(f"  ! {msg}")
    total = sum(r["new"] - float(r["old"] or 0) for r in p["holdings"] if r["ok"])
    print(f"\nTotal holdings cost_thb change (OK rows): {total:+,.2f} THB")


def apply(p: Dict[str, Any], force: bool) -> List[str]:
    changed = []
    by_ticker = {r["ticker"]: r for r in p["holdings"]}
    for h in p["portfolio"]["holdings"]:
        r = by_ticker[h["ticker"]]
        if (r["ok"] or force) and h.get("cost_thb") != r["new"]:
            h["cost_thb"] = r["new"]
            changed.append(h["ticker"])
    trades = p["trades_data"]["trades"]
    for r in p["trades"]:
        t = trades[r["index"]]
        if (r["ok"] or force) and t.get("cost_thb") != r["new"]:
            t["cost_thb"] = r["new"]
            t["realized_pl_thb"] = r["new_pl"]
            changed.append(r["id"])
    if not changed:
        return changed
    backup = data_path(f".backups/cost_thb_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup.mkdir(parents=True, exist_ok=True)
    for name in ("portfolio.json", "trades.json"):
        shutil.copy2(data_path(name), backup / name)
    _atomic_write_many([
        (data_path("portfolio.json"), _json_text(p["portfolio"])),
        (data_path("trades.json"), _json_text(p["trades_data"])),
    ])
    print(f"\nBackup: {backup}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild cost_thb from buy slips (dry run unless --apply).")
    parser.add_argument("--apply", action="store_true", help="write data/portfolio.json and data/trades.json")
    parser.add_argument("--force", action="store_true", help="also write rows whose slip shares do not match")
    parser.add_argument("--usd-fx", type=float, default=FALLBACK_USDTHB, help="THB/USD for slips paid from Dime! USD")
    args = parser.parse_args()

    p = plan(args.usd_fx)
    print_plan(p, args.usd_fx)
    if not args.apply:
        print("\nDry run. Nothing was written. Re-run with --apply to write.")
        return 0
    changed = apply(p, args.force)
    print(f"Updated {len(changed)} rows: {', '.join(changed) or 'none'}. Run `python3 portfolio.py --all` to refresh the reports.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
