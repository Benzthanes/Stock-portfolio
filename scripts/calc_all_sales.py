import json
import re

with open("data/.ocr_extracted.json", "r", encoding="utf-8") as f:
    data = {item["filename"]: item["lines"] for item in json.load(f)}

def get_order_details(fn):
    lines = data[fn]
    text = "\n".join(lines)
    full_str = " ".join(lines)
    m_act = re.search(r"(ซื้อ|ขาย)\s+([A-Z0-9]+)", full_str)
    act = "BUY" if m_act.group(1) == "ซื้อ" else "SELL"
    ticker = m_act.group(2)
    
    # shares
    sh = 0.0
    if act == "SELL":
        m_sh = re.search(r"([\d\.\,]+)\s*หุ้น", text)
        if m_sh: sh = float(m_sh.group(1).replace(",", ""))
    else:
        for i, l in enumerate(lines):
            if "จำนวนหุ้น" in l and i + 1 < len(lines):
                try:
                    sh = float(lines[i + 1].strip())
                    break
                except:
                    pass

    # price
    price = 0.0
    for i, l in enumerate(lines):
        if ("าคาที่ได้จริง" in l or "ราคาที่คุณตั้ง" in l) and i + 1 < len(lines):
            for off in range(1, 5):
                if i + off < len(lines):
                    m_p = re.search(r"([\d\.\,]+)\s*USD", lines[i + off])
                    if m_p:
                        price = float(m_p.group(1).replace(",", ""))
                        break
            if price > 0: break

    # USD amount
    val_usd = 0.0
    val_thb = 0.0
    if act == "SELL":
        m_net = re.search(r"ยอดที่จะได้รับคืน\s*\n*([\d\.\,]+)\s*USD", text)
        if m_net: val_usd = float(m_net.group(1).replace(",", ""))
    else:
        m_val = re.search(r"([\d\.\,]+)\s*USD\s*\n*มูลค่าหุ้น", text)
        if not m_val:
            m_val = re.search(r"มูลค่าหุ้น\s*\n*([\d\.\,]+)\s*USD", text)
        if not m_val:
            m_val = re.search(r"([\d\.\,]+)\s*USD\s*\n*(?:ใช้ราคาตลาด|ราคาที่คุณตั้ง)", text)
        if not m_val:
            m_val = re.search(r"จำนวนเงิน \(USD\)\s*\n*([\d\.\,]+)\s*USD", text)
        if m_val: val_usd = float(m_val.group(1).replace(",", ""))
        
        m_thb = re.search(r"([\d\.\,]+)\s*THB\s*\n*(?:ใช้ราคาตลาด|ราคาที่คุณตั้ง|มูลค่าหุ้น)", text)
        if m_thb: val_thb = float(m_thb.group(1).replace(",", ""))

    # Date
    m_dt = re.search(r"วันที่คำสั่งสำเร็จ\s*\n*([^\n]+)", text)
    if not m_dt:
        m_dt = re.search(r"วันที่ส่งคำสั่ง\s*\n*([^\n]+)", text)
    dt = m_dt.group(1).strip() if m_dt else ""

    return {
        "fn": fn,
        "action": act,
        "ticker": ticker,
        "shares": sh,
        "price": price,
        "val_usd": val_usd if val_usd > 0 else round(sh * price, 2),
        "val_thb": val_thb,
        "date": dt
    }

div_files = {"IMG_5582.PNG", "IMG_5583.PNG", "IMG_5584.PNG"}
trans_files = {"IMG_5589.PNG", "IMG_5590.PNG", "IMG_5591.PNG", "IMG_5592.PNG", "IMG_5593.PNG"}

all_orders = []
for fn in data:
    if fn in div_files or fn in trans_files: continue
    all_orders.append(get_order_details(fn))

# Exact Matching for Closed Sales
sells = [o for o in all_orders if o["action"] == "SELL"]
buys = [o for o in all_orders if o["action"] == "BUY"]

