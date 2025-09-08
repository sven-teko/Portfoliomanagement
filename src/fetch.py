import yfinance as yf
import time

tickers = [
    "NESN.SW",   # Nestle
    "NOVN.SW",   # Novartis
    "ROG.SW",    # Roche
    "UBSG.SW",   # UBS
    "ZURN.SW",   # Zürich
    "ABBN.SW",   # ABB
    "SIKA.SW",   # Sika
    "LOGN.SW",   # Logitech
    "CFR.SW",    # Richemont
    "SREN.SW",   # Swiss Re
    "AAPL",      # Apple
    "AMZN",      # Amazon
    "MSFT",      # Microsoft
    "GOOGL",     # Alphabet
    "TSLA",      # Tesla
    "META",      # Meta
    "NVDA",      # Nvidia
    "JPM",       # JPMorgan Chase
    "V",         # Visa
    "MA",        # Mastercard
]


for symbol in tickers:
    print("="*60)
    print(f"Ticker: {symbol}")

    ticker = yf.Ticker(symbol)

    # Metadaten abfragen
    info = ticker.info
    name = info.get("longName") or info.get("shortName")
    exchange = info.get("fullExchangeName") or info.get("exchange")
    currency = info.get("currency")
    industry = info.get("industry") or info.get("sector")

    print(f"Name     : {name}")
    print(f"Börse    : {exchange}")
    print(f"Währung  : {currency}")
    print(f"Branche  : {industry}")

    # Kursdaten der mindestens letzten 30 Handelstage
    history = ticker.history(period="2mo")
    closes = history["Close"].tail(30)

    print("Schlusskurse:")
    print(closes)
    
    time.sleep(0.5)
