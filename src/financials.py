"""
Financial Statements & Quarterly Metrics Provider (8 Quarters / 2 Years)
Fetches quarterly financial statements (Revenue, Net Income, EPS, D/E, FCF, Margins)
via Yahoo Finance fundamentals-timeseries API using Python standard library only,
caches them locally in data/financials_cache.json, and computes QoQ & YoY growths.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.http import http_get
from src.scoring import ETF_TICKERS, FUNDAMENTAL_RULES, find_band

DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
FINANCIALS_CACHE_FILE = "financials_cache.json"
CACHE_TTL_SECONDS = 86400  # 24 hours


def data_path() -> Path:
    """Return data directory, respecting FILTER_STOCK_DATA_DIR for isolated testing."""
    env = os.environ.get("FILTER_STOCK_DATA_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data"


def load_financials_cache(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load cached financial statement data from disk."""
    d = data_dir or data_path()
    path = d / FINANCIALS_CACHE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_financials_cache(cache: Dict[str, Any], data_dir: Optional[Path] = None) -> None:
    """Save cached financial statement data atomically to prevent corruption."""
    d = data_dir or data_path()
    d.mkdir(parents=True, exist_ok=True)
    target = d / FINANCIALS_CACHE_FILE
    tmp = d / f"{FINANCIALS_CACHE_FILE}.tmp.{os.getpid()}"
    try:
        tmp.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(target)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise


def fmt_currency(val: Optional[float]) -> str:
    """Format large numbers into clean human-readable USD strings (B / M / K)."""
    if val is None:
        return "-"
    abs_v = abs(val)
    sign = "-" if val < 0 else ""
    if abs_v >= 1e12:
        return f"{sign}${abs_v / 1e12:.2f}T"
    elif abs_v >= 1e9:
        return f"{sign}${abs_v / 1e9:.2f}B"
    elif abs_v >= 1e6:
        return f"{sign}${abs_v / 1e6:.2f}M"
    elif abs_v >= 1e3:
        return f"{sign}${abs_v / 1e3:.1f}K"
    else:
        return f"{sign}${abs_v:,.2f}"


def get_quarter_label(date_str: str) -> str:
    """Convert YYYY-MM-DD into a clean quarter label (e.g. Q2'26)."""
    try:
        parts = date_str.split("-")
        y = int(parts[0])
        m = int(parts[1])
        q = (m - 1) // 3 + 1
        return f"Q{q}'{str(y)[2:]}"
    except Exception:
        return date_str


