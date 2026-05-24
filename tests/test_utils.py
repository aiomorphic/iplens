from iplens.utils import dedupe_ips, is_valid_ip


def test_dedupe_ips_preserves_order():
    assert dedupe_ips(["1.1.1.1", "8.8.8.8", "1.1.1.1"]) == ["1.1.1.1", "8.8.8.8"]


def test_is_valid_ip_ipv4_public():
    assert is_valid_ip("8.8.8.8")


def test_is_valid_ip_ipv4_private_rejected():
    assert not is_valid_ip("192.168.1.1")


def test_is_valid_ip_ipv6_public():
    assert is_valid_ip("2001:4860:4860::8888")


def test_is_valid_ip_ipv6_private_rejected():
    assert not is_valid_ip("fe80::1")
