import logging
import time
from typing import Any, Dict, List

import requests

from iplens.base_operations import IPInfoOperation
from iplens.config_loader import load_config
from iplens.db_cache import DBCache
from iplens.logger import logger
from iplens.utils import FIELDNAMES


class IPInfoAPI(IPInfoOperation):
    def __init__(self):
        """
        Initialize the IPInfoAPI class with API URL and backoff factor loaded from the configuration file.
        The class also initializes the cache for storing IP information.
        """
        config = load_config()
        api_url = config.get("API", "url")
        backoff_factor = int(config.get("API", "backoff_factor"))
        super().__init__(api_url, backoff_factor)
        self.cache = DBCache()

    def fetch_data(self, ips: List[str], chunk_size: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch data for a list of IP addresses. The method checks the cache first,
        and if the IP information is not available, it fetches the data from the API.

        Args:
            ips (List[str]): List of IP addresses to fetch data for.
            chunk_size (int): Number of IPs to fetch in each bulk request. Default is 100.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the processed data for each IP address.
        """
        response_data_list = []
        ips_to_fetch = []
        fetched_from_cache = 0
        fetched_from_api = 0
        failed_requests = 0

        logger.info(f"Starting to fetch data for {len(ips)} IP(s)...")

        for ip in ips:
            cached_data = self.cache.get(ip)
            if cached_data:
                logger.info(f"Using cached data for IP: {ip}")
                logger.info("Local cache DB source used")
                response_data_list.append(cached_data)
                fetched_from_cache += 1
            else:
                logger.info(f"IP {ip} not found in cache, adding to fetch list")
                ips_to_fetch.append(ip)

        if len(ips_to_fetch) > 0 and len(ips_to_fetch) < 2:
            logger.info("Using regular requests for fewer than 2 IPs")
            for ip in ips_to_fetch:
                try:
                    response_data = self._fetch_single_ip_info(ip)
                    processed_data = self.process_response(response_data)
                    response_data_list.append(processed_data)
                    self.cache.set(ip, processed_data)
                    logger.info(f"Fetched and cached data for IP: {ip}")
                    fetched_from_api += 1
                except requests.HTTPError as e:
                    logger.error(f"Error fetching IP {ip}: {e}")
                    logger.error(f"Response content: {e.response.text}")
                    failed_requests += 1

        elif len(ips_to_fetch) >= 2:
            logger.info("Using bulk request for 2 or more IPs")
            for i in range(0, len(ips_to_fetch), chunk_size):
                ip_chunk = ips_to_fetch[i : i + chunk_size]
                try:
                    response_data = self._fetch_ip_info(ip_chunk)
                    for ip, ip_data in response_data.items():
                        if ip != "total_elapsed_ms":
                            processed_data = self.process_response(ip_data)
                            response_data_list.append(processed_data)
                            self.cache.set(ip, processed_data)
                            logger.info(f"Fetched and cached data for IP: {ip}")
                            fetched_from_api += 1
                    logger.info(
                        f"Processed IPs {i+1} to {i+len(ip_chunk)} of {len(ips_to_fetch)}."
                    )
                    time.sleep(self.backoff_factor)
                except requests.HTTPError as e:
                    logger.error(f"Error during bulk request: {e}")
                    logger.error(f"Response content: {e.response.text}")
                    failed_requests += 1

        if logger.isEnabledFor(logging.WARNING):
            logger.warning(
                f"Summary: {fetched_from_cache} IP(s) fetched from cache, "
                f"{fetched_from_api} IP(s) fetched from API, "
                f"{failed_requests} IP(s) failed due to issues."
            )

        return response_data_list

    def _fetch_ip_info(self, ips: List[str]) -> Dict:
        """
        Fetch information for a list of IP addresses in bulk.

        Args:
            ips (List[str]): List of IP addresses to fetch data for.

        Returns:
            Dict: A dictionary with IP addresses as keys and their corresponding data as values.
        """
        logger.info(f"Making bulk request for {len(ips)} IP(s)")
        ips_dict = {"ips": ips}
        response = requests.post(self.api_url, json=ips_dict)
        if not response.ok:
            logger.error(f"Bulk request failed with status code {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
        logger.info("Bulk request successful")
        return response.json()

    def _fetch_single_ip_info(self, ip: str) -> Dict:
        """
        Fetch information for a single IP address.

        Args:
            ip (str): The IP address to fetch data for.

        Returns:
            Dict: A dictionary containing the data for the IP address.
        """
        logger.info(f"Making single request for IP: {ip}")
        response = requests.get(f"{self.api_url}?q={ip}")
        if not response.ok:
            logger.error(
                f"Single request failed for IP {ip} with status code {response.status_code}"
            )
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
        logger.info(f"Single request successful for IP: {ip}")
        return response.json()

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the response data from the API, extracting and formatting the relevant fields.

        Args:
            response (Dict[str, Any]): The API response for a single IP address.

        Returns:
            Dict[str, Any]: A dictionary with the processed IP information.
        """
        if not isinstance(response, dict):
            logger.warning("Response is not a dictionary, returning empty data")
            return {}

        data = {}
        for field in FIELDNAMES:
            parts = field.split("_")
            if len(parts) == 1:
                value = response.get(field)
            else:
                category, subfield = parts[0], "_".join(parts[1:])
                value = response.get(category, {}).get(subfield)
                if value is None:
                    value = response.get(field)

            if value is not None:
                if field == "asn_asn" and value and not str(value).startswith("AS"):
                    value = f"AS{value}"

                if value is False:
                    value = "False"
                elif value is True:
                    value = "True"
                data[field] = str(value)
            else:
                data[field] = ""

        if "rir" in FIELDNAMES and "asn" in response and "rir" in response["asn"]:
            data["rir"] = response["asn"]["rir"]

        logger.debug(f"Processed response data: {data}")
        return data

    def clear_expired_cache(self):
        """
        Clear expired cache entries from the local cache.
        """
        logger.info("Clearing expired cache entries")
        self.cache.clear_expired()
