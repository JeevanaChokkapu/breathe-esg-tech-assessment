from .models import AuditEvent


def record_audit_event(*, tenant, actor="", event_type, target, summary, before=None, after=None, metadata=None):
    return AuditEvent.objects.create(
        tenant=tenant,
        actor=actor or "",
        event_type=event_type,
        target_model=target.__class__.__name__,
        target_id=target.id,
        summary=summary,
        before=before or {},
        after=after or {},
        metadata=metadata or {},
    )

