"""
A module that creates a simple logger and returns it.

-----------

Classes list:

No classes!

-----------

Functions list:

- create_logger(name: str = __name__, level: int = logging.DEBUG) -> logging.getLogger

"""

import logging


def create_logger(name: str = __name__, level: int = logging.DEBUG) -> logging.getLogger:
    """
    A simple function to create a logger. You would typically put this right under all the other modules you imported:

    -----------

    from bundle_tools.create_logger import create_logger

    import logging

    logger = create_logger(name=__name__, level=logging.DEBUG)

    -----------

    And then call `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`, `logger.critical()`, and
    `logger.exception` everywhere in that module.

    :param name: A string with the logger name. Defaults to __name__.

    :param level: A integer with the logger level. Defaults to logging.DEBUG.

    :return: A logging.getLogger which you can use as a regular logger.
    """
    logger = logging.getLogger(name=name)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level=level)
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(fmt=console_formatter)
    console_handler.setLevel(level=level)
    logger.propagate = False
    if console_handler not in logger.handlers:
        logger.addHandler(hdlr=console_handler)
    logger.setLevel(level=level)
    logger.debug(f"Created logger named {repr(name)} with level {repr(level)}")
    logger.debug(f"Handlers for {repr(name)}: {repr(logger.handlers)}")
    return logger
