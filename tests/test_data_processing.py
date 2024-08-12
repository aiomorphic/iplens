import unittest

from src.ipapi_api import IPInfoAPI
from src.utils import FIELDNAMES


class TestDataProcessing(unittest.TestCase):
    def setUp(self):
        self.api = IPInfoAPI()

    def test_process_response_complete(self):

        input_data = {
            "ip": "8.8.8.8",
            "request_count": 1,
            "company": {
                "name": "Google LLC",
                "domain": "google.com",
                "network": "8.8.8.0/24",
                "whois": "Google LLC (GOGL)",
            },
            "asn": {
                "asn": "AS15169",
                "route": "8.8.8.0/24",
                "descr": "GOOGLE",
                "country": "US",
                "rir": "ARIN",
            },
            "location": {
                "country": "United States",
                "country_code": "US",
                "state": "California",
                "city": "Mountain View",
            },
        }

        result = self.api.process_response(input_data)

        for field in FIELDNAMES:
            self.assertIn(field, result)

        self.assertEqual(result["ip"], "8.8.8.8")
        self.assertEqual(result["company_name"], "Google LLC")
        self.assertEqual(result["asn_asn"], "AS15169")
        self.assertEqual(result["location_country"], "United States")
        self.assertEqual(result["asn_rir"], "ARIN")

    def test_process_response_empty(self):

        input_data = {}

        result = self.api.process_response(input_data)

        for field in FIELDNAMES:
            self.assertIn(field, result)
            self.assertEqual(result[field], "")

    def test_process_response_invalid(self):

        input_data = "Not a dict"

        result = self.api.process_response(input_data)

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
