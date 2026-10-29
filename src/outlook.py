# -*- coding: utf-8 -*-
"""
Institutional Forward Outlook Intelligence & Growth Catalysts Engine.
Provides secular growth theses, forward drivers, catalyst timelines,
Wall Street consensus analysis, and risk guards for US stocks.
"""

from html import escape
from typing import Dict, Any, Optional, List

from src.fmt import money, pct, num
from src.scoring import EARNINGS_GUARD_DAYS

CURATED_AS_OF = "2026-10-17"


def _rec_count(data: Dict[str, Any], key: str) -> Optional[int]:
    v = data.get(f"rec_{key}", data.get(f"recommendation_{key}"))
    return int(v) if v is not None else None


def broker_consensus(data: Dict[str, Any]) -> str:
    """Live analyst vote phrase, or "" when TradingView has no recommendation counts."""
    b, h, s = (_rec_count(data, k) for k in ("buy", "hold", "sell"))
    if b is None and h is None and s is None:
        return ""
    b, h, s = b or 0, h or 0, s or 0
    return f"โบรกเกอร์ {b + h + s} แห่ง (Buy {b} / Hold {h} / Sell {s}) "


def get_forward_outlook(
    ticker: str,
    data: Optional[Dict[str, Any]] = None,
    fundamentals: Optional[Dict[str, Any]] = None,
    days_to_earnings: Optional[float] = None,
    avg_cost: Optional[float] = None,
    close: Optional[float] = None,
    currency: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build in-depth forward-looking fundamental thesis, secular tailwinds,
    catalyst timeline, Wall Street valuation, and strategic roadmap.
    """
    t = ticker.upper()
    data = data or {}
    fundamentals = fundamentals or {}
    
    close_price = close or data.get("close") or data.get("close_price") or 0.0
    cost_price = avg_cost or 0.0
    
    t_avg = data.get("price_target_average") or 0.0
    t_low = data.get("price_target_low") or 0.0
    t_high = data.get("price_target_high") or 0.0
    upside_avg = round(((t_avg - close_price) / close_price * 100), 1) if (t_avg and close_price > 0) else None
    upside_cost = round(((t_avg - cost_price) / cost_price * 100), 1) if (t_avg and cost_price > 0) else None
    ccy = (currency or data.get("currency") or ("THB" if data.get("exchange") == "SET" else "USD")).upper()

    def m(v: Optional[float]) -> str:
        return money(v, ccy) if v else "-"

    up_s = pct(upside_avg)
    consensus = broker_consensus(data)
    if t_low and cost_price > 0:
        gap = t_low - cost_price
        low_vs_cost = f" ซึ่ง{'สูง' if gap >= 0 else 'ต่ำ'}กว่าต้นทุนของคุณ ({m(cost_price)}) อยู่ {money(abs(gap), ccy)}"
    else:
        low_vs_cost = ""

    rsi = data.get("RSI")
    sma20 = data.get("SMA20")
    sma200 = data.get("SMA200")
    net_g_live = fundamentals.get("net_inc_growth_yoy")
    rev_g_live = fundamentals.get("rev_growth_yoy")
    net_g_str = pct(net_g_live)
    rev_g_str = pct(rev_g_live)
    has_earnings_date = days_to_earnings is not None and days_to_earnings >= 0
    days_int = int(round(days_to_earnings)) if has_earnings_date else 0
    if has_earnings_date and days_to_earnings <= EARNINGS_GUARD_DAYS:
        earnings_period = "งบออกวันนี้" if days_int == 0 else f"ระยะประชิด ({days_int} วัน)"
    elif has_earnings_date:
        earnings_period = f"รอบประกาศงบถัดไป ({days_int} วัน)"
    else:
        earnings_period = "รอบประกาศงบถัดไป"
    if has_earnings_date and days_to_earnings <= EARNINGS_GUARD_DAYS:
        if days_int == 0:
            earnings_note = "มีกำหนดงบออกวันนี้ จึง 'ห้ามถัวเด็ดขาดก่อนงบออก' เพราะอาจเกิด Gap งบ. "
        else:
            earnings_note = f"มีวันงบออกในอีก {days_int} วัน จึง 'ห้ามถัวเด็ดขาดก่อนงบออก' เพราะอาจเกิด Gap งบ. "
    elif has_earnings_date:
        earnings_note = f"วันงบถัดไปอยู่ห่างอีก {days_int} วัน ไม่มีความเสี่ยงเรื่องงบตกใจในระยะสั้น. "
    else:
        earnings_note = ""

    curated: Dict[str, Dict[str, Any]] = {
        "NVDA": {
            "thesis_title": "มหาอำนาจผู้ครองระบบนิเวศ AI Computing และสถาปัตยกรรม Blackwell ระดับโลก",
            "quality_badge": "🟢 King of AI Compute (Monopoly Status)",
            "future_growth_drivers": [
                "สถาปัตยกรรม Blackwell (GB200, B200, B100) มียอดจองเต็มล่วงหน้าข้ามปี สะท้อนดีมานด์ AI Training และ Inference ระดับ Hyperscalers",
                "ซอฟต์แวร์ CUDA และแพลตฟอร์ม NVIDIA AI Enterprise สร้างคูเมือง (Economic Moat) แข็งแกร่ง ยากที่คู่แข่งจะลอกเลียนแบบ",
                f"อัตรากำไรขั้นต้น (Gross Margin) แข็งแกร่งระดับ 73-75% พร้อมกระแสเงินสดอิสระ (FCF) มหาศาลกว่า $50B ต่อปี (ข้อมูล ณ {CURATED_AS_OF})",
                "การขยายตัวของ Sovereign AI (ศูนย์ข้อมูลระดับชาติของแต่ละประเทศ) และ Enterprise AI ขับเคลื่อนการเติบโตระลอกใหม่"
            ],
            "drawdown_root_cause": [
                "ความกังวลชั่วคราวต่อข้อจำกัดด้านความร้อนในเคสเซิร์ฟเวอร์ความหนาแน่นสูงก่อนเริ่มส่งมอบจริง",
                "การพักฐานทางเทคนิคหลังราคาหุ้นปรับตัวขึ้นสร้างจุดสูงสุดใหม่ต่อเนื่อง",
                "แรงขายทำกำไรระยะสั้นของกองทุนเพื่อปรับสมดุลสัดส่วนพอร์ต (Portfolio Rebalancing)"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-30 วัน)", "event": "การเริ่มส่งมอบแร็ค GB200 NVL72 เฟสแรกให้กับลูกค้าระดับ Tier-1 Hyperscalers"},
                {"period": "ระยะ 1-3 เดือน", "event": "รายงานผลประกอบการไตรมาสใหม่และ Guidance ปี 2027 ที่สะท้อนยอดขาย Blackwell เต็มไตรมาส"},
                {"period": "ระยะ 6-12 เดือน", "event": "การเปิดตัวสถาปัตยกรรม Rubin เจเนอเรชันถัดไป (ชิป 3nm และหน่วยความจำ HBM4)"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s}) สะท้อนความเชื่อมั่นว่าการปฏิวัติ AI ยังอยู่ในช่วงเริ่มต้น",
            "tailored_roadmap": "ถือครองในฐานะ Core Growth Holding สูงสุดของพอร์ต. ให้รันเทรนด์ตามเส้นค่าเฉลี่ย EMA 20 และ EMA 50 โดยไม่ต้องกังวลความผันผวนระยะสั้น",
            "invalidation_risk": "ความเสี่ยงการคุมเข้มการส่งออกชิปเพิ่มเติมจากรัฐบาลสหรัฐฯ หรือปัญหาคอขวดซัพพลายเชนบรรจุภัณฑ์ CoWoS-L ของ TSMC"
        },
        "TSLA": {
            "thesis_title": "ผู้นำยานยนต์ไฟฟ้าและแพลตฟอร์ม AI ไร้คนขับ (FSD / Robotaxi / Optimus Humanoid)",
            "quality_badge": "🟢 Autonomous AI & Energy Disrupter",
            "future_growth_drivers": [
                "เทคโนโลยี Full Self-Driving (FSD V12+) พัฒนาเป็น End-to-End Neural Network เร่งความพร้อมในการให้บริการ Robotaxi ไร้คนขับเชิงพาณิชย์",
                "ธุรกิจกักเก็บพลังงาน (Tesla Energy Megapack) เติบโตมากกว่า 100% YoY และมีอัตรากำไรขั้นต้นแซงหน้ารถยนต์ไฟฟ้า",
                "แผนเปิดตัวรถยนต์ไฟฟ้าราคาประหยัด (Next-Gen Affordable EV) ช่วยขยายฐานลูกค้าสู่กลุ่ม Mass Market ทั่วโลก",
                "หุ่นยนต์ฮิวแมนนอยด์ Optimus เริ่มทดสอบใช้งานจริงในไลน์ประกอบ Gigafactory เพื่อเตรียมจำหน่ายเชิงพาณิชย์"
            ],
            "drawdown_root_cause": [
                "การแข่งขันด้านราคารถยนต์ไฟฟ้าในตลาดจีนและยุโรปส่งผลกระทบต่ออัตรากำไรยานยนต์ (Auto Gross Margin) ชั่วคราว",
                "ความผันผวนของรอบส่งมอบรถยนต์และระยะเวลาขออนุมัติใบอนุญาตขับขี่ไร้คนขับจากหน่วยงานภาครัฐ",
                "ความอ่อนไหวต่อทิศทางอัตราดอกเบี้ยสินเชื่อเช่าซื้อรถยนต์ของผู้บริโภค"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-30 วัน)", "event": "ตัวเลขยอดส่งมอบยานยนต์ประจำไตรมาสและความคืบหน้าการทดสอบ Cybercab / Robotaxi"},
                {"period": "ระยะ 1-3 เดือน", "event": "การขออนุมัติใช้งานระบบ FSD แบบไร้การควบคุมในตลาดยุโรปและประเทศจีน"},
                {"period": "ระยะ 6-12 เดือน", "event": "การเริ่มสายการผลิตรถยนต์โมเดลราคาเข้าถึงง่าย ($25,000 Model) และเปิดโรงงาน Megafactory แห่งใหม่"}
            ],
            "wall_street_verdict": f"เป้าหมายเฉลี่ยสถาบันอยู่ที่ {m(t_avg)} (Upside {up_s}) โดยมีเป้าหมายสูงสุดจากนักวิเคราะห์สายเทคโนโลยีถึง {m(t_high)}",
            "tailored_roadmap": "ถือครองตามสัดส่วนการลงทุนเพื่อดักการปลดล็อกมูลค่าจาก AI Ecosystem. ตั้งจุด Stop-Loss หากหลุดแนวรับโครงสร้างหลัก",
            "invalidation_risk": "ความล่าช้าในการขอใบอนุญาต Robotaxi เชิงพาณิชย์ หรือการชะลอตัวของยอดขายรถยนต์ในตลาดจีนเกินคาดการณ์"
        },
        "MSFT": {
            "thesis_title": "ผู้นำคลาวด์องค์กรและแพลตฟอร์มซอฟต์แวร์ผสาน AI ที่สร้างรายได้ได้จริง (Copilot & Azure AI)",
            "quality_badge": "🟢 AAA Cash Flow Machine (AI Enterprise Leader)",
            "future_growth_drivers": [
                "บริการคลาวด์ Microsoft Azure AI เติบโตแข็งแกร่ง รับประโยชน์จากความร่วมมือกับ OpenAI และลูกค้าองค์กรชั้นนำระดับโลก",
                "Microsoft 365 Copilot ทยอยเพิ่มรายได้เฉลี่ยต่อผู้ใช้ (ARPU) จากการต่อสัญญาใช้งานระบบปัญญาประดิษฐ์ในองค์กร",
                "สถานะทางการเงินระดับเครดิต AAA และกระแสเงินสดอิสระมากกว่า $70B ต่อปี หนุนการลงทุน CAPEX และการจ่ายเงินปันผลต่อเนื่อง",
                "การเติบโตของธุรกิจ Cyber Security และโครงสร้างระบบเกมมิ่งหลังควบรวม Activision Blizzard เสร็จสมบูรณ์"
            ],
            "drawdown_root_cause": [
                "เม็ดเงินลงทุนใน AI Data Center CAPEX ที่สูงขึ้น สร้างความกังวลชั่วคราวต่ออัตรากำไรระยะสั้น",
                "การประเมินมูลค่า (P/E Multiple) พักฐานตามกลุ่มเทคโนโลยีขนาดใหญ่",
                "การเติบโตของคลาวด์ Azure ชะลอตัวลงเล็กน้อยเนื่องจากกำลังการประมวลผลเซิร์ฟเวอร์ผลิตไม่ทันดีมานด์"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-30 วัน)", "event": "รายงานผลประกอบการไตรมาสใหม่: ติดตามการเติบโตของ Azure AI และรายได้ต่อผู้ใช้ของ Copilot"},
                {"period": "ระยะ 1-3 เดือน", "event": "การเปิดตัวฟีเจอร์ Autonomous AI Agents ใน Microsoft Copilot Studio สำหรับงานออฟฟิศอัตโนมัติ"},
                {"period": "ระยะ 6-12 เดือน", "event": "การขยายตัวของดาต้าเซ็นเตอร์ AI ภูมิภาคใหม่เพื่อปลดล็อกขีดจำกัดกำลังประมวลผล"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s}) ได้รับการจัดอันดับเป็นหุ้นหลุมหลบภัย AI ที่ปลอดภัยที่สุด",
            "tailored_roadmap": "หุ้นเกรด AAA เหมาะเป็นเสาหลักพอร์ตความมั่งคั่ง. ใช้กลยุทธ์ถือยาวรับการเติบโตและเงินปันผลสม่ำเสมอ",
            "invalidation_risk": "การชะลอตัวของอัตราการเติบโตของ Azure ลงต่ำกว่า 25% หรือการถูกตรวจสอบด้านการผูกขาดเทคโนโลยี AI ในยุโรป"
        },
        "AAPL": {
            "thesis_title": "ระบบนิเวศอุปกรณ์และบริการที่มีฐานผู้ใช้กว่า 2,200 ล้านเครื่อง ขับเคลื่อนด้วย Apple Intelligence",
            "quality_badge": "🟢 Consumer Monopoly & Services Ecosystem",
            "future_growth_drivers": [
                "Apple Intelligence รอบอัปเกรดระบบปฏิบัติการ iOS ใหม่ กระตุ้นรอบการเปลี่ยนเครื่อง (iPhone Upgrade Supercycle)",
                "ธุรกิจบริการ (Apple Services: App Store, iCloud, Apple Pay) อัตรากำไรขั้นต้น 70%+ เติบโตทำสถิติสูงสุดใหม่ต่อเนื่อง",
                "โปรแกรมซื้อหุ้นคืน (Share Buyback) ขนาดใหญ่ที่สุดในโลก ช่วยผลักดันกำไรต่อหุ้น (EPS Growth) ให้เติบโตอย่างมั่นคง",
                "การขยายตัวของส่วนแบ่งการตลาดในอินเดีย ตะวันออกกลาง และตลาดเกิดใหม่ช่วยชดเชยการชะลอตัวในบางภูมิภาค"
            ],
            "drawdown_root_cause": [
                "ความกังวลต่อการทยอยปล่อยฟีเจอร์ Apple Intelligence เป็นระยะ ไม่ได้มาพร้อมกันทั้งหมดตั้งแต่แรก",
                "การแข่งขันในตลาดสมาร์ตโฟนพรีเมียมในประเทศจีน",
                "คดีความด้านกฎหมายการผูกขาดระบบ App Store กับกระทรวงยุติธรรมสหรัฐฯ (DOJ Antitrust Case)"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-30 วัน)", "event": "ยอดขาย iPhone ช่วงเทศกาลปลายปีและวันหยุดยาว (Holiday Shopping Quarter)"},
                {"period": "ระยะ 1-3 เดือน", "event": "การปล่อยอัปเดตฟังก์ชัน Apple Intelligence เวอร์ชันภาษาต่างประเทศและในตลาดจีน"},
                {"period": "ระยะ 6-12 เดือน", "event": "การเปิดตัวผลิตภัณฑ์เจเนอเรชันใหม่และชิปประมวลผล Apple Silicon M5"}
            ],
            "wall_street_verdict": f"เป้าหมายเฉลี่ยของวอลล์สตรีทอยู่ที่ {m(t_avg)} (Upside {up_s}) สถาบันมองว่าฐานผู้ใช้ที่เหนียวแน่นจะสร้างกระแสเงินสดต่อเนื่อง",
            "tailored_roadmap": "ถือครองเพื่อรับกระแสเงินสดและการซื้อหุ้นคืนที่สม่ำเสมอ. เฝ้าระวังแนวรับเส้น 200 วันสำหรับการทยอยสะสม",
            "invalidation_risk": "ยอดขาย iPhone ในจีนทรุดตัวเกินคาดการณ์ หรือคำสั่งศาลที่บังคับให้เปลี่ยนแปลงโครงสร้างรายได้ค่าธรรมเนียม App Store"
        },
        "AMZN": {
            "thesis_title": "ผู้นำคลาวด์ AWS โฆษณาออนไลน์ และระบบโลจิสติกส์ E-Commerce ขับเคลื่อนด้วย AI อัตโนมัติ",
            "quality_badge": "🟢 Cloud Infrastructure & High-Margin Ad Giant",
            "future_growth_drivers": [
                "AWS เร่งตัวเติบโตจากชิป Trainium/Inferentia และบริการ Bedrock สำหรับการประมวลผล Generative AI ระดับองค์กร",
                "ธุรกิจโฆษณาดิจิทัล (Amazon Ads) อัตรากำไรสูง เติบโตแซงหน้าตลาด พร้อมการเปิดรับโฆษณาบนสตรีมมิง Prime Video",
                "การปรับโครงสร้างคลังสินค้าแบบภูมิภาค (Regional Fulfillment) ลดต้นทุนการจัดส่งและเพิ่มอัตรากำไรจากการดำเนินงานอย่างยั่งยืน",
                "ฐานสมาชิก Amazon Prime เหนียวแน่น สร้างกระแสรายได้สม่ำเสมอ (Recurring Revenue) ขนาดมหาศาล"
            ],
            "drawdown_root_cause": [
                "ความกังวลต่อการฟื้นตัวของอัตรากำไร AWS ในช่วงเปลี่ยนผ่านไปสู่โครงสร้าง AI Workload",
                "การชะลอตัวของกำลังซื้อผู้บริโภคในกลุ่มสินค้าฟุ่มเฟือย",
                "การลงทุนในเครือข่ายดาวเทียม Project Kuiper ที่ต้องใช้เงินทุนเริ่มต้นสูง"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-30 วัน)", "event": "มหกรรมช้อปปิ้ง Prime Big Deal Days และยอดขายช่วง Black Friday / Cyber Monday"},
                {"period": "ระยะ 1-3 เดือน", "event": "รายงานผลประกอบการไตรมาส 4: ตัวชี้ขาดการเร่งตัวของรายได้ AWS และอัตรากำไรของธุรกิจโฆษณา"},
                {"period": "ระยะ 6-12 เดือน", "event": "การเริ่มยิงกลุ่มดาวเทียมอินเทอร์เน็ตบรอดแบนด์ Project Kuiper เข้าสู่วงโคจรเชิงพาณิชย์"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s})",
            "tailored_roadmap": "หุ้น Growth เกรดพรีเมียมที่รายได้กระจายตัวดีมาก. แนะนำถือตามแนวโน้มขาขึ้นเพื่อรอรับผลตอบแทนจากโครงสร้างกำไรขยายตัว",
            "invalidation_risk": "การชะลอตัวของอัตรากำไรขั้นต้น AWS หรือผลกระทบจากข้อพิพาทด้านแรงงานในระบบขนส่งโลจิสติกส์"
        },
        "APP": {
            "thesis_title": "ผู้ผูกขาดเทคโนโลยีโฆษณา AI เกรดพรีเมียม — กำไรโตระเบิด +89.9% ที่ราคาต่ำสุดในรอบปี",
            "quality_badge": "🟢 Super Growth AI Monopolist (Top Conviction)",
            "future_growth_drivers": [
                "โมเดลปัญญาประดิษฐ์ AXON 2.0: ระบบแมชชีนเลิร์นนิงสำหรับจับคู่โฆษณามือถือที่ทรงพลังที่สุด ให้ค่า Return on Ad Spend (ROAS) สูงกว่าคู่แข่งอย่างท่วมท้น",
                "การขยายสู่ Web E-Commerce Ads: นำ AI ก้าวข้ามจากโฆษณาเกมมือถือไปสู่สินค้าปลีกออนไลน์ เพิ่มขนาดตลาดเป้าหมาย (TAM) มหาศาลกว่า 5-10 เท่า",
                "การเติบโตของกำไรสุทธิมหาศาล (+89.9% YoY) และอัตรากำไร EBITDA สูงระดับ 50-60%: มีค่า PEG เพียง 0.22 ซึ่งถือว่าถูกมากในกลุ่ม AI Software",
                "สถานะกระแสเงินสดอิสระ (FCF) แข็งแกร่ง: บริษัทสามารถซื้อหุ้นคืนต่อเนื่องและเสริมความแข็งแกร่งของเทคโนโลยีโดยไม่ต้องกู้หนี้"
            ],
            "drawdown_root_cause": [
                "การพักฐานรอบสั้นหลังหุ้นวิ่งขึ้นมาหลายเท่าตัวในรอบปีก่อน เกิดการหมุนเวียนเงินทุน (Tech Sector Rotation) ระยะสั้น",
                "ราคาพักตัวลงมาทดสอบระดับต่ำสุดรอบ 52 สัปดาห์ ซึ่งเป็นแนวรับทางจิตวิทยาสำคัญ",
                "แรงกดดันจากกระแสข่าวการแข่งขันของแพลตฟอร์มโซเชียลมีเดีย แต่พื้นฐานกำไรจริงของบริษัทยังไม่ได้รับผลกระทบ"
            ],
            "catalyst_timeline": [
                {"period": earnings_period, "event": "รายงานงบการเงิน Q3: จับตาการเติบโตของรายได้จากลูกค้า Web Advertising และการเติบโตของซอฟต์แวร์ AXON 2.0"},
                {"period": "ระยะ 1-3 เดือน", "event": "การเปิดตัวโมเดลโฆษณาเจนเนอเรชันถัดไปและการปรับประมาณการกำไรขึ้นจากโบรกเกอร์วอลล์สตรีท"},
                {"period": "ระยะ 6-12 เดือน", "event": "การขยายตลาดสู่ผู้ค้าปลีกระดับโลก (Shopify / Global Brands Integration)"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s}) และเป้าหมายต่ำสุดอยู่ที่ {m(t_low)}{low_vs_cost}",
            "tailored_roadmap": earnings_note + "หุ้นมีพื้นฐานระดับ AAA และ PEG ถูกสุดในกลุ่ม AI. คำแนะนำคือ 'ถือรออย่างสบายใจ' หรือรอสัญญาณแท่งเทียนเขียว Daily Confirmation ที่แนวรับสำคัญแล้วทำ Smart DCA ซื้อเพิ่ม 50% ดึงทุนลงมารอรับ Upside ก้อนใหญ่",
            "invalidation_risk": "จุดยอมจำนนคือการหลุดเส้น Stop-Loss หรือหากตัวเลขอัตรากำไร AXON ชะลอตัวลงต่ำกว่า 20% อย่างมีนัยสำคัญ"
        },
        "VRT": {
            "thesis_title": "ผู้นำระบบระบายความร้อนด้วยของเหลว (Liquid Cooling) และระบบไฟ AI Data Center อันดับหนึ่งของโลก",
            "quality_badge": "🟢 Pure-Play AI Infrastructure Leader",
            "future_growth_drivers": [
                "NVIDIA GB200 NVL72 Architecture: ชิป Blackwell ระดับ 100kW+ ต่อ Rack ไม่สามารถระบายความร้อนด้วยพัดลมลมธรรมดาได้ ต้องใช้ Liquid Cooling 100% ซึ่ง Vertiv เป็นพันธมิตรวิศวกรรมหลักของ NVIDIA",
                "Backlog คำสั่งซื้อค้างส่งสูงเป็นประวัติการณ์: ดีมานด์การสร้าง AI Factory ของ Microsoft, AWS, Google, Oracle ผลักดันให้อัตราจองคำสั่งซื้อยาวต่อเนื่องข้ามปี",
                f"กำไรสุทธิ YoY {net_g_str} และรายได้ YoY {rev_g_str}: สะท้อนอำนาจในการกำหนดราคา (Pricing Power) และการขยายตัวของอัตรากำไรขั้นต้น",
                "ระบบจัดการพลังงานครบวงจร (Switchgear, Busbar, UPS, Thermal): Vertiv เป็นผู้เล่นรายเดียวที่มีโซลูชันครบวงจรตั้งแต่เสาไฟแรงสูงจนถึงหลังชิปประมวลผล"
            ],
            "drawdown_root_cause": [
                "ข่าว Minor Timing Shifts ในช่วง Q2 ทำให้ยอดส่งมอบสินค้าบางโครงการถูกเลื่อนไปส่งมอบในครึ่งปีหลัง จึงมีแรงเทขายทำกำไรระยะสั้น",
                "ประเด็น Investor Rights Probe สร้างความผันผวนต่อจิตวิทยาการลงทุนของรายย่อยในระยะสั้น",
                "การชะลอตัวของราคาหุ้นอุตสาหกรรมโครงสร้างพื้นฐานก่อนเข้าสู่สัปดาห์ประกาศงบไตรมาส 3"
            ],
            "catalyst_timeline": [
                {"period": earnings_period, "event": "ประกาศผลประกอบการ Q3: จับตาการเร่งส่งมอบคำสั่งซื้อและ Guidance ปี 2027"},
                {"period": "ระยะ 1-3 เดือน", "event": "การทยอยส่งมอบแร็ค NVIDIA GB200 ให้กับลูกค้าระดับ Tier-1 Hyperscalers ทั่วโลก"},
                {"period": "ระยะ 6-12 เดือน", "event": "การเปิดโรงงานขยายกำลังการผลิต Liquid Cooling เฟสใหม่เพื่อรองรับอุปสงค์ที่ล้นมือ"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s} จากราคาปัจจุบัน และเทียบต้นทุนของคุณ {pct(upside_cost)})" if cost_price > 0 else f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s})",
            "tailored_roadmap": earnings_note + "ติดตามสถานะตามแผนยุทธศาสตร์และข้อมูล AI Backlog อย่างใกล้ชิด",
            "invalidation_risk": "หากประกาศงบแล้วพบว่าปัญหา Supply Chain คอขวดรุนแรงจนยกเลิกออเดอร์ หรือราคาปิดหลุดแนวรับ Stop-Loss ให้พิจารณาลดสัดส่วนเพื่อถือเงินสด"
        },
        "BAC": {
            "thesis_title": "สถาบันการเงินยักษ์ใหญ่รับประโยชน์ดอกเบี้ยขาลง" + (f" จังหวะย่อตัวรุนแรงในโซน Oversold (RSI {rsi:.0f})" if rsi is not None and rsi < 30 else ""),
            "quality_badge": "🟢 Resilient Major Bank (Value Deep Dip)",
            "future_growth_drivers": [
                "วัฏจักรดอกเบี้ยขาลงของธนาคารกลางสหรัฐฯ (Fed Rate Cuts): ช่วยลดต้นทุนดอกเบี้ยจ่ายเงินฝาก (Deposit Beta) ทำให้ส่วนต่างดอกเบี้ยรับสุทธิ (NII) แตะจุดต่ำสุดและเริ่มฟื้นตัว",
                "พอร์ตตราสารหนี้ระยะยาว (Held-to-Maturity): ภาระขาดทุนทางบัญชีคลี่คลายลงอย่างมากเมื่อ Yield พันธบัตรปรับตัวลดลงตามแนวโน้มดอกเบี้ย",
                "การฟื้นตัวของวาณิชธนกิจ (IB Advisory): ดีลควบรวมกิจการและการเสนอขายหุ้น IPO ที่อั้นมานานจะกลับมาคึกคักหลังทิศทางดอกเบี้ยมีความชัดเจน",
                "ความแข็งแกร่งของพอร์ตลูกค้ารายย่อยและบริหารความมั่งคั่ง (Merrill Lynch Wealth Management): สร้างกระแสรายได้ค่าธรรมเนียมสม่ำเสมอ พร้อมเงินปันผล ~2.5%"
            ],
            "drawdown_root_cause": [
                "ผลการดำเนินงาน Q3 รายได้และกำไรสุทธิปรับลดลงชั่วคราวจากการชะลอตัวของรายได้ค่าธรรมเนียม Fixed Income Trading และดีล M&A",
                "ประเด็นค่าปรับด้านการกำกับดูแล (Regulatory Penalty) ส่งผลให้นักลงทุนเทขายฉับพลันจนราคาดิ่งหลุดกรอบ",
                (f"ดัชนี RSI รายวันอยู่ที่ระดับ {rsi:.2f}" + (" ซึ่งเป็นโซน Extreme Oversold (ขายมากเกินไปอย่างผิดปกติในเชิงสถิติ)" if rsi < 30 else "")) if rsi is not None else "แรงขายทางเทคนิคกดดันราคาในระยะสั้น"
            ],
            "catalyst_timeline": [
                {"period": "ระยะประชิด (0-14 วัน)", "event": "แรงซื้อดักเด้งทางเทคนิค (Mean Reversion) เพื่อกลับไปทดสอบเส้น SMA 20" + (f" ที่ {m(sma20)}" if sma20 else "")},
                {"period": "ระยะ 1-3 เดือน", "event": "การประชุม Fed FOMC รอบใหม่ และการส่งสัญญาณการฟื้นตัวของสินเชื่อเชิงพาณิชย์"},
                {"period": "ระยะ 6-12 เดือน", "event": "การกลับมาของกิจกรรมซื้อหุ้นคืน (Share Repurchase Program) หลังเงินกองทุน Tier 1 แข็งแกร่งเกินเกณฑ์"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายต่ำสุดของวอลล์สตรีทอยู่ที่ {m(t_low)}{low_vs_cost} เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s})",
            "tailored_roadmap": earnings_note + (
                "เนื่องจากราคาซื้อขายต่ำกว่าเป้าหมายต่ำสุดของสถาบัน จึงติดตามจังหวะดีดตัวทางเทคนิคหรือพิจารณาตามแผนแนวรับสำคัญ"
                if (t_low is not None and close_price < t_low)
                else "ติดตามจังหวะดีดตัวทางเทคนิคหรือพิจารณาตามแผนแนวรับสำคัญ"
            ),
            "invalidation_risk": "หากราคาปิดหลุดแนวรับ Stop-Loss และมีปัจจัยเสี่ยงเศรษฐกิจถดถอยรุนแรง (Hard Landing) จนหนี้เสียพุ่ง ให้ลดขนาดสถานะลงครึ่งหนึ่ง"
        },
        "NOK": {
            "thesis_title": "วัฏจักร 5G Telecom ชะลอตัวชั่วคราว vs การรุกตลาด AI Data Center Optics (Infinera)",
            "quality_badge": "🟡 Value Recovery & Optical Transition",
            "future_growth_drivers": [
                "ดีลซื้อกิจการ Infinera ($2.3B): ก้าวกระโดดเข้าสู่โครงสร้างพื้นฐานเครือข่ายแสง (Optical Networking) สำหรับ AI Data Center เชื่อมโยงคลัสเตอร์ GPU ขนาดใหญ่ ซึ่งเป็นตลาด High-Margin เติบโตสูง",
                "Nokia Technologies (ธุรกิจสิทธิบัตร): ทำสัญญาสิทธิบัตร 5G ข้ามปีกับ Apple, Samsung, Vivo และผู้ผลิตรถยนต์ EV สร้างกระแสเงินสดต่อเนื่องสม่ำเสมอ",
                "Private 5G & Defense Networks: องค์กรธุรกิจและกองทัพขยายโครงข่ายไร้สายความมั่นคงสูง ซึ่งมีอัตราการเติบโตของกำไรมากกว่าตลาดทั่วไป",
                "โครงการบรอดแบนด์ภาครัฐสหรัฐฯ (BEAD Program): เริ่มเบิกจ่ายงบประมาณโครงสร้างพื้นฐานไฟเบอร์และอินเทอร์เน็ตความเร็วสูงในชนบท"
            ],
            "drawdown_root_cause": [
                "ผู้ให้บริการเครือข่ายโทรคมนาคมรายใหญ่ในสหรัฐฯ (AT&T, Verizon) ชะลอการลงทุนขยายเสาสัญญาณ 5G ชั่วคราวหลังจากลงทุนหนักไปในช่วง 2-3 ปีก่อนหน้า",
                "การเสียสัญญา Open RAN ให้แก่ Ericsson ปลายปี 2023 ยังคงเป็นแรงกดดันทางจิตวิทยาต่อรายได้กลุ่ม Mobile Networks ในระยะสั้น",
                "ราคาหุ้นแกว่งตัวในกรอบแคบรอผลประกอบการไตรมาสถัดไป เพื่อประเมินอัตรากำไรขั้นต้นและการฟื้นตัวของคำสั่งซื้อ"
            ],
            "catalyst_timeline": [
                {"period": earnings_period, "event": "ประกาศผลประกอบการไตรมาส 3: ตัวชี้ขาด Gross Margin และคำสั่งซื้อ Network Infrastructure"},
                {"period": "ระยะกลาง (1-3 เดือน)", "event": "กระบวนการปิดดีลควบรวม Infinera และการเริ่มส่งมอบอุปกรณ์ชิปเครือข่ายซิลิคอนโฟโตนิกส์"},
                {"period": "ระยะ 6-12 เดือน", "event": "รอบการอัปเกรด 5G-Advanced และการเบิกจ่ายงบประมาณเครือข่ายแสงของคลาวด์ไฮเปอร์สเกลเลอร์"}
            ],
            "wall_street_verdict": f"{consensus}เป้าหมายเฉลี่ย {m(t_avg)} (Upside {up_s}) โดยเป้าหมายต่ำสุดอยู่ที่ {m(t_low)} และสูงสุดที่ {m(t_high)}",
            "tailored_roadmap": f"กำไรสุทธิ YoY {net_g_str}. " + earnings_note + "ให้ถือรอประเมินตัวเลขจริง หากกราฟยืนเหนือแนวรับเส้น 200 วัน" + (f" ({m(sma200)})" if sma200 else "") + " ได้ จึงรอจังหวะ Rebound Exit ปิดความเสี่ยงที่จุดคุ้มทุน" + (f" {m(cost_price)}" if cost_price > 0 else ""),
            "invalidation_risk": "หากงบ Q3 ชะลอตัวลงเกินคาดและราคาหลุดจุดตัดขาดทุน (หลุดแนวรับโครงสร้างหลัก) ต้องพิจารณา Cut Loss เพื่อปกป้องเงินต้นส่วนใหญ่"
        }
    }

    if t in curated:
        out = dict(curated[t])
        out["thesis_title"] = f"{out['thesis_title']} (ข้อมูลอ้างอิงเขียนเอง อัปเดตล่าสุด {CURATED_AS_OF})"
        out["curated_as_of"] = CURATED_AS_OF
        return out

    sec = escape(str(data.get("sector") or "ธุรกิจทั่วไป"))
    ind = escape(str(data.get("industry") or "อุตสาหกรรม"))
    t_html = escape(t)
    rev_g = pct(fundamentals.get("rev_growth_yoy"))
    net_g = pct(fundamentals.get("net_inc_growth_yoy"))
    pe = fundamentals.get("pe")
    peg = fundamentals.get("peg")
    pe_s = f"{pe:.1f}x" if pe is not None else "-"
    peg_s = f"{peg:.2f} เท่า" if peg is not None else "-"

    is_underwater = (cost_price > 0 and close_price < cost_price)
    if is_underwater:
        drawdown_reasons = [
            f"แรงขายทำกำไรและการพักฐานทางเทคนิคตามภาวะความผันผวนของกลุ่ม {sec}",
            "การปรับสมดุลพอร์ตของนักลงทุนสถาบันก่อนรับรู้ข้อมูลปัจจัยมหภาคและทิศทางอัตราดอกเบี้ย",
            "แรงทดสอบแนวรับสำคัญเพื่อสร้างฐานราคาใหม่",
        ]
    else:
        drawdown_reasons = []

    days_str = f"ปฏิทินงบ ({int(round(days_to_earnings))} วัน)" if days_to_earnings is not None else "รอบผลประกอบการถัดไป"

    return {
        "thesis_title": f"การวิเคราะห์เจาะลึกศักยภาพการเติบโต {t_html} ในกลุ่ม {sec} ({ind})",
        "quality_badge": fundamentals.get("quality_tier", "🟡 Market Leader"),
        "future_growth_drivers": [
            f"การขยายตัวของรายได้ระดับ {rev_g} YoY และความสามารถในการทำกำไรสุทธิ {net_g} YoY",
            f"อัตราการประเมินมูลค่า P/E {pe_s} และค่า PEG {peg_s} สะท้อนระดับราคาต่อการเติบโต",
            f"ส่วนแบ่งการตลาดและความแข็งแกร่งของตราสินค้าในกลุ่มอุตสาหกรรม {ind}",
            "การเพิ่มประสิทธิภาพการดำเนินงานและการบริหารจัดการต้นทุนเพื่อผลักดันกระแสเงินสดอิสระ"
        ],
        "drawdown_root_cause": drawdown_reasons,
        "catalyst_timeline": [
            {"period": days_str, "event": "การแถลงงบการเงินและทิศทางคำสั่งซื้อในอนาคต"},
            {"period": "ระยะ 1-3 เดือน", "event": "การปรับบทวิเคราะห์และประมาณการกำไรจากนักวิเคราะห์วอลล์สตรีท"},
            {"period": "ระยะ 6-12 เดือน", "event": "การเปิดตัวผลิตภัณฑ์ใหม่และการขยายตลาดสู่กลุ่มเป้าหมายใหม่"}
        ],
        "wall_street_verdict": f"{consensus}ราคาเป้าหมายเฉลี่ยสถาบันอยู่ที่ {m(t_avg)} (Upside {up_s})" if t_avg else f"{consensus}ยังไม่มีการตั้งราคาเป้าหมายจากสถาบัน",
        "tailored_roadmap": f"{earnings_note}ติดตามกรอบแนวรับแนวต้านสำคัญทางเทคนิค และปฏิบัติตามวินัย Stop-Loss อย่างเคร่งครัด",
        "invalidation_risk": "การปิดหลุดแนวรับโครงสร้างหลัก หรือตัวเลขอัตรากำไรสุทธิชะลอตัวลงเกิน 20%"
    }
