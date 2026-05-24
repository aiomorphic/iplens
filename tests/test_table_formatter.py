from iplens.table_formatter import (
    create_rich_table,
    create_status_icon,
    extract_numeric_score,
    get_score_color,
    safe_str,
)


def test_safe_str_handles_none():
    assert safe_str(None) == ""
    assert safe_str("x") == "x"


def test_extract_numeric_score():
    assert extract_numeric_score("0.0273 (Elevated)") == 0.0273
    assert extract_numeric_score("no digits") == 0.0


def test_get_score_color_thresholds():
    assert get_score_color(0.04) == "bold red"
    assert get_score_color(0.025) == "red"
    assert get_score_color(0.001) == "dim"


def test_create_status_icon_returns_bullet():
    assert create_status_icon(True).plain == "●"
    assert create_status_icon(False).plain == "●"


def test_create_rich_table_has_expected_columns():
    data = [
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
    table = create_rich_table(data)
    assert table.title == "IP Information"
    assert len(table.columns) == 12
    assert len(table.rows) == 1
