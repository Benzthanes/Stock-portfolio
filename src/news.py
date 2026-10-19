"""
Financial News & Catalyst Engine
Fetches live headlines and market catalysts via RSS for US stocks.
Includes sentiment classification (Bullish vs Bearish), parallel batch fetching, and caching.
"""

import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.http import HttpError, http_get

CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / ".news_cache.json"
CACHE_TTL_SECONDS = 1800  # 30 minutes
_CACHE_LOCK = threading.Lock()

TICKER_SEARCH_MAP = {
    "APP": "AppLovin stock OR advertising",
    "BAC": "Bank of America stock OR earnings",
    "NOK": "Nokia stock OR 5G OR Infinera",
    "VRT": "Vertiv stock OR datacenter OR cooling",
    "LLY": "Eli Lilly stock OR Mounjaro",
    "GOOGL": "Alphabet Google stock",
    "ABNB": "Airbnb stock",
    "MNST": "Monster Beverage stock",
    "VOO": "S&P 500 VOO ETF"
}

BEARISH_KEYWORDS = {
    "downgrade", "downgrades", "downgraded", "drop", "drops", "dropped", "fall", "falls",
    "fell", "slide", "slides", "losing", "dispute", "lawsuit", "probe",
    "investigation", "miss", "misses", "missed", "warning", "caution", "weak", "weakness",
    "sell", "debt", "tariff", "antitrust", "slashes", "slashed", "loss", "losses", "delay",
    "delays", "delayed", "tumble", "tumbles", "tumbled", "plunge", "plunges", "plunged",
    "sink", "sinks", "sank", "headwind", "struggle", "struggles", "struggling", "underperform",
    "penalty", "record low", "record lows", "52-week low", "dip", "pullback", "narrow range", "selloff",
    "reject", "rejects", "rejected", "rejection", "declines to approve", "shares lower", "trades lower", "trading lower", "moves lower",
    "closes lower", "closed lower", "slump", "slumps",
    "retreat", "retreats", "crash", "plummets",
    "fear", "fears", "bubble", "charges", "charged", "sued", "recall", "layoffs", "cuts guidance"
}

BULLISH_KEYWORDS = {
    "upgrade", "upgrades", "upgraded", "record", "beat", "beats", "beating", "soar",
    "soars", "soared", "gain", "gains", "gained", "rise", "rises", "invest", "investment",
    "expansion", "profit", "profits", "profitable", "approval", "approves", "approved", "partner",
    "partnership", "surge", "surges", "surged", "growth", "growing", "dividend", "boost",
    "boosts", "outperform", "opportunity", "moat", "rebound", "rebounds", "bull", "bullish",
    "rally", "rallies", "grew", "cheaper", "edge", "buy", "picks", "picks ahead", "winning streak"
}

_BEAR_REGEX = re.compile(r'\b(' + '|'.join(re.escape(k) for k in BEARISH_KEYWORDS) + r')\b', re.IGNORECASE)
_BULL_REGEX = re.compile(r'\b(' + '|'.join(re.escape(k) for k in BULLISH_KEYWORDS) + r')\b(?!\s+lows?\b)', re.IGNORECASE)
_NEUTRAL_PHRASE_REGEX = re.compile(r'\bweight[- ]loss\b', re.IGNORECASE)
# Checked before the word lists: these phrases contain a word from the opposite list.
_BEAR_PHRASE_REGEX = re.compile(r'\b(cuts? (its |the )?dividend|dividend cut|suspends dividend|cuts? (its |the )?price target|lowers? (its |the )?price target|(profit|earnings|revenue|sales) (misses|missed|falls short)|slips?|slipped)\b', re.IGNORECASE)
_BULL_PHRASE_REGEX = re.compile(r'\bnarrows? (its |the )?(quarterly )?loss(es)?\b', re.IGNORECASE)
_QUESTION_REGEX = re.compile(r'^\s*(should you|is it time|is now|can|will|is)\b.*\?\s*$', re.IGNORECASE)


