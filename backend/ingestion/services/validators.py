from ingestion.models import DataSource, ValidationIssue


KNOWN_AIRPORTS = {"DEL", "BOM", "BLR", "HYD", "MAA", "SFO", "JFK", "LHR", "SIN", "DXB", "FRA"}


def issue(rule_code, severity, message, field="", context=None):
    return {
        "rule_code": rule_code,
        "severity": severity,
        "message": message,
        "field": field,
        "context": context or {},
    }


def validate_record(record):
    issues = []

    if not record.unit:
        issues.append(issue("missing_unit", ValidationIssue.Severity.ERROR, "Activity unit is missing.", "unit"))

    if record.data_source.source_type == DataSource.SourceType.SAP_CSV:
        if record.normalized_quantity and record.normalized_quantity > 50000:
            issues.append(
                issue(
                    "high_fuel_consumption",
                    ValidationIssue.Severity.WARNING,
                    "Fuel quantity is unusually high for a single invoice row.",
                    "normalized_quantity",
                    {"threshold_liters": 50000},
                )
            )

    if record.data_source.source_type == DataSource.SourceType.UTILITY_CSV:
        if record.normalized_quantity is not None and record.normalized_quantity < 0:
            issues.append(issue("negative_electricity", ValidationIssue.Severity.ERROR, "Electricity usage cannot be negative.", "normalized_quantity"))
        if record.period_start and record.period_end and (record.period_end - record.period_start).days > 45:
            issues.append(issue("long_billing_period", ValidationIssue.Severity.WARNING, "Billing period is longer than expected.", "period_end"))

    if record.data_source.source_type == DataSource.SourceType.TRAVEL_JSON:
        origin = (record.route or {}).get("origin")
        destination = (record.route or {}).get("destination")
        if origin == destination and origin:
            issues.append(issue("impossible_route", ValidationIssue.Severity.ERROR, "Travel origin and destination are identical.", "route"))
        for airport in [origin, destination]:
            if airport and airport.upper() not in KNOWN_AIRPORTS:
                issues.append(issue("unknown_airport", ValidationIssue.Severity.WARNING, f"Unknown airport code: {airport}.", "route"))
        if (record.route or {}).get("type") in {"flight", "ground"} and record.normalized_quantity is None:
            issues.append(issue("missing_distance", ValidationIssue.Severity.WARNING, "Travel distance is missing and needs analyst review.", "normalized_quantity"))

    if record.source_reference:
        duplicate_exists = record.__class__.objects.filter(
            tenant=record.tenant,
            data_source=record.data_source,
            source_reference=record.source_reference,
        ).exclude(id=record.id).exists()
        if duplicate_exists:
            issues.append(issue("duplicate_invoice", ValidationIssue.Severity.WARNING, "Source reference already exists for this data source.", "source_reference"))

    return issues


def persist_validation_issues(record):
    ValidationIssue.objects.filter(normalized_record=record).delete()
    created = []
    for data in validate_record(record):
        created.append(ValidationIssue.objects.create(tenant=record.tenant, normalized_record=record, **data))
    return created

