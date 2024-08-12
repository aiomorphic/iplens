import re
from typing import Any, Dict, List

from rich import box
from rich.style import Style
from rich.table import Table
from rich.text import Text


def safe_str(value: Any) -> str:
    """
    Safely convert any value to a string, handling None values.
    """
    return str(value) if value is not None else ""


def extract_numeric_score(score_str: str) -> float:
    """
    Extract the numeric part of the score from a string.
    """
    match = re.match(r"(\d+\.\d+|\d+)", score_str)
    if match:
        return float(match.group(1))
    return 0.0


def get_score_color(score: float) -> str:
    """
    Determine the color to be used for displaying the score based on its value.
    """
    if score >= 0.03:
        return "bold red"
    elif score >= 0.02:
        return "red"
    else:
        return "dim"


def create_status_icon(is_true: bool) -> Text:
    """
    Create a modern status icon based on a boolean value.
    """
    if is_true:
        return Text("●", style=Style(color="red"))
    else:
        return Text("●", style=Style(color="white", dim=True))


def create_rich_table(data: List[Dict[str, Any]]) -> Table:
    """
    Create a rich table displaying IP information.
    """
    table = Table(
        title="IP Information",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
    )

    table.add_column("IP Address", style="bold cyan", no_wrap=True)
    table.add_column("Country", style="bold yellow")
    table.add_column("City", style="bold yellow")
    table.add_column("ASN Type", style="bold green")
    table.add_column("Domain", style="bold magenta")
    table.add_column("Is Datacenter", style="bold red", justify="center")
    table.add_column("Is Tor", style="bold red", justify="center")
    table.add_column("Is Proxy", style="bold red", justify="center")
    table.add_column("Is VPN", style="bold red", justify="center")
    table.add_column("Is Abuser", style="bold red", justify="center")
    table.add_column("Abuser Score", style="bold red", justify="right")
    table.add_column("ASN Abuser Score", style="bold red", justify="right")

    for item in data:
        company_score_str = safe_str(item.get("company_abuser_score", "0"))
        asn_score_str = safe_str(item.get("asn_abuser_score", "0"))

        company_score = extract_numeric_score(company_score_str)
        asn_score = extract_numeric_score(asn_score_str)

        company_score_color = get_score_color(company_score)
        asn_score_color = get_score_color(asn_score)

        table.add_row(
            safe_str(item.get("ip")),
            safe_str(item.get("location_country")),
            safe_str(item.get("location_city")),
            safe_str(item.get("asn_type")),
            safe_str(item.get("company_domain")),
            create_status_icon(item.get("is_datacenter") == "True"),
            create_status_icon(item.get("is_tor") == "True"),
            create_status_icon(item.get("is_proxy") == "True"),
            create_status_icon(item.get("is_vpn") == "True"),
            create_status_icon(item.get("is_abuser") == "True"),
            Text(company_score_str, style=company_score_color),
            Text(asn_score_str, style=asn_score_color),
        )

    return table
