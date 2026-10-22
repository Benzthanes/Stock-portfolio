"""
Portfolio Engine
Processes user holdings, connects to TradingView Screener API for live metrics,
computes 1-5 star ratings factoring in technicals and fundamentals, detects risks,
and formats comprehensive Markdown reports with earnings calendars and live news.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.tradingview import fetch_screener_data
from src.screener import evaluate_stock
from src.news import fetch_batch_news, fetch_batch_catalysts
from src.profiles import get_business_summary
from src.outlook import get_forward_outlook
from src.fx import resolve_usdthb
from src.scoring import FundamentalScore, format_score, score_fundamentals, score_stock, score_timing


from src.trades import data_path


def cost_basis(holding: Dict[str, Any], base_currency: str) -> Tuple[float, float]:
    """(avg_cost, total_cost) of a holding in the portfolio's base currency."""
    shares = float(holding.get("shares", 0.0))
    if str(base_currency).upper() == "THB":
        avg = float(holding.get("avg_cost_thb") or holding.get("avg_cost") or 0.0)
        total = holding.get("total_cost_thb")
    else:
        avg = float(holding.get("avg_cost_usd") or holding.get("avg_cost") or 0.0)
        total = holding.get("total_cost_usd")
    return avg, float(total) if total is not None else shares * avg


