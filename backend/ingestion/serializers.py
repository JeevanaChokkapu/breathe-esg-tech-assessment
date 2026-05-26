from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from ingestion.audit import record_audit_event
from ingestion.models import (
    ApprovalReview,
    AuditEvent,
    DataSource,
    EmissionCategory,
    NormalizedEmissionRecord,
    RawImportBatch,
    RawRecord,
    Tenant,
    UnitConversionReference,
    ValidationIssue,
)
from ingestion.services.validators import persist_validation_issues


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "created_at", "updated_at"]


class EmissionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionCategory
        fields = ["id", "code", "name", "scope", "description"]


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["id", "tenant", "name", "source_type", "owner_email", "metadata", "is_active", "created_at"]
        read_only_fields = ["tenant"]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ["id", "row_number", "source_record_id", "raw_payload", "parse_errors", "created_at"]


class RawImportBatchSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source="data_source.name", read_only=True)

    class Meta:
        model = RawImportBatch
        fields = [
            "id",
            "tenant",
            "data_source",
            "data_source_name",
            "status",
            "original_filename",
            "row_count",
            "received_at",
            "completed_at",
            "error_message",
            "source_metadata",
        ]
        read_only_fields = fields


class ValidationIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationIssue
        fields = ["id", "normalized_record", "rule_code", "severity", "message", "field", "status", "context", "created_at"]


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    raw_record = RawRecordSerializer(read_only=True)
    validation_issues = ValidationIssueSerializer(many=True, read_only=True)
    data_source_name = serializers.CharField(source="data_source.name", read_only=True)
    category = EmissionCategorySerializer(source="emission_category", read_only=True)

    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            "id",
            "tenant",
            "raw_record",
            "data_source",
            "data_source_name",
            "emission_category",
            "category",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "unit",
            "normalized_quantity",
            "normalized_unit",
            "source_reference",
            "facility_code",
            "vendor_name",
            "route",
            "original_values",
            "edited_values",
            "provenance",
            "review_status",
            "locked_at",
            "approved_at",
            "approved_by",
            "validation_issues",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "raw_record", "data_source", "emission_category", "locked_at", "approved_at", "approved_by"]

    def update(self, instance, validated_data):
        if instance.is_locked:
            raise serializers.ValidationError("Approved records are locked for audit.")
        before = {
            "normalized_quantity": str(instance.normalized_quantity),
            "normalized_unit": instance.normalized_unit,
            "review_status": instance.review_status,
        }
        record = super().update(instance, validated_data)
        persist_validation_issues(record)
        request = self.context.get("request")
        record_audit_event(
            tenant=record.tenant,
            actor=getattr(request, "audit_actor", ""),
            event_type=AuditEvent.EventType.UPDATED,
            target=record,
            summary="Analyst updated normalized record values.",
            before=before,
            after=validated_data,
        )
        return record


class ApprovalReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalReview
        fields = ["id", "tenant", "normalized_record", "reviewer", "decision", "notes", "edited_values", "created_at"]
        read_only_fields = ["tenant", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        request_tenant = validated_data.pop("tenant", None)
        record = validated_data["normalized_record"]
        if request_tenant and record.tenant_id != request_tenant.id:
            raise serializers.ValidationError("Record does not belong to the active tenant.")
        if record.is_locked:
            raise serializers.ValidationError("Approved records are locked for audit.")

        edited_values = validated_data.get("edited_values") or {}
        if edited_values:
            for field, value in edited_values.items():
                if not hasattr(record, field):
                    raise serializers.ValidationError({field: "Unknown editable field."})
                setattr(record, field, value)
            record.edited_values = {**record.edited_values, **edited_values}

        decision = validated_data["decision"]
        reviewer = validated_data["reviewer"]
        if decision == ApprovalReview.Decision.APPROVED:
            record.review_status = NormalizedEmissionRecord.ReviewStatus.APPROVED
            record.approved_at = timezone.now()
            record.approved_by = reviewer
            record.locked_at = timezone.now()
            event_type = AuditEvent.EventType.APPROVED
        elif decision == ApprovalReview.Decision.REJECTED:
            record.review_status = NormalizedEmissionRecord.ReviewStatus.REJECTED
            event_type = AuditEvent.EventType.REJECTED
        else:
            record.review_status = NormalizedEmissionRecord.ReviewStatus.NEEDS_CHANGES
            event_type = AuditEvent.EventType.REVIEWED

        record.save()
        review = ApprovalReview.objects.create(tenant=record.tenant, **validated_data)
        persist_validation_issues(record)
        record_audit_event(
            tenant=record.tenant,
            actor=reviewer,
            event_type=event_type,
            target=record,
            summary=f"Record review decision: {decision}.",
            after={"decision": decision, "edited_values": edited_values},
        )
        return review


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "actor", "event_type", "target_model", "target_id", "occurred_at", "summary", "before", "after", "metadata"]


class UnitConversionReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitConversionReference
        fields = "__all__"
