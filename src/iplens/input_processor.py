import ast
import csv
import json
import os
import re
from typing import List, Optional, Sequence

from iplens.config_loader import load_config
from iplens.utils import is_valid_ip

DEFAULT_MAX_FILE_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_FOLDER_FILES = 500
DEFAULT_MAX_FOLDER_DEPTH = 8
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}


def _input_limits():
    config = load_config()
    return {
        "max_file_bytes": int(
            config.get("Input", "max_file_bytes", fallback=DEFAULT_MAX_FILE_BYTES)
        ),
        "max_folder_files": int(
            config.get("Input", "max_folder_files", fallback=DEFAULT_MAX_FOLDER_FILES)
        ),
        "max_folder_depth": int(
            config.get("Input", "max_folder_depth", fallback=DEFAULT_MAX_FOLDER_DEPTH)
        ),
    }


def _read_text_file(file_path: str, max_bytes: int) -> str:
    size = os.path.getsize(file_path)
    if size > max_bytes:
        raise ValueError(
            f"File exceeds maximum size ({size} bytes > {max_bytes} bytes): {file_path}"
        )
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def extract_ips_from_logs(content: str) -> List[str]:
    """Extract unique IP addresses from log content."""
    ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ipv6_pattern = (
        r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b|"
        r"\b(?:[0-9a-fA-F]{0,4}:){1,7}:\b|"
        r"\b::(?:[0-9a-fA-F]{0,4}:){0,6}[0-9a-fA-F]{0,4}\b"
    )
    candidates = set(re.findall(ipv4_pattern, content))
    candidates.update(re.findall(ipv6_pattern, content))
    return [ip for ip in candidates if is_valid_ip(ip)]


def parse_input_file(file_path: str) -> List[str]:
    """Parse the input file and return a list of IP addresses."""
    limits = _input_limits()
    content = _read_text_file(file_path, limits["max_file_bytes"]).strip()

    try:
        csv_reader = csv.DictReader(content.splitlines())
        ip_column = find_ip_column(csv_reader.fieldnames)
        if ip_column:
            return [
                row[ip_column] for row in csv_reader if is_valid_ip(row[ip_column])
            ]
    except (csv.Error, KeyError, TypeError):
        pass

    try:
        json_data = json.loads(content)
        if isinstance(json_data, list):
            return [ip for ip in json_data if isinstance(ip, str) and is_valid_ip(ip)]
        if isinstance(json_data, dict):
            for value in json_data.values():
                if isinstance(value, list):
                    return [
                        ip
                        for ip in value
                        if isinstance(ip, str) and is_valid_ip(ip)
                    ]
    except json.JSONDecodeError:
        pass

    try:
        parsed = ast.literal_eval(content)
        if isinstance(parsed, list):
            return [
                ip for ip in parsed if isinstance(ip, str) and is_valid_ip(ip)
            ]
    except (SyntaxError, ValueError):
        pass

    log_ips = extract_ips_from_logs(content)
    if log_ips:
        return log_ips

    return [
        line.strip()
        for line in content.split("\n")
        if is_valid_ip(line.strip())
    ]


def parse_input_folder(folder_path: str) -> List[str]:
    """Parse text files under a folder and return discovered IP addresses."""
    limits = _input_limits()
    root = os.path.abspath(folder_path)
    if not os.path.isdir(root):
        raise ValueError(f"Not a directory: {folder_path}")

    ips: List[str] = []
    files_read = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames if name not in SKIP_DIR_NAMES and not name.startswith(".")
        ]
        depth = os.path.relpath(dirpath, root).count(os.sep)
        if depth >= limits["max_folder_depth"]:
            dirnames.clear()
            continue

        for filename in filenames:
            if files_read >= limits["max_folder_files"]:
                raise ValueError(
                    f"Folder scan exceeded max files ({limits['max_folder_files']}): {folder_path}"
                )
            file_path = os.path.join(dirpath, filename)
            if os.path.islink(file_path) or not os.path.isfile(file_path):
                continue
            try:
                content = _read_text_file(file_path, limits["max_file_bytes"])
                ips.extend(extract_ips_from_logs(content))
                files_read += 1
            except (UnicodeDecodeError, OSError, ValueError):
                continue

    return ips


def find_ip_column(fieldnames: Optional[Sequence[str]]) -> Optional[str]:
    """Find the column name that likely contains IP addresses."""
    if fieldnames is None:
        return None
    return next((col for col in fieldnames if "ip" in col.lower()), None)