def load_portfolio(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Load portfolio holdings JSON file."""
    path = Path(file_path) if file_path else data_path("portfolio.json")
    if not path.exists():
        raise FileNotFoundError(f"Portfolio file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fundamental(pos: Dict[str, Any]) -> FundamentalScore:
    return pos.get("fundamental") or score_fundamentals(
        pos["ticker"], pos.get("sector"), pos.get("rev_growth_yoy"), pos.get("net_inc_growth_yoy"),
        pos.get("roe"), pos.get("peg"), pos.get("debt_to_equity"), pos.get("fcf"),
    )


RATING_TEXT_BY_GRADE = {
    "A+": ("เกรด A+ (ยอดเยี่ยม ปลอดภัยสูง)", "ถือรันเทรนด์ต่อ หรือสะสมเพิ่มเมื่อราคาย่อเข้า Value Zone เหนือ EMA200."),
    "A": ("เกรด A (สุขภาพดี แข็งแกร่ง)", "สถานะแข็งแกร่ง ถือต่อตามแผนเทรดได้อย่างมั่นใจ."),
    "B": ("เกรด B (ปานกลาง / พักฐาน)", "ถือครองสถานะเดิม ไม่เพิ่มเงินลงทุนใหม่จนกว่าพื้นฐานหรือจังหวะจะดีขึ้น."),
    "C": ("เกรด C (เฝ้าระวัง / เสี่ยงสูง)", "งดซื้อถัวเฉลี่ย รอแท่งเทียนสร้างฐานและงบไตรมาสถัดไป."),
    "F": ("เกรด F (น่าเป็นห่วง)", "วางแผน Stop-Loss หรือเตรียมโยกเงินทุน (Capital Rotation) เพื่อรักษาเงินต้น."),
    "ETF": ("กองทุนดัชนี (ETF)", "ถือเป็นแกนหลักของพอร์ต ทยอยสะสมตามแผน DCA."),
    "N/A": ("ข้อมูลไม่พอประเมิน", "ตรวจสอบข้อมูลราคาและงบการเงินก่อนตัดสินใจ."),
}


def top_pick_reason(pick: Dict[str, Any], fmt_money) -> str:
    """Beginner reason for a fresh-cash pick. Shared by the Markdown and HTML reports."""
    if not _fundamental(pick)["applicable"]:
        return "เป็นกองทุนดัชนีรวมที่ช่วยกระจายความเสี่ยงของพอร์ตทันที ช่วยลดการพึ่งพาหุ้นตัวใดตัวหนึ่งมากเกินไป."
    target = pick.get("price_target_average")
    upside = pick.get("target_upside_pct")
    above_200 = (pick.get("dist_sma200_pct") or -1.0) >= 0
    trend = "เทรนด์ขาขึ้นเหนือเส้น 200 วัน" if above_200 else "ราคายังต่ำกว่าเส้น 200 วัน รอยืนกลับเหนือเส้นก่อนเพิ่มน้ำหนัก"
    if pick.get("in_value_zone"):
        return f"ราคาพักตัวลงมาในจุดรับที่มีแต้มต่อสูง (Value Zone 💎) ใกล้เส้น 200 วัน และสถาบันให้เป้าหมายเฉลี่ย {fmt_money(target) if target else 'ไม่ระบุ'}."
    if upside is not None:
        return f"หุ้นคุณภาพดี พื้นฐานแกร่ง {trend} สถาบันให้เป้าหมายมี Upside {upside:+.1f}%."
    return f"หุ้นคุณภาพดี พื้นฐานมั่นคง {trend}."


def compute_stock_rating(pos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute 1-5 star health rating dynamically combining technicals, fundamentals, and risks.
    """
    if pos.get("data_missing"):
        return {
            "stars_str": "⚪",
            "stars_count": 0,
            "grade": "N/A (ไม่มีข้อมูลราคา)",
            "summary": "ไม่สามารถดึงข้อมูลราคาตลาดได้จาก TradingView.",
            "strength": "-",
            "risk": "ข้อมูลตลาดขาดหาย ตรวจสอบชื่อ Ticker หรือ Exchange ใน data/portfolio.json.",
            "action": "ตรวจสอบสัญลักษณ์ Ticker หรือ Exchange."
        }

    ticker = pos["ticker"]
    pl_pct = pos.get("unrealized_pl_pct", 0.0)
    dist_200 = pos.get("dist_sma200_pct")
    in_value = pos.get("in_value_zone", False)
    rsi = pos.get("rsi")
    weight = pos.get("weight_pct", 0.0)
    rec_mark = pos.get("rec_mark")
    is_earnings_near = pos.get("is_earnings_near", False)
    fund = _fundamental(pos)
    etf = not fund["applicable"]

    stock_score = pos.get("stock_score") or score_stock(
        fund,
        score_timing(pos.get("dist_ema200_pct", dist_200), rsi, pos.get("rsi_prev")),
        pos.get("days_to_earnings"),
    )
    star_count = max(1, stock_score["stars"])
    stars_str = "⭐" * star_count

    grade, action = RATING_TEXT_BY_GRADE.get(stock_score["grade"], RATING_TEXT_BY_GRADE["N/A"])

    # Dynamic narrative summary
    trend_desc = f"ยืนเหนือเส้น 200 วัน {dist_200:+.1f}%" if dist_200 is not None else "ไม่มีข้อมูลเส้น 200 วัน"
    pl_desc = f"กำไร {pl_pct:+.1f}%" if pl_pct >= 0 else f"ขาดทุน {pl_pct:.1f}%"
    summary_desc = f"สถานะ {pl_desc}, กราฟ {trend_desc}."

    # Dynamic strengths
    strengths = []
    if dist_200 is not None and dist_200 >= 0:
        strengths.append(f"เทรนด์ขาขึ้นเหนือเส้น 200 วัน ({dist_200:+.1f}%)")
    if in_value:
        strengths.append("อยู่ใน Institutional Value Zone 💎")
    if rsi is not None and rsi <= 35:
        strengths.append(f"RSI Oversold ({rsi:.1f}) ลุ้นเด้งรีบาวด์")
    if etf:
        strengths.append("กองทุนดัชนีชั้นนำ กระจายความเสี่ยงสูง")
    strengths.extend(m["label"] for m in fund["metrics"].values() if m["points"] == m["max"])
    strengths.extend(m["label"] for m in stock_score["timing"]["metrics"].values() if m["points"] == m["max"])
    if rec_mark is not None and rec_mark <= 1.5:
        strengths.append("ฉันทามติตลาด Strong Buy")
    strength_desc = ", ".join(strengths) if strengths else "ราคาทรงตัวในกรอบสะสมพลัง."

    # Dynamic risks
    risks = []
    if weight >= 30.0:
        risks.append(f"สัดส่วนกระจุกตัวสูง ({weight:.1f}%)")
    if pl_pct <= -15.0:
        risks.append(f"ขาดทุนสะสม ({pl_pct:.1f}%)")
    if dist_200 is not None and dist_200 < 0:
        risks.append(f"ราคาหลุดต่ำกว่าเส้น 200 วัน ({dist_200:.1f}%)")
    if is_earnings_near:
        risks.append(f"วันประกาศงบใกล้เข้ามา ({pos.get('days_to_earnings')} วัน)")
    risks.extend(m["label"] for m in fund["metrics"].values() if m["points"] == 0)
    risks.extend(m["label"] for m in stock_score["timing"]["metrics"].values() if m["points"] == 0)
    risk_desc = ", ".join(risks) if risks else "ไม่มีสัญญาณความเสี่ยงผิดปกติ."

    return {
        "stars_count": star_count,
        "stars_str": stars_str,
        "grade": grade,
        "summary": summary_desc,
        "strength": strength_desc,
        "risk": risk_desc,
        "action": action,
        "grade_code": stock_score["grade"],
        "total": stock_score["total"],
        "pillars": stock_score["pillars"],
        "coverage": stock_score["coverage"],
    }


HEALTH_TEXT_BY_GRADE = {
    "A+": ("เกรด A+ (ยอดเยี่ยม 🟢)", "🟢 ยอดเยี่ยม",
           "รายได้เติบโต {rev}, กำไรขยายตัว {net}, ROE คุณภาพสูง {roe}, หนี้สินต่ำ D/E {de}, กระแสเงินสด {fcf}, PEG {peg}."),
    "A": ("เกรด A (แข็งแกร่ง 🟢)", "🟢 สุขภาพดี",
          "งบการเงินแข็งแกร่งต่อเนื่อง, ROE {roe}, กระแสเงินสด {fcf}, หนี้สินคุมได้ D/E {de}."),
    "B": ("เกรด B (ปานกลาง 🟡)", "🟡 ปานกลาง",
          "งบการเงินผ่านเกณฑ์ แต่การเติบโตเริ่มทรงตัว หรือราคาเทรดด้วย Valuation ค่อนข้างตึงตัว."),
    "C": ("เกรด C (เฝ้าระวัง 🟠)", "🟠 เฝ้าระวัง",
          "รายได้หรือกำไรชะลอตัวลง หรือมีภาระหนี้สินเพิ่มขึ้น ควรติดตามทิศทางงบการเงินไตรมาสถัดไป."),
    "F": ("เกรด F (น่าเป็นห่วง 🔴)", "🔴 พื้นฐานอ่อนแอ",
          "พื้นฐานอ่อนแอ กำไรสุทธิ {net}, ROE {roe}, D/E {de} ขาดแรงหนุนด้านพื้นฐาน ควรระมัดระวัง."),
    "N/A": ("ไม่มีข้อมูลพื้นฐาน ⚪", "⚪ ไม่มีข้อมูล",
            "TradingView ไม่มีข้อมูลงบการเงินเพียงพอสำหรับประเมินพื้นฐาน."),
}


def _format_fcf(fcf: Optional[float]) -> str:
    if fcf is None:
        return "-"
    if abs(fcf) >= 1e9:
        return f"${fcf / 1e9:.1f}B"
    if abs(fcf) >= 1e6:
        return f"${fcf / 1e6:.1f}M"
    return f"${fcf:,.0f}"


def _peg_verdict(peg: Optional[float]) -> str:
    if peg is None:
        return "-"
    if 0 < peg <= 0.5:
        return f"ถูกมาก ({peg:.2f} 💎)"
    if 0.5 < peg <= 1.0:
        return f"คุ้มค่ามาก ({peg:.2f} 💎)"
    if 1.0 < peg <= 1.5:
        return f"สมเหตุสมผล ({peg:.2f} 👍)"
    if 1.5 < peg <= 2.5:
        return f"ค่อนข้างตึงตัว ({peg:.2f} ⚠️)"
    if peg > 2.5:
        return f"ราคาตึงตัวสูง ({peg:.2f} 🚨)"
    return f"ติดลบ ({peg:.2f})"


def compute_financial_health(pos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Presents the unified fundamental score (src/scoring.py) as the Health Review grade, badge and narrative.
    """
    fund = _fundamental(pos)
    if not fund["applicable"]:
        return {
            "health_grade": "🏛️ ETF ดัชนี (ความเสี่ยงต่ำ)",
            "health_badge": "🏛️ กองทุนดัชนี",
            "peg_verdict": "N/A (กระจาย 500 บ.)",
            "fcf_str": "-",
            "roe_str": "-",
            "de_str": "-",
            "summary": "กองทุนดัชนีรวมกระจายความเสี่ยงข้าม 500 บริษัทชั้นนำสหรัฐฯ ไร้ความเสี่ยงงบการเงินรายตัว.",
            "score": 5,
            "pct": None,
            "coverage": fund["coverage"],
            "grade_code": fund["grade"],
        }

    rev_g = pos.get("rev_growth_yoy")
    net_g = pos.get("net_inc_growth_yoy")
    roe = pos.get("roe")
    debt_to_equity = pos.get("debt_to_equity")

    fcf_str = _format_fcf(pos.get("fcf"))
    roe_str = f"{roe:+.1f}%" if roe is not None else "-"
    de_str = f"{debt_to_equity:.2f}" if debt_to_equity is not None else "-"
    peg_verdict = _peg_verdict(pos.get("peg"))

    grade, health_badge, summary_tpl = HEALTH_TEXT_BY_GRADE[fund["grade"]]
    summary = summary_tpl.format(
        rev=f"{rev_g:+.1f}%" if rev_g is not None else "-",
        net=f"{net_g:+.1f}%" if net_g is not None else "-",
        roe=roe_str, de=de_str, fcf=fcf_str, peg=peg_verdict,
    )

    return {
        "health_grade": grade,
        "health_badge": health_badge,
        "peg_verdict": peg_verdict,
        "fcf_str": fcf_str,
        "roe_str": roe_str,
        "de_str": de_str,
        "summary": summary,
        "score": round(fund["points"], 1),
        "pct": fund["pct"],
        "coverage": fund["coverage"],
        "grade_code": fund["grade"],
    }


def analyze_portfolio(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch live TradingView market data, fundamentals, and news to compute portfolio metrics.
    """
    holdings = portfolio_data.get("holdings", [])
    fx_rate = resolve_usdthb(portfolio_data.get("fx_rate_usd_thb"))
    portfolio_name = portfolio_data.get("portfolio_name", "My Portfolio")
    broker = portfolio_data.get("broker", "InnovestX")
    base_currency = str(portfolio_data.get("base_currency", "USD")).upper()

    # Map symbols for TradingView scanner
    symbols_to_fetch = []
    for h in holdings:
        ticker = h["ticker"].upper()
        exchange = h.get("exchange", "NASDAQ").upper()
        symbols_to_fetch.append(f"{exchange}:{ticker}")

    # Fetch live TradingView scanner data
    live_rows = fetch_screener_data(symbols_to_fetch)
    live_dict = {row["ticker"]: row for row in live_rows}

    # Batch fetch catalysts and news for all holdings
    tickers = [h["ticker"].upper() for h in holdings]
    all_news = fetch_batch_news(tickers, max_items=2)
    all_catalysts = fetch_batch_catalysts(tickers, max_items=4)

    positions: List[Dict[str, Any]] = []
    total_cost_usd = 0.0
    total_cost_thb = 0.0
    total_market_val_usd = 0.0
    total_market_val_thb = 0.0
    total_daily_change_usd = 0.0
    total_daily_change_thb = 0.0
    unpriced_cost_usd = 0.0
    unpriced_cost_thb = 0.0
    price_missing_tickers: List[str] = []

    for h in holdings:
        ticker = h["ticker"].upper()
        shares = float(h.get("shares", 0.0))
        live_row = live_dict.get(ticker, {})
        price_missing = not bool(live_row.get("close"))
        change_pct = float(live_row.get("change") or 0.0)
        close_price = None if price_missing else float(live_row["close"])
        avg_cost, cost_base = cost_basis(h, base_currency)

        if base_currency == "THB":
            avg_cost_thb, cost_thb = avg_cost, cost_base
            avg_cost_usd = avg_cost_thb / fx_rate if fx_rate > 0 else 0.0
            cost_usd = cost_thb / fx_rate if fx_rate > 0 else 0.0
        else:
            avg_cost_usd, cost_usd = avg_cost, cost_base
            cost_thb = float(h.get("cost_thb") or (cost_usd * fx_rate))
            avg_cost_thb = cost_thb / shares if shares > 0 else avg_cost_usd * fx_rate

        current_val_usd = current_val_thb = None
        unrealized_pl_usd = unrealized_pl_thb = unrealized_pl_pct = None
        daily_diff_usd = daily_diff_thb = None
        if not price_missing:
            if base_currency == "THB":
                current_val_thb = shares * close_price
                current_val_usd = current_val_thb / fx_rate if fx_rate > 0 else 0.0
            else:
                current_val_usd = shares * close_price
                current_val_thb = current_val_usd * fx_rate
            unrealized_pl_usd = current_val_usd - cost_usd
            unrealized_pl_thb = current_val_thb - cost_thb
            base_pl, base_cost = (unrealized_pl_thb, cost_thb) if base_currency == "THB" else (unrealized_pl_usd, cost_usd)
            unrealized_pl_pct = (base_pl / base_cost * 100.0) if base_cost > 0 else 0.0
            growth = 1.0 + (change_pct / 100.0)
            daily_diff_usd = current_val_usd - (current_val_usd / growth if growth != 0 else current_val_usd)
            daily_diff_thb = current_val_thb - (current_val_thb / growth if growth != 0 else current_val_thb)

        # Unpriced holdings stay out of every total so total P&L never counts them as a fake 0%; their cost is reported separately.
        if price_missing:
            price_missing_tickers.append(ticker)
            unpriced_cost_usd += cost_usd
            unpriced_cost_thb += cost_thb
        else:
            total_cost_usd += cost_usd
            total_cost_thb += cost_thb
            total_market_val_usd += current_val_usd
            total_market_val_thb += current_val_thb
            total_daily_change_usd += daily_diff_usd
            total_daily_change_thb += daily_diff_thb

        # Technical evaluation via screener engine
        eval_result = evaluate_stock(live_row) if live_row else {}

        # Fundamentals extraction
        rev_g = live_row.get("total_revenue_yoy_growth_ttm")
        net_g = live_row.get("net_income_yoy_growth_ttm")
        peg = live_row.get("price_earnings_growth_ttm")
        pe = live_row.get("price_earnings_ttm")
        rec_mark = live_row.get("recommendation_mark")
        fcf = live_row.get("free_cash_flow_ttm")
        roe = live_row.get("return_on_equity_fq")
        debt_to_equity = live_row.get("debt_to_equity_fq")

        target_avg = live_row.get("price_target_average")
        target_high = live_row.get("price_target_high")
        target_low = live_row.get("price_target_low")
        target_median = live_row.get("price_target_median")
        rec_buy = live_row.get("recommendation_buy")
        rec_hold = live_row.get("recommendation_hold")
        rec_sell = live_row.get("recommendation_sell")
        target_upside = round(((target_avg - close_price) / close_price * 100.0), 1) if (target_avg and close_price) else None

        biz_summary = get_business_summary(ticker, live_row.get("sector", ""), live_row.get("industry", ""))

        # Key Support & Resistance calculation
        key_support = key_resistance = sl_calc = tp_calc = None
        support_desc = resistance_desc = "-"
        if not price_missing:
            sma20 = live_row.get("SMA20") or 0.0
            sma50 = live_row.get("SMA50") or 0.0
            sma200 = live_row.get("SMA200") or 0.0
            bb_lower = live_row.get("BB.lower") or 0.0
            bb_upper = live_row.get("BB.upper") or 0.0
            atr = live_row.get("ATR") or (close_price * 0.03)
            sl_calc = eval_result.get("stop_loss") or round(close_price - (1.5 * atr), 2)
            tp_calc = eval_result.get("take_profit") or round(close_price * 1.08, 2)

            if eval_result.get("key_support") and eval_result["key_support"] < close_price:
                key_support = eval_result["key_support"]
                support_desc = eval_result.get("support_desc", "แนวรับทางเทคนิค")
            elif sma200 > 0 and sma200 < close_price and (close_price - sma200) / close_price <= 0.08:
                key_support = round(sma200, 2)
                support_desc = "เส้น 200 วัน (SMA 200)"
            elif bb_lower > 0 and bb_lower < close_price:
                key_support = round(bb_lower, 2)
                support_desc = "ขอบล่าง Bollinger Band"
            else:
                key_support = round(sl_calc, 2)
                support_desc = "แนวรับความผันผวน 1.5 ATR"

            if eval_result.get("key_resistance") and eval_result["key_resistance"] > close_price:
                key_resistance = eval_result["key_resistance"]
                resistance_desc = eval_result.get("resistance_desc", "แนวต้านทางเทคนิค")
            elif sma200 > 0 and sma200 > close_price:
                key_resistance = round(sma200, 2)
                resistance_desc = "เส้น 200 วัน (SMA 200)"
            elif sma50 > 0 and sma50 > close_price:
                key_resistance = round(sma50, 2)
                resistance_desc = "เส้น 50 วัน (SMA 50)"
            elif sma20 > 0 and sma20 > close_price:
                key_resistance = round(sma20, 2)
                resistance_desc = "เส้น 20 วัน (SMA 20)"
            elif bb_upper > 0 and bb_upper > close_price:
                key_resistance = round(bb_upper, 2)
                resistance_desc = "ขอบบน Bollinger Band"
            elif target_avg and target_avg > close_price:
                key_resistance = round(target_avg, 2)
                resistance_desc = "ราคาเป้าหมายเฉลี่ยสถาบัน"
            else:
                key_resistance = round(tp_calc, 2)
                resistance_desc = "เป้าหมายรีบาวด์ Take-Profit"

        positions.append({
            "ticker": ticker,
            "data_missing": price_missing,
            "price_missing": price_missing,
            "name": h.get("name", live_row.get("description", ticker)),
            "business_summary": biz_summary,
            "exchange": h.get("exchange", "NASDAQ"),
            "shares": shares,
            "avg_cost_usd": avg_cost_usd,
            "avg_cost_thb": avg_cost_thb,
            "total_cost_usd": cost_usd,
            "cost_thb": cost_thb,
            "close_price": close_price,
            "change_pct": change_pct,
            "current_val_usd": current_val_usd,
            "current_val_thb": current_val_thb,
            "unrealized_pl_usd": unrealized_pl_usd,
            "unrealized_pl_thb": unrealized_pl_thb,
            "unrealized_pl_pct": unrealized_pl_pct,
            "daily_diff_usd": daily_diff_usd,
            "daily_diff_thb": daily_diff_thb,
            "rsi": eval_result.get("rsi"),
            "rsi_weekly": eval_result.get("rsi_weekly"),
            "stoch_k": eval_result.get("stoch_k"),
            "stoch_d": eval_result.get("stoch_d"),
            "mfi": eval_result.get("mfi"),
            "sma200": eval_result.get("sma200"),
            "ema200": eval_result.get("ema200"),
            "dist_sma200_pct": eval_result.get("dist_sma200_pct"),
            "dist_ema200_pct": eval_result.get("dist_ema200_pct"),
            "in_value_zone": eval_result.get("in_value_zone", False),
            "is_plunge_day": eval_result.get("is_plunge_day", False),
            "score": eval_result.get("score_points", 0.0),
            "stock_score": eval_result.get("stock_score"),
            "tier": eval_result.get("tier", "Watchlist"),
            "signal_tags": eval_result.get("signal_tags", []),
            "days_to_earnings": eval_result.get("days_to_earnings"),
            "earnings_date": eval_result.get("earnings_date_str", "-"),
            "is_earnings_near": eval_result.get("is_earnings_near", False),
            "key_support": key_support,
            "support_desc": support_desc,
            "key_resistance": key_resistance,
            "resistance_desc": resistance_desc,
            "stop_loss": sl_calc,
            "take_profit": tp_calc,
            "rr_ratio": eval_result.get("rr_ratio"),
            "tv_url": eval_result.get("tv_url", f"https://www.tradingview.com/chart/?symbol={h.get('exchange', 'NASDAQ')}:{ticker}"),
            "rev_growth_yoy": round(rev_g, 2) if rev_g is not None else None,
            "net_inc_growth_yoy": round(net_g, 2) if net_g is not None else None,
            "roe": round(roe, 2) if roe is not None else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity is not None else None,
            "peg": round(peg, 2) if peg is not None else None,
            "pe": round(pe, 2) if pe is not None else None,
            "rec_mark": round(rec_mark, 2) if rec_mark is not None else None,
            "fcf": fcf,
            "price_target_average": round(target_avg, 2) if target_avg else None,
            "price_target_high": round(target_high, 2) if target_high else None,
            "price_target_low": round(target_low, 2) if target_low else None,
            "target_upside_pct": target_upside,
            "rec_buy": rec_buy,
            "rec_hold": rec_hold,
            "rec_sell": rec_sell,
            "sector": live_row.get("sector") or "Other / Diversified",
            "industry": live_row.get("industry") or "-",
            "fundamental": eval_result.get("fundamental") or score_fundamentals(ticker, live_row.get("sector"), rev_g, net_g, roe, peg, debt_to_equity, fcf),
            "catalysts": all_catalysts.get(ticker, {}),
            "news": all_news.get(ticker, [])
        })

    # Calculate portfolio weights and flags
    for pos in positions:
        if pos["price_missing"]:
            weight_pct = 0.0
        else:
            weight_pct = (pos["current_val_usd"] / total_market_val_usd * 100.0) if total_market_val_usd > 0 else 0.0
        pos["weight_pct"] = weight_pct

        alerts = []
        if pos.get("data_missing"):
            alerts.append("⚠️ Data Missing")
        if weight_pct >= 50.0:
            alerts.append(f"🚨 Extreme Concentration ({weight_pct:.1f}%)")
        elif weight_pct >= 25.0:
            alerts.append(f"⚠️ Heavy Allocation ({weight_pct:.1f}%)")

        if pos["unrealized_pl_pct"] is not None and pos["unrealized_pl_pct"] <= -10.0:
            alerts.append(f"🔻 Drawdown ({pos['unrealized_pl_pct']:.1f}%)")

        if pos.get("is_earnings_near"):
            alerts.append(f"⚠️ Earnings in {pos.get('days_to_earnings')}d")

        pos["alerts"] = alerts
        pos["rating"] = compute_stock_rating(pos)
        pos["financial_health"] = compute_financial_health(pos)
        pos["forward_outlook"] = get_forward_outlook(
            ticker=pos["ticker"],
            data=live_dict.get(pos["ticker"], {}),
            fundamentals={
                "rev_growth_yoy": pos.get("rev_growth_yoy"),
                "net_inc_growth_yoy": pos.get("net_inc_growth_yoy"),
                "pe": pos.get("pe"),
                "peg": pos.get("peg"),
                "fcf": pos.get("fcf")
            },
            days_to_earnings=pos.get("days_to_earnings"),
            avg_cost=pos.get("avg_cost_usd"),
            close=pos.get("close_price")
        )

    # Sort positions by weight descending
    positions.sort(key=lambda x: x["current_val_usd"] if x["current_val_usd"] is not None else -1.0, reverse=True)
    priced = [p for p in positions if not p["price_missing"]]

    total_pl_usd = total_market_val_usd - total_cost_usd
    total_pl_thb = total_market_val_thb - total_cost_thb
    if base_currency == "THB":
        total_pl_pct = (total_pl_thb / total_cost_thb * 100.0) if total_cost_thb > 0 else 0.0
        total_daily_change_pct = (total_daily_change_thb / (total_market_val_thb - total_daily_change_thb) * 100.0) if (total_market_val_thb - total_daily_change_thb) > 0 else 0.0
    else:
        total_pl_pct = (total_pl_usd / total_cost_usd * 100.0) if total_cost_usd > 0 else 0.0
        total_daily_change_pct = (total_daily_change_usd / (total_market_val_usd - total_daily_change_usd) * 100.0) if (total_market_val_usd - total_daily_change_usd) > 0 else 0.0

    # Concentration risk score (HHI)
    hhi = sum((p["weight_pct"]) ** 2 for p in positions)
    concentration_level = "Extremely High" if hhi >= 5000 else ("High" if hhi >= 2500 else ("Moderate" if hhi >= 1500 else "Well Diversified"))

    # Portfolio weighted fundamental growth
    weighted_rev_growth = 0.0
    weighted_net_growth = 0.0
    weight_covered = 0.0
    for p in positions:
        if p["rev_growth_yoy"] is not None and p["net_inc_growth_yoy"] is not None:
            w = p["weight_pct"] / 100.0
            weighted_rev_growth += p["rev_growth_yoy"] * w
            weighted_net_growth += p["net_inc_growth_yoy"] * w
            weight_covered += w

    if weight_covered > 0:
        weighted_rev_growth = weighted_rev_growth / weight_covered
        weighted_net_growth = weighted_net_growth / weight_covered

    # Opportunities: stocks with low RSI or in Value Zone
    dip_opportunities = [
        p for p in positions
        if not p["price_missing"] and ((p["rsi"] is not None and p["rsi"] <= 35) or p["in_value_zone"] or (p["score"] >= 3.0))
    ]

    best_pos = max(priced, key=lambda x: x["unrealized_pl_pct"]) if priced else None
    worst_pos = min(priced, key=lambda x: x["unrealized_pl_pct"]) if priced else None

    # Sector distribution
    sector_distribution = {}
    for p in positions:
        sec = p.get("sector") or "Other / Diversified"
        sector_distribution[sec] = sector_distribution.get(sec, 0.0) + p["weight_pct"]
    sector_sorted = sorted(sector_distribution.items(), key=lambda x: x[1], reverse=True)

    # Overall Portfolio Health Score & Grade
    valid_star_positions = [pos for pos in positions if not pos.get("data_missing")]
    avg_stars = (sum(pos["rating"]["stars_count"] for pos in valid_star_positions) / len(valid_star_positions)) if valid_star_positions else 3.0
    health_score = 65.0
    
    # 1. Star Rating contribution
    if avg_stars >= 4.5:
        health_score += 20.0
    elif avg_stars >= 3.8:
        health_score += 15.0
    elif avg_stars >= 3.0:
        health_score += 10.0
    elif avg_stars < 2.5:
        health_score -= 10.0

    # 2. P/L contribution
    if total_pl_pct >= 15.0:
        health_score += 15.0
    elif total_pl_pct >= 5.0:
        health_score += 10.0
    elif total_pl_pct >= 0.0:
        health_score += 5.0
    elif total_pl_pct <= -15.0:
        health_score -= 15.0
    elif total_pl_pct < 0.0:
        health_score -= 5.0

    # 3. Diversification penalties
    if hhi >= 5000:
        health_score -= 15.0
    elif hhi >= 2500:
        health_score -= 8.0
    elif hhi <= 1500:
        health_score += 5.0

    # 4. Severe underwater penalty
    severe_losers = [p for p in priced if p["unrealized_pl_pct"] <= -20.0]
    if severe_losers:
        health_score -= (len(severe_losers) * 4.0)

    # 5. Imminent earnings risk
    earnings_near = [p for p in positions if p.get("is_earnings_near")]
    if len(earnings_near) >= 2:
        health_score -= 4.0

    health_score = max(10.0, min(99.0, health_score))

    if health_score >= 88.0:
        health_grade = "A+"
        health_status = "🟢 ยอดเยี่ยม แข็งแกร่งมาก"
        health_grade_desc = "พอร์ตมีความแข็งแกร่งสูงมาก หุ้นส่วนใหญ่มีพื้นฐานดี มีกำไร และไม่มีความเสี่ยงรุนแรง."
    elif health_score >= 80.0:
        health_grade = "A"
        health_status = "🟢 ปลอดภัย แข็งแกร่ง"
        health_grade_desc = "สุขภาพพอร์ตแข็งแรงดี สามารถถือลงทุนระยะยาวได้อย่างสบายใจ."
    elif health_score >= 70.0:
        health_grade = "B+"
        health_status = "🟡 สุขภาพดี มีจุดที่ต้องเฝ้าระวัง"
        health_grade_desc = "พอร์ตทำกำไรได้ดี แต่มีการกระจุกตัวของเงินในหุ้นตัวใดตัวหนึ่งมากเกินไป หรือมีหุ้นบางตัวติดลบ."
    elif health_score >= 60.0:
        health_grade = "B"
        health_status = "🟡 ปานกลาง ควรปรับสมดุล"
        health_grade_desc = "พอร์ตอยู่ในระดับประคองตัว ควรหาจังหวะลดการกระจุกตัวและควบคุมหุ้นที่ขาดทุน."
    elif health_score >= 50.0:
        health_grade = "C"
        health_status = "🟠 เปราะบาง มีความเสี่ยงขาดทุน"
        health_grade_desc = "พอร์ตเริ่มมีความเสี่ยง มีหุ้นติดลบหลายตัว ต้องวางแผนแก้ดอย."
    else:
        health_grade = "D"
        health_status = "🔴 เสี่ยงสูง ต้องรีบปรับพอร์ต"
        health_grade_desc = "พอร์ตขาดทุนหนักหรือมีความเสี่ยงรุนแรง ต้องใช้แผนกู้พอร์ตทันที."

    # Rank holdings for fresh capital rebalancing (ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม)
    buy_candidates = []
    forbidden_buys = []
    
    for p in priced:
        t = p["ticker"]
        w = p["weight_pct"]
        is_earn = p.get("is_earnings_near", False)
        stars = p.get("rating", {}).get("stars_count", 1)
        in_val = p.get("in_value_zone", False)
        dist_200 = p.get("dist_sma200_pct")
        upside = p.get("target_upside_pct") or 0.0
        
        is_plunge = p.get("is_plunge_day", False)
        
        # Disqualification checks
        if w >= 25.0:
            forbidden_buys.append({
                "ticker": t,
                "name": p["name"],
                "reason": f"สัดส่วนในพอร์ตสูงเกินเกณฑ์ความปลอดภัยแล้ว ({w:.1f}%) ห้ามซื้อเพิ่มเพื่อป้องกันความเสี่ยงกระจุกตัว ให้ถือรันเทรนด์."
            })
            continue
        if is_earn:
            forbidden_buys.append({
                "ticker": t,
                "name": p["name"],
                "reason": f"วันประกาศงบการเงินใกล้เข้ามาในอีก {p.get('days_to_earnings')} วัน ({p.get('earnings_date')}) มีความเสี่ยง Gap ผันผวน ห้ามซื้อเพิ่มก่อนวันงบออก."
            })
            continue
        if is_plunge:
            forbidden_buys.append({
                "ticker": t,
                "name": p["name"],
                "reason": "ราคาปรับตัวลดลงรุนแรงในวันนี้ (Plunge Day) ยังไม่มีแท่งเทียนยืนยันการกลับตัว ห้ามตั้งรับมีดที่กำลังหล่น."
            })
            continue
        fund = _fundamental(p)
        if fund["grade"] == "F":
            weak = ", ".join(m["label"] for m in fund["metrics"].values() if m["points"] == 0) or "พื้นฐานอ่อนแอ"
            forbidden_buys.append({
                "ticker": t,
                "name": p["name"],
                "reason": f"พื้นฐานได้เกรด F ({weak}) ยังไม่ควรเติมเงินเพิ่มจนกว่างบจะดีขึ้น."
            })
            continue

        # Score eligible holding for fresh cash
        score = float(stars) * 2.5
        if in_val:
            score += 3.5
        if dist_200 is not None and dist_200 >= 0:
            score += 2.0
        if not fund["applicable"]:
            score += 4.0  # Index ETF rebalancing priority to counter extreme single-stock concentration
        if w < 5.0:
            score += 2.0  # Room to increase allocation
        if upside > 15.0:
            score += 1.5
        if fund["pct"] is not None:
            score += fund["pct"] / 100.0 * 6.0

        p_copy = dict(p)
        p_copy["rebalance_score"] = score
        buy_candidates.append(p_copy)

    buy_candidates.sort(key=lambda x: x["rebalance_score"], reverse=True)

    return {
        "portfolio_name": portfolio_name,
        "broker": broker,
        "fx_rate_usd_thb": fx_rate,
        "base_currency": base_currency,
        "cash_balance_thb": float(portfolio_data.get("cash_balance_thb", 0.0)),
        "line_available_thb": float(portfolio_data.get("line_available_thb", 0.0)),
        "total_cost_usd": total_cost_usd,
        "total_cost_thb": total_cost_thb,
        "total_market_val_usd": total_market_val_usd,
        "total_market_val_thb": total_market_val_thb,
        "total_pl_usd": total_pl_usd,
        "total_pl_thb": total_pl_thb,
        "total_pl_pct": total_pl_pct,
        "total_daily_change_usd": total_daily_change_usd,
        "total_daily_change_thb": total_daily_change_thb,
        "total_daily_change_pct": total_daily_change_pct,
        "price_missing_tickers": price_missing_tickers,
        "unpriced_cost_usd": unpriced_cost_usd,
        "unpriced_cost_thb": unpriced_cost_thb,
        "hhi": hhi,
        "concentration_level": concentration_level,
        "health_score": round(health_score, 1),
        "health_grade": health_grade,
        "health_status": health_status,
        "health_grade_desc": health_grade_desc,
        "sector_sorted": sector_sorted,
        "weighted_rev_growth": round(weighted_rev_growth, 2) if weight_covered > 0 else None,
        "weighted_net_growth": round(weighted_net_growth, 2) if weight_covered > 0 else None,
        "positions": positions,
        "top_buy_candidates": buy_candidates[:3],
        "forbidden_buys": forbidden_buys,
        "dip_opportunities": dip_opportunities,
        "best_pos": best_pos,
        "worst_pos": worst_pos
    }


def _fmt_curr(val: float, sym: str = "$") -> str:
    sign = "+" if val > 0 else ("-" if val < 0 else "")
    return f"{sign}{sym}{abs(val):,.2f}"


def generate_portfolio_markdown(summary: Dict[str, Any]) -> str:
    """
    Format portfolio analysis into a comprehensive GitHub-style markdown report.
    """
    port_name = summary["portfolio_name"]
    broker = summary["broker"]
    fx = summary["fx_rate_usd_thb"]
    val_usd = summary["total_market_val_usd"]
    val_thb = summary["total_market_val_thb"]
    cost_usd = summary["total_cost_usd"]
    cost_thb = summary["total_cost_thb"]
    pl_usd = summary["total_pl_usd"]
    pl_thb = summary["total_pl_thb"]
    pl_pct = summary["total_pl_pct"]
    day_usd = summary["total_daily_change_usd"]
    day_thb = summary["total_daily_change_thb"]
    day_pct = summary["total_daily_change_pct"]
    conc_lvl = summary["concentration_level"]
    hhi = summary["hhi"]
    best_pos = summary.get("best_pos")
    worst_pos = summary.get("worst_pos")

    pl_str_usd = _fmt_curr(pl_usd, "$")
    pl_str_thb = _fmt_curr(pl_thb, "฿")
    day_str_usd = _fmt_curr(day_usd, "$")
    day_str_thb = _fmt_curr(day_thb, "฿")
    day_pct_sign = "+" if day_pct > 0 else ("-" if day_pct < 0 else "")
    pl_pct_sign = "+" if pl_pct > 0 else ("-" if pl_pct < 0 else "")

    earnings_near_stocks = [p for p in summary["positions"] if p.get("is_earnings_near")]

    lines = [
        f"# 📊 Portfolio Health & Performance Report",
        f"**Portfolio:** {port_name} | **Broker:** {broker} | **FX Rate:** {fx:.2f} THB/USD",
        "",
        "---",
        "",
        "## 👶 1. สรุปสถานะพอร์ตภาษาคน สำหรับมือใหม่ (Portfolio Layman Summary)",
        "",
        f"### 🏥 สุขภาพพอร์ตโดยรวม: เกรด {summary['health_grade']} ({summary['health_score']:.0f}/100 คะแนน) {summary['health_status']}",
        f"- 💡 **ความหมายสำหรับมือใหม่:** {summary['health_grade_desc']}",
        ""
    ]

    is_thb = summary.get("base_currency") == "THB"

    # Overall layman health
    if pl_usd >= 0:
        health_txt = f"พอร์ตโดยรวมอยู่ในแดนบวก มีกำไรสุทธิรวม {pl_str_thb} ({pl_str_usd}) หรือคิดเป็น {pl_pct_sign}{abs(pl_pct):.2f}% ของเงินต้น." if is_thb else f"พอร์ตโดยรวมอยู่ในแดนบวก มีกำไรสุทธิรวม {pl_str_usd} ({pl_str_thb}) หรือคิดเป็น {pl_pct_sign}{abs(pl_pct):.2f}% ของเงินต้น."
    else:
        health_txt = f"พอร์ตโดยรวมกำลังติดลบ ขาดทุนสุทธิรวม {pl_str_thb} ({pl_str_usd}) หรือคิดเป็น {pl_pct_sign}{abs(pl_pct):.2f}% ของเงินต้น." if is_thb else f"พอร์ตโดยรวมกำลังติดลบ ขาดทุนสุทธิรวม {pl_str_usd} ({pl_str_thb}) หรือคิดเป็น {pl_pct_sign}{abs(pl_pct):.2f}% ของเงินต้น."

    lines.append(f"- 💰 **ภาพรวมสุขภาพเงินลงทุน:** {health_txt}")

    curr_sym = "฿" if is_thb else "$"

    if best_pos:
        target_info = f" สถาบันการเงินให้ราคาเป้าหมายเฉลี่ยที่ {curr_sym}{best_pos['price_target_average']:,.2f} (Upside {best_pos['target_upside_pct']:+.1f}%)." if best_pos.get("price_target_average") else ""
        best_pl_disp = _fmt_curr(best_pos['unrealized_pl_thb'], '฿') if is_thb else _fmt_curr(best_pos['unrealized_pl_usd'], '$')
        lines.append(
            f"- 🚀 **ฮีโร่แบกพอร์ต (ตัวทำเงินสูงสุด):** **[{best_pos['ticker']}]** {best_pos['name']} "
            f"ทำกำไร {best_pos['unrealized_pl_pct']:+.2f}% ({best_pl_disp}) "
            f"โดยทำธุรกิจ{best_pos.get('business_summary', '-')}. มีสัดส่วน {best_pos['weight_pct']:.1f}% ของพอร์ต.{target_info}"
        )

    if worst_pos:
        target_info = f" สถาบันการเงินให้ราคาเป้าหมายเฉลี่ยที่ {curr_sym}{worst_pos['price_target_average']:,.2f} (Upside {worst_pos['target_upside_pct']:+.1f}%)." if worst_pos.get("price_target_average") else ""
        worst_pl_disp = _fmt_curr(worst_pos['unrealized_pl_thb'], '฿') if is_thb else _fmt_curr(worst_pos['unrealized_pl_usd'], '$')
        lines.append(
            f"- 🔻 **ตัวฉุดดอยหนัก (ตัวขาดทุนสูงสุด):** **[{worst_pos['ticker']}]** {worst_pos['name']} "
            f"ติดลบ {worst_pos['unrealized_pl_pct']:.2f}% ({worst_pl_disp}) "
            f"โดยทำธุรกิจ{worst_pos.get('business_summary', '-')}. มีสัดส่วน {worst_pos['weight_pct']:.1f}% ของพอร์ต.{target_info}"
        )

    top_picks = summary.get("top_buy_candidates", [])
    if top_picks:
        top_names = [f"**[{p['ticker']}]** {p['name']}" for p in top_picks[:3]]
        picks_str = ", ".join([f"อันดับ {i+1} คือ {name}" for i, name in enumerate(top_names)])
        lines.append(
            f"- 💵 **ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม:** {picks_str} "
            f"(ระบบคัดกรองจากคะแนนดาว, จุดรับ Value Zone และช่วยลดความเสี่ยงกระจุกตัว ดูรายละเอียดราคาตั้งซื้อในหมวด 7 ด้านล่าง)."
        )
    else:
        lines.append("- 💵 **ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม:** ปัจจุบันหุ้นทุกตัวในพอร์ตยังไม่ผ่านเกณฑ์การเติมเงินเพิ่ม (ติดเงื่อนไขสัดส่วนสูงเกินเกณฑ์ หรือกำไรหดตัว) แนะนำถือเงินสดสำรองไว้ก่อน.")

    lines.append("- 💡 **เช็กลิสต์ 3 ข้อที่มือใหม่ต้องทำทันที (Immediate Action Checklist):**")
    if worst_pos and worst_pos["unrealized_pl_pct"] <= -10.0:
        lines.append(f"  1. **ห้ามรีบถัวเฉลี่ยหุ้นที่กำลังดิ่ง:** หุ้น {worst_pos['ticker']} กำลังปรับฐานหนัก ห้ามเติมเงินถัวจนกว่ากราฟจะเริ่มยืนสร้างฐานหรือมีสัญญาณกลับตัวชัดเจน.")
    else:
        lines.append("  1. **ควบคุมความเสี่ยงการถือครอง:** ไม่มีหุ้นตัวใดในพอร์ตที่ติดลบรุนแรงเกินเกณฑ์ควบคุมความเสี่ยง.")

    if earnings_near_stocks:
        earn_tickers = ", ".join([p["ticker"] for p in earnings_near_stocks])
        lines.append(f"  2. **ระวังวันประกาศงบการเงิน (Earnings Risk Guard):** หุ้น {earn_tickers} กำลังจะประกาศงบใน 14 วันข้างหน้า ราคาจะผันผวนสูง ห้ามใส่เงินเพิ่มก่อนวันงบออก.")
    else:
        lines.append("  2. **ปฏิทินงบการเงินปลอดภัย:** ในระยะ 14 วันข้างหน้า ไม่มีหุ้นในพอร์ตที่มีกำหนดประกาศงบ.")

    if best_pos and best_pos["unrealized_pl_pct"] > 0:
        lines.append(f"  3. **ปล่อยให้กำไรวิ่งต่อ (Let Profits Run):** หุ้น {best_pos['ticker']} อยู่ในเทรนด์ขาขึ้นแข็งแกร่ง ให้ถือตามระบบต่อไปเพื่อรับผลตอบแทนระยะยาว.")
    else:
        lines.append("  3. **ถือครองเงินสดสำรอง:** รักษาวินัยการลงทุนและรอจังหวะ Rebound.")

    # Fundamental Health & PEG Layman Overview
    def _grade_code(p):
        return p.get("financial_health", {}).get("grade_code")
    strong_health = [p for p in summary["positions"] if _grade_code(p) in ("A+", "A")]
    stretched_health = [p for p in summary["positions"] if _grade_code(p) in ("B", "C")]
    weak_health = [p for p in summary["positions"] if _grade_code(p) == "F"]

    health_summary_parts = []
    if strong_health:
        s_names = ", ".join([f"**[{p['ticker']}]** (PEG {p.get('peg', '-')})" for p in strong_health])
        health_summary_parts.append(f"หุ้นงบการเงินยอดเยี่ยมเติบโตสูงและราคาคุ้มค่า (เกรด A/A+): {s_names}")
    if stretched_health:
        st_names = ", ".join([f"**[{p['ticker']}]** ({p.get('financial_health', {}).get('peg_verdict', '-')})" for p in stretched_health])
        health_summary_parts.append(f"หุ้นระดับปานกลาง/ราคาตึงตัว (เกรด B/C): {st_names}")
    if weak_health:
        w_names = ", ".join([f"**[{p['ticker']}]**" + (f" (กำไรหดตัว {p['net_inc_growth_yoy']:+.1f}%)" if p.get('net_inc_growth_yoy') is not None else "") for p in weak_health])
        health_summary_parts.append(f"หุ้นที่ต้องเฝ้าระวังงบหดตัว (เกรด F): {w_names}")

    if health_summary_parts:
        lines.append("- 🔬 **สรุปสุขภาพงบการเงินและค่า PEG ของหุ้นในพอร์ต:** " + " | ".join(health_summary_parts) + ".")

    lines.extend([
        "",
        "---",
        "",
        "## 💼 2. ภาพรวมตัวเลขทางการเงินและการกระจายความเสี่ยง (Financial Overview & Sector Allocation)",
        "",
        f"- Current Portfolio Value: ${val_usd:,.2f} USD (฿{val_thb:,.2f} THB).",
        f"- Total Invested Cost: ${cost_usd:,.2f} USD (฿{cost_thb:,.2f} THB).",
        f"- Total Unrealized P/L: {pl_str_usd} USD ({pl_str_thb} THB) | **{pl_pct_sign}{abs(pl_pct):.2f}%**.",
        f"- Today's P/L Change: {day_str_usd} USD ({day_str_thb} THB) | **{day_pct_sign}{abs(day_pct):.2f}%**.",
        f"- Portfolio Concentration: {conc_lvl} (HHI Score: {hhi:.0f}).",
    ])

    if summary.get("weighted_rev_growth") is not None:
        lines.append(f"- Portfolio Weighted Revenue YoY Growth: **{summary['weighted_rev_growth']:+.1f}%**.")
    if summary.get("weighted_net_growth") is not None:
        lines.append(f"- Portfolio Weighted Net Income YoY Growth: **{summary['weighted_net_growth']:+.1f}%**.")

    # Sector table
    lines.extend([
        "",
        "### 🍰 สัดส่วนการลงทุนแยกตามกลุ่มธุรกิจ (Sector Allocation)",
        "",
        "| กลุ่มธุรกิจ (Sector) | สัดส่วนเงินลงทุน | การประเมินสำหรับมือใหม่ |",
        "| :--- | :---: | :--- |"
    ])
    SECTOR_TRANSLATION = {
        "Health Technology": "สุขภาพและชีวเวชภัณฑ์ (Health Technology)",
        "Technology Services": "เทคโนโลยีและซอฟต์แวร์ (Technology Services)",
        "Electronic Technology": "เทคโนโลยีและอิเล็กทรอนิกส์ (Electronic Tech)",
        "Finance": "การเงินและการธนาคาร (Finance)",
        "Consumer Services": "บริการและท่องเที่ยว (Consumer Services)",
        "Consumer Non-Durables": "สินค้าอุปโภคบริโภค (Consumer Goods)",
        "Consumer Durables": "สินค้าคงทน (Consumer Durables)",
        "Utilities": "สาธารณูปโภคและพลังงาน (Utilities)",
        "Miscellaneous": "กองทุนดัชนีรวม (Index ETF / Diversified)",
    }
    for sec_name, sec_pct in summary.get("sector_sorted", []):
        sec_label = SECTOR_TRANSLATION.get(sec_name, sec_name)
        if sec_pct >= 40.0:
            eval_txt = f"⚠️ สัดส่วนสูงมาก ({sec_pct:.1f}%) ระวังความผันผวนเฉพาะกลุ่ม"
        elif sec_pct >= 20.0:
            eval_txt = "🟢 สัดส่วนเหมาะสม เป็นแกนหลักของพอร์ต"
        else:
            eval_txt = "⚪ สัดส่วนกระจายตัว กระจายความเสี่ยงได้ดี"
        lines.append(f"| {sec_label} | **{sec_pct:.1f}%** | {eval_txt} |")

    lines.extend([
        "",
        "---",
        "",
        "## 📈 3. สรุปสถานะการถือครอง (Current Holdings & Technical Status)",
        "",
        "| Ticker | บริษัท & ลักษณะธุรกิจ | Rating | สัดส่วน | ทุนเฉลี่ย | ราคาตลาด | แนวรับ / แนวต้าน | มูลค่า ($ / ฿) | กำไร/ขาดทุน | 1D Chg | Daily RSI | 200D Trend | สถานะ |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ])

    for p in summary["positions"]:
        t = p["ticker"]
        name = p["name"][:14] + (".." if len(p["name"]) > 14 else "")
        biz = p.get("business_summary", "")
        r = p.get("rating", {})
        stars = f'{r.get("stars_str", "⭐")}<br><small>{format_score(p.get("stock_score"))}</small>'
        avg_c = f"${p['avg_cost_usd']:,.2f}"
        if p.get("price_missing"):
            price = supp_res = val_str = pl_str = "n/a"
        else:
            price = f"${p['close_price']:,.2f}"
            supp_res = f"รับ ${p['key_support']:.2f}<br>ต้าน ${p['key_resistance']:.2f}"
            val_str = f"${p['current_val_usd']:,.2f}<br>฿{p['current_val_thb']:,.0f}"
            pl_color = "+" if p['unrealized_pl_usd'] >= 0 else ""
            pl_str = f"**{pl_color}{p['unrealized_pl_pct']:.2f}%**<br>({pl_color}${p['unrealized_pl_usd']:,.2f})"

        day_c = "+" if p['change_pct'] >= 0 else ""
        day_str = f"{day_c}{p['change_pct']:.2f}%"

        rsi_val = f"{p['rsi']:.1f}" if p['rsi'] is not None else "-"
        if p['rsi'] is not None and p['rsi'] <= 30:
            rsi_val += " 🚨"
        elif p['rsi'] is not None and p['rsi'] <= 35:
            rsi_val += " 📉"

        if p['dist_sma200_pct'] is not None:
            sign_t = "+" if p['dist_sma200_pct'] >= 0 else ""
            trend_str = f"{sign_t}{p['dist_sma200_pct']:.1f}% vs 200D"
            if p['in_value_zone']:
                trend_str += " 💎"
        else:
            trend_str = "-"

        tags = []
        if p["alerts"]:
            tags.extend(p["alerts"])
        if p.get("in_value_zone"):
            tags.append("💎 Value Zone")
        status_str = " ".join(tags) if tags else "Normal"

        chart_link = f"[{t}]({p['tv_url']})"
        weight_str = f"**{p['weight_pct']:.1f}%**"

        lines.append(
            f"| **{chart_link}** | {name}<br><small>*{biz}*</small> | {stars} | {weight_str} | {avg_c} | {price} | {supp_res} | {val_str} | {pl_str} | {day_str} | {rsi_val} | {trend_str} | {status_str} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 🔬 4. ภาพรวมงบการเงินและราคาเป้าหมายจากสถาบัน (Fundamentals & Institutional Target Prices)",
        "",
        "| Ticker | บริษัท | สุขภาพงบ | Rev YoY | Net Inc YoY | ROE | D/E | PEG | ประเมิน PEG | P/E | กระแสเงินสด (FCF) | เป้าหมายสถาบัน (Upside) | มติสถาบัน | ปฏิทินงบ |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ])

    for p in summary["positions"]:
        t = p["ticker"]
        name = p["name"][:14]
        fh = p.get("financial_health", {})
        h_badge = fh.get("health_badge", "-")
        peg_verdict = fh.get("peg_verdict", "-")
        fcf_str = fh.get("fcf_str", "-")
        rev_g = f"{p['rev_growth_yoy']:+.1f}%" if p['rev_growth_yoy'] is not None else "-"
        net_g = f"{p['net_inc_growth_yoy']:+.1f}%" if p['net_inc_growth_yoy'] is not None else "-"
        roe_val = f"{p['roe']:+.1f}%" if p.get('roe') is not None else "-"
        de_val = f"{p['debt_to_equity']:.2f}" if p.get('debt_to_equity') is not None else "-"
        peg_str = f"{p['peg']:.2f}" if p['peg'] is not None else "-"
        pe_str = f"{p['pe']:.1f}x" if p['pe'] is not None else "-"

        t_avg = f"${p['price_target_average']:,.2f}" if p.get('price_target_average') else "-"
        t_up = f"({p['target_upside_pct']:+.1f}%)" if p.get('target_upside_pct') is not None else ""
        target_str = f"**{t_avg}** {t_up}" if p.get('price_target_average') else "-"

        b = p.get('rec_buy')
        h = p.get('rec_hold')
        s = p.get('rec_sell')
        if b is not None:
            votes_str = f"🟢{b} 🟡{h} 🔴{s}"
        else:
            votes_str = "-"

        earn_str = f"{p['earnings_date']} ({p['days_to_earnings']}d)" if p['days_to_earnings'] is not None else "-"
        if p["is_earnings_near"]:
            earn_str = f"⚠️ **{earn_str}**"

        lines.append(
            f"| **[{t}]({p['tv_url']})** | {name} | {h_badge} | {rev_g} | {net_g} | {roe_val} | {de_val} | {peg_str} | {peg_verdict} | {pe_str} | {fcf_str} | {target_str} | {votes_str} | {earn_str} |"
        )

    # Beginner Cheat Sheet & 5 Golden Rules
    lines.extend([
        "",
        "### 📖 พจนานุกรมแปลศัพท์ฉบับ 1 บรรทัด สำหรับคนไม่เคยเล่นหุ้น (Beginner Cheat Sheet)",
        "- **สุขภาพงบการเงิน (Financial Health Grade):** วัดความแข็งแกร่งจากอัตราเติบโตของยอดขายและกำไรสุทธิ ควบคู่กับความถูกแพงของค่า PEG.",
        "- **Rev YoY (การเติบโตของยอดขาย):** รายได้เทียบกับช่วงเดียวกันของปีก่อนหน้า ตัวเลขเป็นบวกแปลว่าบริษัทยังค้าขายดีและเติบโต.",
        "- **Net Inc YoY (การเติบโตของกำไรสุทธิ):** กำไรสุทธิเทียบกับปีก่อนหน้า บ่งบอกว่าบริษัทหาเงินเข้ากระเป๋าได้เก่งขึ้นจริงหรือไม่.",
        "- **PEG Ratio (ความคุ้มค่าเทียบการเติบโต):** ราคาหุ้นหารด้วยอัตราเติบโตกำไร (P/E ÷ Growth Rate). ค่าต่ำกว่า 1.0 คือราคาถูกมาก คุ้มค่าสะสม.",
        "- **FCF (Free Cash Flow - กระแสเงินสดอิสระ):** เงินสดแท้จริงที่เหลือหลังจากหักค่าใช้จ่ายลงทุนทั้งหมด เป็นสายป่านทางการเงินของกิจการ.",
        "- **P/E Ratio (อัตราส่วนราคาต่อกำไร):** บอกจำนวนปีคืนทุนหากบริษัททำกำไรเท่าเดิม หุ้นปลอดภัยส่วนใหญ่ P/E ไม่ควรสูงเกินไปเมื่อเทียบกับอุตสาหกรรม.",
        "- **Daily RSI (ดัชนีวัดแรงซื้อขาย):** สเกล 0 ถึง 100 ถ้าต่ำกว่า 30 แปลว่าคนเทขายมากเกินไป (Oversold) มักเป็นจุดที่มีโอกาสเด้งกลับ.",
        "- **200D Trend (เส้นค่าเฉลี่ย 200 วัน):** ถ้าอยู่เหนือเส้น 200 วัน แสดงว่าภาพรวมระยะยาวยังเป็นแนวโน้มขาขึ้นที่แข็งแรง.",
        "- **เป้าหมายเฉลี่ยสถาบัน (Upside):** ราคาเป้าหมายที่นักวิเคราะห์และสถาบันการเงินวอลล์สตรีทประเมินมูลค่าพื้นฐานไว้ในระยะ 1 ปี.",
        "",
        "### 🛡️ กฎเหล็ก 5 ข้อห้ามเด็ดขาดของมือใหม่ (The 5 Golden Rules for Beginners)",
        "1. **ห้ามถัวหุ้นที่กำไรหดตัวหรือกำลังมีคดีความ:** ยิ่งถัวเงินจะยิ่งจม อย่าเอาเงินดีไปถมในธุรกิจที่กำลังมีปัญหา.",
        "2. **ห้ามทุ่มเงินซื้อไม้เดียวหมดหน้าตัก:** ให้แบ่งเงินเป็น 2 ถึง 3 ไม้เสมอ เพราะตลาดมีโอกาสย่อตัวลงมาทดสอบแนวรับอีกครั้ง.",
        "3. **ห้ามซื้อหุ้นก่อนวันประกาศงบการเงิน 14 วัน:** วันประกาศงบราคามักผันผวนรุนแรงเหมือนแทงหวย ควรรอให้งบออกเสร็จสิ้นก่อน.",
        "4. **ห้ามขายหุ้นที่กำลังทำกำไรเพื่อเอาเงินไปถัวหุ้นที่ขาดทุนหนัก:** ยึดหลักการอย่าตัดดอกไม้ทิ้งเพื่อไปรดน้ำวัชพืช.",
        "5. **ห้ามถือหุ้นโดยไม่มีจุดตัดขาดทุน (Stop Loss):** การยอมขาดทุนเล็กน้อย 5% ถึง 8% แก้ไขได้ง่ายกว่าการปล่อยให้ติดลบ 50%."
    ])

    lines.extend([
        "",
        "---",
        "",
        "## ⚖️ 5. ตาชั่งข่าวดี vs ข่าวร้ายของหุ้นในพอร์ต (Bullish vs Bearish Catalysts)",
        ""
    ])

    for p in summary["positions"]:
        t = p["ticker"]
        cat = p.get("catalysts", {})
        bullish = cat.get("bullish", [])
        bearish = cat.get("bearish", [])
        biz = p.get("business_summary", "")

        lines.append(f"### ⚖️ [{t}] {p['name']} - *{biz}*")
        lines.append("🟢 **ข่าวดีและปัจจัยบวก (Bullish Catalysts):**")
        if bullish:
            for b in bullish:
                title_link = f"[{b['title']}]({b['link']})" if b.get("link") else b["title"]
                lines.append(f"- **[{b['source']}]** {title_link} *({b['published']})*")
        else:
            lines.append("- ยังไม่มีข่าวด้านบวกโดดเด่นในรอบสัปดาห์นี้.")

        lines.append("🔴 **ข่าวร้ายและความเสี่ยงที่ต้องระวัง (Bearish Risks):**")
        if bearish:
            for b in bearish:
                title_link = f"[{b['title']}]({b['link']})" if b.get("link") else b["title"]
                lines.append(f"- **[{b['source']}]** {title_link} *({b['published']})*")
        else:
            lines.append("- ไม่มีข่าวร้ายรุนแรงในระยะสั้น.")

        if p.get("price_missing"):
            lines.append("- ⚠️ ไม่มีราคาตลาดล่าสุด (price missing) จึงไม่คำนวณกำไรขาดทุนและแนวรับแนวต้าน.\n")
            continue

        if p.get("price_target_average"):
            b_cnt = p.get('rec_buy') or 0
            h_cnt = p.get('rec_hold') or 0
            s_cnt = p.get('rec_sell') or 0
            lines.append("🎯 **มุมมองราคาเป้าหมายจากสถาบันการเงิน (Wall Street Targets):**")
            lines.append(
                f"- ราคาเฉลี่ยที่สถาบันให้: **${p['price_target_average']:,.2f}** "
                f"(โอกาสทำกำไร Upside: **{p['target_upside_pct']:+.1f}%** จากราคาตลาด ${p['close_price']:,.2f})."
            )
            if p.get('price_target_low') is not None and p.get('price_target_high') is not None:
                lines.append(
                    f"- กรอบราคาต่ำสุด ถึง สูงสุดที่สถาบันประเมิน: **${p['price_target_low']:,.2f} - ${p['price_target_high']:,.2f}**."
                )
            lines.append(
                f"- มตินักวิเคราะห์จากสถาบัน: **{b_cnt} สถาบันแนะนำซื้อ**, **{h_cnt} สถาบันแนะนำถือ**, **{s_cnt} สถาบันแนะนำขาย**."
            )

        # Beginner explanation
        lines.append("👶 **สรุปภาษาคน สำหรับมือใหม่:**")
        pl_p = p["unrealized_pl_pct"]
        if pl_p >= 10.0:
            verdict_text = f"หุ้นตัวนี้กำลังทำกำไรโดดเด่น ({pl_p:+.1f}%) เทรนด์ขาขึ้นชัดเจน ปล่อยให้ผลกำไรทำงานต่อไป."
        elif pl_p >= 0.0:
            verdict_text = f"หุ้นตัวนี้อยู่ในแดนบวก ({pl_p:+.1f}%) กราฟเทคนิคทรงตัวปกติ ถือต่อตามแผนได้."
        elif pl_p >= -8.0:
            verdict_text = f"หุ้นตัวนี้ย่อตัวเล็กน้อย ({pl_p:.1f}%) ยังเป็นการพักฐานตามปกติ ไม่น่ากังวล."
        else:
            verdict_text = f"หุ้นตัวนี้ติดลบลึก ({pl_p:.1f}%) อยู่ในช่วงปรับฐานหนัก ห้ามรีบร้อนซื้อถัวเฉลี่ย รอสัญญาณกลับตัว."

        if p.get("is_earnings_near"):
            verdict_text += f" กำลังจะประกาศงบในอีก {p.get('days_to_earnings')} วัน ระวังความผันผวนของราคา."

        lines.append(f"- {verdict_text}")
        lines.append(f"- **แนวรับสำคัญ:** **${p['key_support']:.2f} USD** ({p['support_desc']}) | **แนวต้านสำคัญ:** **${p['key_resistance']:.2f} USD** ({p['resistance_desc']}) | **จุดตัดขาดทุน (SL):** ${p['stop_loss']:.2f} USD.\n")

    lines.extend([
        "---",
        "",
        "## ⭐ 6. วิเคราะห์เจาะลึกหุ้นรายตัวและคะแนนดาว",
        ""
    ])

    for p in summary["positions"]:
        r = p.get("rating", {})
        lines.extend([
            f"### {p['ticker']} ({p['name']})",
            f"- คะแนน {r.get('stars_str', '⭐')} ({r.get('stars_count', 1)}/5 ดาว) {r.get('grade', '')} • {format_score(p.get('stock_score'))}.",
            f"- เหตุผลของคะแนน {', '.join((p.get('stock_score') or {}).get('reasons', [])) or '-'}.",
            f"- ภาพรวม {r.get('summary', '')}",
            f"- จุดเด่น {r.get('strength', '')}",
            f"- ข้อควรระวัง {r.get('risk', '')}",
            f"- คำแนะนำ {r.get('action', '')}",
            ""
        ])

    lines.extend([
        "---",
        "",
        "## 💵 7. ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม? (Fresh Capital Rebalancing & Top Picks)",
        ""
    ])

    top_picks = summary.get("top_buy_candidates", [])
    if top_picks:
        lines.append("### 🏆 3 อันดับหุ้นในพอร์ตที่น่าซื้อเพิ่มที่สุด (Top Rebalancing Buys)")
        lines.append("")
        medals = ["🥇 อันดับ 1", "🥈 อันดับ 2", "🥉 อันดับ 3"]
        for idx, pick in enumerate(top_picks[:3]):
            medal = medals[idx] if idx < len(medals) else f"อันดับ {idx+1}"
            t = pick["ticker"]
            name = pick["name"]
            stars = pick.get("rating", {}).get("stars_str", "⭐")
            w = pick["weight_pct"]
            c = pick["close_price"]
            sl = pick.get("stop_loss") or (c * 0.95)
            buy_supp = pick.get("key_support")
            if not buy_supp or buy_supp >= c:
                buy_supp = round(c * 0.98, 2)
            res_tp = pick.get("key_resistance")
            if not res_tp or res_tp <= c:
                res_tp = round(c * 1.08, 2)
            biz = pick.get("business_summary", "")

            # Beginner Reason
            reason = top_pick_reason(pick, lambda v: f"{curr_sym}{v:,.2f}")

            lines.extend([
                f"#### {medal}: [{t}] {name} ({stars})",
                f"- **ธุรกิจ:** {biz}.",
                f"- **เหตุผลสำหรับมือใหม่:** {reason}",
                f"- **สัดส่วนในพอร์ตปัจจุบัน:** {w:.1f}% (ยังมีพื้นที่ให้เพิ่มสัดส่วนเพื่อถ่วงน้ำหนักพอร์ตได้).",
                f"- **ราคาตลาด:** {curr_sym}{c:,.2f} | **แนวรับที่ควรตั้งซื้อ (Limit Order):** **{curr_sym}{buy_supp:,.2f}** ({pick.get('support_desc', 'จุดรับ')}) | **แนวต้านเป้าหมาย (TP):** **{curr_sym}{res_tp:,.2f}** ({pick.get('resistance_desc', 'จุดขายทำกำไร')}) | **จุดตัดขาดทุน (SL):** {curr_sym}{sl:,.2f}.",
                ""
            ])
    else:
        lines.append("- ขณะนี้ไม่มีหุ้นในพอร์ตที่เข้าเกณฑ์เหมาะสมสำหรับการเติมเงินใหม่ ควรรอจังหวะตลาด.\n")

    forbidden = summary.get("forbidden_buys", [])
    if forbidden:
        lines.extend([
            "### 🚫 หุ้นในพอร์ตที่ \"ห้ามซื้อเพิ่มเด็ดขาด\" ในตอนนี้ (Strictly Disqualified)",
            ""
        ])
        for fb in forbidden:
            lines.append(f"- ❌ **[{fb['ticker']}] {fb['name']}:** {fb['reason']}")
        lines.append("")

    lines.extend([
        "### 💡 โอกาสช้อนซื้อตามสัญญาณเทคนิคในพอร์ต (Technical Dip Setups)",
        ""
    ])

    if summary["dip_opportunities"]:
        for d in summary["dip_opportunities"]:
            tags_str = ", ".join(d["signal_tags"]) if d["signal_tags"] else "Oversold Pullback"
            lines.append(
                f"- **{d['ticker']}** ({d['name']}) ราคา {curr_sym}{d['close_price']:,.2f} Daily RSI {d['rsi']} กำไรขาดทุน {d['unrealized_pl_pct']:+.2f}%. สัญญาณเทคนิค {tags_str}. แนวรับ Stop Loss ที่ {curr_sym}{d['stop_loss']} และเป้าหมาย Take Profit ที่ {curr_sym}{d['take_profit']} (R:R {d['rr_ratio']}x)."
            )
    else:
        lines.append("- ไม่มีหุ้นในพอร์ตที่เข้าเงื่อนไข Oversold ลึกในวันนี้.")

    lines.extend([
        "",
        "---",
        "### ⚠️ ข้อสงวนสิทธิ์และความเสี่ยง (Risk Disclaimer)",
        "รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลอัตโนมัติจากข้อมูลตลาดสาธารณะ เพื่อเป็นข้อมูลประกอบการตัดสินใจและให้ความรู้เท่านั้น ไม่ใช่คำแนะนำในการลงทุน ซื้อ หรือขายหลักทรัพย์ ผู้ลงทุนต้องศึกษาข้อมูล ทำความเข้าใจความเสี่ยง และใช้วิจารณญาณของตนเองก่อนการตัดสินใจลงทุนทุกครั้ง.",
        "",
        "---",
        "*Report generated using TradingView Screener live scanner engine and Google News RSS.*"
    ])

    return "\n".join(lines)
