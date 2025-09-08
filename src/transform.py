import sys
import json
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

# Einlesen der Daten

def read_input_json(path: str | None) -> dict:
    try:
        if path:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        data = sys.stdin.read()
        if not data.strip():
            raise ValueError("Keine Eingabedaten erhalten")
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON-Fehler beim Einlesen: {e}") from e
    except OSError as e:
        raise SystemExit(f"Dateifehler beim Einlesen: {e}") from e
    except Exception as e:
        raise SystemExit(f"Unerwarteter Fehler beim Einlesen: {e}") from e

def normalize_portfolio(obj: dict) -> dict:
    items = obj.get("items")
    if not isinstance(items, list):
        raise SystemExit("Ungültiges Format: 'items' fehlt.")

    norm_items = []
    for it in items:
        if not isinstance(it, dict):
            continue

        # letzten 30 closes
        closes = []
        for c in (it.get("last_30_closes") or []):
            if not isinstance(c, dict):
                continue
            date_val = str(c.get("date", ""))
            try:
                close_val = float(c.get("close", 0.0))
            except (TypeError, ValueError):
                close_val = 0.0
            closes.append({"date": date_val, "close": close_val})

        norm_items.append({
            "symbol": it.get("symbol", "") or "",
            "name": it.get("name", "") or "",
            # exchange heißt in CSV/XML "market"
            "exchange": it.get("exchange", "") or "",
            "currency": it.get("currency", "") or "",
            "industry": it.get("industry", "") or "",
            "last_30_closes": closes,
            "fetched_at": it.get("fetched_at") or datetime.now(timezone.utc).isoformat()
        })

    return {
        "as_of": obj.get("as_of") or datetime.now(timezone.utc).isoformat(),
        "items": norm_items
    }

# JSON / CSV / XML

def write_json_utf8(obj: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

def write_csv_semicolon(obj: dict, out_path: Path) -> None:
    """
    symbol;name;currency;market;date;close
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["symbol", "name", "currency", "market", "date", "close"])
        for it in obj.get("items", []):
            symbol = it.get("symbol", "")
            name = it.get("name", "")
            currency = it.get("currency", "")
            market = it.get("exchange", "")
            for c in it.get("last_30_closes", []):
                w.writerow([
                    symbol,
                    name,
                    currency,
                    market,
                    c.get("date", ""),
                    c.get("close", ""),
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
        ...
      </position>
      ...
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

        for c in (it.get("last_30_closes") or []):
            cl = ET.SubElement(pos, "close")
            cl.set("date", str(c.get("date", "")))
            # als Attribut "value"; bei Bedarf kann auf Textinhalt geändert werden
            try:
                cl.set("value", f"{float(c.get('close', 0.0))}")
            except (TypeError, ValueError):
                cl.set("value", "0.0")

    _indent_xml(root)
    tree = ET.ElementTree(root)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)

def main():
    p = argparse.ArgumentParser(description="Transformiert Fetch-JSON zu JSON, CSV und XML")
    p.add_argument("--in", dest="in_path", help="Pfad zur Eingabe-JSON (optional; sonst stdin)")
    p.add_argument("--json-out", default="data/portfolio.json", help="Zielpfad JSON (default: data/portfolio.json)")
    p.add_argument("--csv-out",  default="data/portfolio.csv",  help="Zielpfad CSV  (default: data/portfolio.csv)")
    p.add_argument("--xml-out",  default="data/portfolio.xml",  help="Zielpfad XML  (default: data/portfolio.xml)")
    args = p.parse_args()

    raw = read_input_json(args.in_path)
    portfolio = normalize_portfolio(raw)

    try:
        write_json_utf8(portfolio, Path(args.json_out))
        write_csv_semicolon(portfolio, Path(args.csv_out))
        write_xml(portfolio, Path(args.xml_out))
    except Exception as e:
        raise SystemExit(f"Fehler beim Schreiben der Ausgabedateien: {e}") from e

    print(f"geschrieben: {args.json_out}, {args.csv_out}, {args.xml_out}")

if __name__ == "__main__":
    main()
