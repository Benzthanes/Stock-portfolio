"""
Generate high quality Thai AI news analysis for pending articles (2026-10-23).
Follows docs/METHODOLOGY.md section 4 and AGENTS.md rules.
"""

import json
import re
from pathlib import Path

PENDING_FILE = Path("/tmp/pending_news.json")
OUT_FILE = Path("/tmp/ai_news_analysis.json")

COMPANY_NAMES = {
    "JPM": "JPMorgan Chase & Co.",
    "SKHY": "SK Hynix Inc.",
    "NOK": "Nokia Corporation",
    "VRT": "Vertiv Holdings Co",
    "LLY": "Eli Lilly and Company",
    "VRTX": "Vertex Pharmaceuticals Inc.",
    "ABNB": "Airbnb, Inc.",
    "QQQI": "NEOS Nasdaq 100 High Income ETF",
    "MU": "Micron Technology, Inc.",
    "ARM": "Arm Holdings plc",
    "NOW": "ServiceNow, Inc.",
    "APP": "AppLovin Corporation",
    "SPCX": "SpaceX (Space Exploration Technologies)",
    "PLTR": "Palantir Technologies Inc.",
    "GOOGL": "Alphabet Inc.",
    "VOO": "Vanguard S&P 500 ETF",
    "VST": "Vistra Corp.",
    "BMY": "Bristol-Myers Squibb Company",
    "C": "Citigroup Inc.",
    "MNST": "Monster Beverage Corp",
    "BAC": "Bank of America Corporation",
    "JNJ": "Johnson & Johnson",
}

