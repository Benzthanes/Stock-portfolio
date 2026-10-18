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
from src.trades import (
    load_trades, calculate_trades_summary, load_ledger,
    resolve_slip_relative_path, get_slip_modal_component
)
from html import escape

from src.fmt import FMT_MONEY_JS, money, pct
from src.fx import resolve_usdthb
from src.html_report import get_chart_modal_component, _make_chart_onclick
from src.nav import nav_bar_html

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

        if "รายละเอียดคำสั่ง" in full_str and re.search(r"ซื้อ\s+[A-Z0-9]+", full_str):
            ticker_m = re.search(r"ซื้อ\s+([A-Z0-9]+)", full_str)
            ticker = ticker_m.group(1) if ticker_m else "UNKNOWN"
            if ticker == "SKHYV":
                ticker = "SKHY"

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

    sort_buy_orders(buy_orders)
    return buy_orders


def sort_buy_orders(buy_orders):
    buy_orders.sort(
        key=lambda x: (parse_thai_date(x["date"]), int(re.sub(r"\D", "", x["fn"])) if re.sub(r"\D", "", x["fn"]) else 0),
        reverse=True
    )


def load_statement_cash_flow(manual_movements):
    stmt_path = Path("data/.statement_text.txt")
    if not stmt_path.exists() or stmt_path.stat().st_size == 0:
        return list(manual_movements)

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

    all_records = list(manual_movements) + records

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


def _slip_onclick(*args):
    return escape(f"openSlipModal({', '.join(json.dumps(str(a), ensure_ascii=False) for a in args)})", quote=True)


def dividend_thb(d, fx_rate):
    """THB value of one dividend at the FX recorded with it, else at the current rate."""
    return d["amount_usd"] * (d.get("fx_rate") or fx_rate)


def generate_master_dashboard_data(ledger_path=None):
    ledger = load_ledger(ledger_path)

    # 1. Active Portfolio Live Market Data
    portfolio_data = load_portfolio()
    live_summary = analyze_portfolio(portfolio_data)
    fx_rate = resolve_usdthb(live_summary.get("fx_rate_usd_thb"))

    # 2. Closed Trades Data
    trades_data = load_trades()
    trades_summary = calculate_trades_summary(trades_data)

    # 3. Capital and cash balances from data/ledger.json (seeded from KKP_STATEMENT_20261007.pdf & slips)
    net_injected_capital_thb = ledger["net_injected_capital_thb"]
    gross_promptpay_deposits_thb = ledger["gross_deposits_thb"]
    transfer_out_thb = ledger["transfer_out_thb"]
    dime_save_cash_thb = ledger["cash"]["dime_save_thb"]
    dime_save_interest_thb = ledger["dime_save_interest_thb"]

    # 4. Dime! USD Cash Balance
    dime_usd_cash = ledger["cash"]["dime_usd"]
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
    all_time_roi_pct = round((all_time_profit_thb / net_injected_capital_thb * 100.0), 2) if net_injected_capital_thb else 0.0

    # 6. Realized & Dividend Streams
    total_realized_pl_usd = trades_summary["total_realized_pl_usd"]
    total_realized_pl_thb = trades_summary["total_realized_pl_thb"]
    dividends_list = ledger["dividends"]
    total_dividends_usd = round(sum(d["amount_usd"] for d in dividends_list), 2)
    total_dividends_thb = round(sum(dividend_thb(d, fx_rate) for d in dividends_list), 2)
    total_realized_and_div_thb = round(total_realized_pl_thb + total_dividends_thb + dime_save_interest_thb, 2)

    # 7. Detailed Buy Orders (55 orders from OCR) & Cash Flow (54 transactions from KKP Statement)
    buy_orders = load_ocr_buy_orders() + ledger["buy_orders"]
    sort_buy_orders(buy_orders)
    cash_movements = load_statement_cash_flow(ledger["cash_movements"])

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


