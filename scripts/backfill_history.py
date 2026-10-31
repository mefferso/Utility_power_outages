"""Retrieve documented county/monthly historical outage summaries for 2026.

Historical county summaries are NOT individual utility trouble tickets.
Source: https://massoutage.com/developers/reference
"""
import datetime as dt
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://massoutage.com/api/v1"
YEAR = 2026


def get_history(fips, key=None):
    headers = {"Accept": "application/json", "User-Agent": "UtilityPowerOutages/1.0"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(f"{BASE}/counties/{fips}/history", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload.get("data", {}).get("monthly"), list):
        raise ValueError("History endpoint did not return data.monthly array")
    return payload


def build_history(counties, getter=get_history, key=None, include_2025=False):
    years = {2026, 2025} if include_2025 else {2026}
    result = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "description": "County-level historical monthly outage summaries, not geolocated incidents",
        "years_requested": sorted(years),
        "counties": [],
        "records": [],
        "source": "MassOutage county history / upstream DOE EAGLE-I and ODIN",
    }
    for county in counties:
        try:
            payload = getter(county["fips"], key)
            monthly = payload["data"]["monthly"]
            included = 0
            for r in monthly:
                try:
                    year, month = int(r["year"]), int(r["month"])
                except (ValueError, TypeError, KeyError):
                    continue
                if year not in years or not 1 <= month <= 12:
                    continue
                result["records"].append({
                    "year": year, "month": month, "fips": county["fips"],
                    "county": county["name"], "state": county["state"],
                    "source": r.get("source"),
                    "customer_minutes": r.get("customer_minutes"),
                    "peak_customers_out": r.get("peak_customers_out"),
                    "event_count": r.get("event_count"),
                    "minutes_any_outage": r.get("minutes_any_outage"),
                    "source_url": f"{BASE}/counties/{county['fips']}/history",
                })
                included += 1
            result["counties"].append({"fips": county["fips"], "status": "ok", "records": included})
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            result["counties"].append({"fips": county["fips"], "status": "error", "error": str(exc)[:180]})
        # Stay below authenticated burst limits and be respectful of the free service.
        time.sleep(1.1 if key else 65)
    return result


def main():
    counties = json.loads((ROOT / "config/counties.json").read_text())
    result = build_history(
        counties,
        key=os.getenv("MASSOUTAGE_API_KEY"),
        include_2025=os.getenv("INCLUDE_2025") == "true",
    )
    good = [x for x in result["counties"] if x["status"] == "ok"]
    if not good:
        raise SystemExit("No county history calls succeeded. Refusing to replace saved history.")
    target = ROOT / "data/history.json"
    if target.exists():
        old = json.loads(target.read_text())
        # Preserve older successfully retrieved records when the new refresh is partial.
        new_fips = {r["fips"] for r in result["records"]}
        year_set = set(result["years_requested"])
        for r in old.get("records", []):
            if r["fips"] not in new_fips or r["year"] not in year_set:
                result["records"].append(r)
    result["records"].sort(key=lambda x: (x["year"], x["month"], x["fips"]))
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Retrieved {len(result['records'])} monthly rows; {len(good)}/{len(counties)} counties succeeded")
    if not result["records"]:
        print("NOTE: No matching 2026 history supplied. The UI will show unavailable, not zero.")


if __name__ == "__main__":
    main()
