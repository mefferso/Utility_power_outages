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


## Actual live field audit — October 30, 2026 (20:49 CDT)

Executed the real GitHub Actions job `Audit Entergy public outage fields` against Entergy's public ArcGIS layer:
https://github.com/mefferso/Utility_power_outages/actions/runs/41157150353

- **16 public incidents**: 12 LA, 4 MS.
- **16/16 populated**: title, comments, eventtype (= OUTAGE), identifier, startdate, lastupdated, numpeople, state.
- **0/16 populated**: cause, county, city, status.
- Automated safe keyword scan of **both** title and comments found **0/16** instances of tree/limb/branch/vegetation, pole/crossarm, downed line/wire down/line down, wind/storm/thunderstorm, or lightning.
- Comments were populated but predominantly generic, including outage-related wording. Thus existence of comments does not imply damage descriptions.
- This sampling is current-state only; during major storm restoration, content *could* change. No verified public crew damage feed has been identified.
- Do **not** populate missing cause with title/comments or infer wind damage from geometry/time.
- County/parish mapping could be obtained separately via offline polygon intersection, but that would not solve missing damage evidence.

### Practical path to actual downed-tree and line-damage reports

Obtain an authorized, privacy-screened utility data-sharing feed from Entergy/Cleco outage management or mobile workforce/damage assessment systems. Ask for event ID, incident onset time, crew verification time, approximate location or parish, damage category (tree on line, pole snapped, conductor down), confirmation status, and an optional public-safe description. Explicitly exclude customer PII and exact critical infrastructure locations. A read-only JSON/CSV/SFTP or filtered email feed is adequate; there is no need to request live OMS operator access.

Once confirmed, integrate it as a **separate provenance-tagged provider** with event deduplication, revisions, source errors, and optional email notifications. Keep reports marked preliminary until meteorological corroboration and human review.