def get_live_refresh_script(data):
    net_injected = float(data.get("net_injected_capital_thb", 0.0))
    dime_save_cash = float(data.get("dime_save_cash_thb", 0.0))
    dime_usd_cash = float(data.get("dime_usd_cash", 0.0))
    fx_rate = float(data.get("fx_rate") or resolve_usdthb(None))

    return f"""
    <script>
    {FMT_MONEY_JS}
    const PORTFOLIO_STATIC = {{
        netInjectedCapitalThb: {net_injected},
        dimeSaveCashThb: {dime_save_cash},
        dimeUsdCash: {dime_usd_cash},
        fxRate: {fx_rate}
    }};

    async function refreshLiveQuotes() {{
        const btn = document.getElementById('btn-refresh-live');
        const icon = document.getElementById('refresh-icon');
        const text = document.getElementById('refresh-text');
        const ts = document.getElementById('refresh-timestamp');

        if (!btn) return;
        btn.disabled = true;
        btn.style.opacity = '0.7';
        if (text) text.textContent = 'กำลังดึงราคา...';
        if (icon) icon.style.transform = 'rotate(360deg)';

        try {{
            // 1. Fetch USD/THB rate
            let currentFx = PORTFOLIO_STATIC.fxRate;
            try {{
                const fxRes = await fetch('https://scanner.tradingview.com/forex/scan', {{
                    method: 'POST',
                    mode: 'cors',
                    body: JSON.stringify({{
                        symbols: {{ tickers: ['FX_IDC:USDTHB'] }},
                        columns: ['close']
                    }})
                }});
                if (fxRes.ok) {{
                    const fxData = await fxRes.json();
                    if (fxData.data && fxData.data.length > 0 && fxData.data[0].d && fxData.data[0].d[0]) {{
                        currentFx = parseFloat(fxData.data[0].d[0]);
                    }}
                }}
            }} catch (e) {{
                console.warn('Could not fetch latest FX rate, using fallback', e);
            }}

            // 2. Collect symbols from rows
            const rows = document.querySelectorAll('tr.holding-row');
            const tickers = [];
            rows.forEach(r => {{
                const ex = r.dataset.exchange || 'NASDAQ';
                const tk = r.dataset.ticker;
                if (tk) {{
                    tickers.push(ex + ':' + tk);
                }}
            }});

            if (tickers.length === 0) {{
                throw new Error('ไม่พบรายชื่อหุ้นในตาราง');
            }}

            // 3. Fetch stock quotes from TradingView Scanner API (simple request without custom headers)
            const stockRes = await fetch('https://scanner.tradingview.com/america/scan', {{
                method: 'POST',
                mode: 'cors',
                body: JSON.stringify({{
                    symbols: {{ tickers: tickers }},
                    columns: ['close', 'change']
                }})
            }});

            if (!stockRes.ok) {{
                throw new Error('TradingView ตอบกลับด้วยรหัส ' + stockRes.status);
            }}

            const stockData = await stockRes.json();
            const quotes = {{}};
            (stockData.data || []).forEach(item => {{
                const symParts = (item.s || '').split(':');
                const ticker = symParts.length > 1 ? symParts[1] : symParts[0];
                quotes[ticker] = {{
                    close: item.d[0],
                    change: item.d[1]
                }};
            }});

            // 4. Update rows and compute totals
            let totalMarketValUsd = 0;
            let totalCostUsd = 0;

            rows.forEach(r => {{
                const ticker = r.dataset.ticker;
                const shares = parseFloat(r.dataset.shares) || 0;
                const avgCost = parseFloat(r.dataset.cost) || 0;
                const serverValUsd = parseFloat(r.dataset.serverValUsd);
                const quote = quotes[ticker];
                const costUsd = shares * avgCost;

                if (!(quote && typeof quote.close === 'number')) {{
                    if (!isNaN(serverValUsd)) {{
                        totalMarketValUsd += serverValUsd;
                        totalCostUsd += costUsd;
                        r.dataset.currentValUsd = serverValUsd;
                        r.title = 'ไม่ได้ราคาสด ใช้มูลค่าล่าสุดจากเซิร์ฟเวอร์';
                    }} else {{
                        r.dataset.currentValUsd = 0;
                    }}
                    return;
                }}

                const close = quote.close;
                const valUsd = shares * close;
                const valThb = valUsd * currentFx;
                const plUsd = valUsd - costUsd;
                const plThb = plUsd * currentFx;
                const plPct = costUsd > 0 ? (plUsd / costUsd * 100) : 0;

                totalMarketValUsd += valUsd;
                totalCostUsd += costUsd;

                r.dataset.currentValUsd = valUsd;
                r.title = '';

                const priceCell = r.querySelector('.cell-price');
                const valUsdCell = r.querySelector('.cell-val-usd');
                const valThbCell = r.querySelector('.cell-val-thb');
                const plUsdCell = r.querySelector('.cell-pl-usd');
                const plThbCell = r.querySelector('.cell-pl-thb');
                const plPctCell = r.querySelector('.cell-pl-pct');

                const color = plUsd >= 0 ? '#10b981' : '#f43f5e';

                if (priceCell) priceCell.textContent = fmtMoney(close, '$');
                if (valUsdCell) valUsdCell.textContent = fmtMoney(valUsd, '$');
                if (valThbCell) valThbCell.textContent = fmtMoney(valThb, '฿');

                if (plUsdCell) {{
                    plUsdCell.textContent = fmtMoney(plUsd, '$', true);
                    plUsdCell.style.color = color;
                }}
                if (plThbCell) {{
                    plThbCell.textContent = fmtMoney(plThb, '฿', true);
                    plThbCell.style.color = color;
                }}
                if (plPctCell) {{
                    plPctCell.textContent = fmtPct(plPct, 2);
                    plPctCell.style.color = color;
                }}

                r.style.transition = 'background-color 0.4s ease';
                r.style.backgroundColor = 'rgba(59, 130, 246, 0.12)';
                setTimeout(() => {{ r.style.backgroundColor = ''; }}, 600);
            }});

            // 5. Update weights
            rows.forEach(r => {{
                const valUsd = parseFloat(r.dataset.currentValUsd) || 0;
                const weightPct = totalMarketValUsd > 0 ? (valUsd / totalMarketValUsd * 100) : 0;
                const weightCell = r.querySelector('.cell-weight');
                if (weightCell) weightCell.textContent = weightPct.toFixed(1) + '%';
            }});

            // 6. Update KPIs
            const totalMarketValThb = totalMarketValUsd * currentFx;
            const totalPlUsd = totalMarketValUsd - totalCostUsd;
            const totalPlThb = totalPlUsd * currentFx;
            const totalPlPct = totalCostUsd > 0 ? (totalPlUsd / totalCostUsd * 100) : 0;

            const totalCashThb = PORTFOLIO_STATIC.dimeSaveCashThb + (PORTFOLIO_STATIC.dimeUsdCash * currentFx);
            const totalNetWorthThb = totalMarketValThb + totalCashThb;
            const totalNetWorthUsd = currentFx > 0 ? (totalNetWorthThb / currentFx) : 0;

            const allTimeProfitThb = totalNetWorthThb - PORTFOLIO_STATIC.netInjectedCapitalThb;
            const allTimeRoiPct = PORTFOLIO_STATIC.netInjectedCapitalThb > 0 ? (allTimeProfitThb / PORTFOLIO_STATIC.netInjectedCapitalThb * 100) : 0;

            // DOM updates
            const kpiNetWorthThb = document.getElementById('kpi-net-worth-thb');
            const kpiNetWorthUsdSub = document.getElementById('kpi-net-worth-usd-sub');
            const kpiAllTimeProfitThb = document.getElementById('kpi-all-time-profit-thb');
            const kpiAllTimeRoiSub = document.getElementById('kpi-all-time-roi-sub');
            const kpiStockValUsd = document.getElementById('kpi-stock-market-val-usd');
            const kpiStockValThb = document.getElementById('kpi-stock-market-val-thb');
            const kpiStockUnrealizedPl = document.getElementById('kpi-stock-unrealized-pl');
            const kpiFxPill = document.getElementById('kpi-fx-pill');
            const kpiTotalCashThb = document.getElementById('kpi-total-cash-thb');

            if (kpiNetWorthThb) kpiNetWorthThb.textContent = fmtMoney(totalNetWorthThb, '฿');
            if (kpiNetWorthUsdSub) kpiNetWorthUsdSub.textContent = '~' + fmtMoney(totalNetWorthUsd, '$') + ' USD (หุ้น + เงินสด)';

            const atColor = allTimeProfitThb >= 0 ? '#10b981' : '#f43f5e';
            if (kpiAllTimeProfitThb) {{
                kpiAllTimeProfitThb.textContent = fmtMoney(allTimeProfitThb, '฿', true);
                kpiAllTimeProfitThb.style.color = atColor;
            }}
            if (kpiAllTimeRoiSub) {{
                kpiAllTimeRoiSub.textContent = fmtPct(allTimeRoiPct, 2) + ' All-Time ROI';
                kpiAllTimeRoiSub.style.color = atColor;
            }}

            if (kpiStockValUsd) kpiStockValUsd.textContent = fmtMoney(totalMarketValUsd, '$');
            if (kpiStockValThb) kpiStockValThb.textContent = fmtMoney(totalMarketValThb, '฿');

            const unColor = totalPlUsd >= 0 ? '#10b981' : '#f43f5e';
            if (kpiStockUnrealizedPl) {{
                kpiStockUnrealizedPl.textContent = fmtMoney(totalPlUsd, '$', true) + ' (' + fmtPct(totalPlPct, 2) + ')';
                kpiStockUnrealizedPl.style.color = unColor;
            }}

            if (kpiTotalCashThb) kpiTotalCashThb.textContent = fmtMoney(totalCashThb, '฿');
            if (kpiFxPill) kpiFxPill.textContent = '⚡ 1 USD = ' + currentFx.toFixed(2) + ' THB';

            const now = new Date();
            const timeStr = now.toLocaleTimeString('th-TH', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
            if (ts) ts.innerHTML = '🟢 ราคาเรียลไทม์ล่าสุด: <strong style="color: #60a5fa;">' + timeStr + ' น.</strong>';

        }} catch (err) {{
            console.warn('Direct TradingView fetch blocked (common on mobile iOS/WebKit ITP), syncing from Cloud data:', err);
            try {{
                const cloudRes = await fetch('../data/account_summary.json?t=' + Date.now());
                if (cloudRes.ok) {{
                    const cData = await cloudRes.json();
                    const cPositions = cData.positions || [];
                    const cMap = {{}};
                    cPositions.forEach(p => {{ cMap[p.ticker] = p; }});

                    const rows = document.querySelectorAll('tr.holding-row');
                    rows.forEach(r => {{
                        const ticker = r.dataset.ticker;
                        const p = cMap[ticker];
                        if (p) {{
                            const close = p.close_price;
                            const valUsd = p.current_val_usd;
                            const valThb = p.current_val_thb;
                            const plUsd = p.unrealized_pl_usd;
                            const plThb = p.unrealized_pl_thb;
                            const plPct = p.unrealized_pl_pct;
                            const weightPct = p.weight_pct;

                            const priceCell = r.querySelector('.cell-price');
                            const valUsdCell = r.querySelector('.cell-val-usd');
                            const valThbCell = r.querySelector('.cell-val-thb');
                            const plUsdCell = r.querySelector('.cell-pl-usd');
                            const plThbCell = r.querySelector('.cell-pl-thb');
                            const plPctCell = r.querySelector('.cell-pl-pct');
                            const weightCell = r.querySelector('.cell-weight');

                            const color = plUsd >= 0 ? '#10b981' : '#f43f5e';

                            if (priceCell) priceCell.textContent = fmtMoney(close, '$');
                            if (valUsdCell) valUsdCell.textContent = fmtMoney(valUsd, '$');
                            if (valThbCell) valThbCell.textContent = fmtMoney(valThb, '฿');
                            if (plUsdCell) {{
                                plUsdCell.textContent = fmtMoney(plUsd, '$', true);
                                plUsdCell.style.color = color;
                            }}
                            if (plThbCell) {{
                                plThbCell.textContent = fmtMoney(plThb, '฿', true);
                                plThbCell.style.color = color;
                            }}
                            if (plPctCell) {{
                                plPctCell.textContent = fmtPct(plPct, 2) + '';
                                plPctCell.style.color = color;
                            }}
                            if (weightCell) weightCell.textContent = (weightPct === null || weightPct === undefined) ? '-' : weightPct.toFixed(1) + '%';

                            r.style.transition = 'background-color 0.4s ease';
                            r.style.backgroundColor = 'rgba(16, 185, 129, 0.12)';
                            setTimeout(() => {{ r.style.backgroundColor = ''; }}, 600);
                        }}
                    }});

                    const kpiNetWorthThb = document.getElementById('kpi-net-worth-thb');
                    const kpiNetWorthUsdSub = document.getElementById('kpi-net-worth-usd-sub');
                    const kpiAllTimeProfitThb = document.getElementById('kpi-all-time-profit-thb');
                    const kpiAllTimeRoiSub = document.getElementById('kpi-all-time-roi-sub');
                    const kpiStockValUsd = document.getElementById('kpi-stock-market-val-usd');
                    const kpiStockValThb = document.getElementById('kpi-stock-market-val-thb');
                    const kpiStockUnrealizedPl = document.getElementById('kpi-stock-unrealized-pl');
                    const kpiFxPill = document.getElementById('kpi-fx-pill');
                    const kpiTotalCashThb = document.getElementById('kpi-total-cash-thb');

                    if (kpiNetWorthThb) kpiNetWorthThb.textContent = fmtMoney((cData.total_net_worth_thb || 0), '฿');
                    if (kpiNetWorthUsdSub) kpiNetWorthUsdSub.textContent = '~' + fmtMoney((cData.total_net_worth_usd || 0), '$') + ' USD (หุ้น + เงินสด)';

                    const atProfit = cData.all_time_profit_thb || 0;
                    const atRoi = cData.all_time_roi_pct || 0;
                    const atColor = atProfit >= 0 ? '#10b981' : '#f43f5e';
                    if (kpiAllTimeProfitThb) {{
                        kpiAllTimeProfitThb.textContent = fmtMoney(atProfit, '฿', true);
                        kpiAllTimeProfitThb.style.color = atColor;
                    }}
                    if (kpiAllTimeRoiSub) {{
                        kpiAllTimeRoiSub.textContent = fmtPct(atRoi, 2) + ' All-Time ROI';
                        kpiAllTimeRoiSub.style.color = atColor;
                    }}

                    if (kpiStockValUsd) kpiStockValUsd.textContent = fmtMoney((cData.stock_market_val_usd || 0), '$');
                    if (kpiStockValThb) kpiStockValThb.textContent = fmtMoney((cData.stock_market_val_thb || 0), '฿');

                    const unPlUsd = cData.stock_unrealized_pl_usd || 0;
                    const unPlPct = cData.stock_unrealized_pl_pct || 0;
                    const unColor = unPlUsd >= 0 ? '#10b981' : '#f43f5e';
                    if (kpiStockUnrealizedPl) {{
                        kpiStockUnrealizedPl.textContent = fmtMoney(unPlUsd, '$', true) + ' (' + fmtPct(unPlPct, 2) + ')';
                        kpiStockUnrealizedPl.style.color = unColor;
                    }}

                    if (kpiTotalCashThb) kpiTotalCashThb.textContent = fmtMoney((cData.total_cash_thb || 0), '฿');
                    if (kpiFxPill) kpiFxPill.textContent = '⚡ 1 USD = ' + (cData.fx_rate || PORTFOLIO_STATIC.fxRate).toFixed(2) + ' THB';

                    if (ts) ts.innerHTML = '☁️ ซิงค์ข้อมูลล่าสุดจาก Cloud: <strong style="color: #60a5fa;">' + (cData.updated_at || '') + ' น.</strong>';
                }}
            }} catch (fallbackErr) {{
                console.error('Cloud sync fallback error:', fallbackErr);
                if (ts) ts.innerHTML = '⚠️ ซิงค์ขัดข้อง กรุณาลองใหม่อีกครั้ง';
            }}
        }} finally {{
            btn.disabled = false;
            btn.style.opacity = '1';
            if (text) text.textContent = 'รีเฟรชราคาเรียลไทม์';
            if (icon) icon.style.transform = '';
        }}
    }}
    </script>
    """


