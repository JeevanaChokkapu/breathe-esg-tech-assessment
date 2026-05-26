# Tradeoffs

## Omission 1: Full Authentication

The prototype uses headers for tenant and analyst identity. A full auth system was omitted because the assignment is about ingestion, auditability, and data modeling. In production, Django auth or SSO would provide tenant membership and actor identity.

## Omission 2: Emissions Calculation

The system normalizes activity data but does not calculate CO2e. This keeps the scope focused on data quality before calculation. Production would add emission factor references, factor versioning, geographic factors, and recalculation audit events.

## Omission 3: Background Jobs

Ingestion runs synchronously inside database transactions. This is simpler to evaluate and easier to reason about. For large uploads, Celery/RQ plus object storage would be added so file receipt and row processing can be retried independently.

