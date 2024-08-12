import csv
import json
import os
import unittest

from src.output import save_to_csv, save_to_json
from src.utils import FIELDNAMES


class TestOutput(unittest.TestCase):

    def setUp(self):
        self.test_data = [
            {
                "ip": "8.8.8.8",
                "company_name": "Google LLC",
                "asn_asn": "AS15169",
                "location_country": "United States",
            },
            {
                "ip": "1.1.1.1",
                "company_name": "Cloudflare, Inc.",
                "asn_asn": "AS13335",
                "location_country": "Australia",
            },
        ]
        self.csv_file = "test_output.csv"
        self.json_file = "test_output.json"

    def tearDown(self):

        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        if os.path.exists(self.json_file):
            os.remove(self.json_file)

    def test_save_to_csv(self):
        save_to_csv(self.test_data, self.csv_file)

        self.assertTrue(os.path.exists(self.csv_file))

        with open(self.csv_file, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["ip"], "8.8.8.8")
            self.assertEqual(rows[1]["ip"], "1.1.1.1")

            for field in FIELDNAMES:
                self.assertIn(field, rows[0])

    def test_save_to_json(self):
        save_to_json(self.test_data, self.json_file)

        self.assertTrue(os.path.exists(self.json_file))

        with open(self.json_file, "r") as jsonfile:
            data = json.load(jsonfile)

            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["ip"], "8.8.8.8")
            self.assertEqual(data[1]["ip"], "1.1.1.1")

    def test_save_to_csv_empty(self):
        save_to_csv([], self.csv_file)

        self.assertTrue(os.path.exists(self.csv_file))

        with open(self.csv_file, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            self.assertEqual(len(rows), 0)

            self.assertEqual(reader.fieldnames, FIELDNAMES)

    def test_save_to_json_empty(self):
        save_to_json([], self.json_file)

        self.assertTrue(os.path.exists(self.json_file))

        with open(self.json_file, "r") as jsonfile:
            data = json.load(jsonfile)

            self.assertEqual(len(data), 0)


if __name__ == "__main__":
    unittest.main()
