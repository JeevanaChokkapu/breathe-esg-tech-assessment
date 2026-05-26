# Decisions

## Assumptions

- The prototype demonstrates ingestion and review, not full identity management.
- Tenant isolation is represented by `X-Tenant-Slug`; real auth would bind users to tenants.
- The platform stores activity data, not final emissions calculations. Emission factors can be added later.
- Approved rows are locked at the normalized record level.

## Ambiguities Resolved

SAP integration was interpreted as flat-file procurement/fuel exports instead of RFC/BAPI/OData integration. This matches many real early ESG programs where teams receive periodic exports from SAP owners.

Utility data was interpreted as billing CSV from electricity portals. This supports non-calendar billing periods and tariff metadata without requiring utility-specific APIs.

Travel data was interpreted as mocked Concur-style JSON. This lets the prototype cover flights, hotels, ground transport, airport codes, and missing distances without pretending we have a real vendor credential flow.

## Why These Formats

CSV for SAP and utilities is deliberately boring. It creates realistic problems: multilingual headers, malformed dates, inconsistent units, duplicate invoices, and non-calendar periods.

JSON for travel is realistic because modern travel and expense systems expose API payloads with nested route and expense metadata.

## Questions For PM

- Should approval require all validation issues to be resolved, or can analysts approve with accepted risk?
- Which fields are editable by analysts after ingestion?
- What emission factor library should be used, and who owns factor updates?
- Should duplicate detection be tenant-wide, source-wide, or vendor/invoice/date scoped?
- What retention policy applies to raw files and raw row payloads?

