"""Collect timestamped public utility incident snapshots into monthly JSON archives.

Designed for GitHub Actions. No invented outages, restoration times, or causes.
A successful zero-incident response is recorded distinctly from a failed request.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
API = "https://massoutage.com/api/v1"
UTC = dt.timezone.utc


def fetch(fips, api_key=None, retries=2):
    url = f"{API}/live/counties/{fips}/incidents"
    headers = {"Accept": "application/json", "User-Agent": "UtilityPowerOutagesResearch/0.1 (+github.com/mefferso/Utility_power_outages)"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
                payload = json.load(response)
            if not isinstance(payload.get("data"), list):
                raise ValueError("Expected data array")
            return payload
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Failed for {fips}: {exc}") from exc
            time.sleep(2 ** attempt)


def normalize(row, county, collected_at, source_as_of):
    # Do not infer incident identity from approximate coordinates.
    return {
        "observed_at": collected_at,
        "source_as_of": row.get("as_of") or source_as_of,
        "fips": county["fips"],
        "county": county["name"],
        "state": county["state"],
        "utility_key": row.get("utility_key"),
        "utility": row.get("utility_name"),
        "lat": row.get("lat"),
        "lon": row.get("lon"),
        "customers_out": row.get("customers_out"),
        "customers_below": row.get("customers_below"),
        "cause": row.get("cause"),
        "crew_status": row.get("crew_status"),
        "started_at": row.get("started_at"),
        "etr": row.get("etr"),
        "source": "MassOutage / public utility feeds",
        "source_url": f"{API}/live/counties/{county['fips']}/incidents",
        "verification": "unverified_public_outage",
    }


def collect(counties, now, api_key, getter=fetch):
    incidents, coverage = [], []
    for county in counties:
        try:
            payload = getter(county["fips"], api_key)
            source_time = payload.get("as_of") or payload.get("meta", {}).get("live", {}).get("last_poll_ts")
            status = payload.get("meta", {}).get("live", {}).get("status", "unknown")
            records = payload["data"]
            coverage.append({"fips": county["fips"], "status": "ok" if status != "delayed" else "delayed", "incident_count": len(records), "source_as_of": source_time})
            incidents.extend(normalize(record, county, now, source_time) for record in records)
        except Exception as exc:
            print(f"WARNING: {county['fips']}: {exc}", file=sys.stderr)
            coverage.append({"fips": county["fips"], "status": "error", "incident_count": None, "error": str(exc)[:200]})
        # Anonymous users are heavily rate-limited. A key is strongly recommended.
        if not api_key:
            time.sleep(65)
    return incidents, coverage


def archive(incidents, coverage, now, root=ROOT):
    month = now[:7]
    folder = root / "data"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{month}.json"
    existing = json.loads(path.read_text()) if path.exists() else {"schema_version": 1, "snapshots": []}
    # Idempotent within the same UTC hour; reruns replace that collection attempt.
    slot = now[:13]
    snapshot = {"collected_at": now, "coverage": coverage, "incidents": incidents}
    existing["snapshots"] = [s for s in existing["snapshots"] if s["collected_at"][:13] != slot] + [snapshot]
    existing["snapshots"].sort(key=lambda s: s["collected_at"])
    path.write_text(json.dumps(existing, separators=(",", ":"), ensure_ascii=False) + "\n")
    months = sorted(p.stem for p in folder.glob("????-??.json"))
    (folder / "manifest.json").write_text(json.dumps({"schema_version": 1, "months": months, "latest_collection": now}, indent=2) + "\n")
    return path


def main():
    counties = json.loads((ROOT / "config/counties.json").read_text())
    now = dt.datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    incidents, coverage = collect(counties, now, os.environ.get("MASSOUTAGE_API_KEY"))
    if not any(c["status"] in ("ok", "delayed") for c in coverage):
        raise SystemExit("All sources failed; refusing to write an empty archive.")
    path = archive(incidents, coverage, now)
    print(f"Saved {len(incidents)} incident observations to {path}; {sum(c['status'] == 'error' for c in coverage)} counties failed.")


if __name__ == "__main__":
    main()