def _load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        now = time.time()
        return {k: v for k, v in data.items() if (now - v.get("cached_at", 0)) < CACHE_TTL_SECONDS}
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=CACHE_FILE.parent, prefix=CACHE_FILE.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            os.replace(tmp, CACHE_FILE)
        except BaseException:
            os.unlink(tmp)
            raise
    except Exception as e:
        print(f"[news] cache write failed: {e}", file=sys.stderr)


def _get_from_cache(ticker: str, max_items: int) -> Optional[List[Dict[str, str]]]:
    with _CACHE_LOCK:
        cache = _load_cache()
        entry = cache.get(ticker)
        if entry is None:
            return None
        articles = entry.get("articles", [])
        if entry.get("max_items", len(articles)) < max_items:
            return None
        return articles


def _update_cache(ticker: str, articles: List[Dict[str, str]], max_items: int, keep_timestamp: bool = False) -> None:
    with _CACHE_LOCK:
        cache = _load_cache()
        cached_at = cache.get(ticker, {}).get("cached_at") if keep_timestamp else None
        cache[ticker] = {
            "cached_at": cached_at or time.time(),
            "max_items": max_items,
            "articles": articles
        }
        _save_cache(cache)


def _parse_pub_date(pub_date_str: str) -> Optional[datetime]:
    try:
        dt = parsedate_to_datetime(pub_date_str)
    except (TypeError, ValueError, IndexError):
        return None
    # RFC 2822 "-0000" parses as naive; it still means UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _format_relative_time(pub_date_str: str) -> str:
    """Absolute date (e.g. '16 Oct 2026'). A relative '3h ago' baked into static HTML goes stale the moment the page is opened later."""
    dt = _parse_pub_date(pub_date_str)
    if dt is None:
        return pub_date_str[:16] if pub_date_str else ""
    return dt.astimezone(timezone.utc).strftime("%d %b %Y")


def classify_sentiment(title: str) -> str:
    """
    Classify a headline as 'bullish', 'bearish', or 'neutral' using whole-word regex matching.
    """
    title_clean = _NEUTRAL_PHRASE_REGEX.sub(" ", title)
    if _BULL_PHRASE_REGEX.search(title_clean):
        return "bullish"
    if _BEAR_PHRASE_REGEX.search(title_clean):
        return "bearish"
    if _QUESTION_REGEX.search(title_clean):
        return "neutral"
    is_bear = bool(_BEAR_REGEX.search(title_clean))
    is_bull = bool(_BULL_REGEX.search(title_clean))

    if is_bear and not is_bull:
        return "bearish"
    elif is_bull and not is_bear:
        return "bullish"
    elif is_bear and is_bull:
        return "mixed"
    return "neutral"


def translate_texts_to_thai(texts: List[str]) -> List[str]:
    """Translates headlines to Thai in one Google Translate request. Returns the originals on any failure."""
    if not texts:
        return []
    joined = "\n".join(t.replace("\n", " ") for t in texts)
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=th&dt=t&q={urllib.parse.quote(joined)}"
        body = http_get(url, timeout=3.5, retries=1)
        if body:
            data = json.loads(body.decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part[0]).split("\n")
            if len(translated) == len(texts):
                return [th.strip() or en for th, en in zip(translated, texts)]
    except Exception:
        pass
    return list(texts)


def translate_text_to_thai(text: str) -> str:
    """Translates a single headline to Thai with fallback to the original text."""
    return translate_texts_to_thai([text])[0] if text else ""


