"""
Unified Fundamental Scoring
Single source of truth for fundamental points, grades and ETF detection used by
the Dip screener, Portfolio health/star rating and Recovery analyzer.
"""

from typing import Dict, List, NamedTuple, Optional, TypedDict

EARNINGS_GUARD_DAYS = 14.0
ETF_TICKERS = frozenset({"VOO", "SPY", "QQQ", "QQQI"})
ETF_FALLBACK_SECTORS = ("Miscellaneous", "Other / Diversified")


class Band(NamedTuple):
    lo: Optional[float]
    hi: Optional[float]
    points: int
    label: str


FUNDAMENTAL_RULES: Dict[str, tuple] = {
    "rev_growth_yoy": (5, [
        Band(20.0, None, 5, "Rev Growth {v:+.0f}% 🚀"),
        Band(10.0, 20.0, 4, "Rev Growth {v:+.0f}%"),
        Band(0.0, 10.0, 2, "Slow Rev Growth {v:+.1f}%"),
        Band(None, 0.0, 0, "⚠️ Neg Rev Trap ({v:+.1f}%)"),
    ]),
    "net_inc_growth_yoy": (5, [
        Band(25.0, None, 5, "Net Income {v:+.0f}% 🚀"),
        Band(10.0, 25.0, 4, "Net Income {v:+.0f}%"),
        Band(0.0, 10.0, 2, "Slow Net Income {v:+.1f}%"),
        Band(None, 0.0, 0, "⚠️ Net Income Shrinking ({v:+.1f}%)"),
    ]),
    "roe": (5, [
        Band(25.0, None, 5, "Elite ROE ({v:.0f}%) 🏆"),
        Band(15.0, 25.0, 4, "High ROE ({v:.0f}%) 💎"),
        Band(0.0, 15.0, 2, "Low ROE ({v:.1f}%)"),
        Band(None, 0.0, 0, "⚠️ Neg ROE Trap ({v:.1f}%)"),
    ]),
    "peg": (4, [
        Band(None, 0.0, 0, "⚠️ Negative PEG {v:.2f} (กำไรหดตัว)"),
        Band(0.0, 1.0, 4, "Attractive PEG {v:.2f} 💎"),
        Band(1.0, 1.5, 3, "Fair PEG {v:.2f}"),
        Band(1.5, 2.5, 2, "Stretched PEG {v:.2f}"),
        Band(2.5, 3.0, 1, "Rich PEG {v:.2f}"),
        Band(3.0, None, 0, "⚠️ High PEG Overvalued {v:.2f}"),
    ]),
    "debt_to_equity": (3, [
        Band(None, 0.0, 0, "⚠️ Negative Equity (D/E {v:.2f})"),
        Band(0.0, 0.8, 3, "Safe Debt (D/E {v:.2f}) 🛡️"),
        Band(0.8, 1.5, 2, "Moderate Debt (D/E {v:.2f})"),
        Band(1.5, 2.5, 1, "Elevated Debt (D/E {v:.2f})"),
        Band(2.5, None, 0, "⚠️ High Debt Risk (D/E {v:.2f})"),
    ]),
    "fcf": (3, [
        Band(0.0, None, 3, "FCF Cash Cow 💵"),
        Band(None, 0.0, 0, "⚠️ Negative FCF"),
    ]),
}
MAX_FUNDAMENTAL_POINTS = sum(max_pts for max_pts, _ in FUNDAMENTAL_RULES.values())

# Bank leverage is the business model, so D/E carries no health signal there.
SECTOR_SKIPPED_METRICS = {"Finance": frozenset({"debt_to_equity"})}

GRADE_BANDS = [(85.0, "A+"), (70.0, "A"), (55.0, "B"), (40.0, "C"), (0.0, "F")]
STARS_BY_GRADE = {"A+": 5, "A": 4, "B": 3, "C": 2, "F": 1}
MIN_COVERAGE_FOR_TOP_GRADE = 0.7