def generate_master_dashboard_html(data):
    at_color = "#10b981" if data["all_time_profit_thb"] >= 0 else "#f43f5e"

    un_color = "#10b981" if data["stock_unrealized_pl_thb"] >= 0 else "#f43f5e"
    rz_color = "#10b981" if data["trades_summary"]["total_realized_pl_thb"] >= 0 else "#f43f5e"
    rd_color = "#10b981" if data["total_realized_and_div_thb"] >= 0 else "#f43f5e"

    # 1. Active Holdings Rows
    holdings_rows = ""
    for p in data["positions"]:
        p_pl_usd = p["unrealized_pl_usd"]
        p_pl_thb = p["unrealized_pl_thb"]
        p_pl_pct = p["unrealized_pl_pct"]
        c = "#10b981" if (p_pl_usd or 0) >= 0 else "#f43f5e"
        onclick_js = _make_chart_onclick(p)
        ex = escape(str(p.get('exchange', 'NASDAQ')), quote=True)
        tk = escape(str(p['ticker']), quote=True)
        server_val = p.get('current_val_usd')
        server_val_attr = f' data-server-val-usd="{server_val}"' if server_val is not None else ""
        holdings_rows += f"""
        <tr class="holding-row" data-ticker="{tk}" data-exchange="{ex}" data-shares="{p['shares']}" data-cost="{p['avg_cost_usd']}"{server_val_attr}>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif;">
                <span class="clickable-ticker" onclick="{onclick_js}" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{tk} 📈</span>
            </td>
            <td>{escape(str(p.get('name') or '-'))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{p['shares']:.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{money(p['avg_cost_usd'])}</td>
            <td class="cell-price" style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600;">{money(p.get('close_price'), na='n/a')}</td>
            <td class="cell-val-usd" style="text-align: right; font-family: 'Inter', sans-serif;">{money(p.get('current_val_usd'), na='n/a')}</td>
            <td class="cell-val-thb" style="text-align: right; font-family: 'Inter', sans-serif;">{money(p.get('current_val_thb'), 'THB', na='n/a')}</td>
            <td class="cell-pl-usd" style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{money(p_pl_usd, signed=True, na='n/a')}</td>
            <td class="cell-pl-thb" style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 600;">{money(p_pl_thb, 'THB', signed=True, na='n/a')}</td>
            <td class="cell-pl-pct" style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{pct(p_pl_pct, digits=2, na='n/a')}</td>
            <td class="cell-weight" style="text-align: right; font-family: 'Inter', sans-serif;">{pct(p.get('weight_pct'), signed=False)}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Master Portfolio & Wealth Summary - {escape(str(data['portfolio_name']))}</title>
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
        .master-tab-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 14px;
            overflow-x: auto;
            scrollbar-width: none;
        }}
        .master-tab-bar::-webkit-scrollbar {{ display: none; }}
        .master-tab-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-secondary);
            font-family: 'Prompt', 'Inter', -apple-system, sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}
        .master-tab-btn:hover {{
            color: #fff;
            background: rgba(255, 255, 255, 0.07);
            border-color: rgba(255, 255, 255, 0.2);
        }}
        .master-tab-btn.active {{
            color: #60a5fa;
            background: rgba(59, 130, 246, 0.15);
            border-color: #3b82f6;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
        }}
        .tab-badge {{
            padding: 2px 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 500;
            color: inherit;
        }}
        .sub-tab-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .sub-tab-btn {{
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-secondary);
            font-family: 'Prompt', 'Inter', -apple-system, sans-serif;
            font-size: 0.88rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .sub-tab-btn:hover {{
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }}
        .sub-tab-btn.active {{
            background: rgba(139, 92, 246, 0.2);
            border-color: #8b5cf6;
            color: #c084fc;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        {nav_bar_html('master')}
        <!-- HEADER -->
        <div class="header">
            <div>
                <h1 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px;">
                    💎 ศูนย์รวมข้อมูลพอร์ตการลงทุน Master Summary
                </h1>
                <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">
                    พอร์ต: <strong style="color: #fff;">{escape(str(data['portfolio_name']))}</strong> | 
                    โบรกเกอร์: <strong style="color: #fff;">{escape(str(data['broker']))}</strong> | 
                    บัญชี: <code>{escape(str(data['account_no']))}</code>
                </p>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end;">
                    <span id="kpi-fx-pill" class="meta-pill">⚡ 1 USD = {data['fx_rate']:.2f} THB</span>
                    <button id="btn-refresh-live" onclick="refreshLiveQuotes()" style="display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.35) 100%); border: 1px solid rgba(59, 130, 246, 0.5); color: #93c5fd; padding: 7px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; font-family: inherit;">
                        <span id="refresh-icon" style="display: inline-block; transition: transform 0.6s ease;">🔄</span>
                        <span id="refresh-text">รีเฟรชราคา</span>
                        <span style="font-size: 0.68rem; background: rgba(59, 130, 246, 0.25); border: 1px solid rgba(59, 130, 246, 0.4); padding: 1px 5px; border-radius: 4px; color: #93c5fd; margin-left: 2px;">v2.2</span>
                    </button>
                    <a href="https://github.com/Benzthanes/Stock-portfolio/actions/workflows/update_portfolio.yml" target="_blank" style="display: inline-flex; align-items: center; gap: 4px; text-decoration: none; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; padding: 7px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; transition: all 0.2s ease; font-family: inherit;">
                        <span>⚡ สั่งคำนวณสดบน Cloud ↗</span>
                    </a>
                </div>
                <span id="refresh-timestamp" style="font-size: 0.78rem; color: var(--text-muted);"></span>
            </div>
        </div>

        <!-- 4 MAIN HERO KPIS -->
        <div class="grid-4-cols">
            <div class="card" style="border-left: 4px solid var(--blue);">
                <div class="kpi-label">มูลค่าพอร์ตรวมสุทธิ (Total Net Worth / NAV)</div>
                <div id="kpi-net-worth-thb" class="kpi-value" style="color: #60a5fa;">{money(data['total_net_worth_thb'], 'THB')}</div>
                <div id="kpi-net-worth-usd-sub" class="kpi-subtext">~{money(data['total_net_worth_usd'])} USD (หุ้น + เงินสด)</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--purple);">
                <div class="kpi-label">เงินต้นทุนเติมสุทธิ (Net Deposited Capital)</div>
                <div class="kpi-value">{money(data['net_injected_capital_thb'], 'THB')}</div>
                <div class="kpi-subtext">จาก KKP Statement ทางการ 100% (PromptPay 19 ครั้ง - ถอนออก 1 ครั้ง)</div>
            </div>
            <div class="card" style="border-left: 4px solid {at_color};">
                <div class="kpi-label">กำไรรวมสุทธิของพอร์ต (All-Time Net Profit)</div>
                <div id="kpi-all-time-profit-thb" class="kpi-value" style="color: {at_color};">{money(data['all_time_profit_thb'], 'THB', signed=True)}</div>
                <div id="kpi-all-time-roi-sub" class="kpi-subtext" style="color: {at_color}; font-weight: 700;">{pct(data['all_time_roi_pct'], digits=2)} All-Time ROI</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--emerald);">
                <div class="kpi-label">เงินสดคงเหลือรวม (Total Idle Cash)</div>
                <div id="kpi-total-cash-thb" class="kpi-value">{money(data['total_cash_thb'], 'THB')}</div>
                <div class="kpi-subtext">Dime! Save: {money(data['dime_save_cash_thb'], 'THB')} | Dime! USD: {money(data['dime_usd_cash'])}</div>
            </div>
        </div>

        <!-- SECONDARY METRICS: 3-COLS -->
        <div class="grid-3-cols">
            <div class="card">
                <div class="kpi-label">หุ้นที่กำลังถือครอง (Active Holdings)</div>
                <div style="font-size: 1.45rem; font-weight: 700;">{len(data['positions'])} บริษัท</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    มูลค่าตลาด: <strong id="kpi-stock-market-val-usd">{money(data['stock_market_val_usd'])}</strong> (<span id="kpi-stock-market-val-thb">{money(data['stock_market_val_thb'], 'THB')}</span>)<br>
                    กำไรที่ยังไม่ขาย: <strong id="kpi-stock-unrealized-pl" style="color: {un_color};">{money(data['stock_unrealized_pl_usd'], signed=True)} ({pct(data['stock_unrealized_pl_pct'], digits=2)})</strong>
                </div>
            </div>
            <div class="card">
                <div class="kpi-label">กำไรที่ขายทำกำไรจริง (Realized P&L)</div>
                <div style="font-size: 1.45rem; font-weight: 700; color: {rz_color};">{money(data['trades_summary']['total_realized_pl_usd'], signed=True)}</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    คิดเป็นเงินไทย: <strong style="color: {rz_color};">{money(data['trades_summary']['total_realized_pl_thb'], 'THB', signed=True)}</strong><br>
                    Win Rate: <strong style="color: #10b981;">{data['trades_summary']['win_rate_pct']:.1f}%</strong> (ปิด {data['trades_summary']['total_trades']} ชนะ {data['trades_summary']['winning_trades']} ไม้)
                </div>
            </div>
            <div class="card">
                <div class="kpi-label">เงินปันผลรับสะสม (Dividends)</div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #10b981;">{money(data['total_dividends_usd'], signed=True)}</div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: var(--text-secondary);">
                    คิดเป็นเงินไทย: <strong style="color: #10b981;">{money(data['total_dividends_thb'], 'THB', signed=True)}</strong> (รับรวม {len(data['dividends_list'])} ครั้ง)<br>
                    รวมกำไรปิดไม้ + ปันผล: <strong style="color: {rd_color};">{money(data['total_realized_and_div_thb'], 'THB', signed=True)}</strong>
                </div>
            </div>
        </div>

        <!-- SECTION 1: ACTIVE HOLDINGS TABLE -->
        <div style="margin-bottom: 36px;">
            <div class="section-title">
                <span>📈</span> 1. รายการหุ้นที่กำลังถือครองในพอร์ต (Active Holdings: {len(data.get('positions', []))} ตัว)
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

            <!-- Link to Deep-Dive Health & Catalysts -->
            <div class="card" style="margin-top: 18px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.4rem;">🔭</span>
                    <div>
                        <div style="color: #f8fafc; font-size: 0.95rem; font-weight: 700;">ต้องการอ่านวิสัยทัศน์ ตัวเร่งราคา และบทวิเคราะห์ข่าว AI เชิงลึกรายตัว?</div>
                        <div style="color: var(--text-secondary); font-size: 0.84rem;">ตรวจสุขภาพพอร์ต สัดส่วนกลุ่มธุรกิจ แผน Action Roadmap และปฏิทินงบการเงิน</div>
                    </div>
                </div>
                <a href="portfolio_review.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); color: #60a5fa; padding: 8px 16px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; text-decoration: none; transition: all 0.2s;">
                    <span>ดูรายงานตรวจสุขภาพพอร์ตฉบับเต็ม</span> <span>→</span>
                </a>
            </div>
        </div>

        <!-- LINK TO COMPLETE TRADES LEDGER -->
        <div class="card" style="margin-top: 24px; background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%); border: 1px solid rgba(139, 92, 246, 0.3); padding: 24px; text-align: center;">
            <div style="font-size: 1.2rem; font-weight: 700; color: #fff; margin-bottom: 8px;">
                📑 รายการซื้อขาย เงินปันผล และประวัติเดินบัญชีทั้งหมด
            </div>
            <p style="color: var(--text-secondary); font-size: 0.92rem; margin-bottom: 16px;">
                ตรวจสอบประวัติคำสั่งซื้อหุ้น {len(data.get('buy_orders', []))} ไม้ | ปิดขายทำกำไร {len(data.get('closed_trades', []))} ไม้ | ปันผลรับ {len(data.get('dividends_list', []))} ครั้ง | เดินบัญชี {len(data.get('cash_movements', []))} รายการ
            </p>
            <a href="trades_ledger.html" style="display: inline-flex; align-items: center; gap: 8px; background: #3b82f6; color: #fff; padding: 10px 24px; border-radius: 10px; font-weight: 600; text-decoration: none; transition: background 0.2s;">
                <span>ดูรายการซื้อขายทั้งหมด</span> <span>→</span>
            </a>
        </div>

    </div>
    <script>
    window.addEventListener('DOMContentLoaded', function() {{
        var hash = (window.location.hash || '').replace('#', '');
        if (['ledger', 'transactions', 'trades', 'buys', 'sells', 'divs', 'cash'].indexOf(hash) !== -1) {{
            window.location.replace('trades_ledger.html' + window.location.hash);
        }}
    }});
    </script>
    {get_live_refresh_script(data)}
    {get_chart_modal_component()}
</body>
</html>
"""
    return html