def _enrich_articles(articles: List[Dict[str, str]], ticker: str) -> bool:
    """Adds Thai title and synthesized guidance to articles. Prefers AI-analyzed cache if available."""
    changed = False
    try:
        from src.ai_news import get_ai_analyzed_article
    except Exception:
        get_ai_analyzed_article = None

    # 1. Upgrade or preserve articles using high-quality AI analysis if present
    for a in articles:
        if get_ai_analyzed_article and not a.get("ai_analyzed"):
            ai_data = get_ai_analyzed_article(ticker, a.get("title", ""), a.get("link", ""))
            if ai_data and ai_data.get("ai_analyzed"):
                for key in ("title_th", "summary_th", "impact_th", "action_th", "topic", "sentiment", "ai_analyzed", "ai_analyzed_at"):
                    if key in ai_data:
                        a[key] = ai_data[key]
                changed = True

    # 2. For any remaining articles missing translation or summary, apply programmatic fallback
    missing = [a for a in articles if ("summary_th" not in a or "title_th" not in a) and not a.get("ai_analyzed")]
    if not missing:
        return changed

    need_translation = [a for a in missing if not a.get("title_th")]
    if need_translation:
        for a, th in zip(need_translation, translate_texts_to_thai([a.get("title", "") for a in need_translation])):
            a["title_th"] = th
            changed = True
    for a in missing:
        syn = synthesize_news_summary(a.get("title", ""), a.get("title_th", ""), a.get("source", "News"), ticker, a.get("sentiment", "neutral"))
        for key in ("title_th", "summary_th", "impact_th", "action_th", "topic"):
            a[key] = syn[key]
        a["ai_analyzed"] = False
        changed = True
    return changed


_TOPIC_RULES = [
    (("beat", "beats", "earnings", "q1", "q2", "q3", "q4", "revenue", "profit", "miss", "misses", "estimate", "estimates", "results"),
     "รายงานผลประกอบการและตัวเลขทางการเงิน",
     "การรายงานงบการเงินและตัวเลขกำไรต่อหุ้น (EPS) เทียบกับที่นักวิเคราะห์ Wall Street คาดการณ์"),
    (("underpricing", "undervalued", "overvalued", "valuation", "cheap", "fair value", "discount"),
     "การประเมินมูลค่าหุ้น (Stock Valuation & Fair Value)",
     "การเปรียบเทียบราคาตลาดกับมูลค่าพื้นฐานที่แท้จริง (Intrinsic Value) ของบริษัท"),
    (("ai", "artificial intelligence", "nvidia", "datacenter", "data center", "cooling", "chip", "chips", "semiconductor", "cloud"),
     "เทคโนโลยี AI และการขยายโครงสร้างพื้นฐานดาต้าเซ็นเตอร์",
     "คลื่นการลงทุนโครงสร้างพื้นฐานระบบประมวลผล AI และชิปประมวลผลยุคใหม่"),
    (("upgrade", "upgrades", "downgrade", "downgrades", "price target", "analyst", "analysts", "buy rating", "outperform", "wall street"),
     "มุมมองและอันดับความน่าเชื่อถือจากนักวิเคราะห์ Wall Street",
     "การปรับเป้าหมายราคาและคำแนะนำการลงทุนของสถาบันการเงินชั้นนำ"),
    (("fda", "drug", "drugs", "trial", "trials", "approval", "treatment", "patent", "clinical", "mounjaro", "zepbound"),
     "การอนุมัติยา นวัตกรรมชีวภาพ และการทดลองทางคลินิก",
     "ความคืบหน้าของยารักษาโรคสำคัญและสิทธิบัตรยาที่มีตลาดรองรับขนาดใหญ่"),
    (("dividend", "dividends", "buyback", "buybacks", "cash flow", "payout"),
     "ผลตอบแทนเงินปันผลและการซื้อหุ้นคืน",
     "ความแข็งแกร่งของกระแสเงินสดอิสระ (FCF) และการส่งมอบผลตอบแทนสู่ผู้ถือหุ้น"),
    (("lawsuit", "antitrust", "probe", "sec", "investigation", "tariff", "tariffs", "dispute"),
     "ประเด็นกฎหมาย นโยบายภาษีศุลกากร และการกำกับดูแล",
     "ความเสี่ยงด้านกฎหมายการค้า การแข่งขันทางการค้า และการตรวจสอบของหน่วยงานรัฐ"),
    (("etf", "etfs", "index", "s&p 500", "spy", "voo", "fund", "funds"),
     "กระแสเงินทุนดัชนีและการลงทุนสถาบัน",
     "การไหลเข้าออกของเม็ดเงินกองทุนดัชนี Passive และการปรับสมดุลพอร์ตของสถาบัน"),
]
_TOPIC_REGEXES = [
    (re.compile(r'(?<!\w)(' + '|'.join(re.escape(k) for k in keys) + r')(?!\w)', re.IGNORECASE), topic, context)
    for keys, topic, context in _TOPIC_RULES
]


