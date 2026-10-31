import json
from pathlib import Path
import tempfile
import unittest
from scripts.collect import archive, collect


class CollectorTests(unittest.TestCase):
    def test_archive_retains_snapshots_and_rerun_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            coverage = [{"fips": "22103", "status": "ok", "incident_count": 1}]
            sample = [{"cause": "Tree contact", "observed_at": "2026-10-30T12:00:00Z"}]
            archive(sample, coverage, "2026-10-30T12:00:00Z", root)
            archive(sample, coverage, "2026-10-30T12:40:00Z", root)
            archive(sample, coverage, "2026-10-30T13:00:00Z", root)
            result = json.loads((root / "data/2026-10.json").read_text())
            self.assertEqual(len(result["snapshots"]), 2)
            self.assertEqual(result["snapshots"][0]["incidents"][0]["cause"], "Tree contact")

    def test_failed_county_is_not_a_zero_outage(self):
        counties = [{"fips": "22103", "name": "St. Tammany", "state": "LA"}]
        def failure(fips, key):
            raise RuntimeError("API down")
        incidents, coverage = collect(counties, "2026-10-30T12:00:00Z", "key", getter=failure)
        self.assertEqual(incidents, [])
        self.assertEqual(coverage[0]["status"], "error")
        self.assertIsNone(coverage[0]["incident_count"])


if __name__ == "__main__":
    unittest.main()
