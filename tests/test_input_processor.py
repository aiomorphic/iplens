import os
import tempfile
from unittest.mock import patch

import pytest

from iplens.input_processor import (
    extract_ips_from_logs,
    find_ip_column,
    parse_input_file,
    parse_input_folder,
)


def test_parse_json_list():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as handle:
        handle.write('["8.8.8.8", "1.1.1.1"]')
        path = handle.name

    try:
        assert parse_input_file(path) == ["8.8.8.8", "1.1.1.1"]
    finally:
        os.remove(path)


def test_parse_csv_with_ip_column():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as handle:
        handle.write("client_ip,note\n8.8.8.8,one\n1.1.1.1,two\n")
        path = handle.name

    try:
        assert parse_input_file(path) == ["8.8.8.8", "1.1.1.1"]
    finally:
        os.remove(path)


def test_parse_log_lines():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".log") as handle:
        handle.write("connection from 8.8.8.8 port 443\nfailed 192.168.1.1\n")
        path = handle.name

    try:
        assert parse_input_file(path) == ["8.8.8.8"]
    finally:
        os.remove(path)


def test_parse_python_literal_list_without_eval():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as handle:
        handle.write('["8.8.8.8"]')
        path = handle.name

    try:
        assert parse_input_file(path) == ["8.8.8.8"]
    finally:
        os.remove(path)


def test_parse_rejects_executable_literal():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as handle:
        handle.write("__import__('os').system('echo pwned')")
        path = handle.name

    try:
        assert parse_input_file(path) == []
    finally:
        os.remove(path)


def test_parse_input_file_rejects_oversized_file():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as handle:
        handle.write("8.8.8.8\n")
        path = handle.name

    try:
        with patch(
            "iplens.input_processor._input_limits",
            return_value={"max_file_bytes": 1, "max_folder_files": 10, "max_folder_depth": 2},
        ):
            with pytest.raises(ValueError, match="exceeds maximum size"):
                parse_input_file(path)
    finally:
        os.remove(path)


def test_parse_input_folder_finds_ips():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "access.log"), "w", encoding="utf-8") as handle:
            handle.write("client 103.78.226.49 connected\n")

        ips = parse_input_folder(tmpdir)
        assert "103.78.226.49" in ips


def test_parse_input_folder_skips_git_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        git_dir = os.path.join(tmpdir, ".git")
        os.makedirs(git_dir)
        with open(os.path.join(git_dir, "config"), "w") as handle:
            handle.write("8.8.8.8\n")

        assert parse_input_folder(tmpdir) == []


def test_extract_ips_from_logs_ipv6():
    content = "peer 2001:4860:4860::8888 established"
    assert "2001:4860:4860::8888" in extract_ips_from_logs(content)


def test_find_ip_column():
    assert find_ip_column(["host", "client_ip", "note"]) == "client_ip"
    assert find_ip_column(None) is None
