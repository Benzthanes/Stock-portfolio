import json
import re
from pathlib import Path

with open("data/.ocr_extracted.json", "r", encoding="utf-8") as f:
    ocr_data = json.load(f)

orders = []
dividends = []
transfers = []
others = []

def parse_num(val_str):
    if not val_str:
        return 0.0
    s = re.sub(r"[^\d\.\-]", "", val_str)
    try:
        return float(s)
    except:
        return 0.0

for item in ocr_data:
    fn = item["filename"]
    lines = item["lines"]
    text = "\n".join(lines)
    full_line_str = " ".join(lines)

    # 1. Check if BUY / SELL order
    order_m = re.search(r"(ซื้อ|ขาย)\s+([A-Z0-9]+)", full_line_str)
    if order_m and "รายละเอียดคำสั่ง" in full_line_str:
        action = "BUY" if order_m.group(1) == "ซื้อ" else "SELL"
        ticker = order_m.group(2)

        # Extract shares
        shares = 0.0
        shares_m = re.search(r"([\d\.\,]+)\s*หุ้น", text)
        if shares_m:
            shares = parse_num(shares_m.group(1))

        # Extract actual price (ราคาที่ได้จริง)
        exec_price = 0.0
        # Usually followed by dots or direct USD
        price_m = re.search(r"ราคาที่ได้จริง\s*[\.\s]*\n*([\d\.\,]+)\s*USD", text)
        if not price_m:
            price_m = re.search(r"ราคาที่คุณตั้ง\s*([\d\.\,]+)\s*USD", text)
        if price_m:
            exec_price = parse_num(price_m.group(1))

        # Gross value (มูลค่าหุ้น)
        gross_val = 0.0
        gross_m = re.search(r"([\d\.\,]+)\s*USD\s*\n*มูลค่าหุ้น", text)
        if not gross_m:
            gross_m = re.search(r"มูลค่าหุ้น\s*\n*([\d\.\,]+)\s*USD", text)
        if gross_m:
            gross_val = parse_num(gross_m.group(1))

        # Net amount:
        # If BUY: look for initial amount or total charged
        # If SELL: "ยอดที่จะได้รับคืน"
        net_val = 0.0
        net_m = re.search(r"ยอดที่จะได้รับคืน\s*\n*([\d\.\,]+)\s*USD", text)
        if not net_m:
            net_m = re.search(r"([\d\.\,]+)\s*USD\s*\n*ใช้ราคาตลาด", text)
        if not net_m:
            net_m = re.search(r"([\d\.\,]+)\s*USD\s*\n*ราคาที่คุณตั้ง", text)
        if not net_m:
            net_m = re.search(r"([\d\.\,]+)\s*THB\s*\n*ราคาที่คุณตั้ง", text)
        if net_m:
            net_val = parse_num(net_m.group(1))

        # Date: วันที่คำสั่งสำเร็จ or วันที่ส่งคำสั่ง
        date_str = ""
        date_m = re.search(r"วันที่คำสั่งสำเร็จ\s*\n*([^\n]+)", text)
        if not date_m:
            date_m = re.search(r"วันที่ส่งคำสั่ง\s*\n*([^\n]+)", text)
        if date_m:
            date_str = date_m.group(1).strip()

        orders.append({
            "filename": fn,
            "action": action,
            "ticker": ticker,
            "shares": shares,
            "price_usd": exec_price,
            "gross_usd": gross_val,
            "net_val": net_val,
            "date": date_str,
            "raw_text": text
        })
        continue

    # 2. Check if Dividend screen
    if "ปันผล" in full_line_str or "Corporate Action" in full_line_str:
        # Extract dividend rows
        # Format in text:
        # ปันผล QQQI \n รับเงินเข้า \n Dime! USD \n 0.6297/หุ้น ปิดสมุด: 22 เม.ย. 69 \n 3.68 USD \n 25 เม.ย. 69 - 02:57:57 น.
        div_pattern = re.findall(
            r"ปั[น่]ผล\s+([A-Z0-9]+).*?([\d\.\,]+)\s*USD\s*\n*(\d{1,2}\s+[^\n\-]+\s*-\s*[\d\:]+\s*น)",
            text, re.DOTALL
        )
        for d in div_pattern:
            dividends.append({
                "filename": fn,
                "ticker": d[0],
                "amount_usd": parse_num(d[1]),
                "date": d[2].strip()
            })
        continue

    # 3. Check if Transfer screen (Dime! Save)
    if "รายการบัญชี Dime! Save" in full_line_str:
        # Pattern: (โอนเงิน/ชำระเงิน|รับเงินโอน|ดอกเบี้ย) \n ([+\-]?[\d\.\,]+)\s*THB \n (\d{1,2}\s+[^\n\-]+\s*-\s*[\d\:]+\s*น)
        trans_pattern = re.findall(
            r"(โอนเงิน\s*/?\s*ชำระเงิน|รับเงินโอน|ดอกเบี้ย)\s*\n*([+\-]?[\d\.\,]+)\s*THB\s*\n*(\d{1,2}\s+[^\n\-]+\s*-\s*[\d\:]+\s*น)",
            text
        )
        for t in trans_pattern:
            transfers.append({
                "filename": fn,
                "type": t[0].strip(),
                "amount_thb": parse_num(t[1]),
                "date": t[2].strip()
            })
        continue

    others.append(fn)

print(f"Parsed orders: {len(orders)}")
print(f"Parsed dividends: {len(dividends)}")
print(f"Parsed transfers: {len(transfers)}")
print(f"Others: {len(others)}")