def classify_topic(title: str) -> Tuple[str, str]:
    """Returns (topic, context) for a headline using whole-word keyword matching."""
    for regex, topic, context in _TOPIC_REGEXES:
        if regex.search(title):
            return topic, context
    return "ผลการดำเนินงานและทิศทางธุรกิจ", "การดำเนินงานตามแผนยุทธศาสตร์และการแข่งขันในอุตสาหกรรม"


def synthesize_news_summary(title_en: str, title_th: str, source: str, ticker: str, sentiment: str) -> Dict[str, str]:
    """Generates detailed Thai financial summary, market impact, and actionable strategy."""
    topic, specific_context = classify_topic(title_en)

    clean_src = source or "สำนักข่าวการเงินต่างประเทศ"
    th_title_clean = title_th or title_en

    if sentiment == "bullish":
        summary_th = (
            f"• สำนักข่าว {clean_src} รายงานข่าวเชิงบวกต่อ {ticker} ในประเด็น '{th_title_clean}'.\n"
            f"• บริบทและเนื้อหาสำคัญ: ข่าวนี้เกี่ยวข้องกับ {specific_context} ซึ่งสะท้อนโมเมนตัมธุรกิจที่ขยายตัวได้ดีกว่าค่าเฉลี่ยอุตสาหกรรม.\n"
            f"• นัยต่อปัจจัยพื้นฐาน: สนับสนุนการเติบโตของรายได้ (Top-line Growth) และช่วยรักษาอัตรากำไรขั้นต้นให้อยู่ในระดับสูง.\n"
            f"• พฤติกรรมเม็ดเงินสถาบัน: เพิ่มความน่าสนใจให้แก่กองทุนสถาบันในการพิจารณาเพิ่มน้ำหนักการลงทุน (Accumulation) ในช่วงที่ราคาพักตัว."
        )
        impact_th = (
            f"🟢 เชิงบวกต่อราคาหุ้น (Bullish Catalyst): ข่าวนี้เป็นปัจจัยขับเคลื่อนเชิงจิตวิทยาและปัจจัยพื้นฐาน ช่วยหนุนโมเมนตัมราคาให้มีโอกาสทดสอบแนวต้านถัดไป "
            f"และลดโอกาสการปรับฐานลึกในระยะสั้น."
        )
        action_th = (
            f"💡 แผนกลยุทธ์การเทรด: หากราคาหุ้นย่อตัวลงมาทดสอบแนวรับสำคัญ เช่น เส้นค่าเฉลี่ย EMA 21/50 หรือแนวรับ Fibo 61.8% ถือเป็นจังหวะทยอยสะสม (DCA) "
            f"ไม่แนะนำให้ไล่ราคาเมื่อแท่งเทียนอยู่ห่างจากแนวรับเกิน 1.5 ATR."
        )
    elif sentiment == "bearish":
        summary_th = (
            f"• สำนักข่าว {clean_src} รายงานปัจจัยกดดันต่อ {ticker} ในประเด็น '{th_title_clean}'.\n"
            f"• บริบทและเนื้อหาสำคัญ: ข่าวนี้ระบุถึงประเด็น {specific_context} ที่อาจก่อให้เกิดอุปสรรคชั่วคราวต่อการดำเนินงาน.\n"
            f"• นัยต่อปัจจัยพื้นฐาน: ตลาดมีความกังวลต่อแรงกดดันด้านต้นทุน การชะลอตัวของคำสั่งซื้อ หรือความเสี่ยงด้านกฎระเบียบที่อาจกระทบต่อผลกำไร.\n"
            f"• พฤติกรรมเม็ดเงินสถาบัน: มีแนวโน้มที่ผู้จัดการกองทุนจะชะลอการเข้าซื้อเพื่อประเมินสถานการณ์ หรือทยอยขายทำกำไรลดความเสี่ยงบางส่วน."
        )
        impact_th = (
            f"🔴 เชิงลบต่อราคาหุ้น (Bearish Risk): อาจสร้างแรงกระเพื่อมเชิงลบในระยะสั้น ส่งผลให้ราคาหุ้นเผชิญแรงขายทำกำไรหรือพักฐานลงมาทดสอบแนวรับล่าง."
        )
        action_th = (
            f"💡 แผนกลยุทธ์การเทรด: ชะลอการเข้าซื้อก้อนใหญ่ (Wait & See) ควรรอให้แรงขายชะลอตัวและราคาสร้างฐานแนวรับที่มั่นคง "
            f"พร้อมตั้งระดับ Stop Loss หรือจุด Invalidation ตามกรอบทางเทคนิคอย่างเคร่งครัด."
        )
    elif sentiment == "mixed":
        summary_th = (
            f"• สำนักข่าว {clean_src} รายงานข้อมูลเชิงเปรียบเทียบสองมุมมองต่อ {ticker} ในประเด็น '{th_title_clean}'.\n"
            f"• บริบทและเนื้อหาสำคัญ: ครอบคลุมประเด็น {specific_context} ซึ่งมีทั้งปัจจัยหนุนการเติบโตและปัจจัยความไม่แน่นอนที่ต้องเฝ้าระวัง.\n"
            f"• นัยต่อปัจจัยพื้นฐาน: ศักยภาพการเติบโตระยะยาวยังคงแข็งแกร่ง แต่มูลค่าหุ้นในระยะสั้นเริ่มสะท้อนความคาดหวังไปค่อนข้างมาก.\n"
            f"• พฤติกรรมเม็ดเงินสถาบัน: กองทุนมีแนวโน้มรอดูรายงานผลประกอบการและตัวเลขเศรษฐกิจเพิ่มเติมก่อนตัดสินใจเข้าสถานะใหญ่."
        )
        impact_th = (
            f"🟡 ผสมผสานสองด้าน (Mixed / Neutral Volatility): คาดว่าราคาหุ้นจะแกว่งตัวในกรอบ Sideways เพื่อสร้างฐานราคาใหม่."
        )
        action_th = (
            f"💡 แผนกลยุทธ์การเทรด: เน้นการเทรดตามกรอบแนวรับแนวต้าน (Range Trading) แบ่งไม้ซื้อสะสมที่กรอบล่าง และขายทำกำไรบางส่วนที่กรอบบน."
        )
    else:
        summary_th = (
            f"• สำนักข่าว {clean_src} รายงานสถานการณ์ทั่วไปของ {ticker} ในประเด็น '{th_title_clean}'.\n"
            f"• บริบทและเนื้อหาสำคัญ: ติดตามพัฒนาการในหมวด {specific_context} ซึ่งเป็นการดำเนินงานตามแผนธุรกิจปกติ.\n"
            f"• นัยต่อปัจจัยพื้นฐาน: โครงสร้างพื้นฐานของธุรกิจยังคงดำเนินไปอย่างมีเสถียรภาพ ไม่พบการเปลี่ยนแปลงเชิงโครงสร้างที่มีนัยสำคัญ.\n"
            f"• พฤติกรรมเม็ดเงินสถาบัน: ปริมาณการซื้อขายยังคงเคลื่อนไหวตามสภาวะตลาดโดยรวม."
        )
        impact_th = (
            f"⚪ เป็นกลาง (Neutral Stance): ไม่ได้สร้างแรงกระตุ้นรุนแรงต่อทิศทางราคา ทิศทางยังคงเคลื่อนไหวตามกรอบเทคนิคและเส้นแนวโน้มเดิม."
        )
        action_th = (
            f"💡 แผนกลยุทธ์การเทรด: อ้างอิงสัญญาณเทคนิคจากเส้นค่าเฉลี่ย EMA และระดับ Pivot Points ในการตัดสินใจลงทุนตามรอบปกติ."
        )

    return {
        "title_th": title_th or title_en,
        "summary_th": summary_th,
        "impact_th": impact_th,
        "action_th": action_th,
        "topic": topic
    }


