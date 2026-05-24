from iplens.config_loader import DEFAULT_API_URL, normalize_api_url


def test_normalize_api_url_keeps_current_endpoint():
    assert normalize_api_url("https://api.ipapi.is") == DEFAULT_API_URL


def test_normalize_api_url_rewrites_legacy_endpoint():
    assert (
        normalize_api_url("https://api.incolumitas.com")
        == DEFAULT_API_URL
    )
    assert (
        normalize_api_url("https://api.incolumitas.com/")
        == DEFAULT_API_URL
    )
