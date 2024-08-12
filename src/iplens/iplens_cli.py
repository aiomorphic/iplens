import argparse
import os
import sys
from typing import List

from rich.console import Console

from iplens.ipapi_api import IPInfoAPI
from iplens.input_processor import extract_ips_from_logs, parse_input_file
from iplens.output import save_to_csv, save_to_json
from iplens.table_formatter import create_rich_table
from iplens.utils import is_valid_ip


def ensure_file_extension(filename: str, format: str) -> str:
    """Ensure the filename has the correct extension based on the format."""
    expected_extension = f".{format}"
    if not filename.lower().endswith(expected_extension):
        return f"{filename}{expected_extension}"
    return filename


def parse_folder_for_ips(folder_path: str) -> List[str]:
    """Parse all non-binary files in a folder and return a list of IP addresses."""
    ips = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                    ips.extend(extract_ips_from_logs(content))
            except (UnicodeDecodeError, IsADirectoryError):
                continue
    return ips


def main():
    parser = argparse.ArgumentParser(description="Fetch and display IP info.")
    parser.add_argument(
        "ips", metavar="IP", type=str, nargs="*", help="IP addresses to fetch info for"
    )
    parser.add_argument(
        "--input-file", "-i", type=str, help="Input file containing IP addresses"
    )
    parser.add_argument(
        "--input-folder",
        "-d",
        type=str,
        help="Input folder containing files to parse for IP addresses",
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output file (without extension)"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json"],
        help="Output format (when using --output)",
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear expired cache entries"
    )

    args = parser.parse_args()

    console = Console()
    iplens_api = IPInfoAPI()

    if args.clear_cache:
        console.print("Clearing expired cache entries...", style="bold blue")
        iplens_api.clear_expired_cache()
        console.print("Cache cleared.", style="bold green")
        return

    if args.input_file and args.ips:
        console.print(
            "Error: Cannot use both IP arguments and --input-file.", style="bold red"
        )
        sys.exit(1)

    if args.input_file:
        try:
            ips = parse_input_file(args.input_file)
        except Exception as e:
            console.print(f"Error reading input file: {str(e)}", style="bold red")
            sys.exit(1)
    elif args.input_folder:
        try:
            ips = parse_folder_for_ips(args.input_folder)
        except Exception as e:
            console.print(f"Error reading input folder: {str(e)}", style="bold red")
            sys.exit(1)
    elif args.ips:
        ips = [ip for ip in args.ips if is_valid_ip(ip)]
    else:
        console.print(
            "Error: No IP addresses provided. Use positional arguments, --input-file, or --input-folder. or -h for help",
            style="bold red",
        )
        sys.exit(1)

    if not ips:
        console.print("No valid IP addresses found.", style="bold red")
        sys.exit(1)

    console.print(f"Fetching data for {len(ips)} IP(s)...", style="bold blue")

    processed_data = iplens_api.fetch_data(ips)

    if processed_data:
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
