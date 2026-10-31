"""Safe diagnostics of Entergy's public ArcGIS incident fields.

Print only aggregate field completeness; never raw comments, addresses, names,
identifiers or precise coordinates. Read-only, no persistent record changes.
"""
import collections
import json
import re
import urllib.parse
import urllib.request

ENDPOINT = "https://arcgis.entergy.datacapable.com/arcgis/rest/services/Public/MapServer/1/query"
FIELDS = ("eventtype", "title", "cause", "comments", "county", "city",
          "status", "identifier", "startdate", "lastupdated", "numpeople", "state")
STATES = ("LA", "MS")

def sample(state):
    p = dict(where="state = '%s'" % state, outFields=",".join(FIELDS),
             returnGeometry="false", resultRecordCount=1000, f="json")
    u = ENDPOINT + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(u, headers={"User-Agent": "LIX-outage-research-diagnostic/1.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.load(resp)
    if "error" in data:
        raise RuntimeError("ArcGIS query error: " + str(data["error"].get("message")))
    return data["features"], bool(data.get("exceededTransferLimit"))

def audit(state, features, limited):
    rows = [f.get("attributes") or {} for f in features]
    print(f"{state}: {len(rows)} returned features; transfer_limit={limited}")
    for field in FIELDS:
        vals = [r.get(field) for r in rows]
        present = [v for v in vals if v is not None and str(v).strip()]
        print(f"  {field}: {len(present)}/{len(rows)} populated")
        # Only report low-risk controlled labels. No excerpts from free-text fields.
        if field in ("comments", "title"):
            for label,pattern in {"tree":"tree|limb|branch|vegetation","pole":"pole|crossarm","line":"downed line|wire down|line down","wind":"wind|storm|thunderstorm","lightning":"lightning","estimated":"estimated|restoration|crew|repair","generic":"outage|customer|power"}.items():
                print(f"    {label}: {sum(bool(re.search(pattern, str(v), re.I)) for v in present)}")
            print("    length bands:", dict(collections.Counter("short" if len(str(v)) < 40 else "medium" if len(str(v)) < 160 else "long" for v in present)))
        if field == "eventtype":
            print("  eventtype labels (redacted if long):", [(str(k)[:36], n) for k,n in collections.Counter(map(str,present)).most_common(10)])

if __name__ == "__main__":
    for state in STATES:
        try:
            features, limited = sample(state)
            audit(state, features, limited)
        except Exception as exc:
            print(f"{state}: QUERY FAILED: {type(exc).__name__}: {str(exc)[:180]}")
