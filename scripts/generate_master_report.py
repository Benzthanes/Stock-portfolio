"""
Master Portfolio & Account Summary Engine
Aggregates:
1. KKP Official Statement (Deposits & Cash)
2. Live Active Holdings (from TradingView API)
3. Closed Realized Trades Ledger (trades.json)
4. Dividend Stream
5. Complete Buy Orders Ledger (55 buy orders from OCR with accurate execution dates)
6. Complete Cash Flow & Deposit Ledger (54 transactions from KKP Statement & Dime! Save since account opening)
into one single interactive HTML Master Dashboard and CLI summary.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.portfolio import load_portfolio, analyze_portfolio
from src.trades import load_trades, calculate_trades_summary
from src.html_report import get_chart_modal_component, _make_chart_onclick

MONTH_MAP = {
    "มค": 1, "กพ": 2, "มีค": 3, "เมย": 4, "พค": 5, "มิย": 6,
    "กค": 7, "สค": 8, "กย": 9, "ตค": 10, "พย": 11, "ธค": 12
}


def parse_num(val_str):
    if not val_str:
        return 0.0
    s = re.sub(r"[^\d\.\-]", "", str(val_str))
    try:
        return float(s)
    except:
        return 0.0


def parse_thai_date(date_str):
    if not date_str:
        return (0, 0, 0, 0, 0, 0)
    m = re.search(r"(\d{1,2})\s+([^\s]+)\s+(\d{2,4})\s*-\s*(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", str(date_str))
    if m:
        day = int(m.group(1))
        raw_m = re.sub(r"[\.\s]", "", m.group(2))
        month = MONTH_MAP.get(raw_m, 0)
        year = int(m.group(3))
        if year < 100:
            year += 2000 - 43
        elif year > 2500:
            year -= 543
        hour = int(m.group(4))
        minute = int(m.group(5))
        second = int(m.group(6)) if m.group(6) else 0
        return (year, month, day, hour, minute, second)
    return (0, 0, 0, 0, 0, 0)


def load_ocr_buy_orders():
    ocr_path = Path("data/.ocr_extracted.json")
    if not ocr_path.exists():
        return []
    with open(ocr_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    buy_orders = []

    for item in ocr_data:
        fn = item.get("filename", "")
        lines = item.get("lines", [])
        text = "\n".join(lines)
        full_str = " ".join(lines)

        # Parse Buy Orders
        if "รายละเอียดคำสั่ง" in full_str and re.search(r"ซื้อ\s+[A-Z0-9]+", full_str):
            ticker_m = re.search(r"ซื้อ\s+([A-Z0-9]+)", full_str)
            ticker = ticker_m.group(1) if ticker_m else "UNKNOWN"

            # Shares
            shares = 0.0
            sh_m = re.search(r"จำนวนหุ้น\s*\n*([\d\.]+)", text)
            if not sh_m:
                sh_m = re.search(r"([\d\.]+)\s*\n*จำนวนหุ้น", text)
            if not sh_m:
                sh_m = re.search(r"([\d\.]+)\s*หุ้น", text)
            if sh_m:
                shares = parse_num(sh_m.group(1))

            # Exec price
            price_usd = 0.0
            p_m = re.search(r"[ร]?าคาที่ได้จริง[\s\S]*?([\d\.\,]+)\s*USD", text)
            if not p_m:
                p_m = re.search(r"ราคาที่คุณตั้ง\s*[\.\s]*\n*([\d\.\,]+)\s*USD", text)
            if p_m:
                price_usd = parse_num(p_m.group(1))

            # Amounts USD
            amt_usd = 0.0
            u_m = re.search(r"จำนวนเงิน\s*\(USD\)\s*\n*([\d\.\,]+)\s*USD", text)
            if not u_m:
                u_m = re.search(r"มูลค่าหุ้น\s*\n*([\d\.\,]+)\s*USD", text)
            if not u_m:
                u_m = re.search(r"ยอดที่ต้องชำระ\s*\n*([\d\.\,]+)\s*USD", text)
            if not u_m:
                u_m = re.search(r"([\d\.\,]+)\s*USD\s*\n*ใช้ราคาตลาด", text)
            if not u_m:
                u_m = re.search(r"([\d\.\,]+)\s*USD\s*\n*ราคาที่คุณตั้ง", text)
            if u_m:
                amt_usd = parse_num(u_m.group(1))
            elif shares > 0 and price_usd > 0:
                amt_usd = round(shares * price_usd, 2)

            # Amounts THB
            amt_thb = 0.0
            thb_m = re.search(r"([\d\.\,]+)\s*THB\s*\n*ใช้ราคาตลาด", text)
            if not thb_m:
                thb_m = re.search(r"([\d\.\,]+)\s*THB\s*\n*ราคาที่คุณตั้ง", text)
            if not thb_m:
                thb_m = re.search(r"มูลค่าหุ้น\s*\n*([\d\.\,]+)\s*THB", text)
            if not thb_m:
                thb_m = re.search(r"ยอดที่ต้องชำระ\s*\n*([\d\.\,]+)\s*THB", text)
            if thb_m:
                amt_thb = parse_num(thb_m.group(1))

            # FX Rate
            fx_rate = 0.0
            fx_m = re.search(r"1\s*USD\s*=\s*([\d\.\,]+)\s*THB", text)
            if fx_m:
                fx_rate = parse_num(fx_m.group(1))

            # Date extraction: prioritize actual date format (DD Mon YY - HH:MM)
            date_str = ""
            d_succ = re.search(r"วันที่คำสั่งสำเร็จ[\s\S]*?(\d{1,2}\s+[^\s\n]+\s+\d{2,4}\s*-\s*\d{1,2}:\d{1,2}(?::\d{1,2})?\s*น\.?)", text)
            if d_succ:
                date_str = d_succ.group(1).strip()
            else:
                d_sub = re.search(r"วันที่ส่งคำสั่ง[\s\S]*?(\d{1,2}\s+[^\s\n]+\s+\d{2,4}\s*-\s*\d{1,2}:\d{1,2}(?::\d{1,2})?\s*น\.?)", text)
                if d_sub:
                    date_str = d_sub.group(1).strip()
                else:
                    d_any = re.search(r"(\d{1,2}\s+[^\s\n]+\s+\d{2,4}\s*-\s*\d{1,2}:\d{1,2}(?::\d{1,2})?\s*น\.?)", text)
                    date_str = d_any.group(1).strip() if d_any else ""

            order_type = "Limit" if "ตั้งราคาเอง" in text or "Limit" in text else "Market"
            account = "Dime! Save (THB)" if (amt_thb > 0 or "Dime! Save" in text) else "Dime! USD"

            buy_orders.append({
                "fn": fn,
                "ticker": ticker,
                "shares": shares,
                "price_usd": price_usd,
                "amt_usd": amt_usd,
                "amt_thb": amt_thb,
                "fx_rate": fx_rate,
                "date": date_str,
                "order_type": order_type,
                "account": account
            })

    # Sort chronologically descending
    buy_orders.sort(
        key=lambda x: (parse_thai_date(x["date"]), int(re.sub(r"\D", "", x["fn"])) if re.sub(r"\D", "", x["fn"]) else 0),
        reverse=True
    )

    return buy_orders


def load_statement_cash_flow():
    stmt_path = Path("data/.statement_text.txt")
    if not stmt_path.exists() or stmt_path.stat().st_size == 0:
        return []

    text = stmt_path.read_text(encoding="utf-8")

    # 1. Parse PromptPay deposits from statement
    pp_dates = re.findall(r"(\d{2}/\d{2}/\d{4})\s+รับเงินโอนจากต่าง\s*\n*ธนาคาร", text)
    pp_amts = re.findall(r"([\d\.\,]+)\s+([\d\.\,]+)\s+PROMPTPAY", text)

    records = []
    for d, (amt, bal) in zip(pp_dates, pp_amts):
        records.append({
            "date_str": d,
            "type": "ฝากเงิน (โอนเข้า Dime! Save)",
            "amount_thb": float(amt.replace(",", "")),
            "balance_thb": float(bal.replace(",", "")),
            "channel": "PROMPTPAY",
            "ref": "KKP Statement (ทางการ)"
        })

    # 2. Parse debits/credits from statement
    debits = re.findall(r"(\d{2}/\d{2}/\d{4})\s+([^\d\n]+?)\s+([\d\.\,]+)\s+([\d\.\,]+)\s+([A-Z0-9]+)", text)
    for d, desc, amt_str, bal_str, ch in debits:
        amt = float(amt_str.replace(",", ""))
        bal = float(bal_str.replace(",", ""))
        desc = desc.strip()
        if "โอนเงินไปต่างธนาคาร" in desc:
            t_type = "โอนเงินออกไปต่างธนาคาร"
            amt = -amt
        elif "ดอกเบี้ย" in desc:
            t_type = "ดอกเบี้ยรับบัญชีเงินฝาก"
        else:
            t_type = "ชำระค่าซื้อหุ้น / ตัดเงินลงทุน"
            amt = -amt
        records.append({
            "date_str": d,
            "type": t_type,
            "amount_thb": amt,
            "balance_thb": bal,
            "channel": ch,
            "ref": "KKP Statement (ทางการ)"
        })

    # 3. Post-statement transactions (after 03/10/2026) verified by slips IMG_5683 and IMG_5684
    post_statement = [
        {"date_str": "07/10/2026 23:30 น.", "type": "ชำระค่าซื้อหุ้น BAC", "amount_thb": -4999.73, "balance_thb": 20001.33, "channel": "Dime! Save", "ref": "IMG_5683.PNG"},
        {"date_str": "08/10/2026 23:09 น.", "type": "ชำระค่าซื้อหุ้น NOK", "amount_thb": -4999.70, "balance_thb": 15001.63, "channel": "Dime! Save", "ref": "IMG_5683.PNG"},
        {"date_str": "13/10/2026 21:16 น.", "type": "ชำระค่าซื้อหุ้น BAC", "amount_thb": -4999.80, "balance_thb": 10001.83, "channel": "Dime! Save", "ref": "IMG_5684.PNG"},
        {"date_str": "13/10/2026 21:23 น.", "type": "ชำระค่าซื้อหุ้น VRT", "amount_thb": -10000.94, "balance_thb": 0.89, "channel": "Dime! Save", "ref": "IMG_5684.PNG"},
        {"date_str": "14/10/2026 20:26 น.", "type": "ฝากเงิน (โอนเข้า Dime! Save)", "amount_thb": 20000.00, "balance_thb": 20000.89, "channel": "PROMPTPAY", "ref": "IMG_5684.PNG"},
        {"date_str": "14/10/2026 20:33 น.", "type": "ชำระค่าซื้อหุ้น BAC", "amount_thb": -9999.89, "balance_thb": 10001.00, "channel": "Dime! Save", "ref": "IMG_5684.PNG"},
        {"date_str": "14/10/2026 21:03 น.", "type": "ชำระค่าซื้อหุ้น APP", "amount_thb": -10001.00, "balance_thb": 0.01, "channel": "Dime! Save", "ref": "IMG_5684.PNG"},
    ]

    all_records = post_statement + records

    def parse_dt(d_str):
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", d_str)
        if m:
            tm = re.search(r"(\d{2}):(\d{2})", d_str)
            hr = int(tm.group(1)) if tm else 12
            mn = int(tm.group(2)) if tm else 0
            return (int(m.group(3)), int(m.group(2)), int(m.group(1)), hr, mn)
        return (0, 0, 0, 0, 0)

    all_records.sort(key=lambda x: parse_dt(x["date_str"]), reverse=True)
    return all_records


def generate_master_dashboard_data():
    # 1. Active Portfolio Live Market Data
    portfolio_data = load_portfolio()
    live_summary = analyze_portfolio(portfolio_data)
    fx_rate = live_summary.get("fx_rate_usd_thb", 33.62)

    # 2. Closed Trades Data
    trades_data = load_trades()
    trades_summary = calculate_trades_summary(trades_data)

    # 3. Official KKP Statement Numbers (from KKP_STATEMENT_20261007.pdf & Slips)
    net_injected_capital_thb = 1245000.00
    gross_promptpay_deposits_thb = 1295000.00
    transfer_out_thb = 50000.00
    dime_save_cash_thb = 0.01
    dime_save_interest_thb = 30.91

    # 4. Dime! USD Cash Balance
    dime_usd_cash = 140.96
    dime_usd_cash_thb = round(dime_usd_cash * fx_rate, 2)

    # 5. Total Combined Net Worth (NAV)
    stock_market_val_usd = live_summary["total_market_val_usd"]
    stock_market_val_thb = live_summary["total_market_val_thb"]
    stock_cost_usd = live_summary["total_cost_usd"]
    stock_cost_thb = live_summary["total_cost_thb"]
    stock_unrealized_pl_usd = live_summary["total_pl_usd"]
    stock_unrealized_pl_thb = live_summary["total_pl_thb"]
    stock_unrealized_pl_pct = live_summary["total_pl_pct"]

    total_cash_thb = round(dime_save_cash_thb + dime_usd_cash_thb, 2)
    total_net_worth_thb = round(stock_market_val_thb + total_cash_thb, 2)
    total_net_worth_usd = round(total_net_worth_thb / fx_rate, 2)

    all_time_profit_thb = round(total_net_worth_thb - net_injected_capital_thb, 2)
    all_time_roi_pct = round((all_time_profit_thb / net_injected_capital_thb * 100.0), 2)

    # 6. Realized & Dividend Streams
    total_realized_pl_usd = trades_summary["total_realized_pl_usd"]
    total_realized_pl_thb = trades_summary["total_realized_pl_thb"]
    total_dividends_usd = 141.74
    total_dividends_thb = round(total_dividends_usd * fx_rate, 2)
    total_realized_and_div_thb = round(total_realized_pl_thb + total_dividends_thb + dime_save_interest_thb, 2)

    # Dividend details list
    dividends_list = [
        {"date": "1 ต.ค. 69", "ticker": "VOO", "amount_usd": 0.90, "rate": "1.8226/หุ้น"},
        {"date": "14 ก.ย. 69", "ticker": "GOOGL", "amount_usd": 1.95, "rate": "0.22/หุ้น"},
        {"date": "10 ก.ย. 69", "ticker": "LLY", "amount_usd": 47.83, "rate": "1.73/หุ้น"},
        {"date": "12 ส.ค. 69", "ticker": "NOK", "amount_usd": 2.69, "rate": "0.0285/หุ้น"},
        {"date": "1 ก.ค. 69", "ticker": "VOO", "amount_usd": 0.97, "rate": "1.9622/หุ้น"},
        {"date": "19 มิ.ย. 69", "ticker": "QQQI", "amount_usd": 3.84, "rate": "0.6572/หุ้น"},
        {"date": "11 มิ.ย. 69", "ticker": "LLY", "amount_usd": 46.24, "rate": "1.73/หุ้น"},
        {"date": "23 พ.ค. 69", "ticker": "QQQI", "amount_usd": 3.85, "rate": "0.6589/หุ้น"},
        {"date": "25 เม.ย. 69", "ticker": "QQQI", "amount_usd": 3.68, "rate": "0.6297/หุ้น"},
        {"date": "1 เม.ย. 69", "ticker": "VOO", "amount_usd": 0.93, "rate": "1.8724/หุ้น"},
        {"date": "21 มี.ค. 69", "ticker": "QQQI", "amount_usd": 3.55, "rate": "0.6089/หุ้น"},
        {"date": "10 มี.ค. 69", "ticker": "LLY", "amount_usd": 21.73, "rate": "1.73/หุ้น"},
        {"date": "21 ก.พ. 69", "ticker": "QQQI", "amount_usd": 3.58, "rate": "0.6140/หุ้น"},
    ]

    # 7. Detailed Buy Orders (55 orders from OCR) & Cash Flow (54 transactions from KKP Statement)
    buy_orders = load_ocr_buy_orders()
    cash_movements = load_statement_cash_flow()

    return {
        "portfolio_name": live_summary.get("portfolio_name", "ไม่รวยก็ซวยอ่ะค้าบ"),
        "broker": "Dime! (KKP Securities)",
        "account_no": "2081682995",
        "fx_rate": fx_rate,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "net_injected_capital_thb": net_injected_capital_thb,
        "gross_deposits_thb": gross_promptpay_deposits_thb,
        "transfer_out_thb": transfer_out_thb,
        "dime_save_cash_thb": dime_save_cash_thb,
        "dime_usd_cash": dime_usd_cash,
        "dime_usd_cash_thb": dime_usd_cash_thb,
        "total_cash_thb": total_cash_thb,
        "stock_market_val_usd": stock_market_val_usd,
        "stock_market_val_thb": stock_market_val_thb,
        "stock_cost_usd": stock_cost_usd,
        "stock_cost_thb": stock_cost_thb,
        "stock_unrealized_pl_usd": stock_unrealized_pl_usd,
        "stock_unrealized_pl_thb": stock_unrealized_pl_thb,
        "stock_unrealized_pl_pct": stock_unrealized_pl_pct,
        "total_net_worth_thb": total_net_worth_thb,
        "total_net_worth_usd": total_net_worth_usd,
        "all_time_profit_thb": all_time_profit_thb,
        "all_time_roi_pct": all_time_roi_pct,
        "trades_summary": trades_summary,
        "closed_trades": trades_data.get("trades", []),
        "dividends_list": dividends_list,
        "total_dividends_usd": total_dividends_usd,
        "total_dividends_thb": total_dividends_thb,
        "total_realized_and_div_thb": total_realized_and_div_thb,
        "positions": live_summary.get("positions", []),
        "buy_orders": buy_orders,
        "cash_movements": cash_movements,
    }


def generate_master_dashboard_html(data):
    now_str = data["updated_at"]
    at_sign = "+" if data["all_time_profit_thb"] >= 0 else ""
    at_color = "#10b981" if data["all_time_profit_thb"] >= 0 else "#f43f5e"

    un_sign = "+" if data["stock_unrealized_pl_thb"] >= 0 else ""
    un_color = "#10b981" if data["stock_unrealized_pl_thb"] >= 0 else "#f43f5e"

    # 1. Active Holdings Rows
    holdings_rows = ""
    for p in data["positions"]:
        p_pl_usd = p["unrealized_pl_usd"]
        p_pl_thb = p["unrealized_pl_thb"]
        p_pl_pct = p["unrealized_pl_pct"]
        c = "#10b981" if p_pl_usd >= 0 else "#f43f5e"
        s = "+" if p_pl_usd >= 0 else ""
        onclick_js = _make_chart_onclick(p)
        holdings_rows += f"""
        <tr>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif;">
                <span class="clickable-ticker" onclick="{onclick_js}" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{p['ticker']} 📈</span>
            </td>
            <td>{p.get('name', '-')}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{p['shares']:.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${p['avg_cost_usd']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600;">${p['close_price']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${p['current_val_usd']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">฿{p['current_val_thb']:,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{s}${p_pl_usd:,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 600;">{s}฿{p_pl_thb:,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{s}{p_pl_pct:.2f}%</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{p['weight_pct']:.1f}%</td>
        </tr>
        """

    # 1.1 Master Forward Outlook Cards for Active Holdings
    outlook_cards_master = ""
    for p in data["positions"]:
        t = p["ticker"]
        fo = p.get("forward_outlook", {})
        thesis = fo.get("thesis_title", f"การลงทุนเชิงยุทธศาสตร์ใน {t}")
        quality = fo.get("quality_badge", "🔵 Strategic Core Holding")
        drivers = fo.get("future_growth_drivers", [])
        timeline = fo.get("catalyst_timeline", [])
        next_cat = timeline[0] if timeline else {}
        t_avg = p.get("price_target_average", 0.0)
        up_val = p.get("target_upside_pct")
        up_str = f"+{up_val:.1f}%" if (up_val is not None and up_val > 0) else (f"{up_val:.1f}%" if up_val is not None else "-")
        roadmap = fo.get("tailored_roadmap", p.get("rating", {}).get("action", ""))

        pl_u = p["unrealized_pl_usd"]
        pl_pct = p["unrealized_pl_pct"]
        c_badge = "badge-success" if pl_u >= 0 else "badge-danger"
        s_sign = "+" if pl_u >= 0 else ""

        driver_items = "".join([f"<li style='margin-bottom: 4px;'>• {d}</li>" for d in drivers[:2]]) if drivers else ""
        next_cat_str = f"<strong>{next_cat.get('period', '-')}:</strong> {next_cat.get('event', '-')}" if next_cat else "ไม่มีตัวเร่งเฉพาะระยะสั้น"
        t_avg_disp = f"${t_avg:,.2f}" if t_avg else "-"

        onclick_js = _make_chart_onclick(p)
        outlook_cards_master += f"""
        <div class="card" style="padding: 18px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3px solid {'var(--emerald)' if pl_u >= 0 else 'var(--rose)'};">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div>
                        <span class="clickable-ticker" onclick="{onclick_js}" style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.15rem; color: #fff; cursor: pointer;" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{t} 📈</span>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">{p.get('name', '')}</div>
                    </div>
                    <span class="badge {c_badge}">{s_sign}{pl_pct:.1f}%</span>
                </div>
                <div style="font-size: 0.76rem; background: rgba(59, 130, 246, 0.1); color: #60a5fa; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px;">
                    {quality}
                </div>
                <div style="font-size: 0.86rem; color: #e2e8f0; line-height: 1.4; margin-bottom: 12px; font-weight: 500;">
                    {thesis}
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; background: rgba(0,0,0,0.25); padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                    <div style="color: #38bdf8; font-weight: 600; margin-bottom: 4px;">🚀 ปัจจัยขับเคลื่อนสำคัญ:</div>
                    <ul style="list-style: none; padding-left: 0; line-height: 1.4;">
                        {driver_items}
                    </ul>
                </div>
            </div>
            <div>
                <div style="font-size: 0.78rem; color: #cbd5e1; background: rgba(16, 185, 129, 0.06); padding: 6px 8px; border-radius: 4px; border-left: 2px solid var(--emerald); margin-bottom: 8px;">
                    🎯 <strong>เป้าวอลล์สตรีท:</strong> {t_avg_disp} ({up_str})
                </div>
                <div style="font-size: 0.78rem; color: #fde047; background: rgba(245, 158, 11, 0.08); padding: 6px 8px; border-radius: 4px; border-left: 2px solid var(--amber);">
                    🧭 <strong>แผนแอ็กชัน:</strong> {roadmap}
                </div>
                <div style="margin-top: 10px;">
                    <button onclick="{onclick_js}" style="width: 100%; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); color: #60a5fa; border-radius: 6px; padding: 6px 12px; font-size: 0.82rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s;">📈 ดูกราฟสด & แนวรับแนวต้าน</button>
                </div>
            </div>
        </div>
        """

    # 2. Buy Orders Rows (55 orders)
    buy_rows = ""
    for idx, b in enumerate(data["buy_orders"]):
        acc_badge = '<span class="badge badge-success">Dime! Save (THB)</span>' if "Save" in b["account"] else '<span class="badge badge-info">Dime! USD</span>'
        type_badge = f'<span class="badge badge-purple">{b["order_type"]}</span>' if b["order_type"] == "Limit" else '<span class="badge badge-neutral">Market</span>'
        fx_str = f"฿{b['fx_rate']:.2f}" if b['fx_rate'] > 0 else "-"
        thb_str = f"฿{b['amt_thb']:,.2f}" if b['amt_thb'] > 0 else "-"
        buy_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary);">{b['date']}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; color: #60a5fa;">{b['ticker']}</td>
            <td style="text-align: center;">{type_badge}</td>
            <td style="text-align: center;">{acc_badge}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600;">{b['shares']:.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${b['price_usd']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${b['amt_usd']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{thb_str}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{fx_str}</td>
            <td style="text-align: center; font-family: 'Inter', sans-serif; font-size: 0.78rem; color: var(--text-muted);">{b['fn']}</td>
        </tr>
        """

    # 3. Closed Trades Rows (7 sells with Buy Dates & Multi-Tranche Details)
    closed_rows = ""
    for idx, t in enumerate(data["closed_trades"]):
        c = "#10b981" if t.get("realized_pl_usd", 0) >= 0 else "#f43f5e"
        s = "+" if t.get("realized_pl_usd", 0) >= 0 else ""
        tranches = t.get("buy_tranches", [])
        tranche_count = len(tranches)
        trade_id = t.get("id", f"trade_{idx}").replace("-", "_")

        buy_date_str = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
        days = t.get("holding_days", "-")
        days_str = f"{days} วัน" if isinstance(days, (int, float)) else str(days)

        if tranche_count > 1:
            tranche_btn = f'<button onclick="toggleTranche(\'{trade_id}\')" style="background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 6px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">สะสม {tranche_count} ไม้ <span id="icon-{trade_id}">▼</span></button>'
        else:
            tranche_btn = '<span class="badge badge-neutral" style="font-size: 0.76rem;">1 ไม้</span>'

        closed_rows += f"""
        <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: #60a5fa; font-weight: 500;">{buy_date_str}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary); text-align: center;">{t.get('date', '-')}</td>
            <td style="text-align: center; font-size: 0.82rem; color: var(--text-muted); white-space: nowrap;">{days_str}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; font-size: 1.05rem; color: #fff;">{t.get('ticker')}</td>
            <td>
                <div>{t.get('name', '-')}</div>
                <div style="margin-top: 4px;">{tranche_btn}</div>
            </td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{t.get('shares', 0):.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('buy_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('sell_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('total_cost_usd', 0):,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('net_revenue_usd', 0):,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{s}${t.get('realized_pl_usd', 0):,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 600;">{s}฿{t.get('realized_pl_thb', 0):,.2f}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{s}{t.get('realized_pl_pct', 0):.2f}%</td>
        </tr>
        """

        # Detailed tranche subrow
        if tranches:
            tranche_subrows = ""
            for tr in tranches:
                t_thb_str = f"฿{tr.get('amt_thb', 0):,.2f}" if tr.get('amt_thb', 0) > 0 else "-"
                tranche_subrows += f"""
                <tr style="background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.82rem;">
                    <td style="text-align: center; color: #c084fc; font-weight: 700;">ไม้ที่ {tr.get('tranche')}</td>
                    <td style="color: #60a5fa; font-family: 'Inter', sans-serif;">{tr.get('date')}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">{tr.get('shares'):.4f} หุ้น</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">${tr.get('price_usd'):.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${tr.get('amt_usd'):,.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{t_thb_str}</td>
                    <td style="color: var(--text-secondary);">{tr.get('note', '-')}</td>
                    <td style="text-align: center; color: var(--text-muted); font-size: 0.78rem;">{tr.get('file', '-')}</td>
                </tr>
                """

            closed_rows += f"""
            <tr id="details-{trade_id}" class="tranche-detail-row" style="display: none; background: rgba(139, 92, 246, 0.05);">
                <td colspan="14" style="padding: 12px 18px;">
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


    # 4. Dividend Rows (13 items)
    div_rows = ""
    for d in data["dividends_list"]:
        div_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-secondary);">{d['date']}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif;">{d['ticker']}</td>
            <td>{d['rate']}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 700; color: #10b981;">+${d['amount_usd']:.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #10b981;">+฿{d['amount_usd'] * data['fx_rate']:,.2f}</td>
        </tr>
        """

    # 5. Complete Cash Movements Rows (54 items from KKP Statement + recent)
    cash_rows = ""
    for idx, c in enumerate(data["cash_movements"]):
        if "ฝากเงิน" in c["type"]:
            badge = '<span class="badge badge-success">ฝากเงินเข้าพอร์ต</span>'
            amt_color = "#10b981"
            sign = "+"
        elif "ดอกเบี้ย" in c["type"]:
            badge = '<span class="badge badge-info">ดอกเบี้ยรับเงินฝาก</span>'
            amt_color = "#60a5fa"
            sign = "+"
        elif "โอนเงินออก" in c["type"]:
            badge = '<span class="badge badge-rose">โอนเงินออกไปต่างธนาคาร</span>'
            amt_color = "#f43f5e"
            sign = ""
        else:
            badge = '<span class="badge badge-rose">ตัดชำระค่าซื้อหุ้น</span>'
            amt_color = "#f43f5e"
            sign = ""

        bal_str = f"฿{c['balance_thb']:,.2f}" if "balance_thb" in c else "-"
        ch_str = c.get("channel", "Dime! Save")
        ref_str = c.get("ref", "-")

        cash_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.88rem; color: var(--text-secondary);">{c['date_str']}</td>
            <td>{badge}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 700; color: {amt_color};">{sign}฿{c['amount_thb']:,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; color: #fff;">{bal_str}</td>
            <td style="text-align: center; font-family: 'Inter', sans-serif; font-size: 0.82rem; color: var(--text-muted);">{ch_str}</td>
            <td style="text-align: center; font-family: 'Inter', sans-serif; font-size: 0.78rem; color: var(--text-muted);">{ref_str}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Portfolio & Wealth Summary - {data['portfolio_name']}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #070b14;
            --bg-card: #0d1527;
            --bg-card-subtle: #111c34;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.04);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --rose: #f43f5e;
            --blue: #3b82f6;
            --amber: #f59e0b;
            --purple: #8b5cf6;
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 18px;
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
        .container {{ max-width: 1480px; margin: 0 auto; }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .meta-pill {{
            background: var(--bg-card); padding: 8px 16px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-color); font-size: 0.88rem; color: var(--text-secondary);
        }}
        .grid-4-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .grid-3-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .card {{
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: var(--radius-md); padding: 24px;
        }}
        .kpi-label {{ font-size: 0.82rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }}
        .kpi-value {{ font-size: 1.95rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .kpi-subtext {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; }}
        .section-title {{
            font-size: 1.25rem; font-weight: 700; margin-bottom: 16px;
            display: flex; align-items: center; gap: 10px;
        }}
        .table-container {{
            max-height: 520px;
            overflow-y: auto;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            background: var(--bg-card);
        }}
        table {{
            width: 100%; border-collapse: collapse; font-size: 0.90rem;
        }}
        th {{
            background: #0f192e; color: var(--text-secondary);
            padding: 12px 14px; text-align: left; font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            position: sticky; top: 0; z-index: 10;
        }}
        td {{
            padding: 12px 14px; border-bottom: 1px solid var(--border-subtle);
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .badge {{
            padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; display: inline-block;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.15); color: var(--emerald); }}
        .badge-rose {{ background: rgba(244, 63, 94, 0.15); color: var(--rose); }}
        .badge-info {{ background: rgba(59, 130, 246, 0.15); color: var(--blue); }}
        .badge-purple {{ background: rgba(139, 92, 246, 0.15); color: var(--purple); }}
        .badge-neutral {{ background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <div>
                <h1 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px;">
                    💎 ศูนย์รวมข้อมูลพอร์ตการลงทุน Master Summary
                </h1>
                <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">
                    พอร์ต: <strong style="color: #fff;">{data['portfolio_name']}</strong> | 
                    โบรกเกอร์: <strong style="color: #fff;">{data['broker']}</strong> | 
                    บัญชี: <code>{data['account_no']}</code>
                </p>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <a href="portfolio_master.html" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid var(--blue); font-weight: 600; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.88rem;">🏛️ พอร์ตหลัก Master</a>
                    <a href="portfolio_review.html" style="color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border-color); padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.88rem;">🏥 ตรวจสุขภาพพอร์ต</a>
                    <a href="portfolio_recovery.html" style="color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border-color); padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.88rem;">🩹 แผนกู้พอร์ต 360°</a>
                    <a href="portfolio_dip_sim.html" style="color: #a855f7; background: rgba(168, 85, 247, 0.1); border: 1px solid var(--purple); padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.88rem; font-weight: 600;">🧪 พอร์ตจำลอง Dip (ตัวละ ฿10k)</a>
                    <a href="trades_ledger.html" style="color: #10b981; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--emerald); padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.88rem; font-weight: 600;">📈 บัญชีขายปิดรอบ</a>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <span class="meta-pill">⚡ 1 USD = {data['fx_rate']:.2f} THB</span>
                    <span class="meta-pill">🕒 {now_str}</span>
                </div>
            </div>
        </div>

        <!-- 4 MAIN HERO KPIS -->
        <div class="grid-4-cols">
            <div class="card" style="border-left: 4px solid var(--blue);">
                <div class="kpi-label">มูลค่าพอร์ตรวมสุทธิ (Total Net Worth / NAV)</div>
                <div class="kpi-value" style="color: #60a5fa;">฿{data['total_net_worth_thb']:,.2f}</div>
                <div class="kpi-subtext">~${data['total_net_worth_usd']:,.2f} USD (หุ้น + เงินสด)</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--purple);">
                <div class="kpi-label">เงินต้นทุนเติมสุทธิ (Net Deposited Capital)</div>
                <div class="kpi-value">฿{data['net_injected_capital_thb']:,.2f}</div>
                <div class="kpi-subtext">จาก KKP Statement ทางการ 100% (PromptPay 19 ครั้ง - ถอนออก 1 ครั้ง)</div>
            </div>
            <div class="card" style="border-left: 4px solid {at_color};">
                <div class="kpi-label">กำไรรวมสุทธิของพอร์ต (All-Time Net Profit)</div>
                <div class="kpi-value" style="color: {at_color};">{at_sign}฿{data['all_time_profit_thb']:,.2f}</div>
                <div class="kpi-subtext" style="color: {at_color}; font-weight: 700;">{at_sign}{data['all_time_roi_pct']:.2f}% All-Time ROI</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--emerald);">
                <div class="kpi-label">เงินสดคงเหลือรวม (Total Idle Cash)</div>
                <div class="kpi-value">฿{data['total_cash_thb']:,.2f}</div>
                <div class="kpi-subtext">Dime! Save: ฿{data['dime_save_cash_thb']:,.2f} | Dime! USD: ${data['dime_usd_cash']:.2f}</div>
            </div>
        </div>

        <!-- SECONDARY METRICS: 3-COLS -->
        <div class="grid-3-cols">
            <div class="card">
                <div class="kpi-label">หุ้นที่กำลังถือครอง (Active Holdings)</div>
                <div style="font-size: 1.45rem; font-weight: 700;">{len(data['positions'])} บริษัท</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    มูลค่าตลาด: <strong>${data['stock_market_val_usd']:,.2f}</strong> (฿{data['stock_market_val_thb']:,.2f})<br>
                    กำไรที่ยังไม่ขาย: <strong style="color: {un_color};">{un_sign}${data['stock_unrealized_pl_usd']:,.2f} ({un_sign}{data['stock_unrealized_pl_pct']:.2f}%)</strong>
                </div>
            </div>
            <div class="card">
                <div class="kpi-label">กำไรที่ขายทำกำไรจริง (Realized P&L)</div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #10b981;">+${data['trades_summary']['total_realized_pl_usd']:,.2f}</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    คิดเป็นเงินไทย: <strong style="color: #10b981;">+฿{data['trades_summary']['total_realized_pl_thb']:,.2f}</strong><br>
                    Win Rate: <strong style="color: #10b981;">{data['trades_summary']['win_rate_pct']:.1f}%</strong> (ปิด {data['trades_summary']['total_trades']} ชนะ {data['trades_summary']['winning_trades']} ไม้)
                </div>
            </div>
            <div class="card">
                <div class="kpi-label">เงินปันผลรับสะสม (Dividends)</div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #10b981;">+${data['total_dividends_usd']:,.2f}</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    คิดเป็นเงินไทย: <strong style="color: #10b981;">+฿{data['total_dividends_thb']:,.2f}</strong> (รับรวม {len(data['dividends_list'])} ครั้ง)<br>
                    รวมกำไรปิดไม้ + ปันผล: <strong style="color: #10b981;">+฿{data['total_realized_and_div_thb']:,.2f}</strong>
                </div>
            </div>
        </div>

        <!-- SECTION 1: ACTIVE HOLDINGS TABLE -->
        <div style="margin-bottom: 36px;">
            <div class="section-title">
                <span>📈</span> 1. รายการหุ้นที่กำลังถือครองในพอร์ต (Active Holdings: {len(data['positions'])} ตัว)
                <span class="badge badge-info">ราคาตลาดสดจาก TradingView API</span>
            </div>
            <div class="card" style="padding: 0; overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>ชื่อบริษัท</th>
                            <th style="text-align: right;">จำนวนหุ้น</th>
                            <th style="text-align: right;">ต้นทุน ($)</th>
                            <th style="text-align: right;">ราคาตลาด ($)</th>
                            <th style="text-align: right;">มูลค่า ($)</th>
                            <th style="text-align: right;">มูลค่า (฿)</th>
                            <th style="text-align: right;">กำไร ($)</th>
                            <th style="text-align: right;">กำไร (฿)</th>
                            <th style="text-align: right;">% ผลตอบแทน</th>
                            <th style="text-align: right;">สัดส่วน</th>
                        </tr>
                    </thead>
                    <tbody>
                        {holdings_rows}
                    </tbody>
                </table>
            </div>

            <!-- Master Forward Outlook Dossiers -->
            <div style="margin-top: 24px;">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                    <span>🔭</span> วิสัยทัศน์ & ตัวเร่งราคาในอนาคตรายตัว (Forward Intelligence & Catalysts)
                    <span class="badge badge-purple">{len(data['positions'])} หุ้นในพอร์ต</span>
                </div>
                <div class="grid-3-cols">
                    {outlook_cards_master}
                </div>
            </div>
        </div>

        <!-- SECTION 2: COMPLETE BUY ORDERS HISTORY (55 BUYS) -->
        <div style="margin-bottom: 36px;">
            <div class="section-title">
                <span>🛒</span> 2. ประวัติคำสั่งซื้อหุ้นทั้งหมดอย่างละเอียด (Complete Buy Orders History: {len(data['buy_orders'])} ไม้)
                <span class="badge badge-info">สกัดจากสลิปคำสั่งซื้อ Dime! 100% เรียงตามวันเวลาสำเร็จจริง</span>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: center; width: 45px;">#</th>
                            <th>วัน-เวลาสำเร็จ</th>
                            <th>Ticker</th>
                            <th style="text-align: center;">ประเภท</th>
                            <th style="text-align: center;">บัญชีที่ชำระ</th>
                            <th style="text-align: right;">จำนวนหุ้น</th>
                            <th style="text-align: right;">ราคาที่ได้จริง ($)</th>
                            <th style="text-align: right;">ยอดเงิน ($)</th>
                            <th style="text-align: right;">ยอดเงิน (฿)</th>
                            <th style="text-align: right;">FX Rate</th>
                            <th style="text-align: center;">สลิปอ้างอิง</th>
                        </tr>
                    </thead>
                    <tbody>
                        {buy_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 3: CLOSED TRADES TABLE (7 SELLS) -->
        <div style="margin-bottom: 36px;">
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span>🏆</span> 3. รายการหุ้นที่ขายทำกำไรปิดรอบสำเร็จ (Closed Trades: {len(data['closed_trades'])} ไม้)
                    <span class="badge badge-success">Win Rate 100.0% (กำไรสะสม +฿{data['trades_summary']['total_realized_pl_thb']:,.2f})</span>
                </div>
                <button onclick="toggleAllTranches()" style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); color: #c084fc; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                    <span>🔍</span> <span id="toggleAllBtnText">คลี่ดูรายละเอียดทุกไม้ (Expand All)</span>
                </button>
            </div>
            <div class="card" style="padding: 0; overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: center; width: 45px;">#</th>
                            <th>วันที่ซื้อ (Buy Date)</th>
                            <th style="text-align: center;">วันที่ขาย</th>
                            <th style="text-align: center;">ระยะถือ</th>
                            <th>Ticker</th>
                            <th>ชื่อหุ้น / ไม้สะสม</th>
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
                        {closed_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 4: DIVIDEND STREAM -->
        <div style="margin-bottom: 36px;">
            <div class="section-title">
                <span>💵</span> 4. ประวัติเงินปันผลรับสะสม (Dividends Received: {len(data['dividends_list'])} ครั้ง)
                <span class="badge badge-success">รวม +${data['total_dividends_usd']:.2f} (~฿{data['total_dividends_thb']:,.2f})</span>
            </div>
            <div class="card" style="padding: 0; overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: center;">วันที่รับเงิน</th>
                            <th>Ticker</th>
                            <th>อัตราปันผลต่อหุ้น</th>
                            <th style="text-align: right;">ยอดรับ ($)</th>
                            <th style="text-align: right;">ยอดรับ (฿)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {div_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 5: CAPITAL & CASH MOVEMENTS STATEMENT -->
        <div style="margin-bottom: 36px;">
            <div class="section-title">
                <span>🏦</span> 5. ข้อมูลการเติมเงินและการเคลื่อนไหวเงินสดในบัญชี (Complete Cash Flow & Deposit Ledger: {len(data['cash_movements'])} รายการ)
                <span class="badge badge-info">KKP Official Statement & สลิป Dime! Save ตั้งแต่วันเปิดบัญชี 2 ก.พ. 69</span>
            </div>
            <!-- STATEMENT OVERVIEW CARDS -->
            <div class="card" style="margin-bottom: 20px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; font-size: 0.95rem;">
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดโอนเข้าจากต่างธนาคารรวม (PromptPay):</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #fff;">฿{data['gross_deposits_thb']:,.2f}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(19 รายการ: Statement 18 ครั้ง + 14 ต.ค. 1 ครั้ง)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดโอนเงินกลับออกไปต่างธนาคาร:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--rose);">-฿{data['transfer_out_thb']:,.2f}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(เมื่อวันที่ 03/02/2026 ผ่านช่องทาง DIME)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดเงินต้นสุทธิที่คงอยู่ใน Dime!:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #60a5fa;">฿{data['net_injected_capital_thb']:,.2f}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(ใช้เป็นฐานคำนวณผลตอบแทนรวมจริง 100%)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">เงินสดคงเหลือในบัญชี Dime! Save:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--emerald);">฿{data['dime_save_cash_thb']:,.2f}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(หักซื้อหุ้นชุดล่าสุด 4 ไม้ ฿35,001.63 เมื่อ 13-14 ต.ค. 69)</div>
                    </div>
                </div>
            </div>

            <!-- DETAILED CASH MOVEMENTS TABLE -->
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: center; width: 45px;">#</th>
                            <th>วัน-เวลาที่ทำรายการ</th>
                            <th>ประเภทรายการ</th>
                            <th style="text-align: right;">จำนวนเงิน (บาท)</th>
                            <th style="text-align: right;">ยอดเงินคงเหลือ</th>
                            <th style="text-align: center;">ช่องทาง</th>
                            <th style="text-align: center;">แหล่งอ้างอิง</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cash_rows}
                    </tbody>
                </table>
            </div>
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
</body>
</html>
"""
    return html


def main():
    print("Generating Unified Master Dashboard...", file=sys.stderr)
    data = generate_master_dashboard_data()

    # Save to reports/portfolio_master.html
    out_path = Path("reports/portfolio_master.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_master_dashboard_html(data)
    out_path.write_text(html_content, encoding="utf-8")

    # Save JSON summary
    json_path = Path("data/account_summary.json")
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Master Dashboard saved to: {out_path.resolve()}")
    print(f"Account JSON data saved to: {json_path.resolve()}")


if __name__ == "__main__":
    main()