def fetch_stock_news_with_status(ticker: str, max_items: int = 4, timeout: int = 6) -> Tuple[List[Dict[str, str]], bool]:
    """
    Fetch the latest news for a ticker. Returns (articles, fetch_ok); fetch_ok is False when the
    feed could not be retrieved or parsed, so callers can tell "no news" from "fetch failed".
    """
    clean_ticker = ticker.strip().upper()
    cached = _get_from_cache(clean_ticker, max_items)
    if cached is not None:
        if _enrich_articles(cached, clean_ticker):
            _update_cache(clean_ticker, cached, max_items, keep_timestamp=True)
        return cached[:max_items], True

    search_query = TICKER_SEARCH_MAP.get(clean_ticker, f"{clean_ticker} stock")
    encoded_q = urllib.parse.quote(search_query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        tree = ET.fromstring(http_get(url, headers=headers, timeout=timeout))
    except (HttpError, ET.ParseError) as e:
        print(f"[news] {clean_ticker}: fetch failed: {e}", file=sys.stderr)
        return [], False

    articles: List[Dict[str, str]] = []
    # Google News search RSS is ordered by relevance; sort so "latest" really means newest.
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    items = sorted(tree.findall(".//item"), key=lambda it: _parse_pub_date(it.findtext("pubDate") or "") or epoch, reverse=True)
    for item in items[:max_items]:
        raw_title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""

        title = raw_title or ""
        source = "News"
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0].strip()
            source = parts[1].strip()

        title = re.sub(r"<[^>]+>", "", title).strip()
        articles.append({
            "title": title,
            "source": source,
            "link": link or "",
            "published": _format_relative_time(pub_date or ""),
            "raw_date": pub_date or "",
            "sentiment": classify_sentiment(title)
        })

    _enrich_articles(articles, clean_ticker)
    _update_cache(clean_ticker, articles, max_items)
    return articles[:max_items], True


