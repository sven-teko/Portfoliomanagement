# Portfoliomanagement

Fondverwaltung mit Yahoo Finance

# Projektziel

Dieses Repository kann Kurs- und Stammdaten von Fonds/ETFs als CSV, XML und JSON sammeln und versionieren.
Die Daten werden über das Python-Paket yfinance API abgerufen und in einer klaren Ordnerstruktur abgelegt.

# Verwendete Ticker & Datenquellen

Liste der gewünschten Fonds/ETFs:


- Yahoo Finance via yfinance
- Repository-CSV

# Datenformat & Schema

Encoding: UTF-8
Trennzeichen: , (Komma)
Dezimaltrenner: . (Punkt)
Datum/Zeit: (DD-MM-YYYY)
Fehlwerte: leer oder NaN

Dateinamen: data/<layer>/<TICKER>.<typ>.csv