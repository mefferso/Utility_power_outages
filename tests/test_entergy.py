import json
import tempfile
from pathlib import Path
import unittest
from scripts.entergy import collect, normalized, write


class EntergyTests(unittest.TestCase):
    def test_sanitized_geometry_and_date(self):
        f={"geometry":{"coordinates":[-90.12345,30.45678]},"properties":{"identifier":"a","state":"LA","county":"St. Tammany","cause":"Tree on line","comments":"private note","street":"private address","numpeople":12,"startdate":1720000000000}}
        row=normalized(f,"2026-10-31T01:00:00Z")
        self.assertEqual((row["lat"],row["lon"]),(30.46,-90.12))
        self.assertNotIn("comments", row)
        self.assertNotIn("street",row)
        self.assertEqual(row["cause"],"Tree on line")

    def test_partial_outage_is_not_zero(self):
        def fake(state, offset):
            if state=="MS":
                raise RuntimeError("Blocked")
            return {"type":"FeatureCollection","features":[{"geometry":{"coordinates":[-90,30]},"properties":{"state":"LA","county":"Orleans","numpeople":3}}]}
        now, records, coverage=collect(getter=fake)
        self.assertEqual(len(records),1)
        self.assertEqual(coverage[1]["status"],"error")
        with tempfile.TemporaryDirectory() as tmp:
            write(now,records,coverage,Path(tmp))
            target=Path(tmp)/"data/entergy"/(now[:7]+".json")
            saved=json.loads(target.read_text())
            self.assertEqual(saved["snapshots"][0]["incidents"][0]["utility"],"Entergy")


if __name__=="__main__":
    unittest.main()
