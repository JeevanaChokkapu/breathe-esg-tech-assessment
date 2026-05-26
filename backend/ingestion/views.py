from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import (
    ApprovalReview,
    AuditEvent,
    DataSource,
    NormalizedEmissionRecord,
    RawImportBatch,
    Tenant,
    ValidationIssue,
)
from ingestion.serializers import (
    ApprovalReviewSerializer,
    AuditEventSerializer,
    DataSourceSerializer,
    NormalizedEmissionRecordSerializer,
    RawImportBatchSerializer,
    TenantSerializer,
    ValidationIssueSerializer,
)
from ingestion.services.pipeline import ingest_sap_csv, ingest_travel_json, ingest_utility_csv


def get_tenant_from_request(request):
    slug = request.headers.get("X-Tenant-Slug") or request.query_params.get("tenant")
    if not slug:
        raise ValidationError("Provide tenant via X-Tenant-Slug header or tenant query parameter.")
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist as exc:
        raise NotFound("Tenant not found.") from exc


class TenantScopedViewSet(viewsets.ModelViewSet):
    tenant_field = "tenant"

    def get_tenant(self):
        return get_tenant_from_request(self.request)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{self.tenant_field: self.get_tenant()})

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSerializer


class DataSourceViewSet(TenantScopedViewSet):
    queryset = DataSource.objects.select_related("tenant").order_by("name")
    serializer_class = DataSourceSerializer


class RawImportBatchViewSet(TenantScopedViewSet):
    queryset = RawImportBatch.objects.select_related("tenant", "data_source").order_by("-received_at")
    serializer_class = RawImportBatchSerializer


class NormalizedEmissionRecordViewSet(TenantScopedViewSet):
    queryset = (
        NormalizedEmissionRecord.objects.select_related("tenant", "raw_record", "data_source", "emission_category")
        .prefetch_related("validation_issues")
        .order_by("-created_at")
    )
    serializer_class = NormalizedEmissionRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        suspicious = self.request.query_params.get("suspicious")
        if status_filter:
            queryset = queryset.filter(review_status=status_filter)
        if suspicious == "true":
            queryset = queryset.filter(validation_issues__status=ValidationIssue.Status.OPEN).distinct()
        return queryset


class ValidationIssueViewSet(TenantScopedViewSet):
    queryset = ValidationIssue.objects.select_related("tenant", "normalized_record").order_by("-created_at")
    serializer_class = ValidationIssueSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        record_id = self.request.query_params.get("record")
        if record_id:
            queryset = queryset.filter(normalized_record_id=record_id)
        return queryset


class ApprovalReviewViewSet(TenantScopedViewSet):
    queryset = ApprovalReview.objects.select_related("tenant", "normalized_record").order_by("-created_at")
    serializer_class = ApprovalReviewSerializer


class AuditEventViewSet(TenantScopedViewSet):
    queryset = AuditEvent.objects.select_related("tenant").order_by("-occurred_at")
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        target_id = self.request.query_params.get("target_id")
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        return queryset


class BaseIngestView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    expected_source_type = None

    def get_data_source(self, request, tenant):
        source_id = request.data.get("data_source")
        if not source_id:
            raise ValidationError("data_source is required.")
        try:
            return DataSource.objects.get(id=source_id, tenant=tenant, source_type=self.expected_source_type, is_active=True)
        except DataSource.DoesNotExist as exc:
            raise NotFound("Active data source not found for tenant and source type.") from exc


class SapCsvIngestView(BaseIngestView):
    expected_source_type = DataSource.SourceType.SAP_CSV

    def post(self, request):
        tenant = get_tenant_from_request(request)
        data_source = self.get_data_source(request, tenant)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError("CSV file is required.")
        batch = ingest_sap_csv(tenant=tenant, data_source=data_source, uploaded_file=uploaded_file, actor=request.audit_actor)
        return Response(RawImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class UtilityCsvIngestView(BaseIngestView):
    expected_source_type = DataSource.SourceType.UTILITY_CSV

    def post(self, request):
        tenant = get_tenant_from_request(request)
        data_source = self.get_data_source(request, tenant)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError("CSV file is required.")
        batch = ingest_utility_csv(tenant=tenant, data_source=data_source, uploaded_file=uploaded_file, actor=request.audit_actor)
        return Response(RawImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class TravelJsonIngestView(BaseIngestView):
    expected_source_type = DataSource.SourceType.TRAVEL_JSON

    def post(self, request):
        tenant = get_tenant_from_request(request)
        data_source = self.get_data_source(request, tenant)
        batch = ingest_travel_json(tenant=tenant, data_source=data_source, payload=request.data, actor=request.audit_actor)
        return Response(RawImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
