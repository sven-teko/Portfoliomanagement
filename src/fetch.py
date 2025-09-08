import yfinance as yf
import time
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import csv
import xml.etree.ElementTree as ET
import platform
import subprocess

# Liste der Ticker
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


def get_info_safe(ticker_obj):
    info = {}
    try:
        info = ticker_obj.get_info()
    except Exception:
        try:
            info = ticker_obj.info
        except Exception:
            info = {}
    return info or {}

def get_history_batch_last30(tickers_list, chunk_size=5):
    
    result = {t: [] for t in tickers_list}

    def download_chunk(chunk):
        delay = 0.8
        for _ in range(3):
            try:
                df = yf.download(
                    tickers=chunk,
                    period="60d",
                    interval="1d",
                    auto_adjust=False,
                    threads=False,
                    progress=False,
                    group_by="ticker",
                )
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    raise RuntimeError("Leerer Download-Frame")
                return df
            except Exception:
                time.sleep(delay)
                delay *= 1.6
        return None

    # in Chunks laden
    for i in range(0, len(tickers_list), chunk_size):
        chunk = tickers_list[i:i+chunk_size]
        df = download_chunk(chunk)
        if df is None:
            continue

        for t in chunk:
            try:
                if isinstance(df.columns, pd.MultiIndex):
                    if (t, "Close") not in df.columns:
                        continue
                    ser = df[(t, "Close")].dropna().tail(30)
                else:
                    if "Close" not in df.columns:
                        continue
                    ser = df["Close"].dropna().tail(30)
                closes = []
                for idx, val in ser.items():
                    if isinstance(idx, pd.Timestamp):
                        d = idx.tz_localize(None).date().isoformat()
                    else:
                        d = str(idx)
                    closes.append({"date": d, "close": float(val)})
                result[t] = closes
            except Exception:
                pass

        # kleine Pause damit Yahoo nicht überlastet ist
        time.sleep(0.6)

    return result


# Writer

def ensure_outdir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def write_json_utf8(obj: dict, out_path: Path) -> None:
    ensure_outdir(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

def write_csv_semicolon(obj: dict, out_path: Path) -> None:
    ensure_outdir(out_path)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["symbol", "name", "currency", "market", "date", "close"])
        for it in obj.get("items", []):
            symbol  = it.get("symbol", "")
            name    = it.get("name", "")
            currency= it.get("currency", "")
            market  = it.get("exchange", "")
            closes  = it.get("last_30_closes", [])
            if not closes:
                w.writerow([symbol, name, currency, market, "", ""])
                continue
            for c in closes:
                w.writerow([
                    symbol, name, currency, market,
                    c.get("date", ""), c.get("close", "")
                ])


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def write_xml(obj: dict, out_path: Path) -> None:
    """
    <portfolio as_of="...">
      <position symbol="..." name="..." currency="..." market="...">
        <close date="YYYY-MM-DD" value="123.45"/>
      </position>
    </portfolio>
    """
    root = ET.Element("portfolio")
    as_of = obj.get("as_of", "")
    if as_of:
        root.set("as_of", as_of)

    for it in obj.get("items", []):
        pos = ET.SubElement(root, "position")
        pos.set("symbol", str(it.get("symbol", "")))
        pos.set("name", str(it.get("name", "")))
        pos.set("currency", str(it.get("currency", "")))
        pos.set("market", str(it.get("exchange", "")))

        closes = it.get("last_30_closes", [])
        for c in closes:
            cl = ET.SubElement(pos, "close")
            cl.set("date", str(c.get("date", "")))
            try:
                cl.set("value", f"{float(c.get('close', 0.0))}")
            except (TypeError, ValueError):
                cl.set("value", "0.0")

    _indent_xml(root)
    tree = ET.ElementTree(root)
    ensure_outdir(out_path)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)

