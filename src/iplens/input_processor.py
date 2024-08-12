import csv
import json
import re
from typing import List, Optional, Sequence

from iplens.utils import is_valid_ip


def extract_ips_from_logs(content: str) -> List[str]:
    """Extract unique IP addresses from log content."""
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ips = set(re.findall(ip_pattern, content))
    return [ip for ip in ips if is_valid_ip(ip)]


def parse_input_file(file_path: str) -> List[str]:
    """Parse the input file and return a list of IP addresses."""
    with open(file_path, "r") as file:
        content = file.read().strip()

        try:
            csv_reader = csv.DictReader(content.splitlines())
            ip_column = find_ip_column(csv_reader.fieldnames)
            if ip_column:
                return [
                    row[ip_column] for row in csv_reader if is_valid_ip(row[ip_column])
                ]
        except Exception:
            pass

        try:
            json_data = json.loads(content)
            if isinstance(json_data, list):
                return [ip for ip in json_data if is_valid_ip(ip)]
            elif isinstance(json_data, dict):

                for value in json_data.values():
                    if isinstance(value, list):
                        return [ip for ip in value if is_valid_ip(ip)]
            raise ValueError("No valid IP list found in JSON")
        except json.JSONDecodeError:
            pass

        try:
            python_list = eval(content)
            if isinstance(python_list, list):
                return [ip for ip in python_list if is_valid_ip(ip)]
        except Exception:
            pass

        log_ips = extract_ips_from_logs(content)
        if log_ips:
            return log_ips

        return [
            line.strip() for line in content.split("\n") if is_valid_ip(line.strip())
        ]


def find_ip_column(fieldnames: Optional[Sequence[str]]) -> Optional[str]:
    """Find the column name that likely contains IP addresses."""
    if fieldnames is None:
        return None
    return next((col for col in fieldnames if "ip" in col.lower()), None)
