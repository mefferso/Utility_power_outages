# Direct utility incident source investigation — 2026-10-30

## High-value discovery: Entergy ArcGIS Outages layer

Official-looking public service metadata (verify provider ownership and reuse terms before automating):
https://arcgis.entergy.datacapable.com/arcgis/rest/services/Public/MapServer/1?f=pjson

**Verified from reachable metadata**: layer 1 is named `Outages`, point geometry; capabilities `Map,Query,Data`, with JSON and GeoJSON query formats. Fields include `identifier`, `cause`, `comments`, `startdate`, `enddate`, `etrdate`, `lastupdated`, `numpeople`, `county`, `state`, `city`, and `status`. Service advertises pagination; maximum 1000 records per response.

The open-source project https://github.com/lukesteve03/OpenSourcePowerOutageScraper documents the same Entergy layer and county summary services in `outage-scraper/config/sources_config/datacapable_sources.json`:

- https://entergy.datacapable.com/datacapable/v1/entergy/EntergyLouisiana/county
- https://entergy.datacapable.com/datacapable/v1/entergy/EntergyMississippi/county
- Event layer above: `where=state = 'LA'` or `state = 'MS'`.

**Not yet validated**: actual feature query responses, present-day incidents, coordinate precision, whether `comments`/`cause` are populated, data freshness, permission for scheduled harvesting, and whether any query protections exist. A web-access probe was unable to fetch the query results; metadata alone is NOT proof of live incident accessibility.

IMPORTANT: The layer reports `isDataArchived=false` and `supportsQueryWithHistoricMoment=false`. It should be considered a *current-state source*, not a provider of full 2026 individual incident backfill.

## Cleco

Official public map: https://myaccount.cleco.com/Portal/#/PreOutages
Official FAQ: https://www.cleco.com/residential-commercial/faqs/outage-map-faqs

Verified publicly: outage icons and approximate locations, customers affected, estimated restoration, roughly 10-minute map updates. It does not publicly promise downed-tree cause or crew comments. Cleco says tree contact is a leading cause of outages and downed lines result in emergency service orders.

**Not yet identified**: direct machine-readable Cleco incident endpoint. Avoid guessing KUBRA, Esri or DataCapable without inspecting its actual network requests.

## Immediate validation plan

1. Test Entergy layer with a **small, read-only** ArcGIS REST query limited to public outage fields and a modest resultRecordCount, no private customer/precise infrastructure exports. Respect server terms, authentication and rate limits. Check `error` JSON and `exceededTransferLimit`. Do not automate if access is forbidden.
2. Check if `cause` and `comments` contain actionable descriptions (tree on lines / broken poles), and inspect spatial accuracy and timestamp semantics. Scrub personal data before archival.
3. If verified and reuse permitted, build a separate Entergy connector with captured timestamps, stable identifiers, pagination, normalized public fields, source health, and integration tests. Keep it distinct from MassOutage aggregates.
4. Determine whether authorized Cleco-specific integration is needed; seek direct API/email partnership for crew-confirmed damage descriptions.
5. Distinguish utility-reported outage cause from NWS-verified wind damage. Never automatically generate LSRs from outage events.

## Sources

- Entergy official map entry: https://www.entergy.com/viewoutages
- Entergy outage map explanation: https://www.entergy.com/stormcenter/january-winter-storm-update-1-22-26-7-a-m
- Public ArcGIS metadata: https://arcgis.entergy.datacapable.com/arcgis/rest/services/Public/MapServer/1?f=pjson
- Independent open-source config: https://github.com/lukesteve03/OpenSourcePowerOutageScraper/blob/main/outage-scraper/config/sources_config/datacapable_sources.json
- Cleco outage map FAQ: https://www.cleco.com/residential-commercial/faqs/outage-map-faqs
