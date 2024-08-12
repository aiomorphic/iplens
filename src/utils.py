import ipaddress
import re

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

LOCAL_IPS = [
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


def is_local_ip(ip: str) -> bool:
    """
    Check if the IP is a local/private IP address.

    Args:
        ip (str): The IP address to check.

    Returns:
        bool: True if the IP is local or private, False otherwise.
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        for local_ip in LOCAL_IPS:
            if ip_obj in ipaddress.ip_network(local_ip):
                return True
    except ValueError:
        pass
    return False


def is_valid_ip(ip: str) -> bool:
    """
    Validate if the given string is a valid IP address and not a local IP.

    Args:
        ip (str): The IP address string to validate.

    Returns:
        bool: True if the IP is valid and not local, False otherwise.
    """
    disallowed_keywords = ["version", "ver", "v"]
    if any(keyword in ip.lower() for keyword in disallowed_keywords):
        return False

    ip_pattern = re.compile(r"^(?!0)(?!.*\.\.)(?!.*\.\d+\.$)(\d{1,3}\.){3}\d{1,3}$")
    if ip_pattern.match(ip):
        try:
            ip_obj = ipaddress.ip_address(ip)
            return not is_local_ip(str(ip_obj))
        except ValueError:
            return False
    return False


def chunks(lst, n):
    """
    Yield successive n-sized chunks from a list.

    Args:
        lst (list): The list to split into chunks.
        n (int): The size of each chunk.

    Yields:
        list: A chunk of the original list.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