def fetch_ticker_quarterly_raw(ticker: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch raw timeseries quarterly financials for a US ticker from Yahoo Finance.
    Standard library only, 0 dependencies, requires no auth token or crumb.
    """
    clean = ticker.replace(".", "-").upper().strip()
    types = (
        "quarterlyTotalRevenue,"
        "quarterlyNetIncome,"
        "quarterlyDilutedEPS,"
        "quarterlyFreeCashFlow,"
        "quarterlyTotalDebt,"
        "quarterlyStockholdersEquity,"
        "quarterlyGrossProfit,"
        "quarterlyOperatingIncome"
    )
    now = int(time.time())
    p1 = now - (4 * 365 * 86400)  # 4 years back to capture all available quarters
    url = f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{clean}?type={types}&period1={p1}&period2={now}"
    try:
        raw_bytes = http_get(url, timeout=timeout)
        data = json.loads(raw_bytes.decode("utf-8"))
        return data
    except Exception as e:
        print(f"[financials] fetch failed for {ticker}: {e}", file=sys.stderr)
        return None


def _find_closest_candle_price(candles: List[Dict[str, Any]], target_date_str: str) -> Optional[float]:
    """Find the closing price on or just before the quarter end date."""
    if not candles:
        return None
    closest_price = None
    for c in candles:
        d = c.get("time") or c.get("date")
        if not d:
            continue
        if str(d) <= target_date_str:
            closest_price = c.get("close")
        else:
            break
    if closest_price is None and candles:
        closest_price = candles[-1].get("close")
    return closest_price


def process_quarterly_metrics(
    ticker: str,
    raw_data: Optional[Dict[str, Any]],
    existing_quarters: Optional[List[Dict[str, Any]]] = None,
    candles: Optional[List[Dict[str, Any]]] = None,
    existing_timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Parse raw Yahoo timeseries data, merge with existing historical quarters to accumulate
    a rich timeline (up to 8+ quarters), and calculate QoQ/YoY growth and margin ratios.
    """
    is_stale = (raw_data is None)
    if is_stale:
        timestamp = existing_timestamp if existing_timestamp is not None else 0
    else:
        timestamp = int(time.time())

    # 1. Merge existing quarters by date
    merged_by_date: Dict[str, Dict[str, Any]] = {}
    if existing_quarters:
        for q in existing_quarters:
            d = q.get("date")
            if d:
                merged_by_date[d] = dict(q)

    # 2. Ingest new raw data
    if raw_data:
        timeseries_res = raw_data.get("timeseries", {}).get("result", [])
        for item in timeseries_res:
            metric_type = item.get("meta", {}).get("type", [None])[0]
            if not metric_type:
                continue
            for pt in item.get(metric_type, []):
                d = pt.get("asOfDate")
                if not d:
                    continue
                val = pt.get("reportedValue", {}).get("raw")
                if d not in merged_by_date:
                    merged_by_date[d] = {"date": d}
                merged_by_date[d][metric_type] = val

    if not merged_by_date:
        return {
            "ticker": ticker,
            "timestamp": existing_timestamp if (is_stale and existing_timestamp is not None) else 0,
            "quarters_count": 0,
            "has_data": False,
            "stale": is_stale,
            "quarters": [],
        }

    # 3. Sort chronologically
    sorted_dates = sorted(merged_by_date.keys())
    clean_quarters: List[Dict[str, Any]] = []

    for d in sorted_dates:
        row = merged_by_date[d]
        rev = row.get("quarterlyTotalRevenue") or row.get("revenue")
        ni = row.get("quarterlyNetIncome") or row.get("net_income")
        gp = row.get("quarterlyGrossProfit") or row.get("gross_profit")
        op = row.get("quarterlyOperatingIncome") or row.get("operating_income")
        eps = row.get("quarterlyDilutedEPS") or row.get("eps")
        fcf = row.get("quarterlyFreeCashFlow") or row.get("fcf")
        debt = row.get("quarterlyTotalDebt") or row.get("total_debt")
        eq = row.get("quarterlyStockholdersEquity") or row.get("stockholders_equity")

        gross_margin = round((gp / rev) * 100, 2) if (gp is not None and rev and rev > 0) else None
        operating_margin = round((op / rev) * 100, 2) if (op is not None and rev and rev > 0) else None
        net_margin = round((ni / rev) * 100, 2) if (ni is not None and rev and rev > 0) else None
        debt_to_equity = round(debt / eq, 2) if (debt is not None and eq and eq > 0) else None

        close_price = _find_closest_candle_price(candles or [], d)
        pe_quarterly = round(close_price / (eps * 4), 2) if (close_price and eps and eps > 0) else None

        clean_quarters.append({
            "date": d,
            "quarter_label": get_quarter_label(d),
            "revenue": rev,
            "revenue_fmt": fmt_currency(rev),
            "net_income": ni,
            "net_income_fmt": fmt_currency(ni),
            "gross_profit": gp,
            "gross_profit_fmt": fmt_currency(gp),
            "gross_margin": gross_margin,
            "operating_income": op,
            "operating_income_fmt": fmt_currency(op),
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "eps": round(eps, 3) if eps is not None else None,
            "fcf": fcf,
            "fcf_fmt": fmt_currency(fcf),
            "total_debt": debt,
            "total_debt_fmt": fmt_currency(debt),
            "stockholders_equity": eq,
            "stockholders_equity_fmt": fmt_currency(eq),
            "debt_to_equity": debt_to_equity,
            "close_price": close_price,
            "pe_quarterly": pe_quarterly,
        })

    # Filter out forward projection quarters that have neither revenue nor net income
    clean_quarters = [q for q in clean_quarters if q.get("revenue") is not None or q.get("net_income") is not None]

    # 4. Compute QoQ & YoY Growth percentages
    for i in range(len(clean_quarters)):
        cur = clean_quarters[i]
        # QoQ (compared to i-1)
        if i >= 1:
            prev = clean_quarters[i - 1]
            if cur["revenue"] is not None and prev["revenue"] and prev["revenue"] != 0:
                cur["rev_growth_qoq"] = round(((cur["revenue"] - prev["revenue"]) / abs(prev["revenue"])) * 100, 2)
            else:
                cur["rev_growth_qoq"] = None

            if cur["net_income"] is not None and prev["net_income"] and prev["net_income"] != 0:
                cur["net_income_growth_qoq"] = round(((cur["net_income"] - prev["net_income"]) / abs(prev["net_income"])) * 100, 2)
            else:
                cur["net_income_growth_qoq"] = None

            if cur["eps"] is not None and prev["eps"] and prev["eps"] != 0:
                cur["eps_growth_qoq"] = round(((cur["eps"] - prev["eps"]) / abs(prev["eps"])) * 100, 2)
            else:
                cur["eps_growth_qoq"] = None

            if cur["fcf"] is not None and prev["fcf"] and prev["fcf"] != 0:
                cur["fcf_growth_qoq"] = round(((cur["fcf"] - prev["fcf"]) / abs(prev["fcf"])) * 100, 2)
            else:
                cur["fcf_growth_qoq"] = None
        else:
            cur["rev_growth_qoq"] = None
            cur["net_income_growth_qoq"] = None
            cur["eps_growth_qoq"] = None
            cur["fcf_growth_qoq"] = None

        # YoY (compared to 4 quarters prior: i-4)
        if i >= 4:
            yoy_prev = clean_quarters[i - 4]
            if cur["revenue"] is not None and yoy_prev["revenue"] and yoy_prev["revenue"] != 0:
                cur["rev_growth_yoy"] = round(((cur["revenue"] - yoy_prev["revenue"]) / abs(yoy_prev["revenue"])) * 100, 2)
            else:
                cur["rev_growth_yoy"] = None

            if cur["net_income"] is not None and yoy_prev["net_income"] and yoy_prev["net_income"] != 0:
                cur["net_income_growth_yoy"] = round(((cur["net_income"] - yoy_prev["net_income"]) / abs(yoy_prev["net_income"])) * 100, 2)
            else:
                cur["net_income_growth_yoy"] = None

            if cur["eps"] is not None and yoy_prev["eps"] and yoy_prev["eps"] != 0:
                cur["eps_growth_yoy"] = round(((cur["eps"] - yoy_prev["eps"]) / abs(yoy_prev["eps"])) * 100, 2)
            else:
                cur["eps_growth_yoy"] = None

            if cur["fcf"] is not None and yoy_prev["fcf"] and yoy_prev["fcf"] != 0:
                cur["fcf_growth_yoy"] = round(((cur["fcf"] - yoy_prev["fcf"]) / abs(yoy_prev["fcf"])) * 100, 2)
            else:
                cur["fcf_growth_yoy"] = None
        else:
            cur["rev_growth_yoy"] = None
            cur["net_income_growth_yoy"] = None
            cur["eps_growth_yoy"] = None
            cur["fcf_growth_yoy"] = None

    # Limit to latest 8 quarters for concise display if more exist
    display_quarters = clean_quarters[-8:] if len(clean_quarters) > 8 else clean_quarters

    # Calculate TTM figures from latest up to 4 quarters
    ttm_slice = clean_quarters[-4:] if len(clean_quarters) >= 4 else clean_quarters
    ttm_rev = sum(q["revenue"] for q in ttm_slice if q.get("revenue"))
    ttm_ni = sum(q["net_income"] for q in ttm_slice if q.get("net_income"))
    ttm_fcf = sum(q["fcf"] for q in ttm_slice if q.get("fcf"))

    latest = display_quarters[-1] if display_quarters else {}

    # Compute Piotroski F-Score (0-9) and Executive Summary in Thai
    f_score_data = compute_piotroski_f_score(clean_quarters)
    exec_summary = generate_financial_executive_summary(clean_quarters)

    return {
        "ticker": ticker,
        "timestamp": timestamp,
        "stale": is_stale,
        "quarters_count": len(display_quarters),
        "has_data": len(display_quarters) > 0 and (latest.get("revenue") is not None or latest.get("net_income") is not None),
        "latest_quarter": latest.get("quarter_label", "-"),
        "latest_date": latest.get("date", "-"),
        "latest_revenue_fmt": latest.get("revenue_fmt", "-"),
        "latest_net_income_fmt": latest.get("net_income_fmt", "-"),
        "latest_net_margin": latest.get("net_margin"),
        "latest_debt_to_equity": latest.get("debt_to_equity"),
        "latest_fcf_fmt": latest.get("fcf_fmt", "-"),
        "ttm_revenue": ttm_rev if ttm_rev else None,
        "ttm_revenue_fmt": fmt_currency(ttm_rev) if ttm_rev else "-",
        "ttm_net_income": ttm_ni if ttm_ni else None,
        "ttm_net_income_fmt": fmt_currency(ttm_ni) if ttm_ni else "-",
        "ttm_fcf_fmt": fmt_currency(ttm_fcf) if ttm_fcf else "-",
        "f_score": f_score_data,
        "executive_summary": exec_summary,
        "quarters": display_quarters,
    }


def compute_piotroski_f_score(quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute financial checklist (0-9) measuring business financial strength.
    Scores 8-9 = Elite Strong, 6-7 = Good, 4-5 = Moderate, 0-3 = Weak.
    """
    if not quarters:
        return {
            "title": "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)",
            "name": "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)",
            "score": None,
            "max_score": 9,
            "label": "ไม่มีข้อมูล",
            "color": "#94a3b8",
            "badge_class": "fin-badge-neutral",
            "criteria": [],
        }

    latest = quarters[-1]
    has_yoy = len(quarters) >= 5
    prev_year = quarters[-5] if has_yoy else None

    criteria = []
    score = 0

    # 1. Positive Net Income
    ni = latest.get("net_income")
    if ni is None:
        criteria.append({"name": "กำไรสุทธิเป็นบวก (Positive Net Income)", "passed": None, "detail": "N/A"})
    elif ni > 0:
        score += 1
        criteria.append({"name": "กำไรสุทธิเป็นบวก (Positive Net Income)", "passed": True, "detail": fmt_currency(ni)})
    else:
        criteria.append({"name": "กำไรสุทธิเป็นบวก (Positive Net Income)", "passed": False, "detail": fmt_currency(ni)})

    # 2. Positive Free Cash Flow
    fcf = latest.get("fcf")
    if fcf is None:
        criteria.append({"name": "กระแสเงินสดอิสระเป็นบวก (Positive FCF)", "passed": None, "detail": "N/A"})
    elif fcf > 0:
        score += 1
        criteria.append({"name": "กระแสเงินสดอิสระเป็นบวก (Positive FCF)", "passed": True, "detail": fmt_currency(fcf)})
    else:
        criteria.append({"name": "กระแสเงินสดอิสระเป็นบวก (Positive FCF)", "passed": False, "detail": fmt_currency(fcf)})

    # 3. Quality of Earnings: FCF > Net Income
    if fcf is None or ni is None:
        criteria.append({"name": "คุณภาพกำไรสูง (FCF > Net Income)", "passed": None, "detail": "N/A"})
    elif fcf > ni and ni > 0:
        score += 1
        criteria.append({"name": "คุณภาพกำไรสูง (FCF > Net Income)", "passed": True, "detail": "เงินสดเข้าจริงมากกว่ากำไรบัญชี"})
    else:
        criteria.append({"name": "คุณภาพกำไรสูง (FCF > Net Income)", "passed": False, "detail": "กำไรบัญชีสูงกว่าเงินสดจริง"})

    # 4. YoY Net Income Growth
    if not has_yoy:
        criteria.append({"name": "กำไรสุทธิเติบโต YoY", "passed": None, "detail": "N/A"})
    else:
        ni_prev = prev_year.get("net_income") if prev_year else None
        if ni is None or ni_prev is None:
            criteria.append({"name": "กำไรสุทธิเติบโต YoY", "passed": None, "detail": "N/A"})
        elif ni > ni_prev:
            score += 1
            criteria.append({"name": "กำไรสุทธิเติบโต YoY", "passed": True, "detail": f"โตจาก {fmt_currency(ni_prev)}"})
        else:
            criteria.append({"name": "กำไรสุทธิเติบโต YoY", "passed": False, "detail": "กำไรชะลอตัว"})

    # 5. Debt to Equity Safety
    de = latest.get("debt_to_equity")
    de_prev = prev_year.get("debt_to_equity") if (has_yoy and prev_year) else None
    if de is None:
        criteria.append({"name": "สัดส่วนหนี้สินปลอดภัย (D/E ต่ำ)", "passed": None, "detail": "N/A"})
    elif de >= 0 and ((de_prev is not None and de <= de_prev) or de < 1.0):
        score += 1
        criteria.append({"name": "สัดส่วนหนี้สินปลอดภัย (D/E ต่ำ)", "passed": True, "detail": f"{de:.2f}x"})
    else:
        criteria.append({"name": "สัดส่วนหนี้สินปลอดภัย", "passed": False, "detail": f"{de:.2f}x"})

    # 6. Gross Margin Expansion or High Moat (>50%)
    gm = latest.get("gross_margin")
    gm_prev = prev_year.get("gross_margin") if (has_yoy and prev_year) else None
    if gm is None:
        criteria.append({"name": "อัตรากำไรขั้นต้นขยายตัว / มี Moat สูง", "passed": None, "detail": "N/A"})
    elif (gm_prev is not None and gm >= gm_prev) or gm >= 50.0:
        score += 1
        criteria.append({"name": "อัตรากำไรขั้นต้นขยายตัว / มี Moat สูง", "passed": True, "detail": f"{gm:.1f}%"})
    else:
        criteria.append({"name": "อัตรากำไรขั้นต้นขยายตัว", "passed": False, "detail": f"{gm:.1f}%"})

    # 7. Revenue Growth YoY
    if not has_yoy:
        criteria.append({"name": "รายได้รวมเติบโต YoY", "passed": None, "detail": "N/A"})
    else:
        rev = latest.get("revenue")
        rev_prev = prev_year.get("revenue") if prev_year else None
        if rev is None or rev_prev is None:
            criteria.append({"name": "รายได้รวมเติบโต YoY", "passed": None, "detail": "N/A"})
        elif rev > rev_prev:
            score += 1
            criteria.append({"name": "รายได้รวมเติบโต YoY", "passed": True, "detail": f"โตจาก {fmt_currency(rev_prev)}"})
        else:
            criteria.append({"name": "รายได้รวมเติบโต YoY", "passed": False, "detail": "รายได้ชะลอตัว"})

    # 8. Operating Margin Expansion
    op_m = latest.get("operating_margin")
    op_m_prev = prev_year.get("operating_margin") if (has_yoy and prev_year) else None
    if op_m is None:
        criteria.append({"name": "กำไรดำเนินงานแข็งแกร่ง (Operating Margin)", "passed": None, "detail": "N/A"})
    elif (op_m_prev is not None and op_m >= op_m_prev) or op_m >= 25.0:
        score += 1
        criteria.append({"name": "กำไรดำเนินงานแข็งแกร่ง (Operating Margin)", "passed": True, "detail": f"{op_m:.1f}%"})
    else:
        criteria.append({"name": "กำไรดำเนินงานแข็งแกร่ง", "passed": False, "detail": f"{op_m:.1f}%"})

    # 9. Equity Health
    eq = latest.get("stockholders_equity")
    eq_prev = prev_year.get("stockholders_equity") if (has_yoy and prev_year) else None
    if eq is None:
        criteria.append({"name": "ส่วนของผู้ถือหุ้นมั่นคง (Growing Equity)", "passed": None, "detail": "N/A"})
    elif eq > 0 and (eq_prev is None or eq >= eq_prev):
        score += 1
        criteria.append({"name": "ส่วนของผู้ถือหุ้นมั่นคง (Growing Equity)", "passed": True, "detail": fmt_currency(eq)})
    else:
        criteria.append({"name": "ส่วนของผู้ถือหุ้นมั่นคง", "passed": False, "detail": fmt_currency(eq) if eq is not None else "N/A"})

    evaluable = [c for c in criteria if c["passed"] is not None]
    evaluable_count = len(evaluable)
    max_score = evaluable_count if evaluable_count > 0 else 9
    pct_score = (score / max_score * 100.0) if max_score > 0 else 0.0

    MIN_EVALUABLE_CRITERIA = 5
    if evaluable_count < MIN_EVALUABLE_CRITERIA:
        label = "ข้อมูลไม่พอ"
        color = "#94a3b8"
        badge_class = "fin-badge-neutral"
    elif pct_score >= 85.0:
        label = "สุขภาพการเงินแข็งแกร่งมาก (Elite)"
        color = "#34d399"
        badge_class = "fin-badge-pos"
    elif pct_score >= 65.0:
        label = "สุขภาพการเงินดี มั่นคง (Good)"
        color = "#60a5fa"
        badge_class = "fin-badge-pos"
    elif pct_score >= 40.0:
        label = "สุขภาพการเงินปานกลาง (Moderate)"
        color = "#fbbf24"
        badge_class = "fin-badge-neutral"
    else:
        label = "สุขภาพการเงินเปราะบาง (Weak)"
        color = "#fb7185"
        badge_class = "fin-badge-neg"

    return {
        "title": "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)",
        "name": "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)",
        "score": score,
        "max_score": max_score,
        "evaluable_count": evaluable_count,
        "label": label,
        "color": color,
        "badge_class": badge_class,
        "criteria": criteria,
    }


def generate_financial_executive_summary(quarters: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate concise Thai executive summary across 3 dimensions:
    Growth, Profitability, and Solvency/Debt.
    """
    if not quarters:
        return {
            "growth": "ยังไม่มีรายงานงบการเงินรายไตรมาสย้อนหลังของบริษัทนี้",
            "profitability": "-",
            "debt": "-",
        }

    latest = quarters[-1]
    rev_yoy = latest.get("rev_growth_yoy")
    rev_qoq = latest.get("rev_growth_qoq")
    net_margin = latest.get("net_margin")
    de = latest.get("debt_to_equity")

    # 1. Growth
    if rev_yoy is not None:
        if rev_yoy >= 20.0:
            growth_text = f"รายได้เติบโตอย่างร้อนแรง +{rev_yoy:.1f}% YoY และไตรมาสล่าสุดอยู่ที่ {latest.get('revenue_fmt')} ธุรกิจขยายตัวเด่นชัด"
        elif rev_yoy > 0:
            growth_text = f"รายได้เติบโตในเกณฑ์ดี +{rev_yoy:.1f}% YoY โดยทำได้ {latest.get('revenue_fmt')} ในไตรมาสล่าสุด"
        else:
            growth_text = f"รายได้ชะลอตัวลง {rev_yoy:.1f}% YoY แตะระดับ {latest.get('revenue_fmt')} ควรจับตาความต้องการของตลาด"
    elif rev_qoq is not None:
        growth_text = f"รายได้ไตรมาสล่าสุดทำได้ {latest.get('revenue_fmt')} ({rev_qoq:+.1f}% QoQ)"
    else:
        growth_text = f"รายได้ไตรมาสล่าสุดอยู่ที่ {latest.get('revenue_fmt', '-')}"

    # 2. Profitability
    fcf_val = latest.get("fcf")
    fcf_str = latest.get("fcf_fmt", "-")
    fcf_clause = ""
    fcf_pos_clause = ""
    if fcf_val is not None:
        if fcf_val > 0:
            fcf_clause = f" และมีกระแสเงินสด FCF แข็งแกร่ง {fcf_str}"
            fcf_pos_clause = f" พร้อม FCF เป็นบวก {fcf_str}"
        else:
            fcf_clause = f" แต่กระแสเงินสด FCF ติดลบ {fcf_str}"
            fcf_pos_clause = f" แต่ FCF ติดลบ {fcf_str}"

    if net_margin is not None:
        if net_margin >= 25.0:
            prof_text = f"ความสามารถในการทำกำไรระดับยอดเยี่ยม Net Margin สูงถึง {net_margin:.1f}%{fcf_clause}"
        elif net_margin >= 10.0:
            prof_text = f"อัตรากำไรสุทธิอยู่ในเกณฑ์ดี {net_margin:.1f}% มีกำไรสุทธิ {latest.get('net_income_fmt')}{fcf_pos_clause}"
        elif net_margin >= 0:
            prof_text = f"อัตรากำไรสุทธิค่อนข้างบาง {net_margin:.1f}% ทำกำไรได้ {latest.get('net_income_fmt')} ต้องควบคุมต้นทุนเพิ่มเติม"
        else:
            prof_text = f"งบล่าสุดยังคงขาดทุนสุทธิ {latest.get('net_income_fmt')} (Margin {net_margin:.1f}%)"
    else:
        prof_text = f"กำไรสุทธิล่าสุด {latest.get('net_income_fmt', '-')}"

    # 3. Debt & Balance Sheet
    if de is not None:
        try:
            matching_band = find_band(FUNDAMENTAL_RULES["debt_to_equity"][1], de)
            pts = matching_band.points
        except Exception:
            pts = 0
        if de < 0.0:
            debt_text = f"ส่วนของผู้ถือหุ้นติดลบ (Negative Equity D/E {de:.2f}x หนี้สินรวม {latest.get('total_debt_fmt')}) มีความเสี่ยงด้านโครงสร้างทุน"
        elif pts == 3: # 0.0 <= de <= 0.8
            debt_text = f"โครงสร้างเงินทุนปลอดภัยสูงมาก สัดส่วนหนี้สินต่อทุน (D/E) เพียง {de:.2f}x ไร้แรงกดดันจากภาระดอกเบี้ยจ่าย"
        elif pts == 2: # 0.8 < de <= 1.5
            debt_text = f"ภาระหนี้สินอยู่ในเกณฑ์ปกติที่บริหารจัดการได้ D/E {de:.2f}x หนี้สินรวม {latest.get('total_debt_fmt')}"
        elif pts == 1: # 1.5 < de <= 2.5
            debt_text = f"ภาระหนี้สินค่อนข้างสูง D/E {de:.2f}x หนี้สินรวม {latest.get('total_debt_fmt')} ต้องติดตามกระแสเงินสด"
        else: # de > 2.5
            debt_text = f"สัดส่วนหนี้สินต่อทุนค่อนข้างตึงตัว D/E {de:.2f}x (หนี้สินรวม {latest.get('total_debt_fmt')}) ต้องระวังความผันผวนของดอกเบี้ย"
    else:
        debt_text = f"หนี้สินรวม {latest.get('total_debt_fmt', '-')}"

    return {
        "growth": growth_text,
        "profitability": prof_text,
        "debt": debt_text,
    }


def get_all_financials_payload(
    tickers: List[str],
    candles_cache: Optional[Dict[str, Any]] = None,
    max_workers: int = 5,
    force_refresh: bool = False,
    data_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Fetch and build financial statement datasets for all specified tickers.
    Uses cached data if fresh (TTL < 24h), fetches missing/expired tickers concurrently,
    and updates data/financials_cache.json atomically.
    """
    cache = load_financials_cache(data_dir=data_dir)
    now = int(time.time())
    tickers_to_fetch = []

    for t in tickers:
        # Known ETFs have no corporate quarterly financial statements
        if t in ETF_TICKERS:
            if t not in cache:
                cache[t] = {
                    "ticker": t,
                    "timestamp": now,
                    "quarters_count": 0,
                    "has_data": False,
                    "is_etf": True,
                    "quarters": [],
                }
            continue

        entry = cache.get(t)
        needs_fetch = (
            force_refresh
            or not entry
            or (not entry.get("has_data") and not entry.get("is_etf"))
            or (now - entry.get("timestamp", 0) > CACHE_TTL_SECONDS)
        )
        if needs_fetch:
            tickers_to_fetch.append(t)

    if tickers_to_fetch:
        candles_c = candles_cache or {}

        def _worker(ticker_symbol: str):
            candles = candles_c.get(ticker_symbol, {}).get("candles", [])
            raw = fetch_ticker_quarterly_raw(ticker_symbol)
            entry = cache.get(ticker_symbol, {})
            existing = entry.get("quarters", [])
            existing_ts = entry.get("timestamp")
            processed = process_quarterly_metrics(
                ticker_symbol,
                raw,
                existing_quarters=existing,
                candles=candles,
                existing_timestamp=existing_ts,
            )
            return ticker_symbol, processed

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            fetched_results = list(pool.map(_worker, tickers_to_fetch))

        for t_sym, res in fetched_results:
            if res.get("has_data") or res.get("is_etf"):
                cache[t_sym] = res
            elif t_sym not in cache or not cache[t_sym].get("has_data"):
                # If failed, record without setting a fresh 24h timestamp so it retries
                res["timestamp"] = 0
                cache[t_sym] = res

        save_financials_cache(cache, data_dir=data_dir)

    # Ensure cached entries have f_score and executive_summary computed
    cache_dirty = False
    for t in tickers:
        entry = cache.get(t)
        if entry and entry.get("has_data") and ("f_score" not in entry or "executive_summary" not in entry):
            quarters = entry.get("quarters", [])
            entry["f_score"] = compute_piotroski_f_score(quarters)
            entry["executive_summary"] = generate_financial_executive_summary(quarters)
            cache_dirty = True

    if cache_dirty:
        save_financials_cache(cache, data_dir=data_dir)

    return cache
