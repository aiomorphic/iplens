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
    config_path = pkg_resources.files(config_loader).joinpath(config_file)
    with config_path.open("r", encoding="utf-8") as config_file_handle:
        config.read_file(config_file_handle)
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
