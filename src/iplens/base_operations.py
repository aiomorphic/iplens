from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

T = TypeVar("T")


class BaseOperation(ABC, Generic[T]):
    @abstractmethod
    def process(self, data: T) -> List[Dict[str, Any]]:
        """
        Process the input data.

        Args:
            data (T): Input data to process.

        Returns:
            List[Dict[str, Any]]: Processed data.
        """
        pass


class IPInfoOperation(BaseOperation[List[str]]):
    def __init__(self, api_url: str, backoff_factor: int):
        self.api_url = api_url
        self.backoff_factor = backoff_factor

    @abstractmethod
    def fetch_data(self, ips: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch data from the API.

        Args:
            ips (List[str]): List of IP addresses.

        Returns:
            List[Dict[str, Any]]: Fetched data.
        """
        pass

    @abstractmethod
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single API response.

        Args:
            response (Dict[str, Any]): API response for a single IP.

        Returns:
            Dict[str, Any]: Processed IP information.
        """
        pass

    def process(self, ips: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of IP addresses by fetching data and processing the response.

        Args:
            ips (List[str]): List of IP addresses.

        Returns:
            List[Dict[str, Any]]: Processed data for each IP address.
        """
        raw_data = self.fetch_data(ips)
        return [self.process_response(item) for item in raw_data]
