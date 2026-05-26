from django.core.management.base import BaseCommand

from ingestion.models import DataSource, EmissionCategory, Tenant, UnitConversionReference


class Command(BaseCommand):
    help = "Creates demo tenant, emission categories, data sources, and unit conversions."

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(slug="demo-corp", defaults={"name": "Demo Corp"})

        categories = [
            ("stationary_fuel", "Stationary fuel combustion", EmissionCategory.Scope.SCOPE_1),
            ("purchased_electricity", "Purchased electricity", EmissionCategory.Scope.SCOPE_2),
            ("business_travel", "Business travel", EmissionCategory.Scope.SCOPE_3),
        ]
        for code, name, scope in categories:
            EmissionCategory.objects.get_or_create(code=code, defaults={"name": name, "scope": scope})

        sources = [
            ("SAP Fuel Export", DataSource.SourceType.SAP_CSV, {"module": "SAP MM/FI flat-file export"}),
            ("Utility Portal Export", DataSource.SourceType.UTILITY_CSV, {"portal": "monthly meter CSV"}),
            ("Concur Travel Mock", DataSource.SourceType.TRAVEL_JSON, {"api": "mocked Concur expense payload"}),
        ]
        for name, source_type, metadata in sources:
            DataSource.objects.get_or_create(
                tenant=tenant,
                name=name,
                defaults={"source_type": source_type, "owner_email": "data-owner@example.com", "metadata": metadata},
            )

        conversions = [
            ("gallon", "liter", "3.78541000", "NIST conversion factor"),
            ("mwh", "kwh", "1000.00000000", "Standard metric conversion"),
            ("mile", "km", "1.60934000", "Standard length conversion"),
        ]
        for from_unit, to_unit, factor, source in conversions:
            UnitConversionReference.objects.get_or_create(
                from_unit=from_unit,
                to_unit=to_unit,
                valid_from=None,
                defaults={"factor": factor, "source": source},
            )

        self.stdout.write(self.style.SUCCESS("Seeded demo-corp tenant and reference data."))

