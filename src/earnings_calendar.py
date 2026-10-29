"""
Earnings Announcement Calendar.
Contains confirmed quarterly earnings release dates for portfolio stocks (2024-2026).
These dates represent actual press release and earnings call dates confirmed via official
corporate investor relations releases and regulatory filings, avoiding volume-based heuristics.
"""

import hashlib
import json
import sys
from typing import Dict, List, Any, Optional
from src.scoring import ETF_TICKERS

# Confirmed 3-year historical and scheduled earnings announcement dates (2024-2026).
# For stocks reporting Before Market Open (BMO), reaction occurs on the same calendar day.
# For stocks reporting After Market Close (AMC), reaction occurs on the next trading session.
CONFIRMED_EARNINGS_DATES: Dict[str, List[str]] = {
    "VRT": [
        # 2024-02-21: https://investors.vertiv.com/news-releases/news-details/2024/Vertiv-Reports-Fourth-Quarter-and-Full-Year-2023-Results-Provides-Strong-2024-Outlook/default.aspx
        "2024-02-21", "2024-04-24", "2024-07-24", "2024-10-23",
        "2025-02-12", "2025-04-23", "2025-07-30", "2025-10-22",
        "2026-02-11", "2026-04-22", "2026-07-29", "2026-10-28",
    ],
    "NOK": [
        "2024-01-25", "2024-04-18", "2024-07-18", "2024-10-17",
        "2025-01-30", "2025-04-24", "2025-07-24", "2025-10-23",
        "2026-01-29", "2026-04-23", "2026-07-23", "2026-10-22",
    ],
    "LLY": [
        # 2024-02-06: https://investor.lilly.com/news-releases/news-details/2024/Lilly-Reports-Strong-Fourth-Quarter-2023-Financial-Results-and-Provides-2024-Guidance/default.aspx
        "2024-02-06", "2024-04-30", "2024-08-08", "2024-10-30",
        "2025-02-06", "2025-05-01", "2025-08-07", "2025-10-30",
        "2026-02-04", "2026-04-30", "2026-08-05", "2026-10-29",
    ],
    "GOOGL": [
        "2024-01-30", "2024-04-25", "2024-07-23", "2024-10-29",
        "2025-02-04", "2025-04-24", "2025-07-23", "2025-10-29",
        # 2026-02-04: https://abc.xyz/investor/earnings/2025/q4/
        "2026-02-04", "2026-04-29", "2026-07-22", "2026-10-28",
    ],
    "BAC": [
        # 2024-01-12: https://newsroom.bankofamerica.com/content/newsroom/press-releases/2024/01/bank-of-america-reports-fourth-quarter-2023-financial-results.html
        "2024-01-12", "2024-04-16", "2024-07-16", "2024-10-15",
        "2025-01-16", "2025-04-15", "2025-07-16", "2025-10-15",
        "2026-01-14", "2026-04-15", "2026-07-14", "2026-10-14",
    ],
    "ABNB": [
        "2024-02-13", "2024-05-08", "2024-08-06", "2024-11-07",
        "2025-02-13", "2025-05-01", "2025-08-06", "2025-11-06",
        # 2026-02-12: https://news.airbnb.com/airbnb-fourth-quarter-and-full-year-2025-financial-results/
        "2026-02-12", "2026-05-07", "2026-08-06", "2026-11-05",
    ],
    "APP": [
        # 2024-02-14: https://investors.applovin.com/news/news-details/2024/AppLovin-Reports-Fourth-Quarter-and-Fiscal-Year-2023-Financial-Results/default.aspx
        "2024-02-14", "2024-05-08", "2024-08-07", "2024-11-06",
        "2025-02-12", "2025-05-07", "2025-08-06", "2025-11-05",
        "2026-02-11", "2026-05-06", "2026-08-05", "2026-11-04",
    ],
    "MNST": [
        "2024-02-28", "2024-05-02", "2024-08-06", "2024-11-07",
        "2025-02-27", "2025-05-08", "2025-08-07", "2025-11-06",
        # 2026-02-26: https://investors.monsterbevcorp.com/news-releases/news-release-details/monster-beverage-reports-2025-fourth-quarter-and-full-year-financial
        "2026-02-26", "2026-05-07", "2026-08-06", "2026-11-05",
    ],
    "NOW": [
        # 2024-01-24: https://investors.servicenow.com/news-and-events/press-releases/press-release-details/2024/ServiceNow-Reports-Fourth-Quarter-and-Full-Year-2023-Financial-Results/default.aspx
        "2024-01-24", "2024-04-24", "2024-07-24", "2024-10-23",
        "2025-01-29", "2025-04-23", "2025-07-23", "2025-10-29",
        "2026-01-28", "2026-04-22", "2026-07-22", "2026-10-28",
    ],
    "PLTR": [
        "2024-02-05", "2024-05-06", "2024-08-05", "2024-11-04",
        "2025-02-03", "2025-05-05", "2025-08-04", "2025-11-03",
        "2026-02-02", "2026-05-04", "2026-08-03", "2026-11-02",
    ],
    "VST": [
        # 2024-05-08: https://investor.vistracorp.com/2024-05-08-Vistra-Reports-First-Quarter-2024-Results
        "2024-02-28", "2024-05-08", "2024-08-08", "2024-11-07",
        "2025-02-27", "2025-05-07", "2025-08-07", "2025-11-06",
        "2026-02-26", "2026-05-07", "2026-08-07", "2026-11-06",
    ],
    "SKHY": [
        # 2024-01-25: https://news.skhynix.com/sk-hynix-reports-4q23-financial-results/
        "2024-01-25", "2024-04-25", "2024-07-25", "2024-10-23",
        "2025-01-22", "2025-04-23", "2025-07-23", "2025-10-28",
        "2026-01-28", "2026-04-22", "2026-07-29", "2026-10-28",
    ],
    "NVDA": [
        "2024-02-21", "2024-05-22", "2024-08-28", "2024-11-20",
        "2025-02-26", "2025-05-28", "2025-08-27", "2025-11-19",
        # 2026-11-17: https://nvidianews.nvidia.com/news/nvidia-to-host-conference-call-for-third-quarter-financial-results-fy27
        "2026-02-25", "2026-05-20", "2026-08-26", "2026-11-17",
    ],
    "AAPL": [
        "2024-02-01", "2024-05-02", "2024-08-01", "2024-10-31",
        "2025-01-30", "2025-05-01", "2025-07-31", "2025-10-30",
        "2026-01-29", "2026-04-30", "2026-07-30", "2026-11-02",
    ],
    "MSFT": [
        "2024-01-30", "2024-04-25", "2024-07-30", "2024-10-30",
        "2025-01-29", "2025-04-30", "2025-07-30", "2025-10-29",
        "2026-01-28", "2026-04-29", "2026-07-29", "2026-10-28",
    ],
    "AMZN": [
        "2024-02-01", "2024-04-30", "2024-08-01", "2024-10-31",
        "2025-02-06", "2025-05-01", "2025-07-31", "2025-10-30",
        "2026-02-05", "2026-04-29", "2026-07-30", "2026-10-29",
    ],
    "JPM": [
        "2024-01-12", "2024-04-12", "2024-07-12", "2024-10-11",
        "2025-01-15", "2025-04-11", "2025-07-15", "2025-10-14",
        "2026-01-13", "2026-04-14", "2026-07-14", "2026-10-13",
    ],
    "SPCX": [
        # เข้าตลาด IPO เมื่อ 2026-06-12 (มีงบได้เฉพาะหลังวัน IPO)
        # 2026-08-04: Direxion 2026-08-06 "SpaceX reports its first quarterly results as a public company on August 4" (อ้างผ่าน https://www.stocktitan.net/news/SPCX/)
        # 2026-10-20: https://teslanorth.com/2026/10/16/spacex-q3-2026-results-webcast/
        "2026-08-04", "2026-10-20",
    ],
}

