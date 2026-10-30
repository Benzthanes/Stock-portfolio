#!/usr/bin/env python3
"""
Check the generated reports for bugs a browser does not show as errors.

The pages still render when these go wrong, so this reads reports/chart_data.js and
data/account_summary.json directly:
* every signal keeps its stop below price and its target above it (the portfolio is long only)
* an earnings-guarded signal carries guard_days between 0 and EARNINGS_GUARD_DAYS
* for each holding, the chart's latest signal agrees with days_to_earnings in account_summary.json
  (a stale indicator cache once kept LLY guarded after its report date)
* the last candle of every ticker is a weekday and not later than today's US market date

Usage:
    python3 scripts/check_reports.py                 # exit 0 when clean, 1 with one line per problem
    python3 scripts/check_reports.py --reports-dir reports --summary data/account_summary.json
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chart_data import _market_today  # noqa: E402
from src.scoring import EARNINGS_GUARD_DAYS  # noqa: E402
from src.trades import data_path  # noqa: E402


def load_charts(chart_js: Path) -> Dict[str, Any]:
    """Parse the `window.CHARTS_DATA = {...}` object from chart_data.js."""
    text = chart_js.read_text(encoding="utf-8")
    start = text.index("window.CHARTS_DATA")
    data, _ = json.JSONDecoder().raw_decode(text, text.index("{", start))
    return data


def check(charts: Dict[str, Any], positions: List[Dict[str, Any]], market_today: str) -> List[str]:
    problems = []
    for ticker, chart in charts.items():
        signals = chart.get("ai_signals") or []
        for sig in signals:
            price, sl, tp = sig.get("price"), sig.get("stop_loss"), sig.get("target")
            if price is not None and sl is not None and tp is not None and not sl < price < tp:
                problems.append(f"{ticker} {sig.get('time')} {sig.get('type')}: stop {sl} / price {price} / target {tp} not long-side")
        latest = signals[-1] if signals else {}
        if latest.get("earnings_guard"):
            gd = latest.get("guard_days")
            if gd is None or not 0 <= gd <= EARNINGS_GUARD_DAYS:
                problems.append(f"{ticker}: earnings guard on but guard_days is {gd}")
        candles = chart.get("candles") or []
        if candles:
            last = candles[-1].get("time")
            day = date.fromisoformat(last)
            if day.weekday() >= 5:
                problems.append(f"{ticker}: last candle {last} falls on a weekend")
            if last > market_today:
                problems.append(f"{ticker}: last candle {last} is after the US market date {market_today}")

    for pos in positions:
        ticker = pos.get("ticker")
        if ticker not in charts:
            continue
        latest = (charts[ticker].get("ai_signals") or [{}])[-1]
        days = pos.get("days_to_earnings")
        should_guard = days is not None and 0 <= days <= EARNINGS_GUARD_DAYS
        if bool(latest.get("earnings_guard")) != should_guard:
            problems.append(f"{ticker}: chart guard {bool(latest.get('earnings_guard'))} but account_summary days_to_earnings is {days}")
        elif should_guard and latest.get("guard_days") != int(round(days)):
            problems.append(f"{ticker}: chart guard_days {latest.get('guard_days')} but account_summary days_to_earnings is {days}")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check generated reports for silent data bugs.")
    parser.add_argument("--reports-dir", default=str(ROOT / "reports"), help="folder holding chart_data.js")
    parser.add_argument("--summary", default=None, help="account_summary.json (default: data dir)")
    args = parser.parse_args(argv)

    charts = load_charts(Path(args.reports_dir) / "chart_data.js")
    summary_path = Path(args.summary) if args.summary else data_path("account_summary.json")
    positions = json.loads(summary_path.read_text(encoding="utf-8")).get("positions", [])
    problems = check(charts, positions, _market_today())
    for p in problems:
        print(p)
    print(f"check_reports: {len(charts)} tickers, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
