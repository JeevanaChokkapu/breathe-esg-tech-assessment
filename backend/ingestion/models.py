import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimestampedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class EmissionCategory(TimestampedModel):
    class Scope(models.TextChoices):
        SCOPE_1 = "scope_1", "Scope 1"
        SCOPE_2 = "scope_2", "Scope 2"
        SCOPE_3 = "scope_3", "Scope 3"

    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=160)
    scope = models.CharField(max_length=20, choices=Scope.choices)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_scope_display()} - {self.name}"


class DataSource(TimestampedModel):
    class SourceType(models.TextChoices):
        SAP_CSV = "sap_csv", "SAP CSV export"
        UTILITY_CSV = "utility_csv", "Utility CSV export"
        TRAVEL_JSON = "travel_json", "Travel JSON API"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="data_sources")
    name = models.CharField(max_length=160)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    owner_email = models.EmailField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "name")]
        indexes = [models.Index(fields=["tenant", "source_type"], name="ingestion_d_tenant__a6fe4f_idx")]

    def __str__(self):
        return f"{self.tenant.slug}/{self.name}"


class RawImportBatch(TimestampedModel):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="import_batches")
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="import_batches")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    original_filename = models.CharField(max_length=255, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    received_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    source_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "status", "received_at"], name="ingestion_r_tenant__bb33a0_idx")]


class RawRecord(TimestampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="raw_records")
    batch = models.ForeignKey(RawImportBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    source_record_id = models.CharField(max_length=160, blank=True)
    raw_payload = models.JSONField()
    parse_errors = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = [("batch", "row_number")]
        indexes = [
            models.Index(fields=["tenant", "source_record_id"], name="ingestion_r_tenant__ec07af_idx"),
            models.Index(fields=["tenant", "created_at"], name="ingestion_r_tenant__d805d8_idx"),
        ]


class UnitConversionReference(TimestampedModel):
    from_unit = models.CharField(max_length=40)
    to_unit = models.CharField(max_length=40)
    factor = models.DecimalField(max_digits=18, decimal_places=8)
    source = models.CharField(max_length=160)
    notes = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [("from_unit", "to_unit", "valid_from")]


class NormalizedEmissionRecord(TimestampedModel):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        NEEDS_CHANGES = "needs_changes", "Needs changes"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="normalized_records")
    raw_record = models.OneToOneField(RawRecord, on_delete=models.PROTECT, related_name="normalized_record")
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="normalized_records")
    emission_category = models.ForeignKey(EmissionCategory, on_delete=models.PROTECT)
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    normalized_unit = models.CharField(max_length=40, blank=True)
    source_reference = models.CharField(max_length=160, blank=True)
    facility_code = models.CharField(max_length=80, blank=True)
    vendor_name = models.CharField(max_length=160, blank=True)
    route = models.JSONField(default=dict, blank=True)
    original_values = models.JSONField(default=dict, blank=True)
    edited_values = models.JSONField(default=dict, blank=True)
    provenance = models.JSONField(default=dict, blank=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    locked_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=160, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "review_status"], name="ingestion_n_tenant__09775b_idx"),
            models.Index(fields=["tenant", "source_reference"], name="ingestion_n_tenant__9c28ee_idx"),
            models.Index(fields=["tenant", "activity_date"], name="ingestion_n_tenant__2668ab_idx"),
        ]

    @property
    def is_locked(self):
        return self.locked_at is not None

    def clean(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError("period_end cannot be earlier than period_start.")

    def save(self, *args, **kwargs):
        if self.pk:
            locked = NormalizedEmissionRecord.objects.filter(pk=self.pk, locked_at__isnull=False).exists()
            if locked and self.review_status == self.ReviewStatus.APPROVED:
                if kwargs.get("update_fields") is None:
                    raise ValidationError("Approved records are locked for audit.")
                update_fields = set(kwargs.get("update_fields") or [])
                allowed = {"review_status", "updated_at"}
                if not update_fields.issubset(allowed):
                    raise ValidationError("Approved records are locked for audit.")
        super().save(*args, **kwargs)


class ValidationIssue(TimestampedModel):
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        ACCEPTED = "accepted", "Accepted risk"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="validation_issues")
    normalized_record = models.ForeignKey(
        NormalizedEmissionRecord, on_delete=models.CASCADE, related_name="validation_issues"
    )
    rule_code = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    message = models.TextField()
    field = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "status", "severity"], name="ingestion_v_tenant__cc5df4_idx")]


class ApprovalReview(TimestampedModel):
    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        NEEDS_CHANGES = "needs_changes", "Needs changes"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="approval_reviews")
    normalized_record = models.ForeignKey(
        NormalizedEmissionRecord, on_delete=models.CASCADE, related_name="approval_reviews"
    )
    reviewer = models.CharField(max_length=160)
    decision = models.CharField(max_length=20, choices=Decision.choices)
    notes = models.TextField(blank=True)
    edited_values = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "reviewer", "created_at"], name="ingestion_a_tenant__6cae07_idx")]


class AuditEvent(UUIDModel):
    class EventType(models.TextChoices):
        INGESTED = "ingested", "Ingested"
        VALIDATED = "validated", "Validated"
        UPDATED = "updated", "Updated"
        REVIEWED = "reviewed", "Reviewed"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.CharField(max_length=160, blank=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    target_model = models.CharField(max_length=80)
    target_id = models.UUIDField()
    occurred_at = models.DateTimeField(default=timezone.now)
    summary = models.TextField()
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "target_model", "target_id", "occurred_at"], name="ingestion_a_tenant__bd9afd_idx"),
            models.Index(fields=["tenant", "event_type", "occurred_at"], name="ingestion_a_tenant__e38208_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit events are immutable.")
        super().save(*args, **kwargs)