# Timing of quarterly earnings announcements:
# "amc" = After Market Close (reaction on next trading session idx + 1 vs idx)
# "bmo" = Before Market Open (reaction on same calendar trading session idx vs idx - 1)
CONFIRMED_EARNINGS_TIMING: Dict[str, Any] = {
    "VRT": "bmo",     # ยืนยัน IR (Vertiv ประกาศก่อนเปิดตลาด 07:00 ET, Call 11:00 ET - Q3 2024: https://www.businesswire.com/news/home/20241023253723/en/Vertiv-Reports-Strong-Third-Quarter-2024-Results-and-Raises-Full-Year-Guidance)
    "NOK": "bmo",     # ยืนยัน IR (Nokia ประกาศ 08:00 EET/02:00 ET ก่อนเปิดตลาดสหรัฐฯ - Q3 2024: https://www.nokia.com/about-us/investors/results-reports/financial-results/q3-2024/)
    "LLY": "bmo",     # ยืนยัน IR (Eli Lilly ประกาศก่อนเปิดตลาด - Q4 2023: https://investor.lilly.com/news-releases/news-details/2024/Lilly-Reports-Strong-Fourth-Quarter-2023-Financial-Results-and-Provides-2024-Guidance/default.aspx)
    "GOOGL": "amc",   # ยืนยัน IR (Alphabet ประกาศหลังปิดตลาด - Q4 2025: https://abc.xyz/investor/earnings/2025/q4/)
    "BAC": "bmo",     # ยืนยัน IR (Bank of America ประกาศก่อนเปิดตลาด 06:45 ET - Q4 2023: https://newsroom.bankofamerica.com/content/newsroom/press-releases/2024/01/bank-of-america-reports-fourth-quarter-2023-financial-results.html)
    "ABNB": "amc",    # ยืนยัน IR (Airbnb ประกาศหลังปิดตลาด - Q4 2025: https://news.airbnb.com/airbnb-fourth-quarter-and-full-year-2025-financial-results/)
    "APP": "amc",     # ยืนยัน IR (AppLovin ประกาศหลังปิดตลาด - Q4 2023: https://investors.applovin.com/news/news-details/2024/AppLovin-Reports-Fourth-Quarter-and-Fiscal-Year-2023-Financial-Results/default.aspx)
    "MNST": "amc",    # ยืนยัน IR (Monster Beverage ประกาศหลังปิดตลาด - Q4 2025: https://investors.monsterbevcorp.com/news-releases/news-release-details/monster-beverage-reports-2025-fourth-quarter-and-full-year-financial)
    "NOW": "amc",     # ยืนยัน IR (ServiceNow ประกาศหลังปิดตลาด - Q4 2023: https://investors.servicenow.com/news-and-events/press-releases/press-release-details/2024/ServiceNow-Reports-Fourth-Quarter-and-Full-Year-2023-Financial-Results/default.aspx)
    "PLTR": "amc",    # ยืนยัน IR (Palantir ประกาศหลังปิดตลาด 17:00 ET - Q3 2024: https://investors.palantir.com/news-details/2024/Palantir-Reports-Third-Quarter-2024-Revenue-Growth-of-30-YOY-GAAP-Operating-Margin-of-16/default.aspx)
    "VST": "bmo",     # ยืนยัน IR (Vistra ประกาศก่อนเปิดตลาด, Call 10:00 ET - Q1 2024: https://investor.vistracorp.com/2024-04-15-Vistra-to-Report-First-Quarter-Results-on-May-8,-2024)
    "SKHY": "bmo",    # ยืนยัน IR (SK hynix ประกาศ 09:00 KST ก่อนเปิดตลาดสหรัฐฯ - Q4 2023: https://news.skhynix.com/sk-hynix-reports-4q23-financial-results/)
    "NVDA": "amc",    # ยืนยัน IR (NVIDIA ประกาศหลังปิดตลาด, Call 17:00 ET - Q3 FY27: https://nvidianews.nvidia.com/news/nvidia-to-host-conference-call-for-third-quarter-financial-results-fy27)
    "AAPL": "amc",    # ยืนยัน IR (Apple ประกาศหลังปิดตลาด 16:30 ET, Call 17:00 ET - Q4 FY24: https://www.apple.com/newsroom/2024/10/apple-reports-fourth-quarter-results/)
    "MSFT": "amc",    # ยืนยัน IR (Microsoft ประกาศหลังปิดตลาด 16:05 ET, Call 17:30 ET - Q4 FY24: https://www.microsoft.com/en-us/investor/earnings/fy-2024-q4/press-release-webcast)
    "AMZN": "amc",    # ยืนยัน IR (Amazon ประกาศหลังปิดตลาด ~16:00 ET, Call 17:30 ET - Q3 2024: https://ir.aboutamazon.com/news-release/news-release-details/2024/Amazon.com-Announces-Third-Quarter-Results/default.aspx)
    "JPM": "bmo",     # ยืนยัน IR (JPMorgan Chase ประกาศก่อนเปิดตลาด ~07:00 ET, Call 08:30 ET - Q3 2024: https://www.jpmorganchase.com/ir/news/2024/3q24-earnings)
    "SPCX": "amc",    # แหล่งรอง ยังไม่มี IR ทางการ (SpaceX ประกาศหลังปิดตลาด webcast 15:30 CT - Q3 2026: https://teslanorth.com/2026/10/16/spacex-q3-2026-results-webcast/)
}

