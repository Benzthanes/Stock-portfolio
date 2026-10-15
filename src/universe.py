"""
US Top 100 Stocks Universe (S&P 100 + Nasdaq 100)
Provides ticker symbols with TradingView exchange prefixes (NASDAQ: / NYSE:).
"""

# S&P 100 (OEX) constituents with primary exchange
SP100_TICKERS = {
    "AAPL": "NASDAQ", "ABBV": "NYSE", "ABT": "NYSE", "ACN": "NYSE", "ADBE": "NASDAQ",
    "AIG": "NYSE", "AMD": "NASDAQ", "AMGN": "NASDAQ", "AMT": "NYSE", "AMZN": "NASDAQ",
    "AVGO": "NASDAQ", "AXP": "NYSE", "BA": "NYSE", "BAC": "NYSE", "BNY": "NYSE",
    "BKNG": "NASDAQ", "BLK": "NYSE", "BMY": "NYSE", "BRK.B": "NYSE", "C": "NYSE",
    "CAT": "NYSE", "CHTR": "NASDAQ", "CL": "NYSE", "CMCSA": "NASDAQ", "COF": "NYSE",
    "COP": "NYSE", "COST": "NASDAQ", "CRM": "NYSE", "CSCO": "NASDAQ", "CVS": "NYSE",
    "CVX": "NYSE", "DE": "NYSE", "DHR": "NYSE", "DIS": "NYSE", "DOW": "NYSE",
    "DUK": "NYSE", "EMR": "NYSE", "EXC": "NASDAQ", "F": "NYSE", "FDX": "NYSE",
    "GD": "NYSE", "GE": "NYSE", "GILD": "NASDAQ", "GM": "NYSE", "GOOG": "NASDAQ",
    "GOOGL": "NASDAQ", "GS": "NYSE", "HD": "NYSE", "HON": "NASDAQ", "IBM": "NYSE",
    "INTC": "NASDAQ", "INTU": "NASDAQ", "ISRG": "NASDAQ", "JNJ": "NYSE", "JPM": "NYSE",
    "KHC": "NYSE", "KO": "NYSE", "LIN": "NASDAQ", "LLY": "NYSE", "LMT": "NYSE",
    "LOW": "NYSE", "MA": "NYSE", "MCD": "NYSE", "MDT": "NYSE", "MET": "NYSE",
    "META": "NASDAQ", "MMM": "NYSE", "MO": "NYSE", "MRK": "NYSE", "MS": "NYSE",
    "MSFT": "NASDAQ", "NEE": "NYSE", "NFLX": "NASDAQ", "NKE": "NYSE", "NVDA": "NASDAQ",
    "ORCL": "NYSE", "PEP": "NASDAQ", "PFE": "NYSE", "PG": "NYSE", "PM": "NYSE",
    "PYPL": "NASDAQ", "QCOM": "NASDAQ", "RTX": "NYSE", "SBUX": "NASDAQ", "SCHW": "NYSE",
    "SO": "NYSE", "SPG": "NYSE", "T": "NYSE", "TGT": "NYSE", "TMO": "NYSE",
    "TMUS": "NASDAQ", "TSLA": "NASDAQ", "TXN": "NASDAQ", "UNH": "NYSE", "UNP": "NYSE",
    "UPS": "NYSE", "USB": "NYSE", "V": "NYSE", "VRT": "NYSE", "VZ": "NYSE", "WFC": "NYSE",
    "WMT": "NASDAQ", "XOM": "NYSE"
}

