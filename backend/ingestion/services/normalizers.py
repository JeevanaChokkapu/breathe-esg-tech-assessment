from decimal import Decimal

from django.utils import timezone

from ingestion.models import DataSource, EmissionCategory, NormalizedEmissionRecord
from ingestion.services.parsers import parse_date, parse_decimal


UNIT_ALIASES = {
    "l": "liter",
    "ltr": "liter",
    "litre": "liter",
    "liters": "liter",
    "gal": "gallon",
    "gallons": "gallon",
    "kwh": "kwh",
    "mwh": "mwh",
    "km": "km",
    "mi": "mile",
}

CONVERSION_TO_BASE = {
    ("gallon", "liter"): Decimal("3.78541"),
    ("mwh", "kwh"): Decimal("1000"),
    ("mile", "km"): Decimal("1.60934"),
}


def canonical_unit(unit):
    if not unit:
        return ""
    return UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def normalize_quantity(quantity, unit, target_unit):
    if quantity is None:
        return None
    source_unit = canonical_unit(unit)
    if source_unit == target_unit:
        return quantity
    factor = CONVERSION_TO_BASE.get((source_unit, target_unit))
    return quantity * factor if factor else quantity


def category_for_source(source_type):
    if source_type == DataSource.SourceType.UTILITY_CSV:
        return EmissionCategory.objects.get(code="purchased_electricity")
    if source_type == DataSource.SourceType.TRAVEL_JSON:
        return EmissionCategory.objects.get(code="business_travel")
    return EmissionCategory.objects.get(code="stationary_fuel")


def build_sap_record(*, tenant, data_source, raw_record, row):
    quantity = parse_decimal(row.get("quantity"))
    unit = canonical_unit(row.get("unit"))
    normalized_quantity = normalize_quantity(quantity, unit, "liter")
    category = category_for_source(DataSource.SourceType.SAP_CSV)
    return NormalizedEmissionRecord(
        tenant=tenant,
        raw_record=raw_record,
        data_source=data_source,
        emission_category=category,
        activity_date=parse_date(row.get("activity_date")),
        quantity=quantity,
        unit=unit,
        normalized_quantity=normalized_quantity,
        normalized_unit="liter",
        source_reference=row.get("invoice_number", ""),
        facility_code=row.get("plant_code", ""),
        vendor_name=row.get("vendor_name", ""),
        original_values=row,
        provenance={"normalized_at": timezone.now().isoformat(), "parser": "sap_csv"},
    )


def build_utility_record(*, tenant, data_source, raw_record, row):
    quantity = parse_decimal(row.get("quantity"))
    unit = canonical_unit(row.get("unit") or "kwh")
    normalized_quantity = normalize_quantity(quantity, unit, "kwh")
    category = category_for_source(DataSource.SourceType.UTILITY_CSV)
    return NormalizedEmissionRecord(
        tenant=tenant,
        raw_record=raw_record,
        data_source=data_source,
        emission_category=category,
        period_start=parse_date(row.get("period_start")),
        period_end=parse_date(row.get("period_end")),
        activity_date=parse_date(row.get("period_end")),
        quantity=quantity,
        unit=unit,
        normalized_quantity=normalized_quantity,
        normalized_unit="kwh",
        source_reference=row.get("invoice_number") or row.get("meter_number", ""),
        facility_code=row.get("plant_code", ""),
        vendor_name=row.get("utility_name", ""),
        original_values=row,
        provenance={"tariff": row.get("tariff", ""), "normalized_at": timezone.now().isoformat(), "parser": "utility_csv"},
    )


def build_travel_record(*, tenant, data_source, raw_record, expense):
    category = category_for_source(DataSource.SourceType.TRAVEL_JSON)
    expense_type = expense.get("type", "")
    distance = parse_decimal(expense.get("distance"))
    distance_unit = canonical_unit(expense.get("distance_unit") or "km")
    normalized_distance = normalize_quantity(distance, distance_unit, "km")
    return NormalizedEmissionRecord(
        tenant=tenant,
        raw_record=raw_record,
        data_source=data_source,
        emission_category=category,
        activity_date=parse_date(expense.get("transaction_date") or expense.get("start_date")),
        quantity=distance,
        unit=distance_unit,
        normalized_quantity=normalized_distance,
        normalized_unit="km" if expense_type in {"flight", "ground"} else "night",
        source_reference=expense.get("expense_id", ""),
        vendor_name=expense.get("vendor", ""),
        route={"origin": expense.get("origin"), "destination": expense.get("destination"), "type": expense_type},
        original_values=expense,
        provenance={"normalized_at": timezone.now().isoformat(), "parser": "travel_json"},
    )