class FundamentalScore(TypedDict):
    applicable: bool
    points: float
    max_points: int
    pct: Optional[float]
    coverage: float
    grade: str
    metrics: Dict[str, dict]
    reasons: List[str]


def is_etf(ticker: str, sector: Optional[str] = None, rev_growth_yoy: Optional[float] = None) -> bool:
    return ticker in ETF_TICKERS or (sector in ETF_FALLBACK_SECTORS and rev_growth_yoy is None)


def find_band(bands: List[Band], value: float) -> Band:
    for band in bands:
        if (band.lo is None or value >= band.lo) and (band.hi is None or value < band.hi):
            return band
    raise ValueError(f"No band covers value {value}")


def grade_for(pct: float, coverage: float) -> str:
    grade = next(g for floor, g in GRADE_BANDS if pct >= floor)
    if coverage < MIN_COVERAGE_FOR_TOP_GRADE and grade in ("A+", "A"):
        return "B"
    return grade


def score_fundamentals(
    ticker: str,
    sector: Optional[str],
    rev_growth_yoy: Optional[float],
    net_inc_growth_yoy: Optional[float],
    roe: Optional[float],
    peg: Optional[float],
    debt_to_equity: Optional[float],
    fcf: Optional[float],
) -> FundamentalScore:
    if is_etf(ticker, sector, rev_growth_yoy):
        return FundamentalScore(
            applicable=False, points=0.0, max_points=0, pct=None, coverage=0.0, grade="ETF",
            metrics={}, reasons=["Index ETF (ไม่ประเมินงบรายบริษัท)"],
        )

    values = {
        "rev_growth_yoy": rev_growth_yoy,
        "net_inc_growth_yoy": net_inc_growth_yoy,
        "roe": roe,
        "peg": peg,
        "debt_to_equity": debt_to_equity,
        "fcf": fcf,
    }
    for name in SECTOR_SKIPPED_METRICS.get(sector or "", frozenset()):
        values[name] = None
    metrics = _score_table(FUNDAMENTAL_RULES, values)

    points = float(sum(m["points"] for m in metrics.values()))
    max_points = sum(m["max"] for m in metrics.values())
    coverage = round(max_points / MAX_FUNDAMENTAL_POINTS, 2)
    pct = round(points / max_points * 100.0, 1) if max_points else None
    return FundamentalScore(
        applicable=True,
        points=points,
        max_points=max_points,
        pct=pct,
        coverage=coverage,
        grade=grade_for(pct, coverage) if pct is not None else "N/A",
        metrics=metrics,
        reasons=[m["label"] for m in metrics.values()],
    )


# Timing rules keep only the states that separated outcomes in scripts/backtest_scoring.py
# (173 tickers, 2023-2026, see data/backtest_scoring.json). EMA200 distance moved the 60-day
# drawdown (0..10% above: about 1.6 points shallower, more than 10% below: 2.7 points deeper).
# An RSI hook from below 40 added about 0.8% to the 20-day return, so it is reported as an
# entry signal rather than folded into holding health. VFI, WAE, Squeeze, UT Bot, Chandelier,
# WaveTrend and Lorentzian showed no stable edge, so they earn no points.
TIMING_RULES: Dict[str, tuple] = {
    "ema200_dist": (6, [
        Band(None, -10.0, 0, "⚠️ หลุด EMA200 เกิน 10% ({v:+.1f}%) เสี่ยง Drawdown ลึก"),
        Band(-10.0, -3.0, 2, "ต่ำกว่า EMA200 ({v:+.1f}%)"),
        Band(-3.0, 0.0, 4, "ทดสอบ EMA200 จากด้านล่าง ({v:+.1f}%)"),
        Band(0.0, 10.0, 6, "Value Zone เหนือ EMA200 ({v:+.1f}%) 💎"),
        Band(10.0, None, 3, "ยืดเหนือ EMA200 ({v:+.1f}%) รอย่อ"),
    ]),
}
MAX_TIMING_POINTS = sum(max_pts for max_pts, _ in TIMING_RULES.values())
PILLAR_WEIGHTS = {"fundamental": 0.6, "timing": 0.4}
ETF_STARS = 4


