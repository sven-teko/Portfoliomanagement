import sys
import subprocess
import importlib.util
from pathlib import Path

# requirements.txt installieren wenn yfinance fehlt
if importlib.util.find_spec("yfinance") is None:
    print("yfinance nicht gefunden – installiere requirements.txt …")
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
    except Exception as e:
        print(f"Fehler bei der Installation: {e}", file=sys.stderr)
        sys.exit(1)

import yfinance as yf
import time, argparse, json
from datetime import datetime, timezone
import pandas as pd
from utils import write_all_outputs, menu_open_file, logger


# Liste der Ticker
tickers = [
    "NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ZURN.SW",
    "ABBN.SW","SIKA.SW","LOGN.SW","CFR.SW","SREN.SW",
    "AAPL","AMZN","MSFT","GOOGL","TSLA",
    "META","NVDA","JPM","V","MA",
]

# Fetch-helfer

def get_info_safe(t):
    try:
        return t.get_info() or {}
    except Exception:
        try:
            return t.info or {}
        except Exception:
            return {}

def get_history_batch_last30(tickers_list, chunk_size=5):
    result = {t: [] for t in tickers_list}

    def dl(chunk):
        delay = 0.8
        for _ in range(3):
            try:
                df = yf.download(
                    chunk, period="60d", interval="1d",
                    auto_adjust=False, threads=False,
                    progress=False, group_by="ticker"
                )
                if df is None or df.empty:
                    raise RuntimeError("empty")
                return df
            except Exception as e:
                logger.warning(f"Download-Fehler für {chunk}: {e}, retry …")
                time.sleep(delay)
                delay *= 1.6
        return None

    for i in range(0, len(tickers_list), chunk_size):
        chunk = tickers_list[i:i+chunk_size]
        df = dl(chunk)
        if df is None:
            logger.error(f"Chunk fehlgeschlagen: {chunk}")
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
                result[t] = [
                    {
                        "date": idx.tz_localize(None).date().isoformat() if isinstance(idx, pd.Timestamp) else str(idx),
                        "close": float(val)
                    }
                    for idx, val in ser.items()
                ]
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {t}: {e}")
        time.sleep(0.6)
    return result

# Portfolio erstellen

def build_portfolio(print_console: bool):
    as_of = datetime.now(timezone.utc).isoformat()
    meta_map, items = {}, []

    for sym in tickers:
        t = yf.Ticker(sym)
        info = get_info_safe(t)
        meta_map[sym] = {
            "name": info.get("longName") or info.get("shortName") or "",
            "exchange": info.get("fullExchangeName") or info.get("exchange") or "",
            "currency": info.get("currency") or "",
            "industry": info.get("industry") or info.get("sector") or "",
        }
        if print_console:
            print("="*60, f"\nTicker: {sym}")
            for k,v in meta_map[sym].items():
                print(f"{k:9}: {v}")
        time.sleep(0.4)

    closes_map = get_history_batch_last30(tickers)

    for sym in tickers:
        closes = closes_map.get(sym, [])
        if print_console:
            s = pd.Series(
                [c["close"] for c in closes],
                index=pd.to_datetime([c["date"] for c in closes])
            ) if closes else pd.Series(dtype="float64")
            print("Schlusskurse:")
            print(s)
        m = meta_map[sym]
        items.append({
            "symbol": sym, "name": m["name"], "exchange": m["exchange"],
            "currency": m["currency"], "industry": m["industry"],
            "last_30_closes": closes,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        })

    return {"as_of": as_of, "items": items}

# Ausführmodus

def run_text():
    logger.info("Starte run_text Mode")
    obj = build_portfolio(True)
    n_items, n_rows = write_all_outputs(obj)
    logger.info(f"geschrieben: {n_items} Ticker, {n_rows} CSV-Zeilen")
    print(f"geschrieben: data/portfolio.* ({n_items} Ticker, ~{n_rows} Zeilen)")
    menu_open_file()

def run_json():
    logger.info("Starte run_json Mode")
    obj = build_portfolio(False)
    n_items, n_rows = write_all_outputs(obj)
    logger.info(f"geschrieben: {n_items} Ticker, {n_rows} CSV-Zeilen")
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    menu_open_file()

# CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        run_json() if args.json else run_text()
        logger.info("Lauf erfolgreich beendet")
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Netzwerkfehler: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Fehler im Hauptprogramm")
        sys.exit(1)