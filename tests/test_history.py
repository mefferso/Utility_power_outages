import unittest
from scripts.backfill_history import build_history


class HistoryTests(unittest.TestCase):
    def test_only_requested_year_and_monthly_statistics(self):
        county=[{"fips":"22103","name":"St. Tammany","state":"LA"}]
        def fake(fips,key):
            return {"data":{"monthly":[
                {"year":2025,"month":12,"peak_customers_out":50},
                {"year":2026,"month":4,"peak_customers_out":120,"source":"odin"},
                {"year":2024,"month":1,"peak_customers_out":90}
            ]}}
        result=build_history(county,getter=fake,key="test")
        self.assertEqual(len(result["records"]),1)
        self.assertEqual(result["records"][0]["peak_customers_out"],120)
        self.assertEqual(result["records"][0]["year"],2026)
        self.assertEqual(result["counties"][0]["status"],"ok")


if __name__=="__main__":
    unittest.main()