class TimingScore(TypedDict):
    entry_signal: bool
    points: float
    max_points: int
    pct: Optional[float]
    coverage: float
    metrics: Dict[str, dict]
    reasons: List[str]


class StockScore(TypedDict):
    total: Optional[float]
    grade: str
    stars: int
    pillars: Dict[str, Optional[float]]
    coverage: float
    earnings_guard: bool
    reasons: List[str]
    fundamental: FundamentalScore
    timing: TimingScore


def format_score(score: Optional["StockScore"]) -> str:
    """Short label shared by the Markdown and HTML reports, e.g. "เกรด A · 75/100 ⤴"."""
    if not score:
        return "-"
    label = f"เกรด {score['grade']}"
    if score.get("total") is not None and score["grade"] != "ETF":
        label += f" · {score['total']:.0f}/100"
    if score.get("timing", {}).get("entry_signal"):
        label += " ⤴"
    return label


def _score_table(rules: Dict[str, tuple], values: Dict[str, Optional[float]]) -> Dict[str, dict]:
    metrics: Dict[str, dict] = {}
    for name, (max_pts, bands) in rules.items():
        value = values.get(name)
        if value is None:
            continue
        band = find_band(bands, value)
        metrics[name] = {"value": value, "points": band.points, "max": max_pts, "label": band.label.format(v=value)}
    return metrics


def score_timing(dist_ema200_pct: Optional[float], rsi: Optional[float], rsi_prev: Optional[float]) -> TimingScore:
    entry_signal = rsi is not None and rsi_prev is not None and rsi > rsi_prev and min(rsi, rsi_prev) < 40.0
    metrics = _score_table(TIMING_RULES, {"ema200_dist": dist_ema200_pct})
    points = float(sum(m["points"] for m in metrics.values()))
    max_points = sum(m["max"] for m in metrics.values())
    return TimingScore(
        entry_signal=entry_signal,
        points=points,
        max_points=max_points,
        pct=round(points / max_points * 100.0, 1) if max_points else None,
        coverage=round(max_points / MAX_TIMING_POINTS, 2),
        metrics=metrics,
        reasons=[m["label"] for m in metrics.values()] + (["RSI Hook ยกหัวจากต่ำกว่า 40 ⤴"] if entry_signal else []),
    )


def score_stock(
    fundamental: FundamentalScore, timing: TimingScore, days_to_earnings: Optional[float] = None
) -> StockScore:
    pillars = {"fundamental": fundamental["pct"], "timing": timing["pct"]}
    coverages = {"fundamental": fundamental["coverage"], "timing": timing["coverage"]}
    earnings_guard = days_to_earnings is not None and 0 <= days_to_earnings <= EARNINGS_GUARD_DAYS
    reasons = fundamental["reasons"] + timing["reasons"]

    if not fundamental["applicable"]:
        return StockScore(
            total=timing["pct"], grade="ETF", stars=ETF_STARS, pillars=pillars, coverage=timing["coverage"],
            earnings_guard=earnings_guard, reasons=reasons, fundamental=fundamental, timing=timing,
        )

    available = {k: w for k, w in PILLAR_WEIGHTS.items() if pillars[k] is not None}
    coverage = round(sum(w * coverages[k] for k, w in PILLAR_WEIGHTS.items()), 2)
    if not available:
        return StockScore(
            total=None, grade="N/A", stars=0, pillars=pillars, coverage=coverage,
            earnings_guard=earnings_guard, reasons=reasons, fundamental=fundamental, timing=timing,
        )
    total = round(sum(pillars[k] * w for k, w in available.items()) / sum(available.values()), 1)
    grade = grade_for(total, coverage)
    return StockScore(
        total=total, grade=grade, stars=STARS_BY_GRADE[grade], pillars=pillars, coverage=coverage,
        earnings_guard=earnings_guard, reasons=reasons, fundamental=fundamental, timing=timing,
    )
