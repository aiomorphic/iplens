import logging
import time
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from iplens.base_operations import IPInfoOperation
from iplens.config_loader import DEFAULT_API_URL, load_config, normalize_api_url
from iplens.db_cache import DBCache
from iplens.logger import logger
from iplens.utils import FIELDNAMES, chunks, dedupe_ips

REQUEST_TIMEOUT = 30
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class IPInfoAPI(IPInfoOperation):
    def __init__(self):
        config = load_config()
        api_url = normalize_api_url(
            config.get("API", "url", fallback=DEFAULT_API_URL)
        )
        backoff_factor = int(config.get("API", "backoff_factor", fallback=2))
        timeout = int(config.get("API", "timeout", fallback=REQUEST_TIMEOUT))
        super().__init__(api_url, backoff_factor)
        self.timeout = timeout
        self.cache = DBCache()
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=list(RETRY_STATUS_CODES),
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch_data(self, ips: List[str], chunk_size: int = 100) -> List[Dict[str, Any]]:
        unique_ips = dedupe_ips(ips)
        response_data_list: List[Dict[str, Any]] = []
        ips_to_fetch: List[str] = []
        fetched_from_cache = 0
        fetched_from_api = 0
        failed_requests = 0

        logger.info(f"Starting to fetch data for {len(unique_ips)} IP(s)...")

        for ip in unique_ips:
            cached_data = self.cache.get(ip)
            if cached_data:
                logger.info(f"Using cached data for IP: {ip}")
                response_data_list.append(cached_data)
                fetched_from_cache += 1
            else:
                ips_to_fetch.append(ip)

        if len(ips_to_fetch) == 1:
            api_count, fail_count = self._fetch_ips_individually(
                ips_to_fetch, response_data_list
            )
            fetched_from_api += api_count
            failed_requests += fail_count
        elif len(ips_to_fetch) >= 2:
            api_count, fail_count = self._fetch_ips_in_chunks(
                ips_to_fetch, response_data_list, chunk_size
            )
            fetched_from_api += api_count
            failed_requests += fail_count

        summary = (
            f"Summary: {fetched_from_cache} IP(s) from cache, "
            f"{fetched_from_api} IP(s) from API, "
            f"{failed_requests} IP(s) failed."
        )
        if failed_requests:
            logger.warning(summary)
        else:
            logger.info(summary)

        return response_data_list

    def _fetch_ips_individually(
        self, ips: List[str], response_data_list: List[Dict[str, Any]]
    ) -> tuple[int, int]:
        fetched = 0
        failed = 0
        for ip in ips:
            if self._fetch_and_store_single(ip, response_data_list):
                fetched += 1
            else:
                failed += 1
        return fetched, failed

    def _fetch_ips_in_chunks(
        self,
        ips_to_fetch: List[str],
        response_data_list: List[Dict[str, Any]],
        chunk_size: int,
    ) -> tuple[int, int]:
        fetched = 0
        failed = 0
        chunk_list = list(chunks(ips_to_fetch, chunk_size))

        for index, ip_chunk in enumerate(chunk_list):
            chunk_fetched, chunk_failed = self._fetch_chunk(
                ip_chunk, response_data_list
            )
            fetched += chunk_fetched
            failed += chunk_failed

            if index < len(chunk_list) - 1:
                time.sleep(self.backoff_factor)

        return fetched, failed

    def _fetch_chunk(
        self, ip_chunk: List[str], response_data_list: List[Dict[str, Any]]
    ) -> tuple[int, int]:
        try:
            response_data = self._fetch_ip_info(ip_chunk)
            fetched = 0
            for ip, ip_data in response_data.items():
                if ip == "total_elapsed_ms":
                    continue
                processed_data = self.process_response(ip_data)
                response_data_list.append(processed_data)
                self.cache.set(ip, processed_data)
                fetched += 1
            logger.info(f"Bulk request succeeded for {fetched} IP(s).")
            return fetched, 0
        except requests.RequestException as error:
            self._log_request_error("Error during bulk request", error)
            return self._fetch_ips_individually(ip_chunk, response_data_list)

    def _fetch_and_store_single(
        self, ip: str, response_data_list: List[Dict[str, Any]]
    ) -> bool:
        try:
            response_data = self._fetch_single_ip_info(ip)
            processed_data = self.process_response(response_data)
            response_data_list.append(processed_data)
            self.cache.set(ip, processed_data)
            return True
        except requests.RequestException as error:
            self._log_request_error(f"Error fetching IP {ip}", error)
            return False

    def _log_request_error(self, message: str, error: requests.RequestException) -> None:
        logger.error(f"{message}: {error}")
        response = getattr(error, "response", None)
        if response is not None:
            logger.error(f"Response content: {response.text}")

    def _fetch_ip_info(self, ips: List[str]) -> Dict:
        logger.info(f"Making bulk request for {len(ips)} IP(s)")
        response = self.session.post(
            self.api_url,
            json={"ips": ips},
            timeout=self.timeout,
        )
        if not response.ok:
            logger.error(f"Bulk request failed with status code {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
        return response.json()

    def _fetch_single_ip_info(self, ip: str) -> Dict:
        logger.info(f"Making single request for IP: {ip}")
        response = self.session.get(
            f"{self.api_url}?q={ip}",
            timeout=self.timeout,
        )
        if not response.ok:
            logger.error(
                f"Single request failed for IP {ip} with status code {response.status_code}"
            )
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
        return response.json()

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        if not response or not isinstance(response, dict):
            logger.warning(f"Invalid response received: {response}")
            return {field: "" for field in FIELDNAMES}

        data: Dict[str, str] = {}
        for field in FIELDNAMES:
            try:
                parts = field.split("_")
                if len(parts) == 1:
                    value = response.get(field)
                else:
                    category, subfield = parts[0], "_".join(parts[1:])
                    category_data = response.get(category, {})
                    if not isinstance(category_data, dict):
                        value = response.get(field)
                    else:
                        value = category_data.get(subfield)
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
            except (TypeError, AttributeError, KeyError) as error:
                logger.error(f"Error processing field {field}: {error}")
                data[field] = ""

        if (
            "rir" in FIELDNAMES
            and "asn" in response
            and isinstance(response["asn"], dict)
        ):
            data["rir"] = str(response["asn"].get("rir", "") or "")

        return data

    def clear_expired_cache(self) -> int:
        logger.info("Clearing expired cache entries")
        return self.cache.clear_expired()

    def clear_all_cache(self) -> int:
        logger.info("Clearing entire cache")
        return self.cache.clear_all()
