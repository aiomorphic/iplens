import argparse
import sys
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from iplens.iplens_cli import build_parser, collect_ips, ensure_file_extension, main


def test_build_parser_includes_examples_in_help():
    parser = build_parser()
    help_text = parser.format_help()
    assert "examples:" in help_text
    assert "--clear-cache-all" in help_text
    assert "api.ipapi.is" in help_text


def test_build_parser_version():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0


def test_ensure_file_extension_adds_suffix():
    assert ensure_file_extension("results", "json") == "results.json"
    assert ensure_file_extension("results.JSON", "json") == "results.JSON"


def test_collect_ips_from_argv():
    args = argparse.Namespace(ips=["8.8.8.8", "not-an-ip"], input_file=None, input_folder=None)
    console = Console(record=True)
    ips = collect_ips(args, console)
    assert ips == ["8.8.8.8"]
    assert "Ignored 1 invalid" in console.export_text()


def test_collect_ips_rejects_file_and_folder():
    args = argparse.Namespace(ips=[], input_file="a.txt", input_folder="/tmp")
    with pytest.raises(SystemExit) as exc:
        collect_ips(args, Console())
    assert exc.value.code == 1


def test_collect_ips_rejects_ips_and_file():
    args = argparse.Namespace(ips=["8.8.8.8"], input_file="a.txt", input_folder=None)
    with pytest.raises(SystemExit) as exc:
        collect_ips(args, Console())
    assert exc.value.code == 1


def test_collect_ips_requires_input():
    args = argparse.Namespace(ips=[], input_file=None, input_folder=None)
    with pytest.raises(SystemExit) as exc:
        collect_ips(args, Console())
    assert exc.value.code == 1


@patch("iplens.iplens_cli.parse_input_file", return_value=["1.1.1.1"])
def test_collect_ips_from_file(mock_parse):
    args = argparse.Namespace(ips=[], input_file="ips.txt", input_folder=None)
    assert collect_ips(args, Console()) == ["1.1.1.1"]


@patch("iplens.iplens_cli.IPInfoAPI")
def test_main_clear_expired_cache(mock_api_cls):
    mock_api = mock_api_cls.return_value
    mock_api.clear_expired_cache.return_value = 3

    with patch.object(sys, "argv", ["iplens", "--clear-cache"]):
        main()

    mock_api.clear_expired_cache.assert_called_once()


@patch("iplens.iplens_cli.IPInfoAPI")
def test_main_clear_all_cache(mock_api_cls):
    mock_api = mock_api_cls.return_value
    mock_api.clear_all_cache.return_value = 10

    with patch.object(sys, "argv", ["iplens", "--clear-cache-all"]):
        main()

    mock_api.clear_all_cache.assert_called_once()


@patch("iplens.iplens_cli.IPInfoAPI")
def test_main_rejects_both_cache_flags(mock_api_cls):
    with patch.object(sys, "argv", ["iplens", "--clear-cache", "--clear-cache-all"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    mock_api_cls.return_value.clear_expired_cache.assert_not_called()


@patch("iplens.iplens_cli.IPInfoAPI")
def test_main_fetch_and_print_table(mock_api_cls):
    mock_api = mock_api_cls.return_value
    mock_api.fetch_data.return_value = [
        {
            "ip": "8.8.8.8",
            "location_country": "United States",
            "location_city": "Mountain View",
            "asn_type": "hosting",
            "company_domain": "google.com",
            "is_datacenter": "True",
            "is_tor": "False",
            "is_proxy": "False",
            "is_vpn": "False",
            "is_abuser": "True",
            "company_abuser_score": "0.0039 (Low)",
            "asn_abuser_score": "0.001 (Low)",
        }
    ]

    with patch.object(sys, "argv", ["iplens", "8.8.8.8"]):
        main()

    mock_api.fetch_data.assert_called_once_with(["8.8.8.8"])


@patch("iplens.iplens_cli.IPInfoAPI")
def test_main_output_requires_format(mock_api_cls):
    mock_api_cls.return_value.fetch_data.return_value = [{"ip": "8.8.8.8"}]

    with patch.object(sys, "argv", ["iplens", "8.8.8.8", "-o", "out"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
