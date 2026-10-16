"""
Display formatting for money and percentages: the sign always precedes the currency symbol.
"""
from typing import Optional

SYMBOLS = {"USD": "$", "THB": "฿", "$": "$", "฿": "฿"}

FMT_MONEY_JS = """function fmtMoney(v, sym, signed) {
    if (v === null || v === undefined || isNaN(v)) return '-';
    var a = Math.abs(v).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    var zero = a === '0.00';
    var sign = (v < 0 && !zero) ? '-' : ((signed && v > 0 && !zero) ? '+' : '');
    return sign + (sym === undefined ? '$' : sym) + a;
}
function fmtPct(v, digits) {
    if (v === null || v === undefined || isNaN(v)) return '-';
    var d = digits === undefined ? 1 : digits;
    var a = Math.abs(v).toFixed(d);
    var zero = parseFloat(a) === 0;
    return (zero ? '' : (v < 0 ? '-' : '+')) + a + '%';
}"""


def symbol(ccy: str) -> str:
    return SYMBOLS.get(ccy, ccy)


def _sign(v: float, digits: int, show_plus: bool) -> str:
    if round(abs(v), digits) == 0:
        return ""
    if v < 0:
        return "-"
    return "+" if show_plus else ""


def money(v: Optional[float], ccy: str = "USD", signed: bool = False, digits: int = 2, na: str = "-") -> str:
    """money(-356.38) -> '-$356.38'; money(1234, 'THB') -> '฿1,234.00'; money(None) -> '-'."""
    if v is None:
        return na
    v = float(v)
    return f"{_sign(v, digits, signed)}{symbol(ccy)}{abs(v):,.{digits}f}"


def pct(v: Optional[float], signed: bool = True, digits: int = 1, na: str = "-") -> str:
    """pct(4.2) -> '+4.2%'; pct(-4.2) -> '-4.2%'; pct(None) -> '-'."""
    if v is None:
        return na
    v = float(v)
    return f"{_sign(v, digits, signed)}{abs(v):.{digits}f}%"


def signed(v: Optional[float], digits: int = 2) -> str:
    """signed(3.5) -> '+3.50'; signed(-3.5) -> '-3.50'; signed(None) -> '-'."""
    if v is None:
        return "-"
    v = float(v)
    return f"{_sign(v, digits, True)}{abs(v):,.{digits}f}"


def num(v: Optional[float], digits: int = 2) -> str:
    """Plain thousands-separated number; None -> '-'."""
    if v is None:
        return "-"
    return f"{float(v):,.{digits}f}"
