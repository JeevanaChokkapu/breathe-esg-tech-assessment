import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation


HEADER_ALIASES = {
    "invoice": "invoice_number",
    "invoice no": "invoice_number",
    "rechnung": "invoice_number",
    "plant": "plant_code",
    "werk": "plant_code",
    "vendor": "vendor_name",
    "lieferant": "vendor_name",
    "date": "activity_date",
    "belegdatum": "activity_date",
    "fuel qty": "quantity",
    "menge": "quantity",
    "unit": "unit",
    "einheit": "unit",
    "meter": "meter_number",
    "kwh": "quantity",
    "usage": "quantity",
    "billing start": "period_start",
    "billing end": "period_end",
    "tariff": "tariff",
}


def parse_decimal(value):
    if value in (None, ""):
        return None
    cleaned = str(value).strip().replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_header(header):
    key = header.strip().lower()
    return HEADER_ALIASES.get(key, key.replace(" ", "_"))


def parse_csv_upload(uploaded_file):
    text = uploaded_file.read().decode("utf-8-sig")
    sample = text[:2048]
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    normalized_headers = [normalize_header(h) for h in reader.fieldnames or []]

    for row_number, raw_row in enumerate(reader, start=2):
        normalized = {}
        for original_key, normalized_key in zip(reader.fieldnames or [], normalized_headers):
            normalized[normalized_key] = raw_row.get(original_key, "").strip()
        yield row_number, raw_row, normalized


def iter_travel_payload(payload):
    expenses = payload.get("expenses", payload if isinstance(payload, list) else [])
    for index, expense in enumerate(expenses, start=1):
        yield index, expense

