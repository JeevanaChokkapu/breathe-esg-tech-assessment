from django.contrib import admin

from .models import (
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


admin.site.register(Tenant)
admin.site.register(DataSource)
admin.site.register(RawImportBatch)
admin.site.register(RawRecord)
admin.site.register(NormalizedEmissionRecord)
admin.site.register(ValidationIssue)
admin.site.register(ApprovalReview)
admin.site.register(AuditEvent)
admin.site.register(UnitConversionReference)
admin.site.register(EmissionCategory)

