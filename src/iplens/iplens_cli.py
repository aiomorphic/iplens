import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import List

import requests
from rich.console import Console

from iplens.input_processor import parse_input_file, parse_input_folder
from iplens.ipapi_api import IPInfoAPI
from iplens.output import save_to_csv, save_to_json
from iplens.paths import default_cache_db_path
from iplens.table_formatter import create_rich_table
from iplens.utils import dedupe_ips, is_valid_ip

try:
    __version__ = version("iplens")
except PackageNotFoundError:
    __version__ = "0.0.0"

HELP_EPILOG = f"""
examples:
  %(prog)s 8.8.8.8 1.1.1.1
  %(prog)s -i ips.txt
  %(prog)s -d /var/log/nginx/ -o results -f json
  %(prog)s --clear-cache

input (pick one):
  IP ...             One or more public IPv4/IPv6 addresses
  -i, --input-file   Plain text, JSON list, CSV (column with "ip"), or logs
  -d, --input-folder Scan text files under a directory (skips .git, node_modules)

export:
  -o/--output requires -f/--format (csv or json). Extension is added if missing.

cache:
  {default_cache_db_path()}

API endpoint and limits are set in the package config.cfg (default: api.ipapi.is).
Uncached lookups are sent to that API. See the README for rate limits.
""".strip()


def ensure_file_extension(filename: str, format: str) -> str:
    expected_extension = f".{format}"
    if not filename.lower().endswith(expected_extension):
        return f"{filename}{expected_extension}"
    return filename


def collect_ips(args, console: Console) -> List[str]:
    if args.input_file and args.input_folder:
        console.print(
            "Error: Use only one of --input-file or --input-folder.",
            style="bold red",
        )
        sys.exit(1)

    if args.input_file and args.ips:
        console.print(
            "Error: Cannot use both IP arguments and --input-file.",
            style="bold red",
        )
        sys.exit(1)

    if args.input_folder and args.ips:
        console.print(
            "Error: Cannot use both IP arguments and --input-folder.",
            style="bold red",
        )
        sys.exit(1)

    if args.input_file:
        try:
            return parse_input_file(args.input_file)
        except (OSError, ValueError) as error:
            console.print(f"Error reading input file: {error}", style="bold red")
            sys.exit(1)

    if args.input_folder:
        try:
            return parse_input_folder(args.input_folder)
        except (OSError, ValueError) as error:
            console.print(f"Error reading input folder: {error}", style="bold red")
            sys.exit(1)

    if args.ips:
        valid_ips = [ip for ip in args.ips if is_valid_ip(ip)]
        invalid_count = len(args.ips) - len(valid_ips)
        if invalid_count:
            console.print(
                f"Warning: Ignored {invalid_count} invalid IP argument(s).",
                style="yellow",
            )
        return valid_ips

    console.print(
        "Error: No IP addresses provided. Use positional arguments, "
        "--input-file, --input-folder, or -h for help.",
        style="bold red",
    )
    sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iplens",
        description=(
            "Look up IP intelligence (geo, ASN, company, abuse flags) and print "
            "a table. Supports IPv4/IPv6, bulk input, CSV/JSON export, and a "
            "local SQLite cache."
        ),
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "ips",
        metavar="IP",
        nargs="*",
        help="public IP address(es); cannot combine with -i or -d",
    )
    parser.add_argument(
        "--input-file",
        "-i",
        metavar="PATH",
        help="file with IPs (text, JSON, CSV, or logs); cannot combine with IP args or -d",
    )
    parser.add_argument(
        "--input-folder",
        "-d",
        metavar="DIR",
        help="scan directory for IPs in text files; cannot combine with IP args or -i",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="write results to PATH (adds .csv or .json from -f)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json"],
        metavar="FORMAT",
        help="export format; required with --output",
    )
    cache = parser.add_argument_group("cache")
    cache.add_argument(
        "--clear-cache",
        action="store_true",
        help="delete expired rows from the local cache DB",
    )
    cache.add_argument(
        "--clear-cache-all",
        action="store_true",
        help="delete every row from the local cache DB",
    )
    return parser


def main():
    args = build_parser().parse_args()
    console = Console()
    iplens_api = IPInfoAPI()

    if args.clear_cache and args.clear_cache_all:
        console.print(
            "Error: Use only one of --clear-cache or --clear-cache-all.",
            style="bold red",
        )
        sys.exit(1)

    if args.clear_cache_all:
        removed = iplens_api.clear_all_cache()
        console.print(f"Cleared {removed} cache entries.", style="bold green")
        return

    if args.clear_cache:
        removed = iplens_api.clear_expired_cache()
        console.print(f"Cleared {removed} expired cache entries.", style="bold green")
        return

    ips = dedupe_ips(collect_ips(args, console))
    if not ips:
        console.print("No valid IP addresses found.", style="bold red")
        sys.exit(1)

    console.print(
        f"Fetching data for {len(ips)} IP(s)...",
        style="bold blue",
    )

    try:
        processed_data = iplens_api.fetch_data(ips)
    except requests.RequestException as error:
        console.print(f"Error: Failed to fetch IP data: {error}", style="bold red")
        if isinstance(error, requests.exceptions.SSLError):
            console.print(
                "Hint: The configured API endpoint may have an invalid TLS certificate. "
                "Use https://api.ipapi.is in config.cfg.",
                style="yellow",
            )
        sys.exit(1)

    if not processed_data:
        console.print(
            "No IP data returned. Check your network connection or API rate limits.",
            style="bold red",
        )
        sys.exit(1)

    table = create_rich_table(processed_data)
    console.print(table)

    if args.output:
        if not args.format:
            console.print(
                "Error: --format must be specified when using --output",
                style="bold red",
            )
            sys.exit(1)

        output_file = ensure_file_extension(args.output, args.format)
        console.print(f"Saving results to {output_file}...", style="bold green")

        if args.format == "csv":
            save_to_csv(processed_data, output_file)
        else:
            save_to_json(processed_data, output_file)

        console.print("Done.", style="bold green")


if __name__ == "__main__":
    main()