def generate_master_ledger_html(data):
    buy_orders = data.get("buy_orders", [])
    closed_trades = data.get("closed_trades", [])
    dividends_list = data.get("dividends_list", [])
    cash_movements = data.get("cash_movements", [])
    trades_summary = data.get("trades_summary", {})
    fx_rate = data.get("fx_rate") or resolve_usdthb(None)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rz_color = "#10b981" if trades_summary.get("total_realized_pl_thb", 0) >= 0 else "#f43f5e"

    total_buys_usd = sum(b.get("amt_usd", 0.0) for b in buy_orders)
    total_buys_thb = sum(b.get("amt_thb", 0.0) for b in buy_orders)

    # 1. Buy Orders Rows
    buy_rows = ""
    for idx, b in enumerate(buy_orders):
        acc_badge = '<span class="badge badge-success">Dime! Save (THB)</span>' if "Save" in b.get("account", "") else '<span class="badge badge-info">Dime! USD</span>'
        type_badge = f'<span class="badge badge-purple">{escape(str(b.get("order_type", "Market")))}</span>' if b.get("order_type") == "Limit" else '<span class="badge badge-neutral">Market</span>'
        fx_val = b.get("fx_rate", 0)
        fx_str = money(fx_val, 'THB') if fx_val > 0 else "-"
        amt_thb_val = b.get("amt_thb", 0)
        thb_str = money(amt_thb_val, 'THB') if amt_thb_val > 0 else "-"
        fn_val = b.get("fn", "")
        fn_html = escape(str(fn_val or "-"))
        slip_path = resolve_slip_relative_path(fn_val)
        if slip_path:
            b_tick = b.get("ticker", "-")
            b_dt = b.get("date", "-")
            b_sh = b.get("shares", 0.0)
            b_pr = b.get("price_usd", 0.0)
            b_info = f"{b_sh:.4f} หุ้น @ {money(b_pr)}"
            slip_html = f'<button type="button" onclick="{_slip_onclick(slip_path, fn_val, b_tick, b_dt, b_info)}" class="slip-badge-btn" title="คลิกเพื่อดูสลิปคำสั่งซื้อ">🧾 {fn_html}</button>'
        else:
            slip_html = f'<span style="color: var(--text-muted); font-size: 0.78rem;">{fn_html}</span>'

        buy_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary);">{escape(str(b.get('date', '-')))}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; color: #60a5fa;">{escape(str(b.get('ticker', '-')))}</td>
            <td style="text-align: center;">{type_badge}</td>
            <td style="text-align: center;">{acc_badge}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600;">{b.get('shares', 0):.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{money(b.get('price_usd', 0))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">{money(b.get('amt_usd', 0))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{thb_str}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{fx_str}</td>
            <td style="text-align: center;">{slip_html}</td>
        </tr>
        """

    # 2. Closed Trades Rows (Multi-tranche expand)
    closed_rows = ""
    for idx, t in enumerate(closed_trades):
        c = "#10b981" if t.get("realized_pl_usd", 0) >= 0 else "#f43f5e"
        tranches = t.get("buy_tranches", [])
        tranche_count = len(tranches)
        trade_id = t.get("id", f"trade_{idx}").replace("-", "_")

        buy_date_str = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
        t_ticker = escape(str(t.get("ticker", "")))
        days = t.get("holding_days", "-")
        days_str = f"{days} วัน" if isinstance(days, (int, float)) else str(days)

        if tranche_count > 1:
            tranche_btn = f'<button onclick="toggleTranche(\'{trade_id}\')" style="background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 6px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">สะสม {tranche_count} ไม้ <span id="icon-{trade_id}">▼</span></button>'
        else:
            single_fn = tranches[0].get('file') if tranches else None
            single_path = resolve_slip_relative_path(single_fn) if single_fn else ""
            if single_path:
                t_tk = t.get("ticker", "")
                t_sh = t.get("shares", 0.0)
                t_pr = t.get("buy_price_usd", 0.0)
                t_info = f"{t_sh:.4f} หุ้น @ {money(t_pr)}"
                tranche_btn = f'<span class="badge badge-neutral" style="font-size: 0.76rem;">1 ไม้</span> <button type="button" onclick="{_slip_onclick(single_path, single_fn, t_tk, buy_date_str, t_info)}" class="slip-badge-btn" style="padding: 2px 7px; font-size: 0.74rem;" title="คลิกดูภาพสลิปคำสั่งซื้อ">🧾 สลิป</button>'
            else:
                tranche_btn = '<span class="badge badge-neutral" style="font-size: 0.76rem;">1 ไม้</span>'

        closed_rows += f"""
        <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: #60a5fa; font-weight: 500;">{escape(buy_date_str)}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary); text-align: center;">{escape(str(t.get('date', '-')))}</td>
            <td style="text-align: center; font-size: 0.82rem; color: var(--text-muted); white-space: nowrap;">{days_str}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; font-size: 1.05rem; color: #fff;">{t_ticker}</td>
            <td>
                <div>{escape(str(t.get('name') or '-'))}</div>
                <div style="margin-top: 4px;">{tranche_btn}</div>
            </td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{t.get('shares', 0):.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{money(t.get('buy_price_usd', 0))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">{money(t.get('sell_price_usd', 0))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{money(t.get('total_cost_usd', 0))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">{money(t.get('net_revenue_usd', 0))}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{money(t.get('realized_pl_usd', 0), signed=True)}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 600;">{money(t.get('realized_pl_thb', 0), 'THB', signed=True)}</td>
            <td style="text-align: right; color: {c}; font-family: 'Inter', sans-serif; font-weight: 700;">{pct(t.get('realized_pl_pct', 0), digits=2)}</td>
        </tr>
        """

        if tranches:
            tranche_subrows = ""
            for tr in tranches:
                t_thb_str = money(tr.get('amt_thb', 0), 'THB') if tr.get('amt_thb', 0) > 0 else "-"
                tr_fn = tr.get('file', '')
                tr_path = resolve_slip_relative_path(tr_fn)
                if tr_path:
                    tr_tk = t.get("ticker", "")
                    tr_dt = tr.get("date", "-")
                    tr_num = tr.get("tranche", 1)
                    tr_sh = tr.get("shares", 0.0)
                    tr_pr = tr.get("price_usd", 0.0)
                    tr_info = f"ไม้ที่ {tr_num} • {tr_sh:.4f} หุ้น @ {money(tr_pr)}"
                    slip_col = f'<button type="button" onclick="{_slip_onclick(tr_path, tr_fn, tr_tk, tr_dt, tr_info)}" class="slip-badge-btn" title="คลิกดูภาพสลิปคำสั่งซื้อ">🧾 {escape(str(tr_fn))}</button>'
                else:
                    slip_col = f'<span style="color: var(--text-muted); font-size: 0.78rem;">{escape(str(tr_fn or "-"))}</span>'

                tranche_subrows += f"""
                <tr style="background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.82rem;">
                    <td style="text-align: center; color: #c084fc; font-weight: 700;">ไม้ที่ {tr.get('tranche')}</td>
                    <td style="color: #60a5fa; font-family: 'Inter', sans-serif;">{escape(str(tr.get('date')))}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">{tr.get('shares', 0):.4f} หุ้น</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">{money(tr.get('price_usd', 0))}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">{money(tr.get('amt_usd', 0))}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{t_thb_str}</td>
                    <td style="color: var(--text-secondary);">{escape(str(tr.get('note', '-')))}</td>
                    <td style="text-align: center;">{slip_col}</td>
                </tr>
                """

            closed_rows += f"""
            <tr id="details-{trade_id}" class="tranche-detail-row" style="display: none; background: rgba(139, 92, 246, 0.05);">
                <td colspan="14" style="padding: 12px 18px;">
                    <div style="background: #090e1a; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 14px 18px;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #c084fc; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                            <span>🔍</span> รายละเอียดการเข้าซื้อทีละไม้ของ {t_ticker} (ทั้งหมด {tranche_count} ไม้ | ต้นทุนเฉลี่ย {money(t.get('buy_price_usd', 0))}):
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

    # 3. Dividend Rows
    div_rows = ""
    for d in dividends_list:
        div_amt_usd = d.get('amount_usd', 0)
        div_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-secondary);">{escape(str(d.get('date', '-')))}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif;">{escape(str(d.get('ticker', '-')))}</td>
            <td>{escape(str(d.get('rate', '-')))}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 700; color: #10b981;">{money(div_amt_usd, signed=True)}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #10b981;">{money(dividend_thb({**d, "amount_usd": div_amt_usd}, fx_rate), 'THB', signed=True)}</td>
        </tr>
        """

    # 4. Cash Movements Rows
    cash_rows = ""
    for idx, c in enumerate(cash_movements):
        c_type = c.get("type", "")
        if "ฝากเงิน" in c_type:
            badge = '<span class="badge badge-success">ฝากเงินเข้าพอร์ต</span>'
            amt_color = "#10b981"
        elif "ดอกเบี้ย" in c_type:
            badge = '<span class="badge badge-info">ดอกเบี้ยรับเงินฝาก</span>'
            amt_color = "#60a5fa"
        elif "โอนเงินออก" in c_type:
            badge = '<span class="badge badge-rose">โอนเงินออกไปต่างธนาคาร</span>'
            amt_color = "#f43f5e"
        else:
            badge = '<span class="badge badge-rose">ตัดชำระค่าซื้อหุ้น</span>'
            amt_color = "#f43f5e"

        bal_str = money(c['balance_thb'], 'THB') if "balance_thb" in c else "-"
        ch_str = escape(str(c.get("channel", "Dime! Save")))
        ref_str = escape(str(c.get("ref", "-")))

        cash_rows += f"""
        <tr>
            <td style="text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;">{idx+1:02d}</td>
            <td style="white-space: nowrap; font-size: 0.88rem; color: var(--text-secondary);">{escape(str(c.get('date_str', '-')))}</td>
            <td>{badge}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 700; color: {amt_color};">{money(c.get('amount_thb', 0), 'THB', signed=True)}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; color: #fff;">{bal_str}</td>
            <td style="text-align: center; font-family: 'Inter', sans-serif; font-size: 0.82rem; color: var(--text-muted);">{ch_str}</td>
            <td style="text-align: center; font-family: 'Inter', sans-serif; font-size: 0.78rem; color: var(--text-muted);">{ref_str}</td>
        </tr>
        """

    total_records = len(buy_orders) + len(closed_trades) + len(dividends_list) + len(cash_movements)
    gross_deposits = data.get('gross_deposits_thb', data.get('gross_promptpay_deposits_thb', 0.0))
    transfer_out = data.get('transfer_out_thb', 0.0)
    dime_save_cash = data.get('dime_save_cash_thb', 0.0)

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>รายการซื้อขายและเดินบัญชีทั้งหมด - {escape(str(data.get('portfolio_name', 'Portfolio')))}</title>
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
        .sub-tab-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .sub-tab-btn {{
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-secondary);
            font-family: 'Prompt', 'Inter', -apple-system, sans-serif;
            font-size: 0.88rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .sub-tab-btn:hover {{
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }}
        .sub-tab-btn.active {{
            background: rgba(139, 92, 246, 0.2);
            border-color: #8b5cf6;
            color: #c084fc;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        {nav_bar_html('ledger')}

        <!-- HEADER -->
        <div class="header">
            <div>
                <h1 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px;">
                    📑 รายการซื้อขายและเดินบัญชีทั้งหมด
                </h1>
                <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">
                    พอร์ต: <strong style="color: #fff;">{escape(str(data.get('portfolio_name', 'ไม่รวยก็ซวยอ่ะค้าบ')))}</strong> | บันทึกประวัติคำสั่งซื้อ ปิดขายทำกำไร เงินปันผล และการเดินบัญชีครบวงจร
                </p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <button onclick="toggleAllTranches()" style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); color: #c084fc; padding: 8px 16px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                    <span>🔍</span> <span id="toggleAllBtnText">คลี่ดูรายละเอียดทุกไม้ (Expand All)</span>
                </button>
                <span class="meta-pill">🕒 ข้อมูล ณ: {now_str}</span>
            </div>
        </div>

        <!-- TRANSACTIONS KPI OVERVIEW (4-COLS) -->
        <div class="grid-4-cols">
            <div class="card">
                <div class="kpi-label">เงินต้นฝากสะสมสุทธิ (Net Capital)</div>
                <div class="kpi-value" style="color: #60a5fa;">{money(data.get('net_injected_capital_thb', 0), 'THB')}</div>
                <div class="kpi-subtext">ฝากรวม {money(gross_deposits, 'THB')} (โอนออก {money(-abs(transfer_out), 'THB')})</div>
            </div>
            <div class="card">
                <div class="kpi-label">ยอดคำสั่งซื้อหุ้นรวม (Total Buys)</div>
                <div class="kpi-value" style="color: #38bdf8;">{money(total_buys_thb, 'THB')}</div>
                <div class="kpi-subtext">{money(total_buys_usd)} USD ({len(buy_orders)} คำสั่งซื้อ)</div>
            </div>
            <div class="card">
                <div class="kpi-label">กำไรปิดรอบที่ขายแล้ว (Realized P&L)</div>
                <div class="kpi-value" style="color: {rz_color};">{money(trades_summary.get('total_realized_pl_thb', 0), 'THB', signed=True)}</div>
                <div class="kpi-subtext">Win Rate {trades_summary.get('win_rate_pct', 0):.1f}% ({trades_summary.get('winning_trades', 0)} ชนะ / {trades_summary.get('losing_trades', 0)} แพ้)</div>
            </div>
            <div class="card">
                <div class="kpi-label">เงินปันผลรับสะสม (Dividends)</div>
                <div class="kpi-value" style="color: #10b981;">{money(data.get('total_dividends_thb', 0), 'THB', signed=True)}</div>
                <div class="kpi-subtext">{money(data.get('total_dividends_usd', 0), signed=True)} USD ({len(dividends_list)} ครั้ง)</div>
            </div>
        </div>

        <!-- SUB-TAB BAR -->
        <div class="sub-tab-bar">
            <button id="btn-sub-all" class="sub-tab-btn active" onclick="switchSubTab('all')">ทั้งหมด ({total_records})</button>
            <button id="btn-sub-buys" class="sub-tab-btn" onclick="switchSubTab('buys')">🛒 คำสั่งซื้อหุ้น ({len(buy_orders)})</button>
            <button id="btn-sub-sells" class="sub-tab-btn" onclick="switchSubTab('sells')">🏆 ปิดขายทำกำไร ({len(closed_trades)})</button>
            <button id="btn-sub-divs" class="sub-tab-btn" onclick="switchSubTab('divs')">💵 เงินปันผล ({len(dividends_list)})</button>
            <button id="btn-sub-cash" class="sub-tab-btn" onclick="switchSubTab('cash')">🏦 เติมเงิน & เดินบัญชี ({len(cash_movements)})</button>
        </div>

        <!-- SECTION 1: COMPLETE BUY ORDERS HISTORY -->
        <div id="section-buys" class="sub-section" style="margin-bottom: 36px;">
            <div class="section-title">
                <span>🛒</span> 1. ประวัติคำสั่งซื้อหุ้นทั้งหมดอย่างละเอียด (Complete Buy Orders History: {len(buy_orders)} ไม้)
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

        <!-- SECTION 2: CLOSED TRADES TABLE -->
        <div id="section-sells" class="sub-section" style="margin-bottom: 36px;">
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span>🏆</span> 2. รายการหุ้นที่ขายทำกำไรปิดรอบสำเร็จ (Closed Trades: {len(closed_trades)} ไม้)
                    <span class="badge badge-success">Win Rate {trades_summary.get('win_rate_pct', 0):.1f}% (กำไรสะสม {money(trades_summary.get('total_realized_pl_thb', 0), 'THB', signed=True)})</span>
                </div>
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

        <!-- SECTION 3: DIVIDEND STREAM -->
        <div id="section-divs" class="sub-section" style="margin-bottom: 36px;">
            <div class="section-title">
                <span>💵</span> 3. ประวัติเงินปันผลรับสะสม (Dividends Received: {len(dividends_list)} ครั้ง)
                <span class="badge badge-success">รวม {money(data.get('total_dividends_usd', 0), signed=True)} (~{money(data.get('total_dividends_thb', 0), 'THB')})</span>
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

        <!-- SECTION 4: CAPITAL & CASH MOVEMENTS STATEMENT -->
        <div id="section-cash" class="sub-section" style="margin-bottom: 36px;">
            <div class="section-title">
                <span>🏦</span> 4. ข้อมูลการเติมเงินและการเคลื่อนไหวเงินสดในบัญชี (Complete Cash Flow & Deposit Ledger: {len(cash_movements)} รายการ)
                <span class="badge badge-info">KKP Official Statement & สลิป Dime! Save ตั้งแต่วันเปิดบัญชี 2 ก.พ. 69</span>
            </div>
            <!-- STATEMENT OVERVIEW CARDS -->
            <div class="card" style="margin-bottom: 20px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; font-size: 0.95rem;">
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดโอนเข้าจากต่างธนาคารรวม (PromptPay):</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #fff;">{money(gross_deposits, 'THB')}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(19 รายการ: Statement 18 ครั้ง + 14 ต.ค. 1 ครั้ง)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดโอนเงินกลับออกไปต่างธนาคาร:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--rose);">{money(-abs(transfer_out), 'THB')}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(เมื่อวันที่ 03/02/2026 ผ่านช่องทาง DIME)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">ยอดเงินต้นสุทธิที่คงอยู่ใน Dime!:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #60a5fa;">{money(data.get('net_injected_capital_thb', 0), 'THB')}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">(ใช้เป็นฐานคำนวณผลตอบแทนรวมจริง 100%)</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); margin-bottom: 4px;">เงินสดคงเหลือในบัญชี Dime! Save:</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--emerald);">{money(dime_save_cash, 'THB')}</div>
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

    function switchSubTab(subName) {{
        document.querySelectorAll('.sub-tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
        var btn = document.getElementById('btn-sub-' + subName);
        if (btn) btn.classList.add('active');
        var sections = ['buys', 'sells', 'divs', 'cash'];
        sections.forEach(function(s) {{
            var el = document.getElementById('section-' + s);
            if (el) {{
                el.style.display = (subName === 'all' || subName === s) ? 'block' : 'none';
            }}
        }});
        if (window.history && window.history.replaceState) {{
            window.history.replaceState(null, null, '#' + subName);
        }}
    }}

    window.addEventListener('DOMContentLoaded', function() {{
        var hash = (window.location.hash || '').replace('#', '');
        if (['buys', 'sells', 'divs', 'cash', 'all'].indexOf(hash) !== -1) {{
            switchSubTab(hash);
        }}
    }});
    </script>
    {get_chart_modal_component()}
    {get_slip_modal_component()}
</body>
</html>
"""
    return html


def main():
    print("Generating Unified Master Dashboard & Complete Ledger...", file=sys.stderr)
    data = generate_master_dashboard_data()

    # Save to reports/portfolio_master.html
    out_path = Path("reports/portfolio_master.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_master_dashboard_html(data)
    out_path.write_text(html_content, encoding="utf-8")

    # Save to reports/trades_ledger.html (Complete Trading & Cash Ledger)
    trades_path = Path("reports/trades_ledger.html")
    trades_path.parent.mkdir(parents=True, exist_ok=True)
    trades_content = generate_master_ledger_html(data)
    trades_path.write_text(trades_content, encoding="utf-8")

    # Save JSON summary
    json_path = Path("data/account_summary.json")
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print_master_summary(data, out_path, json_path)


def print_master_summary(data, html_path, json_path):
    ts = data['trades_summary']
    print("==========================================================================")
    print("         MASTER WEALTH & PORTFOLIO SUMMARY (DIME! & KKP)")
    print("==========================================================================")
    print(f"Portfolio Name       : {data['portfolio_name']}")
    print(f"Total Net Worth (NAV): {money(data['total_net_worth_thb'], 'THB')} (~{money(data['total_net_worth_usd'])} USD)")
    print(f"Net Injected Capital : {money(data['net_injected_capital_thb'], 'THB')} (from KKP Statement)")
    print(f"All-Time Net Profit  : {money(data['all_time_profit_thb'], 'THB', signed=True)} ({pct(data['all_time_roi_pct'], digits=2)} All-Time ROI)")
    print(f"Total Idle Cash      : {money(data['total_cash_thb'], 'THB')} (Dime! Save: {money(data['dime_save_cash_thb'], 'THB')} | Dime! USD: {money(data['dime_usd_cash'])})")
    print(f"Active Stock Holdings: {len(data['positions'])} stocks | Market Val: {money(data['stock_market_val_usd'])} ({money(data['stock_market_val_thb'], 'THB')})")
    print(f"Realized Trades P&L  : {money(ts['total_realized_pl_usd'], signed=True)} ({money(ts['total_realized_pl_thb'], 'THB', signed=True)}) | Win Rate {ts['win_rate_pct']:.1f}%")
    print(f"Total Dividends Recv : {money(data['total_dividends_usd'], signed=True)} ({money(data['total_dividends_thb'], 'THB', signed=True)}) | {len(data['dividends_list'])} payments")
    print("==========================================================================")
    print(f"Master HTML Dashboard: {html_path.resolve()}")
    print(f"Account JSON File    : {json_path.resolve()}")


if __name__ == "__main__":
    main()
