import csv
import json
import logging
import os
from typing import Any, Dict, Iterable, List

from xml.etree.ElementTree import Element, SubElement, ElementTree

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - only used when dependency installed
    Workbook = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

def export_data(rows: Iterable[Dict[str, Any]], output_path: str, fmt: str) -> None:
    rows_list: List[Dict[str, Any]] = list(rows)
    fmt = fmt.lower()
    if fmt == "json":
        _export_json(rows_list, output_path)
    elif fmt == "csv":
        _export_csv(rows_list, output_path)
    elif fmt == "xlsx":
        _export_xlsx(rows_list, output_path)
    elif fmt == "html":
        _export_html(rows_list, output_path)
    elif fmt == "xml":
        _export_xml(rows_list, output_path)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def _export_json(rows: List[Dict[str, Any]], output_path: str) -> None:
    _ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    logger.info("JSON export complete: %s", output_path)

def _export_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
    _ensure_parent_dir(output_path)
    if not rows:
        logger.warning("No data to export to CSV. Creating empty file: %s", output_path)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write("")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    logger.info("CSV export complete: %s", output_path)

def _export_xlsx(rows: List[Dict[str, Any]], output_path: str) -> None:
    if Workbook is None:
        logger.error(
            "openpyxl is not installed. Cannot export XLSX. "
            "Install it with `pip install openpyxl`."
        )
        return

    _ensure_parent_dir(output_path)
    wb = Workbook()
    ws = wb.active
    ws.title = "TikTok Shop Data"

    if not rows:
        wb.save(output_path)
        logger.warning("No data to export to XLSX. Created empty workbook: %s", output_path)
        return

    headers = sorted({key for row in rows for key in row.keys()})
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])

    wb.save(output_path)
    logger.info("XLSX export complete: %s", output_path)

def _export_html(rows: List[Dict[str, Any]], output_path: str) -> None:
    _ensure_parent_dir(output_path)
    if not rows:
        html = "<html><body><p>No data available.</p></body></html>"
    else:
        headers = sorted({key for row in rows for key in row.keys()})
        header_html = "".join(f"<th>{h}</th>" for h in headers)
        rows_html = ""
        for row in rows:
            cells = "".join(f"<td>{row.get(h, '')}</td>" for h in headers)
            rows_html += f"<tr>{cells}</tr>"
        html = (
            "<html><head><meta charset='utf-8'><title>TikTok Shop Data</title></head>"
            "<body><table border='1'><thead><tr>"
            f"{header_html}</tr></thead><tbody>{rows_html}</tbody></table></body></html>"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("HTML export complete: %s", output_path)

def _export_xml(rows: List[Dict[str, Any]], output_path: str) -> None:
    _ensure_parent_dir(output_path)
    root = Element("products")
    for row in rows:
        product_el = SubElement(root, "product")
        for key, value in row.items():
            field_el = SubElement(product_el, key)
            field_el.text = "" if value is None else str(value)

    tree = ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logger.info("XML export complete: %s", output_path)