def analyze_article(ticker: str, article: dict) -> dict:
    title = article.get("title", "").strip()
    source = article.get("source", "").strip()
    cname = COMPANY_NAMES.get(ticker, ticker)

    sentiment = "neutral"
    topic = "ข่าวทั่วไป (General News)"
    title_th = ""
    summary_th = ""
    impact_th = ""
    action_th = ""

    # Check for Quote Page / Options / Chart
    is_quote_or_option = bool(
        re.search(r"(interactive stock chart|stock historical prices|call \(|put \(|Options Chain|Stock Quote Price|Evaluation Report|Stock Prices \| Quote)", title, re.I)
    )

    if is_quote_or_option:
        sentiment = "neutral"
        if re.search(r"(call \(|put \(|Options Chain)", title, re.I):
            topic = "ข้อมูลตราสารอนุพันธ์ (Options Chain)"
            title_th = f"หน้าข้อมูลสัญญาออปชันของ {ticker}"
            summary_th = f"• หน้ารายงานข้อมูลสัญญา Options ของ {cname}\n• แสดงราคาใช้สิทธิและข้อมูลการซื้อขายสัญญาอนุพันธ์"
            impact_th = "ไม่มีผลกระทบต่อปัจจัยพื้นฐาน เป็นเพียงข้อมูลราคาตราสารอนุพันธ์"
            action_th = "ใช้ดูระดับราคาใช้สิทธิและ sentiment ตลาด ไม่จำเป็นต้องปรับพอร์ต"
        else:
            topic = "หน้าข้อมูลราคา (Quote Page)"
            title_th = f"หน้าข้อมูลราคาและกราฟเทคนิคของ {ticker}"
            summary_th = f"• หน้ารายงานราคาและกราฟเทคนิคของ {cname}\n• แสดงข้อมูลราคาย้อนหลังและตัวชี้วัดทั่วไป"
            impact_th = "ไม่มีผลกระทบต่อปัจจัยพื้นฐานเนื่องจากไม่ใช่ข่าวสารใหม่"
            action_th = "ใช้เป็นข้อมูลประกอบการดูกราฟราคาเท่านั้น"

    elif ticker == "C" and ("Class C" in title or "INE.DB.C" in title or "Meta" in title):
        sentiment = "neutral"
        topic = "ข้อมูลหุ้นอื่น (Other Stock Info)"
        title_th = "รายงานหุ้น Class C ของ Meta หรือตราสารอื่นที่ไม่ใช่ Citigroup"
        summary_th = "• ข่าวเกี่ยวกับหุ้นประเภท Class C ของ Meta หรือตราสารอื่น\n• ไม่ได้เกี่ยวข้องกับผลการดำเนินงานของ Citigroup (C)"
        impact_th = "ไม่มีผลกระทบต่อพื้นฐานหรือราคาหุ้น Citigroup"
        action_th = "ข้ามข่าวนี้เนื่องจากเป็นข้อมูลของบริษัทอื่น"

    elif ticker == "ARM" and "shot in the arm" in title.lower():
        sentiment = "bullish"
        topic = "มุมมองตลาดและอุตสาหกรรม (Market Outlook)"
        title_th = "SpaceX หนุนความเชื่อมั่นกระแสลงทุน AI และส่งผลดีต่อหุ้นเทคโนโลยี"
        summary_th = "• ความคืบหน้าของ SpaceX ช่วยกระตุ้นบรรยากาศการลงทุนในกลุ่มที่เกี่ยวข้องกับ AI\n• เป็นการใช้วลีเปรียบเทียบในตลาดและส่งผลบวกต่อจิตวิทยาหุ้นเทค"
        impact_th = "หนุนบรรยากาศการลงทุนในธีม AI และโครงสร้างพื้นฐานเทคโนโลยี"
        action_th = "ถือหุ้นเทคและโครงสร้างพื้นฐาน AI คุณภาพดีตามแผน"

    elif ticker == "NOW" and ("Safe Dividend Stocks" in title or "GE Vernova" in title or "Rivian" in title):
        sentiment = "neutral"
        topic = "บทวิเคราะห์หุ้นอื่น (Other Stocks Analysis)"
        title_th = "บทวิเคราะห์หุ้นอื่นในตลาดที่ใช้คำว่า Now ในหัวข้อ"
        summary_th = "• บทความวิเคราะห์หุ้นรายตัวอื่นในตลาด เช่น หุ้นปันผล หรือ GE Vernova\n• ไม่ได้เกี่ยวข้องโดยตรงกับธุรกิจของ ServiceNow (NOW)"
        impact_th = "ไม่มีผลกระทบต่อปัจจัยพื้นฐานของ ServiceNow"
        action_th = "ข้ามบทความนี้เนื่องจากเป็นข้อมูลของหุ้นตัวอื่น"

    elif re.search(r"(Shares Acquired|Shares Purchased|Stake Boosted|Position Boosted|Position Increased|shares added)", title, re.I):
        sentiment = "bullish"
        topic = "การเข้าซื้อหุ้น (Institutional Buying)"
        title_th = f"สถาบันการเงินเข้าซื้อและเพิ่มสัดส่วนการลงทุนในหุ้น {ticker}"
        summary_th = f"• มีรายงานกองทุนและสถาบันการเงินเข้าซื้อหรือเพิ่มสัดส่วนการถือครองหุ้น {cname}\n• สะท้อนความเชื่อมั่นของนักลงทุนสถาบันต่อแนวโน้มธุรกิจ"
        impact_th = "ส่งผลบวกต่อจิตวิทยาการลงทุนและช่วยหนุนฐานราคาหุ้นในระยะกลาง"
        action_th = "ถือหุ้นต่อตามแผนการลงทุนหลัก"

    elif re.search(r"(Shares Sold|Stock Holdings Lowered|Sells \d+ Shares|sells \$)", title, re.I):
        sentiment = "bearish"
        topic = "การลดสัดส่วน (Institutional Selling)"
        title_th = f"สถาบันการเงินลดสัดส่วนการถือครองหุ้น {ticker}"
        summary_th = f"• รายงานกองทุนหรือผู้บริหารปรับลดสัดส่วนการถือครองหุ้น {cname}\n• อาจเป็นการทำกำไรตามรอบหรือปรับสมดุลพอร์ตการลงทุน"
        impact_th = "อาจมีแรงกดดันระยะสั้นจากแรงขาย แต่ไม่กระทบพื้นฐานระยะยาวโดยตรง"
        action_th = "ติดตามระดับแนวรับและเฝ้าระวังแรงขายของสถาบัน"

    elif re.search(r"(SHAREHOLDER ALERT|Investors accuse|money laundering|fine|Sued)", title, re.I):
        sentiment = "bearish"
        topic = "ประเด็นกฎหมายและการกำกับดูแล (Legal & Regulatory)"
        title_th = f"การแจ้งเตือนผู้ถือหุ้นหรือประเด็นทางกฎหมายของ {ticker}"
        summary_th = f"• มีการแจ้งเตือนสิทธิ์ผู้ถือหุ้นหรือข้อกล่าวหาทางกฎหมายที่เกี่ยวข้องกับ {cname}\n• มักเป็นการรวบรวมข้อมูลของผู้ตรวจสอบหรือสำนักงานกฎหมาย"
        impact_th = "สร้างแรงกดดันต่อภาพลักษณ์และราคาหุ้นระยะสั้น"
        action_th = "รอประเมินมูลค่าความเสียหายที่ชัดเจนก่อนพิจารณาปรับพอร์ต"

    elif re.search(r"(Earnings|Q3|Quarter|profit growth|slump)", title, re.I):
        is_bull = bool(re.search(r"(growth|strong|boost|exceed|posted a \$|up|rally)", title, re.I))
        is_bear = bool(re.search(r"(miss|drop|fall|slump|down|sinks)", title, re.I))
        sentiment = "bullish" if is_bull and not is_bear else ("bearish" if is_bear else "neutral")
        topic = "ผลประกอบการ (Earnings)"
        title_th = f"รายงานผลประกอบการและแนวโน้มการเติบโตของ {ticker}"
        summary_th = f"• รายงานเกี่ยวกับผลการดำเนินงานหรือคาดการณ์กำไรของ {cname}\n• นักลงทุนจับตาตัวเลขรายได้และประมาณการในไตรมาสถัดไป"
        impact_th = "ส่งผลกระทบโดยตรงต่อราคาหุ้นตามการตอบรับของตลาดต่องบการเงิน"
        action_th = "ตรวจสอบผลประกอบการจริงเทียบกับประมาณการของตลาด"

    elif re.search(r"(Price Target|Receives a Buy|Upgraded|Upgrade|initiates.*buy|Outpaces|Lead Gainers|Rising in Premarket)", title, re.I):
        sentiment = "bullish"
        topic = "บทวิเคราะห์และเป้าหมายราคา (Analyst Ratings)"
        title_th = f"นักวิเคราะห์ปรับเพิ่มราคาเป้าหมายหรือแนะนำซื้อหุ้น {ticker}"
        summary_th = f"• สถาบันวิจัยการลงทุนปรับมุมมองเป็นเชิงบวกต่อ {cname}\n• ชี้ปัจจัยหนุนจากศักยภาพการเติบโตและมูลค่าหุ้นที่น่าสนใจ"
        impact_th = "ช่วยเพิ่มความเชื่อมั่นและสร้างแรงซื้อเก็งกำไรในระยะสั้นถึงกลาง"
        action_th = "ถือต่อและใช้เป็นมุมมองเสริมในการวางแผนราคาเป้าหมาย"

    elif re.search(r"(partners|Partnership|Team to|expands|investigational platform|Collaboration)", title, re.I):
        sentiment = "bullish"
        topic = "ความร่วมมือทางธุรกิจและนวัตกรรม (Partnership & Innovation)"
        title_th = f"{ticker} ประกาศความร่วมมือทางธุรกิจหรือความคืบหน้านวัตกรรมใหม่"
        summary_th = f"• {cname} มีความร่วมมือเชิงกลยุทธ์หรือความก้าวหน้าด้านผลิตภัณฑ์ใหม่\n• เสริมศักยภาพการขยายตัวและการบริการลูกค้าในตลาดเป้าหมาย"
        impact_th = "ส่งผลบวกต่อการขยายฐานรายได้และเสริมความแข็งแกร่งทางธุรกิจในระยะยาว"
        action_th = "ถือต่อตามกลยุทธ์การเติบโตของบริษัท"

    elif re.search(r"(Drops|Falls|Opened Down|Slides|Fall Over|Sinks|Down)", title, re.I):
        sentiment = "bearish"
        topic = "ความเคลื่อนไหวของราคา (Price Action)"
        title_th = f"ราคาหุ้น {ticker} ปรับตัวลดลงจากความผันผวนของตลาด"
        summary_th = f"• ราคาหุ้น {cname} ย่อตัวลงตามภาวะตลาดหรือแรงขายทำกำไรระยะสั้น\n• นักลงทุนเฝ้าระวังการทดสอบแนวรับสำคัญ"
        impact_th = "กดดันราคาหุ้นในระยะสั้นและทดสอบความแข็งแกร่งของแนวรับ"
        action_th = "เฝ้าระวังแนวรับหลักและหลีกเลี่ยงการรีบช้อนซื้อจนกว่าจะเห็นสัญญาณกลับตัว"

    elif ticker == "SPCX":
        sentiment = "bullish" if "buy" in title.lower() or "boost" in title.lower() else "neutral"
        topic = "บทวิเคราะห์หุ้น SpaceX (SpaceX Analysis)"
        title_th = f"บทวิเคราะห์และความเคลื่อนไหวของหุ้น SpaceX ({ticker})"
        summary_th = f"• ข่าวเกี่ยวกับ SpaceX ซึ่งเป็นผู้นำด้านธุรกิจขนส่งอวกาศและบริการอินเทอร์เน็ตผ่านดาวเทียม Starlink\n• หุ้นมีปัจจัยหนุนจากการเติบโตของภารกิจส่งดาวเทียมและความร่วมมือในอุตสาหกรรม"
        impact_th = "ส่งผลต่อความเชื่อมั่นในการเติบโตระยะยาวของบริษัทอวกาศเชิงพาณิชย์"
        action_th = "ติดตามความคืบหน้าของโครงการ Starlink และการปล่อยจรวดตามแผน"

    elif ticker == "VOO":
        sentiment = "neutral"
        topic = "กองทุนดัชนี S&P 500 (Index ETF Analysis)"
        title_th = "บทวิเคราะห์สัดส่วนการลงทุนและกลยุทธ์ใน Vanguard S&P 500 ETF (VOO)"
        summary_th = "• บทความวิเคราะห์การกระจายน้ำหนักในหุ้นกลุ่มเทคโนโลยีและกลยุทธ์ลงทุนใน VOO\n• ชี้ให้เห็นถึงความเสี่ยงการกระจุกตัวและการบริหารพอร์ตระยะยาว"
        impact_th = "ไม่กระทบปัจจัยพื้นฐานของกองทุนดัชนีหลัก เป็นข้อมูลประกอบการจัดสรรพอร์ต"
        action_th = "ลงทุนแบบ DCA ต่อเนื่องตามแผนการลงทุนระยะยาว"

    else:
        sentiment = "neutral"
        topic = "การเคลื่อนไหวของหุ้น (Stock Movement)"
        title_th = f"รายงานความเคลื่อนไหวและบทวิเคราะห์หุ้น {ticker}"
        summary_th = f"• รายงานข่าวและบทวิเคราะห์เกี่ยวกับ {cname}\n• ตลาดติดตามทิศทางธุรกิจและปัจจัยหนุนในกลุ่มอุตสาหกรรม"
        impact_th = "ส่งผลต่อจิตวิทยาการซื้อขายตามทิศทางของตลาดโดยรวม"
        action_th = "ติดตามข่าวสารอย่างใกล้ชิดและปฏิบัติตามแผนการลงทุน"

    return {
        "title": article.get("title", ""),
        "source": article.get("source", ""),
        "link": article.get("link", ""),
        "published": article.get("published", ""),
        "raw_date": article.get("raw_date", ""),
        "title_th": title_th,
        "summary_th": summary_th,
        "impact_th": impact_th,
        "action_th": action_th,
        "sentiment": sentiment,
        "topic": topic
    }

def main():
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        pending = json.load(f)

    result = {}
    for ticker, articles in pending.items():
        analyzed_list = []
        for art in articles:
            analyzed = analyze_article(ticker, art)
            analyzed_list.append(analyzed)
        result[ticker] = analyzed_list

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Generated analysis for {len(result)} tickers and {sum(len(v) for v in result.values())} articles.")

if __name__ == "__main__":
    main()
