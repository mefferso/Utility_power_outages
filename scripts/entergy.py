"""Read-only Entergy public ArcGIS incident collector.

Only public coarse geolocations and outage information are retained.
No street address, ZIP, customer details or raw crew comments are stored.
This is not a verified damage or NWS reporting feed.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://arcgis.entergy.datacapable.com/arcgis/rest/services/Public/MapServer/1/query"
STATES = ("LA", "MS")
FIELDS = "identifier,cause,startdate,enddate,etrdate,lastupdated,numpeople,county,state,city,status"
UTC = dt.timezone.utc


def query(state, offset=0, page_size=500, opener=None):
    """Query only published non-address fields, capped per request."""
    if state not in STATES:
        raise ValueError("Unsupported state")
    params = {
        "where": "state = '%s'" % state, "outFields": FIELDS, "returnGeometry": "true",
        "outSR": 4326, "resultOffset": offset, "resultRecordCount": min(page_size, 500),
        "f": "geojson",
    }
    url = URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Accept": "application/geo+json, application/json", "User-Agent": "LIXOutageResearch/1.0"})
    with (opener or urllib.request.urlopen)(request, timeout=25) as stream:
        payload = json.load(stream)
    if isinstance(payload, dict) and "error" in payload:
        raise RuntimeError("ArcGIS returned error: " + str(payload["error"].get("message", "Unknown"))[:120])
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("Unexpected ArcGIS GeoJSON response")
    return payload


def iso_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v / 1000, UTC).isoformat().replace("+00:00", "Z")
    return str(v)


def normalized(feature, seen_at):
    prop = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    lon, lat = (coords[:2] if len(coords) >= 2 else (None, None))
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        lat = lon = None
    # Snap coordinates to ~1 km: public map points may otherwise reveal infrastructure locations.
    lat = round(lat, 2) if lat is not None else None
    lon = round(lon, 2) if lon is not None else None
    return {
        "observed_at": seen_at, "source_as_of": iso_date(prop.get("lastupdated")),
        "fips": None, "county": prop.get("county"), "state": prop.get("state"),
        "utility_key": "entergy", "utility": "Entergy",
        "lat": lat, "lon": lon, "customers_out": prop.get("numpeople"),
        "cause": prop.get("cause"), "crew_status": prop.get("status"),
        "started_at": iso_date(prop.get("startdate")), "etr": iso_date(prop.get("etrdate")),
        "incident_id": prop.get("identifier"),
        "source": "Entergy public ArcGIS outage map", "source_url": URL,
        "verification": "unverified_public_outage"
    }


def collect(getter=query, max_pages=20):
    now = dt.datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshots, coverage = [], []
    for state in STATES:
        count = 0
        try:
            for page in range(max_pages):
                payload = getter(state, page * 500)
                features = payload["features"]
                snapshots.extend(normalized(f, now) for f in features)
                count += len(features)
                if len(features) < 500 and not payload.get("exceededTransferLimit"):
                    break
            else:
                raise RuntimeError("Pagination limit reached; data might be incomplete")
            coverage.append({"state": state, "status": "ok", "incident_count": count})
        except Exception as exc:
            # Discard incomplete state instead of publishing partial results as complete.
            snapshots = [s for s in snapshots if s["state"] != state]
            coverage.append({"state": state, "status": "error", "incident_count": None, "error": str(exc)[:180]})
    return now, snapshots, coverage


def write(now, incidents, coverage, root=ROOT):
    if not any(c["status"] == "ok" for c in coverage):
        raise RuntimeError("No state succeeded; refusing to overwrite archive")
    folder = root / "data" / "entergy"
    folder.mkdir(parents=True, exist_ok=True)
    month = now[:7]
    path = folder / (month + ".json")
    existing = json.loads(path.read_text()) if path.exists() else {"schema_version": 1, "snapshots": []}
    slot = now[:13]
    existing["snapshots"] = [s for s in existing["snapshots"] if s["collected_at"][:13] != slot] + [{"collected_at": now, "coverage": coverage, "incidents": incidents}]
    existing["snapshots"].sort(key=lambda s: s["collected_at"])
    path.write_text(json.dumps(existing, separators=(",", ":"), ensure_ascii=False) + "\n")
    (folder / "manifest.json").write_text(json.dumps({"schema_version": 1, "months": sorted(f.stem for f in folder.glob("????-??.json")), "latest_collection": now}, indent=2) + "\n")


if __name__ == "__main__":
    now, incidents, coverage = collect()
    write(now, incidents, coverage)
    print("Entergy states:", coverage, "observations:", len(incidents))
