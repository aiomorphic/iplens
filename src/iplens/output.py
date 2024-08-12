import csv
import json
from typing import Dict, List

from iplens.logger import logger
from iplens.utils import FIELDNAMES


def save_to_csv(data: List[Dict], output_file: str):
    """
    Save processed IP information to a CSV file.

    Args:
        data (List[Dict]): Processed IP information.
        output_file (str): Path to the output CSV file.
    """
    logger.info(f"Saving data to CSV file: {output_file}")
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def save_to_json(data: List[Dict], output_file: str):
    """
    Save processed IP information to a JSON file.

    Args:
        data (List[Dict]): Processed IP information.
        output_file (str): Path to the output JSON file.
    """
    logger.info(f"Saving data to JSON file: {output_file}")
    with open(output_file, "w") as jsonfile:
        json.dump(data, jsonfile, indent=2)
