import configparser
import os


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
