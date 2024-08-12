from unittest.mock import Mock, patch

import pytest
import requests

from src.ipapi_api import IPInfoAPI
from src.db_cache import DBCache


@pytest.fixture
def mock_db_cache():
    return Mock(spec=DBCache)


@pytest.fixture
def ip_info_api(mock_db_cache):
    with patch("src.api.DBCache", return_value=mock_db_cache):
        return IPInfoAPI()


@pytest.fixture
def sample_ip_data():
    return {
        "ip": "172.71.223.44",
        "rir": "ARIN",
        "company_name": "Cloudflare, Inc.",
        "asn_asn": "13335",
        "location_country": "United States",
    }


def test_fetch_data_cached(ip_info_api, mock_db_cache, sample_ip_data):

    mock_db_cache.get.return_value = sample_ip_data

    result = ip_info_api.fetch_data(["172.71.223.44"])

    assert result[0]["ip"] == sample_ip_data["ip"]
    assert result[0]["rir"] == sample_ip_data["rir"]

    print(f"mock_db_cache.get.call_count: {mock_db_cache.get.call_count}")
    mock_db_cache.get.assert_called_once_with("172.71.223.44")


@patch("src.api.requests.get")
def test_fetch_data_single_ip(mock_get, ip_info_api, mock_db_cache, sample_ip_data):
    mock_db_cache.get.return_value = None
    mock_get.return_value.json.return_value = sample_ip_data
    mock_get.return_value.ok = True

    result = ip_info_api.fetch_data(["172.71.223.44"])

    expected_result = {
        "ip": "172.71.223.44",
        "rir": "ARIN",
        "company_name": "Cloudflare, Inc.",
        "asn_asn": "AS13335",
        "location_country": "United States",
        "company_abuser_score": "",
        "asn_abuser_score": "",
        "is_bogon": "",
        "is_datacenter": "",
        "is_tor": "",
        "is_proxy": "",
        "is_vpn": "",
        "is_abuser": "",
        "company_domain": "",
        "company_network": "",
        "company_whois": "",
        "asn_route": "",
        "asn_descr": "",
        "asn_country": "",
        "asn_active": "",
        "asn_org": "",
        "asn_domain": "",
        "asn_abuse": "",
        "asn_type": "",
        "asn_created": "",
        "asn_updated": "",
        "asn_rir": "",
        "asn_whois": "",
        "location_country_code": "",
        "location_state": "",
        "location_city": "",
        "location_latitude": "",
        "location_longitude": "",
        "location_zip": "",
        "location_timezone": "",
    }

    filtered_result = {key: result[0].get(key, "") for key in expected_result.keys()}

    assert filtered_result == expected_result
    mock_get.assert_called_once_with(f"{ip_info_api.api_url}?q=172.71.223.44")
    mock_db_cache.set.assert_called_once()


@patch("src.api.requests.post")
def test_fetch_data_bulk(mock_post, ip_info_api, mock_db_cache):
    mock_db_cache.get.return_value = None
    mock_post.return_value.json.return_value = {
        "172.71.223.44": {"ip": "172.71.223.44", "rir": "ARIN"},
        "8.8.8.8": {"ip": "8.8.8.8", "rir": "ARIN"},
        "total_elapsed_ms": 100,
    }
    mock_post.return_value.ok = True

    result = ip_info_api.fetch_data(["172.71.223.44", "8.8.8.8"])

    assert len(result) == 2
    assert all(ip_data["rir"] == "ARIN" for ip_data in result)
    mock_post.assert_called_once_with(
        ip_info_api.api_url, json={"ips": ["172.71.223.44", "8.8.8.8"]}
    )
    assert mock_db_cache.set.call_count == 2

    filtered_result = [{k: v for k, v in ip_data.items() if v} for ip_data in result]

    for ip_data in filtered_result:
        assert set(ip_data.keys()) == {"ip", "rir"}
        assert ip_data["ip"] in ["172.71.223.44", "8.8.8.8"]
        assert ip_data["rir"] == "ARIN"


def test_process_response(ip_info_api, sample_ip_data):
    processed_data = ip_info_api.process_response(sample_ip_data)

    assert processed_data["ip"] == "172.71.223.44"
    assert processed_data["rir"] == "ARIN"
    assert processed_data["company_name"] == "Cloudflare, Inc."
    assert processed_data["asn_asn"] == "AS13335"
    assert processed_data["location_country"] == "United States"


@patch("src.api.requests.get")
def test_fetch_single_ip_info_error(mock_get, ip_info_api):
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "404 Client Error: Not Found"
    )

    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError) as exc_info:
        ip_info_api._fetch_single_ip_info("172.71.223.44")

    assert "404 Client Error: Not Found" in str(exc_info.value)
    mock_get.assert_called_once_with(f"{ip_info_api.api_url}?q=172.71.223.44")


@patch("src.api.requests.post")
def test_fetch_ip_info_error(mock_post, ip_info_api):
    mock_post.return_value.ok = False
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Internal Server Error"
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
        "500 Server Error: Internal Server Error"
    )

    with pytest.raises(requests.HTTPError):
        ip_info_api._fetch_ip_info(["172.71.223.44", "8.8.8.8"])


def test_clear_expired_cache(ip_info_api, mock_db_cache):
    ip_info_api.clear_expired_cache()
    mock_db_cache.clear_expired.assert_called_once()
