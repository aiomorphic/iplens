import logging

from rich.logging import RichHandler

from iplens.config_loader import load_config

config = load_config()
log_level_str = config.get("Logging", "level", fallback="INFO").upper()


log_level = getattr(logging, log_level_str, logging.INFO)


logging.basicConfig(
    level=log_level,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)


logger = logging.getLogger("iplens")
