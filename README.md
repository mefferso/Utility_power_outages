# Utility Power Outages — LIX storm-damage research archive

**Research / historical analysis only — not operational, not an official NWS Storm Data source.**

Collect hourly public outage incident observations and search an expanding historical archive by date, county/parish, utility, reported cause, description text, and affected-customer count. Export matching rows to CSV. The dashboard is in `index.html` and `src/app.js`.

## Set up

1. Review and merge the feature pull request to `main`.
2. Obtain a free key at https://massoutage.com/developers and save it under GitHub repository **Settings → Secrets and variables → Actions → New repository secret**, named `MASSOUTAGE_API_KEY`.
3. Run **Actions → Archive utility outage snapshots → Run workflow** to start collection. The workflow is also scheduled hourly (best effort). Each successful run commits monthly JSON archives under `data/`.
4. Enable GitHub Pages with **Settings → Pages → Deploy from branch → main → root**. Dashboard: https://mefferso.github.io/Utility_power_outages/
5. Test with `python -m unittest discover -s tests -v`.

Source: MassOutage `/api/v1/live/counties/{fips}/incidents`, documentation at https://massoutage.com/developers/reference. Public incident availability and reported causes vary by provider; **Cleco-specific incident coverage has not been validated**. MassOutage is an unofficial aggregate, requires attribution (CC BY 4.0), and is rate limited. An API key is strongly recommended.

## Archive methodology and limitations

- The initial 13 LA/MS parishes and counties in `config/counties.json` are a *starter footprint*, not the complete WFO LIX CWA.
- Each record retains collection time, source time when provided, utility, county, public coordinates, cause, crew status, customers affected, start time and ETR when provided.
- Archives are monthly `data/YYYY-MM.json`; each snapshot also stores county-by-county success, stale and error state so failed collections aren't mistaken for zero outages.
- This archives **repeated hourly observations** rather than deduplicating into authoritative incidents. A single outage may appear in several snapshots; positions may be approximate and events between polls may be missed.
- There is **no individual incident backfill before the first successful run**. MassOutage's older county-level historical totals are different from individual damage reports.
- A reported tree contact or outage is a *lead*, not proof of convective wind damage or a verified Local Storm Report. Independently corroborate exact location, timing, cause and meteorological association.
- Future enhancements: historical event grouping, warning polygons/radar overlays, provider-specific feeds, source-coverage dashboard, local CDT/CST display and reviewed LSR candidate export.

This repository is public. Do not store API keys, private customer records, or restricted utility infrastructure information in committed datasets.
