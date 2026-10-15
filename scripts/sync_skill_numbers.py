#!/usr/bin/env python3
"""
Refresh the readable counts in .agents/skills/master/SKILL.md from the master dashboard data.
Only the numbers change. Running it twice on the same data produces no diff.

Usage: python3 scripts/sync_skill_numbers.py [--summary data/account_summary.json] [--skill PATH]
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SKILL_PATH = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "master" / "SKILL.md"
DEFAULT_SUMMARY_PATH = Path("data/account_summary.json")


def _pct(value):
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def skill_number_rules(data):
    ts = data["trades_summary"]
    buys = str(len(data["buy_orders"]))
    divs = str(len(data["dividends_list"]))
    moves = str(len(data["cash_movements"]))
    return [
        (r"(all )\d+( buy orders)", rf"\g<1>{buys}\g<2>"),
        (r"(\(Buy Orders History\):\*\* )\d+( ไม้)", rf"\g<1>{buys}\g<2>"),
        (r"(- )\d+( winning sales)", rf"\g<1>{ts['winning_trades']}\g<2>"),
        (r"\(\d+( ไม้ Win Rate )[\d.]+%\)", rf"({ts['total_trades']}\g<1>{_pct(ts['win_rate_pct'])}%)"),
        (r"\(\d+( payments)", rf"({divs}\g<1>"),
        (r"\(\d+( ครั้ง\)\.)", rf"({divs}\g<1>"),
        (r"\(\d+( transactions)", rf"({moves}\g<1>"),
        (r"(Dime! Save )\d+( รายการ)", rf"\g<1>{moves}\g<2>"),
        (r"\([\d,]+\.\d{2}( บาท\))", f"({data['net_injected_capital_thb']:,.2f}\\g<1>"),
    ]


def sync_skill_numbers(data, skill_path=None):
    """Rewrite the counts in SKILL.md. Returns True when the file changed."""
    path = Path(skill_path) if skill_path else DEFAULT_SKILL_PATH
    if not path.exists():
        print(f"Warning: {path} not found, skipping skill number sync.", file=sys.stderr)
        return False
    text = path.read_text(encoding="utf-8")
    new_text = text
    for pattern, repl in skill_number_rules(data):
        new_text, n = re.subn(pattern, repl, new_text)
        if n != 1:
            print(f"Warning: pattern {pattern!r} matched {n} times in {path}.", file=sys.stderr)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Refresh hardcoded counts in the master SKILL.md")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH), help="Master data JSON (default: data/account_summary.json)")
    parser.add_argument("--skill", default=str(DEFAULT_SKILL_PATH), help="SKILL.md to update")
    args = parser.parse_args()
    data = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    changed = sync_skill_numbers(data, args.skill)
    print(f"{args.skill}: {'updated' if changed else 'already up to date'}")


if __name__ == "__main__":
    main()
