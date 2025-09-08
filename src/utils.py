import json
import csv
from pathlib import Path
import xml.etree.ElementTree as ET
import platform
import subprocess
import logging

# Logging
logging.basicConfig(
    filename="fetch.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)

logger = logging.getLogger(__name__)



# Schreibt abgerufene Daten

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
                w.writerow([symbol, name, currency, market, c.get("date",""), c.get("close","")])

def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip(): elem.text = i + "  "
        for child in elem: _indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip(): elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()): elem.tail = i

def write_xml(obj: dict, out_path: Path) -> None:
    root = ET.Element("portfolio")
    if obj.get("as_of"): root.set("as_of", obj["as_of"])
    for it in obj.get("items", []):
        pos = ET.SubElement(root, "position")
        pos.set("symbol", str(it.get("symbol","")))
        pos.set("name", str(it.get("name","")))
        pos.set("currency", str(it.get("currency","")))
        pos.set("market", str(it.get("exchange","")))
        for c in it.get("last_30_closes", []):
            cl = ET.SubElement(pos, "close")
            cl.set("date", str(c.get("date","")))
            try: cl.set("value", f"{float(c.get('close',0.0))}")
            except (TypeError, ValueError): cl.set("value","0.0")
    _indent_xml(root)
    ensure_outdir(out_path)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)

def write_all_outputs(portfolio_obj: dict) -> tuple[int, int]:
    write_json_utf8(portfolio_obj, Path("data/portfolio.json"))
    write_csv_semicolon(portfolio_obj, Path("data/portfolio.csv"))
    write_xml(portfolio_obj, Path("data/portfolio.xml"))
    n_items = len(portfolio_obj.get("items", []))
    n_rows = sum(len(it.get("last_30_closes", [])) or 1 for it in portfolio_obj.get("items", []))
    return n_items, n_rows

# Explorer öffnen

def open_in_explorer(file_path: Path) -> None:
    p = file_path.resolve()
    sys = platform.system()
    try:
        if sys == "Windows":
            subprocess.run(["explorer", "/select,", str(p)], check=False)
        elif sys == "Darwin":
            subprocess.run(["open", "-R", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p.parent)], check=False)
    except Exception as e:
        logging.error(f"Explorer öffnen fehlgeschlagen: {e}")

def menu_open_file():
    print("-"*28)
    print("- a : portfolio.csv")
    print("- b : portfolio.xml")
    print("- c : portfolio.json")
    print("-"*28)
    ch = input("Welche Datei im Explorer öffnen? [a/b/c] ").strip().lower()
    if ch.startswith("a"): open_in_explorer(Path("data/portfolio.csv"))
    elif ch.startswith("b"): open_in_explorer(Path("data/portfolio.xml"))
    elif ch.startswith("c"): open_in_explorer(Path("data/portfolio.json"))
    else: print("Keine gültige Auswahl.")