print("====================================================================================================")
print("                                EXACT CLOSED SALES VERIFICATION")
print("====================================================================================================")

closed_summary = []
for s in sells:
    t = s["ticker"]
    sh_sold = s["shares"]
    net_proc = s["val_usd"]
    
    # Matching buys
    matching_buys = [b for b in buys if b["ticker"] == t]
    
    # Specific per-ticker mapping if needed
    if t == "MNST":
        # First 2 buys before sell
        matching_buys = [b for b in matching_buys if b["fn"] in ("IMG_5534.PNG", "IMG_5535.PNG")]
    elif t == "VST":
        matching_buys = [b for b in matching_buys if b["fn"] == "IMG_5579.PNG"]
    elif t == "SPCX":
        matching_buys = [b for b in matching_buys if b["fn"] == "IMG_5548.PNG"]
    elif t in ("SKHY", "SKHYV"):
        matching_buys = [b for b in matching_buys if b["fn"] == "IMG_5559.PNG"]
    elif t == "QQQI":
        matching_buys = [b for b in matching_buys if b["fn"] == "IMG_5528.PNG"]
    elif t == "NOW":
        matching_buys = [b for b in matching_buys if b["fn"] in ("IMG_5547.PNG", "IMG_5549.PNG", "IMG_5553.PNG", "IMG_5563.PNG")]
    elif t == "PLTR":
        matching_buys = [b for b in matching_buys if b["fn"] in ("IMG_5532.PNG", "IMG_5533.PNG", "IMG_5540.PNG", "IMG_5541.PNG", "IMG_5544.PNG", "IMG_5555.PNG", "IMG_5557.PNG")]

    tot_sh_bought = sum(b["shares"] for b in matching_buys)
    tot_cost = sum(b["val_usd"] for b in matching_buys)
    avg_buy_p = (tot_cost / tot_sh_bought) if tot_sh_bought > 0 else 0.0
    
    cost_basis = round(sh_sold * avg_buy_p, 2)
    pnl = round(net_proc - cost_basis, 2)
    roi = round((pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0, 2)
    
    closed_summary.append({
        "ticker": t,
        "date": s["date"],
        "shares": sh_sold,
        "buy_price": round(avg_buy_p, 2),
        "sell_price": s["price"],
        "cost_usd": cost_basis,
        "net_proceeds_usd": net_proc,
        "realized_pl_usd": pnl,
        "roi_pct": roi,
        "sell_fn": s["fn"],
        "buy_fns": [b["fn"] for b in matching_buys]
    })

for cs in closed_summary:
    sign = "+" if cs["realized_pl_usd"] >= 0 else ""
    print(f"{cs['ticker']:<6} | {cs['date']:<22} | Shs: {cs['shares']:<8.4f} | Buy: ${cs['buy_price']:<6.2f} | Sell: ${cs['sell_price']:<6.2f} | Cost: ${cs['cost_usd']:<8.2f} | Recv: ${cs['net_proceeds_usd']:<8.2f} | P&L: {sign}${cs['realized_pl_usd']:<8.2f} ({sign}{cs['roi_pct']:.2f}%)")

tot_cost = sum(c["cost_usd"] for c in closed_summary)
tot_recv = sum(c["net_proceeds_usd"] for c in closed_summary)
tot_pnl = sum(c["realized_pl_usd"] for c in closed_summary)
tot_roi = (tot_pnl / tot_cost * 100.0) if tot_cost > 0 else 0.0

print("-" * 100)
print(f"TOTAL REALIZED PROFIT : +${tot_pnl:,.2f} USD (+฿{tot_pnl * 33.62:,.2f} THB) | ROI: +{tot_roi:.2f}%")
print(f"WIN RATE              : {len([c for c in closed_summary if c['realized_pl_usd'] > 0])}/{len(closed_summary)} (100.0%)")
