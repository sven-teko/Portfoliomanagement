# Portfoliomanagement

Fondverwaltung mit Yahoo Finance

# Projektziel

Dieses Repository kann Kurs- und Stammdaten von Fonds/ETFs als CSV, XML und JSON sammeln und versionieren.
Die Daten werden über Python yfinance API abgerufen und in einer klaren Ordnerstruktur abgelegt.

# Verwendete Ticker & Datenquellen

Liste der gewünschten Fonds/ETFs:

    "NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ZURN.SW",
    "ABBN.SW","SIKA.SW","LOGN.SW","CFR.SW","SREN.SW",
    "AAPL","AMZN","MSFT","GOOGL","TSLA",
    "META","NVDA","JPM","V","MA",

- [Yahoo Finance](https://finance.yahoo.com) via [yfinance](https://pypi.org/project/yfinance/)
- Repository-CSV

# Datenformat & Schema

Encoding: UTF-8
Trennzeichen: , (Komma)
Dezimaltrenner: . (Punkt)
Datum/Zeit: (DD-MM-YYYY)
Fehlwerte: leer oder NaN

Dateinamen: data/<layer>/<TICKER>.<typ>.csv

# need-to-know

[Download latest Release](https://github.com/sven-teko/Portfoliomanagement/releases)
Python version 3.0.3 wurde verwendet

ausführen setzt "pip install yfinance" vorraus wenn requirements nicht korrekt geladen werden kann.
