# Sources And Prototype Limits

## SAP Exports

The SAP source is modeled as procurement/fuel CSV because enterprise ESG teams commonly receive periodic flat-file exports from SAP modules rather than direct transactional API access during early implementation. The parser handles multilingual headers such as German `Werk`, `Lieferant`, `Menge`, and `Einheit`, inconsistent units, plant codes, vendor names, and malformed dates.

## Utility Exports

Electricity portals commonly expose billing-period CSV exports with meter identifiers, usage quantities, tariffs, and invoice references. The model supports `period_start` and `period_end` because billing cycles often do not match calendar months.

## Concur/Navan-Style Travel

The travel source is mocked as JSON because travel platforms expose structured expense and itinerary data through APIs. The prototype handles flights, hotels, ground transport, airport codes, routes, and missing distance values.

## Limitations

This repository does not include vendor credentials, real SAP connectivity, utility-specific portal adapters, or actual Concur/Navan API clients. It intentionally focuses on the ingestion contract, row-level provenance, validation, review, and audit workflow.

