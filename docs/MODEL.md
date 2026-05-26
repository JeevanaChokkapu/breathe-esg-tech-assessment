# Data Model

## Schema

The backend uses one relational Django app because the assignment is about traceability, validation, and review workflows. PostgreSQL is the production target; SQLite is only a local fallback.

- `Tenant`: owns all tenant-scoped records. A real product would derive this from authentication, but this prototype uses `X-Tenant-Slug` so tenant isolation is easy to inspect.
- `DataSource`: describes the incoming system and format: SAP CSV, utility CSV, or travel JSON. It stores owner and source metadata because analysts often need to contact the upstream owner.
- `RawImportBatch`: one upload or API ingestion event. It captures file name, status, timestamps, row count, and source metadata.
- `RawRecord`: immutable row-level source payload. Normalization never overwrites this record.
- `NormalizedEmissionRecord`: analyst-facing activity row with Scope 1/2/3 category, normalized quantity/unit, provenance, edited values, review status, and approval lock fields.
- `ValidationIssue`: rule output attached to a normalized record. Suspicious rows are flagged, not rejected.
- `ApprovalReview`: analyst decisions and notes. A record can have multiple reviews before final approval.
- `AuditEvent`: immutable append-only history for ingestion, edits, reviews, approvals, and rejections.
- `UnitConversionReference`: explainable conversion metadata. The service currently keeps a small in-code conversion map for speed of the prototype, while the model shows the production reference-table shape.
- `EmissionCategory`: maps activity types to Scope 1, Scope 2, and Scope 3.

## Tenancy

All operational tables include `tenant_id` and queries are scoped by tenant in DRF viewsets. This is simple and visible. PostgreSQL row-level security was not used because it adds deployment complexity that would distract from the assessment; it would be a strong next step for a production multi-tenant system.

## Normalization

Raw records preserve original headers and values. Normalized records store canonical units such as liters, kWh, and km while retaining:

- `original_values`: normalized parser output from the source row.
- `edited_values`: analyst changes applied during review.
- `provenance`: parser name, normalization timestamp, tariff metadata, route metadata, or other source facts.

This split makes the audit story defensible: a reviewer can compare the exact source payload, the normalized interpretation, and any manual correction.

## Auditability

Approved rows set `locked_at` and cannot be edited through serializers. `AuditEvent` rows are append-only in the model. Approval does not delete validation issues; it records the analyst decision so accepted risk remains visible.

## Decisions And Tradeoffs

UUID primary keys were chosen because imported datasets may move between environments and should not expose sequential IDs. The tradeoff is less compact indexes than integers.

JSON fields are used for raw payloads and provenance because source formats vary. The tradeoff is weaker schema enforcement inside those fields, so normalized columns still hold the facts needed for filtering and reporting.

The validation engine is a plain service module. A rules DSL was rejected because the prototype needs readable domain rules more than configurable rule authoring.

