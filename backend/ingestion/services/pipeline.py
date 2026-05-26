from django.db import transaction
from django.utils import timezone

from ingestion.audit import record_audit_event
from ingestion.models import AuditEvent, RawImportBatch, RawRecord
from ingestion.services.normalizers import build_sap_record, build_travel_record, build_utility_record
from ingestion.services.parsers import iter_travel_payload, parse_csv_upload
from ingestion.services.validators import persist_validation_issues


@transaction.atomic
def ingest_sap_csv(*, tenant, data_source, uploaded_file, actor=""):
    batch = _create_batch(tenant, data_source, uploaded_file.name)
    try:
        for row_number, raw_row, normalized_row in parse_csv_upload(uploaded_file):
            raw_record = _create_raw_record(tenant, batch, row_number, raw_row, normalized_row.get("invoice_number", ""))
            record = build_sap_record(tenant=tenant, data_source=data_source, raw_record=raw_record, row=normalized_row)
            record.save()
            persist_validation_issues(record)
        return _complete_batch(batch, actor)
    except Exception as exc:
        batch.status = RawImportBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.save(update_fields=["status", "error_message", "updated_at"])
        raise


@transaction.atomic
def ingest_utility_csv(*, tenant, data_source, uploaded_file, actor=""):
    batch = _create_batch(tenant, data_source, uploaded_file.name)
    try:
        for row_number, raw_row, normalized_row in parse_csv_upload(uploaded_file):
            source_id = normalized_row.get("invoice_number") or normalized_row.get("meter_number", "")
            raw_record = _create_raw_record(tenant, batch, row_number, raw_row, source_id)
            record = build_utility_record(tenant=tenant, data_source=data_source, raw_record=raw_record, row=normalized_row)
            record.save()
            persist_validation_issues(record)
        return _complete_batch(batch, actor)
    except Exception as exc:
        batch.status = RawImportBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.save(update_fields=["status", "error_message", "updated_at"])
        raise


@transaction.atomic
def ingest_travel_json(*, tenant, data_source, payload, actor=""):
    batch = _create_batch(tenant, data_source, "travel-api-payload.json", {"transport": "mock_concur_api"})
    try:
        for row_number, expense in iter_travel_payload(payload):
            raw_record = _create_raw_record(tenant, batch, row_number, expense, expense.get("expense_id", ""))
            record = build_travel_record(tenant=tenant, data_source=data_source, raw_record=raw_record, expense=expense)
            record.save()
            persist_validation_issues(record)
        return _complete_batch(batch, actor)
    except Exception as exc:
        batch.status = RawImportBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.save(update_fields=["status", "error_message", "updated_at"])
        raise


def _create_batch(tenant, data_source, filename, metadata=None):
    return RawImportBatch.objects.create(
        tenant=tenant,
        data_source=data_source,
        original_filename=filename,
        source_metadata=metadata or {},
        status=RawImportBatch.Status.PROCESSING,
    )


def _create_raw_record(tenant, batch, row_number, raw_payload, source_record_id):
    return RawRecord.objects.create(
        tenant=tenant,
        batch=batch,
        row_number=row_number,
        source_record_id=source_record_id,
        raw_payload=raw_payload,
    )


def _complete_batch(batch, actor):
    batch.row_count = batch.raw_records.count()
    batch.status = RawImportBatch.Status.COMPLETED
    batch.completed_at = timezone.now()
    batch.save(update_fields=["row_count", "status", "completed_at", "updated_at"])
    record_audit_event(
        tenant=batch.tenant,
        actor=actor,
        event_type=AuditEvent.EventType.INGESTED,
        target=batch,
        summary=f"Ingested {batch.row_count} raw records from {batch.data_source.name}.",
        after={"row_count": batch.row_count, "status": batch.status},
    )
    return batch

