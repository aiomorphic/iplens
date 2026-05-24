from unittest.mock import Mock, patch

import pytest
import requests

from iplens.db_cache import DBCache
from iplens.ipapi_api import IPInfoAPI
from iplens.utils import FIELDNAMES


@pytest.fixture
def mock_db_cache():
    return Mock(spec=DBCache)


@pytest.fixture
def ip_info_api(mock_db_cache):
    with patch("iplens.ipapi_api.DBCache", return_value=mock_db_cache):
        api = IPInfoAPI()
        api.session = Mock()
        return api


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
    mock_db_cache.get.assert_called_once_with("172.71.223.44")
    ip_info_api.session.get.assert_not_called()


def test_fetch_data_dedupes_ips(ip_info_api, mock_db_cache, sample_ip_data):
    mock_db_cache.get.return_value = sample_ip_data

    result = ip_info_api.fetch_data(["172.71.223.44", "172.71.223.44"])

    assert len(result) == 1
    assert mock_db_cache.get.call_count == 1


def test_fetch_data_single_ip(ip_info_api, mock_db_cache, sample_ip_data):
    mock_db_cache.get.return_value = None
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = sample_ip_data
    ip_info_api.session.get.return_value = mock_response

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
    ip_info_api.session.get.assert_called_once_with(
        f"{ip_info_api.api_url}?q=172.71.223.44",
        timeout=ip_info_api.timeout,
    )
    mock_db_cache.set.assert_called_once()


def test_fetch_data_bulk(ip_info_api, mock_db_cache):
    mock_db_cache.get.return_value = None
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "172.71.223.44": {"ip": "172.71.223.44", "rir": "ARIN"},
        "8.8.8.8": {"ip": "8.8.8.8", "rir": "ARIN"},
        "total_elapsed_ms": 100,
    }
    ip_info_api.session.post.return_value = mock_response

    result = ip_info_api.fetch_data(["172.71.223.44", "8.8.8.8"])

    assert len(result) == 2
    ip_info_api.session.post.assert_called_once_with(
        ip_info_api.api_url,
        json={"ips": ["172.71.223.44", "8.8.8.8"]},
        timeout=ip_info_api.timeout,
    )
    assert mock_db_cache.set.call_count == 2


def test_fetch_data_bulk_fallback_to_single(ip_info_api, mock_db_cache, sample_ip_data):
    mock_db_cache.get.return_value = None
    bulk_error = requests.HTTPError("bulk failed")
    bulk_error.response = Mock(text="error")

    single_response = Mock()
    single_response.ok = True
    single_response.json.return_value = sample_ip_data

    ip_info_api.session.post.side_effect = bulk_error
    ip_info_api.session.get.return_value = single_response

    result = ip_info_api.fetch_data(["172.71.223.44", "8.8.8.8"])

    assert len(result) == 2
    assert ip_info_api.session.get.call_count == 2


def test_process_alias(ip_info_api, mock_db_cache, sample_ip_data):
    mock_db_cache.get.return_value = sample_ip_data
    assert ip_info_api.process(["172.71.223.44"]) == ip_info_api.fetch_data(
        ["172.71.223.44"]
    )


def test_process_response(ip_info_api, sample_ip_data):
    processed_data = ip_info_api.process_response(sample_ip_data)
    assert processed_data["ip"] == "172.71.223.44"
    assert processed_data["asn_asn"] == "AS13335"


def test_fetch_single_ip_info_error(ip_info_api):
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "404 Client Error: Not Found"
    )
    ip_info_api.session.get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        ip_info_api._fetch_single_ip_info("172.71.223.44")


def test_fetch_ip_info_error(ip_info_api):
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "500 Server Error"
    )
    ip_info_api.session.post.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        ip_info_api._fetch_ip_info(["172.71.223.44", "8.8.8.8"])


def test_clear_expired_cache(ip_info_api, mock_db_cache):
    mock_db_cache.clear_expired.return_value = 3
    assert ip_info_api.clear_expired_cache() == 3
    mock_db_cache.clear_expired.assert_called_once()


def test_clear_all_cache(ip_info_api, mock_db_cache):
    mock_db_cache.clear_all.return_value = 10
    assert ip_info_api.clear_all_cache() == 10
    mock_db_cache.clear_all.assert_called_once()


def test_process_response_with_none_values(ip_info_api):
    sample_data_with_none = {
        "ip": "172.71.223.44",
        "asn": None,
        "location": None,
        "company": None,
    }
    processed_data = ip_info_api.process_response(sample_data_with_none)
    assert processed_data["ip"] == "172.71.223.44"
    assert processed_data["asn_asn"] == ""


def test_process_response_completely_none(ip_info_api):
    processed_data = ip_info_api.process_response(None)
    assert set(processed_data.keys()) == set(FIELDNAMES)
    assert all(v == "" for v in processed_data.values())


def test_fetch_data_logs_warning_when_failures(ip_info_api, mock_db_cache, caplog):
    import logging

    mock_db_cache.get.return_value = None
    ip_info_api.session.get.side_effect = requests.RequestException("network down")

    with caplog.at_level(logging.WARNING, logger="iplens"):
        result = ip_info_api.fetch_data(["172.71.223.44"])

    assert result == []
    assert any("failed" in record.message.lower() for record in caplog.records)