def fetch_stock_news(ticker: str, max_items: int = 4, timeout: int = 6) -> List[Dict[str, str]]:
    """Fetch the latest news for a ticker. Returns [] both when there is no news and when the fetch fails."""
    return fetch_stock_news_with_status(ticker, max_items, timeout)[0]


def get_catalyst_breakdown(ticker: str, max_items: int = 4) -> Dict[str, Any]:
    """
    Get news categorized into Bullish Catalysts, Bearish Risks, and All items.
    """
    articles, fetch_ok = fetch_stock_news_with_status(ticker, max_items=max_items)
    for a in articles:
        if "sentiment" not in a:
            a["sentiment"] = classify_sentiment(a.get("title", ""))

    bullish = [a for a in articles if a["sentiment"] == "bullish"]
    bearish = [a for a in articles if a["sentiment"] == "bearish"]
    neutral_or_mixed = [a for a in articles if a["sentiment"] in ("neutral", "mixed")]

    return {
        "ticker": ticker.upper(),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral_or_mixed,
        "all": articles,
        "fetch_ok": fetch_ok
    }


def fetch_batch_news(tickers: List[str], max_items: int = 3, max_workers: int = 5) -> Dict[str, List[Dict[str, str]]]:
    """
    Fetch news for multiple tickers in parallel.
    """
    results: Dict[str, List[Dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_stock_news, t, max_items): t.upper()
            for t in tickers
        }
        for future in as_completed(future_to_ticker):
            t = future_to_ticker[future]
            try:
                results[t] = future.result()
            except Exception:
                results[t] = []
    return results


def fetch_batch_catalysts(tickers: List[str], max_items: int = 4, max_workers: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Fetch categorized catalysts (Bullish vs Bearish) for multiple tickers in parallel.
    """
    results: Dict[str, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(get_catalyst_breakdown, t, max_items): t.upper()
            for t in tickers
        }
        for future in as_completed(future_to_ticker):
            t = future_to_ticker[future]
            try:
                results[t] = future.result()
            except Exception:
                results[t] = {"ticker": t, "bullish": [], "bearish": [], "neutral": [], "all": [], "fetch_ok": False}
    return results
