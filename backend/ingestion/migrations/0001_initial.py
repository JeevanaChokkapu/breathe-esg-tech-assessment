# Generated for the assessment prototype. Keep migrations committed so deploys are deterministic.
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EmissionCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("scope", models.CharField(choices=[("scope_1", "Scope 1"), ("scope_2", "Scope 2"), ("scope_3", "Scope 3")], max_length=20)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="UnitConversionReference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("from_unit", models.CharField(max_length=40)),
                ("to_unit", models.CharField(max_length=40)),
                ("factor", models.DecimalField(decimal_places=8, max_digits=18)),
                ("source", models.CharField(max_length=160)),
                ("notes", models.TextField(blank=True)),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_to", models.DateField(blank=True, null=True)),
            ],
            options={"unique_together": {("from_unit", "to_unit", "valid_from")}},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("actor", models.CharField(blank=True, max_length=160)),
                ("event_type", models.CharField(choices=[("ingested", "Ingested"), ("validated", "Validated"), ("updated", "Updated"), ("reviewed", "Reviewed"), ("approved", "Approved"), ("rejected", "Rejected")], max_length=30)),
                ("target_model", models.CharField(max_length=80)),
                ("target_id", models.UUIDField()),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("summary", models.TextField()),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="DataSource",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160)),
                ("source_type", models.CharField(choices=[("sap_csv", "SAP CSV export"), ("utility_csv", "Utility CSV export"), ("travel_json", "Travel JSON API")], max_length=30)),
                ("owner_email", models.EmailField(blank=True, max_length=254)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="data_sources", to="ingestion.tenant")),
            ],
            options={
                "indexes": [models.Index(fields=["tenant", "source_type"], name="ingestion_d_tenant__a6fe4f_idx")],
                "unique_together": {("tenant", "name")},
            },
        ),
        migrations.CreateModel(
            name="RawImportBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("received", "Received"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="received", max_length=20)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("received_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("source_metadata", models.JSONField(blank=True, default=dict)),
                ("data_source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="import_batches", to="ingestion.datasource")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="import_batches", to="ingestion.tenant")),
            ],
            options={"indexes": [models.Index(fields=["tenant", "status", "received_at"], name="ingestion_r_tenant__bb33a0_idx")]},
        ),
        migrations.CreateModel(
            name="RawRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("row_number", models.PositiveIntegerField()),
                ("source_record_id", models.CharField(blank=True, max_length=160)),
                ("raw_payload", models.JSONField()),
                ("parse_errors", models.JSONField(blank=True, default=list)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.rawimportbatch")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.tenant")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "source_record_id"], name="ingestion_r_tenant__ec07af_idx"),
                    models.Index(fields=["tenant", "created_at"], name="ingestion_r_tenant__d805d8_idx"),
                ],
                "unique_together": {("batch", "row_number")},
            },
        ),
        migrations.CreateModel(
            name="NormalizedEmissionRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("activity_date", models.DateField(blank=True, null=True)),
                ("period_start", models.DateField(blank=True, null=True)),
                ("period_end", models.DateField(blank=True, null=True)),
                ("quantity", models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True)),
                ("unit", models.CharField(blank=True, max_length=40)),
                ("normalized_quantity", models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True)),
                ("normalized_unit", models.CharField(blank=True, max_length=40)),
                ("source_reference", models.CharField(blank=True, max_length=160)),
                ("facility_code", models.CharField(blank=True, max_length=80)),
                ("vendor_name", models.CharField(blank=True, max_length=160)),
                ("route", models.JSONField(blank=True, default=dict)),
                ("original_values", models.JSONField(blank=True, default=dict)),
                ("edited_values", models.JSONField(blank=True, default=dict)),
                ("provenance", models.JSONField(blank=True, default=dict)),
                ("review_status", models.CharField(choices=[("pending", "Pending review"), ("needs_changes", "Needs changes"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.CharField(blank=True, max_length=160)),
                ("data_source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="normalized_records", to="ingestion.datasource")),
                ("emission_category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="ingestion.emissioncategory")),
                ("raw_record", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="normalized_record", to="ingestion.rawrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="normalized_records", to="ingestion.tenant")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "review_status"], name="ingestion_n_tenant__09775b_idx"),
                    models.Index(fields=["tenant", "source_reference"], name="ingestion_n_tenant__9c28ee_idx"),
                    models.Index(fields=["tenant", "activity_date"], name="ingestion_n_tenant__2668ab_idx"),
                ]
            },
        ),
        migrations.CreateModel(
            name="ApprovalReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewer", models.CharField(max_length=160)),
                ("decision", models.CharField(choices=[("approved", "Approved"), ("rejected", "Rejected"), ("needs_changes", "Needs changes")], max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("edited_values", models.JSONField(blank=True, default=dict)),
                ("normalized_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_reviews", to="ingestion.normalizedemissionrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_reviews", to="ingestion.tenant")),
            ],
            options={"indexes": [models.Index(fields=["tenant", "reviewer", "created_at"], name="ingestion_a_tenant__6cae07_idx")]},
        ),
        migrations.CreateModel(
            name="ValidationIssue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rule_code", models.CharField(max_length=80)),
                ("severity", models.CharField(choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error")], max_length=20)),
                ("message", models.TextField()),
                ("field", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("open", "Open"), ("resolved", "Resolved"), ("accepted", "Accepted risk")], default="open", max_length=20)),
                ("context", models.JSONField(blank=True, default=dict)),
                ("normalized_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="validation_issues", to="ingestion.normalizedemissionrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="validation_issues", to="ingestion.tenant")),
            ],
            options={"indexes": [models.Index(fields=["tenant", "status", "severity"], name="ingestion_v_tenant__cc5df4_idx")]},
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["tenant", "target_model", "target_id", "occurred_at"], name="ingestion_a_tenant__bd9afd_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["tenant", "event_type", "occurred_at"], name="ingestion_a_tenant__e38208_idx"),
        ),
    ]

