from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ingestion import views
from ingestion.views import frontend
from django.urls import path

urlpatterns = [
    path("", frontend),
]
router = DefaultRouter()
router.register("tenants", views.TenantViewSet, basename="tenant")
router.register("data-sources", views.DataSourceViewSet, basename="data-source")
router.register("batches", views.RawImportBatchViewSet, basename="batch")
router.register("records", views.NormalizedEmissionRecordViewSet, basename="record")
router.register("issues", views.ValidationIssueViewSet, basename="issue")
router.register("reviews", views.ApprovalReviewViewSet, basename="review")
router.register("audit-events", views.AuditEventViewSet, basename="audit-event")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/ingest/sap-csv/", views.SapCsvIngestView.as_view(), name="sap-csv-ingest"),
    path("api/ingest/utility-csv/", views.UtilityCsvIngestView.as_view(), name="utility-csv-ingest"),
    path("api/ingest/travel-json/", views.TravelJsonIngestView.as_view(), name="travel-json-ingest"),
]