# Nasdaq 100 (NDX) constituents
NASDAQ100_TICKERS = {
    "AAPL": "NASDAQ", "ABNB": "NASDAQ", "ADBE": "NASDAQ", "ADI": "NASDAQ", "ADP": "NASDAQ",
    "ADSK": "NASDAQ", "AEP": "NASDAQ", "AMAT": "NASDAQ", "AMD": "NASDAQ", "AMGN": "NASDAQ",
    "AMZN": "NASDAQ", "APP": "NASDAQ", "ARM": "NASDAQ", "ASML": "NASDAQ",
    "AVGO": "NASDAQ", "AXON": "NASDAQ", "AZN": "NYSE", "BIIB": "NASDAQ", "BKNG": "NASDAQ",
    "BKR": "NASDAQ", "CCEP": "NASDAQ", "CDNS": "NASDAQ", "CDW": "NASDAQ", "CEG": "NASDAQ",
    "CHTR": "NASDAQ", "CPRT": "NASDAQ", "CRWD": "NASDAQ", "CSCO": "NASDAQ", "CSGP": "NASDAQ",
    "CSX": "NASDAQ", "CTAS": "NASDAQ", "CTSH": "NASDAQ", "DASH": "NASDAQ", "DDOG": "NASDAQ",
    "DLTR": "NASDAQ", "DXCM": "NASDAQ", "EXC": "NASDAQ", "FANG": "NASDAQ",
    "FAST": "NASDAQ", "FTNT": "NASDAQ", "GEHC": "NASDAQ", "GFS": "NASDAQ", "GILD": "NASDAQ",
    "GOOG": "NASDAQ", "GOOGL": "NASDAQ", "HON": "NASDAQ", "IDXX": "NASDAQ", "ILMN": "NASDAQ",
    "INTC": "NASDAQ", "INTU": "NASDAQ", "ISRG": "NASDAQ", "KDP": "NASDAQ", "KHC": "NYSE",
    "KLAC": "NASDAQ", "LIN": "NASDAQ", "LRCX": "NASDAQ", "LULU": "NASDAQ", "MAR": "NASDAQ",
    "MCHP": "NASDAQ", "MDB": "NASDAQ", "MDLZ": "NASDAQ", "MELI": "NASDAQ", "META": "NASDAQ",
    "MNST": "NASDAQ", "MRNA": "NASDAQ", "MRVL": "NASDAQ", "MSFT": "NASDAQ", "MSTR": "NASDAQ",
    "MU": "NASDAQ", "NFLX": "NASDAQ", "NVDA": "NASDAQ", "NXPI": "NASDAQ", "ODFL": "NASDAQ",
    "ON": "NASDAQ", "ORLY": "NASDAQ", "PANW": "NASDAQ", "PAYX": "NASDAQ", "PCAR": "NASDAQ",
    "PDD": "NASDAQ", "PEP": "NASDAQ", "PLTR": "NASDAQ", "PYPL": "NASDAQ", "QCOM": "NASDAQ",
    "REGN": "NASDAQ", "ROP": "NASDAQ", "ROST": "NASDAQ", "SBUX": "NASDAQ", "SNPS": "NASDAQ",
    "TEAM": "NASDAQ", "TMUS": "NASDAQ", "TSLA": "NASDAQ", "TTD": "NASDAQ", "TTWO": "NASDAQ",
    "TXN": "NASDAQ", "VRSK": "NASDAQ", "VRTX": "NASDAQ", "WDAY": "NASDAQ",
    "XEL": "NASDAQ", "ZS": "NASDAQ"
}

def get_universe(category: str = "all") -> dict[str, str]:
    """
    Get dictionary mapping {ticker: exchange}.
    category: 'all' (S&P 100 + Nasdaq 100), 'sp100', or 'nasdaq100'
    """
    cat = category.lower().strip()
    if cat == "sp100":
        return dict(SP100_TICKERS)
    elif cat == "nasdaq100":
        return dict(NASDAQ100_TICKERS)
    elif cat == "all":
        # Combine both (S&P 100 primary, Nasdaq 100 added)
        combined = dict(SP100_TICKERS)
        combined.update(NASDAQ100_TICKERS)
        return combined
    else:
        raise ValueError(f"Unknown universe category: {category}. Choose 'all', 'sp100', or 'nasdaq100'.")

def get_tv_symbols(category: str = "all") -> list[str]:
    """
    Get list of symbols formatted for TradingView Scanner (e.g. 'NASDAQ:AAPL', 'NYSE:JPM')
    """
    univ = get_universe(category)
    return [f"{exchange}:{ticker}" for ticker, exchange in sorted(univ.items())]

def resolve_custom_tickers(ticker_list: list[str]) -> list[str]:
    """
    Resolve a list of ticker symbols into TradingView format.
    Accepts raw tickers like 'AAPL', 'BRK.B', or pre-formatted 'NASDAQ:AAPL'.
    If exchange is omitted and unknown, queries both NASDAQ and NYSE candidate prefixes.
    """
    all_univ = get_universe("all")
    symbols = []
    seen = set()

    for item in ticker_list:
        clean = item.strip().upper()
        if not clean:
            continue
        if ":" in clean:
            if clean not in seen:
                seen.add(clean)
                symbols.append(clean)
            continue
        
        # Check known universe
        if clean in all_univ:
            sym = f"{all_univ[clean]}:{clean}"
            if sym not in seen:
                seen.add(sym)
                symbols.append(sym)
        else:
            # Add NASDAQ and NYSE candidate prefixes for unknown ticker
            for ex in ["NASDAQ", "NYSE"]:
                sym = f"{ex}:{clean}"
                if sym not in seen:
                    seen.add(sym)
                    symbols.append(sym)
    return symbols
