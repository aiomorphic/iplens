import configparser
import os

DEFAULT_API_URL = "https://api.ipapi.is"
LEGACY_API_HOST = "api.incolumitas.com"


def normalize_api_url(url: str) -> str:
    """Map deprecated incolumitas endpoint to the current ipapi.is API."""
    cleaned = url.strip().rstrip("/")
    if LEGACY_API_HOST in cleaned:
        return DEFAULT_API_URL
    return cleaned


def load_config(config_file="config.cfg"):
    """
    Load configuration from a file within the package.

    Args:
        config_file (str): Path to the configuration file. Defaults to "config.cfg".

    Returns:
        configparser.ConfigParser: Loaded configuration object.
    """
    config = configparser.ConfigParser()

    # Resolve path relative to the current module
    config_path = os.path.join(os.path.dirname(__file__), config_file)

    # Read the configuration file
    config.read(config_path)

    return config
