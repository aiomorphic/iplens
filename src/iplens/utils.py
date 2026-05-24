import ipaddress
from typing import List

FIELDNAMES = [
    "ip",
    "rir",
    "is_bogon",
    "is_datacenter",
    "is_tor",
    "is_proxy",
    "is_vpn",
    "is_abuser",
    "company_name",
    "company_abuser_score",
    "company_type",
    "company_domain",
    "company_network",
    "company_whois",
    "abuse_email",
    "asn_asn",
    "asn_abuser_score",
    "asn_route",
    "asn_descr",
    "asn_country",
    "asn_active",
    "asn_org",
    "asn_domain",
    "asn_abuse",
    "asn_type",
    "asn_created",
    "asn_updated",
    "asn_rir",
    "asn_whois",
    "location_country",
    "location_country_code",
    "location_state",
    "location_city",
    "location_latitude",
    "location_longitude",
    "location_zip",
    "location_timezone",
]

LOCAL_IPV4_NETWORKS = [
    "255.255.255.255",
    "127.0.0.0/8",
    "0.0.0.0",
    "0.9.9.9",
    "224.0.0.22",
    "169.254.0.0/16",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]

DISALLOWED_IP_SUBSTRINGS = ("version", "ver")


def is_local_ip(ip: str) -> bool:
    """Return True if the IPv4 address is local, private, or otherwise non-public."""
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if ip_obj.version != 4:
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        )
    for network in LOCAL_IPV4_NETWORKS:
        if ip_obj in ipaddress.ip_network(network):
            return True
    return False


def is_valid_ip(ip: str) -> bool:
    """Validate a public IPv4 or IPv6 address string."""
    candidate = ip.strip()
    lowered = candidate.lower()
    if any(keyword in lowered for keyword in DISALLOWED_IP_SUBSTRINGS):
        return False
    try:
        ip_obj = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return not is_local_ip(str(ip_obj))


def dedupe_ips(ips: List[str]) -> List[str]:
    """Return unique IPs preserving first-seen order."""
    seen = set()
    unique: List[str] = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            unique.append(ip)
    return unique


def chunks(items: List[str], size: int):
    """Yield successive fixed-size chunks from a list."""
    for index in range(0, len(items), size):
        yield items[index : index + size]