def write_all_outputs(portfolio_obj: dict) -> None:
    write_json_utf8(portfolio_obj, Path("data/portfolio.json"))
    write_csv_semicolon(portfolio_obj, Path("data/portfolio.csv"))
    write_xml(portfolio_obj, Path("data/portfolio.xml"))

#  Explorer-Öffnen

def open_in_explorer(file_path: Path) -> None:
    file_path = file_path.resolve()
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["explorer", "/select,", str(file_path)], check=False)
        elif system == "Darwin":
            subprocess.run(["open", "-R", str(file_path)], check=False)
        else:
            subprocess.run(["xdg-open", str(file_path.parent)], check=False)
    except Exception as e:
        print(f"Konnte den Explorer nicht öffnen: {e}")

def menu_open_file():
    print("-" * 28)
    print("- a : portfolio.csv")
    print("- b : portfolio.xml")
    print("- c : portfolio.json")
    print("-" * 28)
    choice = input("Welche Datei im Explorer öffnen? [a/b/c] ").strip().lower()
    if choice.startswith("a"):
        open_in_explorer(Path("data/portfolio.csv"))
    elif choice.startswith("b"):
        open_in_explorer(Path("data/portfolio.xml"))
    elif choice.startswith("c"):
        open_in_explorer(Path("data/portfolio.json"))
    else:
        print("Keine gültige Auswahl. Überspringe das Öffnen.")

#  Laufmodi

def build_portfolio_object(print_to_console: bool) -> dict:
    
    # Metadaten holen und darstellen

    as_of = datetime.now(timezone.utc).isoformat()
    portfolio_items = []


    meta_map = {}
    for symbol in tickers:
        t = yf.Ticker(symbol)
        info = get_info_safe(t)
        meta_map[symbol] = {
            "name": (info.get("longName") or info.get("shortName") or ""),
            "exchange": (info.get("fullExchangeName") or info.get("exchange") or ""),
            "currency": (info.get("currency") or ""),
            "industry": (info.get("industry") or info.get("sector") or ""),
        }
        if print_to_console:
            print("=" * 60)
            print(f"Ticker: {symbol}")
            print(f"Name     : {meta_map[symbol]['name']}")
            print(f"Börse    : {meta_map[symbol]['exchange']}")
            print(f"Währung  : {meta_map[symbol]['currency']}")
            print(f"Branche  : {meta_map[symbol]['industry']}")
        time.sleep(0.4)

    # Kurse im Batch für alle 20 kombinieren
    closes_map = get_history_batch_last30(tickers)

    for symbol in tickers:
        closes = closes_map.get(symbol, [])
        if print_to_console:
            if closes:
                s = pd.Series(
                    data=[c["close"] for c in closes],
                    index=pd.to_datetime([c["date"] for c in closes])
                )
            else:
                s = pd.Series(dtype="float64")
            print("Schlusskurse:")
            print(s)

        m = meta_map.get(symbol, {})
        portfolio_items.append({
            "symbol": symbol,
            "name": m.get("name", ""),
            "exchange": m.get("exchange", ""),
            "currency": m.get("currency", ""),
            "industry": m.get("industry", ""),
            "last_30_closes": closes,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        })

    return {"as_of": as_of, "items": portfolio_items}

def run_text_mode():
    portfolio_obj = build_portfolio_object(print_to_console=True)
    write_all_outputs(portfolio_obj)
    print("geschrieben: data/portfolio.json, data/portfolio.csv, data/portfolio.xml")
    menu_open_file()

def run_json_mode():
    portfolio_obj = build_portfolio_object(print_to_console=False)
    write_all_outputs(portfolio_obj)
    print(json.dumps(portfolio_obj, ensure_ascii=False, indent=2))
    menu_open_file()

# CLI erstellen

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Ticker-Daten via yfinance")
    parser.add_argument("--json", action="store_true", help="JSON-Ausgabe zusätzlich zur Datei-Aktualisierung")
    args = parser.parse_args()

    if args.json:
        run_json_mode()
    else:
        run_text_mode()
