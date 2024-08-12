import configparser
import importlib.resources as pkg_resources
from iplens import config_loader


def load_config(config_file="config.cfg"):
    """
    Load configuration from a file within the package.

    Args:
        config_file (str): Path to the configuration file. Defaults to "config.cfg".

    Returns:
        configparser.ConfigParser: Loaded configuration object.
    """
    config = configparser.ConfigParser()

    with pkg_resources.path(config_loader, config_file) as config_path:
        config.read(config_path)

    return config


def get_all_config_values(config):
    """
    Get all configuration values from the loaded configuration.

    Args:
        config (configparser.ConfigParser): Configuration object.

    Returns:
        dict: Dictionary of configuration values organized by section.
    """
    config_values = {
        section: {key: config.get(section, key) for key in config[section]}
        for section in config.sections()
    }
    return config_values