_LOGGED_UNKNOWN_TIMING = set()


def get_confirmed_earnings_dates(ticker: str) -> List[str]:
    """
    Returns confirmed quarterly earnings announcement dates for the given ticker.
    Returns an empty list for ETFs or unlisted tickers.
    """
    if not ticker:
        return []
    ticker = ticker.strip().upper()
    if ticker in ETF_TICKERS:
        return []
    return CONFIRMED_EARNINGS_DATES.get(ticker, [])


def get_earnings_timing(ticker: str, date: Optional[str] = None) -> Optional[str]:
    """
    Returns confirmed earnings announcement timing for the given ticker:
    'amc' (After Market Close) or 'bmo' (Before Market Open).
    Supports either string timing ('bmo'/'amc') or date-specific dict mapping {date: 'bmo'}.
    Returns None if ticker timing is unknown or unlisted.
    """
    if not ticker:
        return None
    val = CONFIRMED_EARNINGS_TIMING.get(ticker.strip().upper(), None)
    if isinstance(val, dict):
        if date:
            return val.get(date, None)
        return next(iter(val.values()), None)
    return val


def get_earnings_calendar_hash() -> str:
    """
    Returns an 8-character deterministic MD5 hash of CONFIRMED_EARNINGS_DATES and timings.
    Used for cache invalidation when the earnings calendar is updated.
    """
    payload = json.dumps({"dates": CONFIRMED_EARNINGS_DATES, "timing": CONFIRMED_EARNINGS_TIMING}, sort_keys=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:8]


