import logging
import sys
import time

_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(module)s:%(lineno)d - %(funcName)s - %(message)s"
_log_formatter = logging.Formatter(_log_format)


def _get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_log_formatter)
    console_handler.formatter.converter = time.gmtime

    return console_handler


def get_logger(name):
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)

    # leave the handlers level at NOTSET so the level checking is only handled by the logger
    logger.addHandler(_get_console_handler())

    # no propagation to avoid propagating to root logger
    logger.propagate = False

    return logger


print(f">>> init logging <<<")

# Set some shortcuts
logging.Logger.d = logging.Logger.debug
logging.Logger.i = logging.Logger.info

LOG = get_logger("sl")