def calculate_confirmed_earnings_reaction(
    candles: List[Dict[str, Any]],
    dates: List[str],
    timing: Optional[str] = None,
    ticker: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Calculates the exact earnings announcement price reaction percentage
    for each confirmed announcement date present in historical candle data.
    - Explicit timing overrides ticker default if provided.
    - Supports per-date timing overrides if configured in CONFIRMED_EARNINGS_TIMING.
    - For BMO: reaction occurs on the same calendar day (idx vs idx - 1).
    - For AMC: reaction occurs on the next trading session (idx + 1 vs idx).
      If idx + 1 does not exist yet (announcement pending or occurred today after close),
      the event is skipped to prevent placing premature markers.
    - If timing is unknown (None), reaction % is omitted (None) and logged once.
    """
    if not candles or len(candles) < 2 or not dates:
        return []

    # Map candle time to index
    time_to_idx = {c["time"]: i for i, c in enumerate(candles)}
    last_candle_date = candles[-1]["time"]

    events: List[Dict[str, Any]] = []

    for d in sorted(dates):
        # If the announcement date is beyond the latest historical candle,
        # it is upcoming or pending today's close; do not emit a premature marker.
        if d > last_candle_date:
            continue

        if timing is not None:
            timing_mode = timing.lower()
        elif ticker:
            timing_mode = get_earnings_timing(ticker, d)
        else:
            timing_mode = None

        if timing_mode is None:
            t_key = ticker.strip().upper() if ticker else "unknown"
            if t_key not in _LOGGED_UNKNOWN_TIMING:
                _LOGGED_UNKNOWN_TIMING.add(t_key)
                print(f"[earnings_calendar] Warning: Unknown earnings timing for {t_key}, reaction % omitted", file=sys.stderr)

        idx = time_to_idx.get(d)
        if idx is None:
            # If date fell on non-trading day, snap to next trading session
            for i, c in enumerate(candles):
                if c["time"] >= d:
                    idx = i
                    break

        if idx is None:
            continue

        if timing_mode is None:
            events.append({
                "time": candles[idx]["time"],
                "reaction_pct": None,
                "text": "🗓️ งบ",
                "color": "#94a3b8",
                "position": "aboveBar",
            })
        elif timing_mode == "amc":
            # After Market Close: market reaction happens on next trading session idx + 1
            if idx + 1 >= len(candles):
                # Reaction bar has not closed yet (announcement tonight or pending next open)
                continue
            cur = candles[idx + 1]
            base = candles[idx]
            base_close = base.get("close", 0)
            if base_close > 0:
                pct = round(((cur["close"] - base_close) / base_close) * 100, 1)
                events.append({
                    "time": cur["time"],
                    "reaction_pct": pct,
                    "text": f"🗓️ {pct:+.1f}%",
                    "color": "#10b981" if pct >= 0 else "#f43f5e",
                    "position": "belowBar" if pct >= 0 else "aboveBar",
                })
        else:
            # Before Market Open: market reaction happens on same trading session idx vs idx - 1
            if idx > 0:
                cur = candles[idx]
                prev = candles[idx - 1]
                prev_close = prev.get("close", 0)
                if prev_close > 0:
                    pct = round(((cur["close"] - prev_close) / prev_close) * 100, 1)
                    events.append({
                        "time": cur["time"],
                        "reaction_pct": pct,
                        "text": f"🗓️ {pct:+.1f}%",
                        "color": "#10b981" if pct >= 0 else "#f43f5e",
                        "position": "belowBar" if pct >= 0 else "aboveBar",
                    })

    events.sort(key=lambda x: x["time"])
    return events

