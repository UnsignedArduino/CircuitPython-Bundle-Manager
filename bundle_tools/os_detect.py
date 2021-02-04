"""
A module that detects and abstracts detecting what OS we are on.

-----------

Classes list:

- UnknownPlatform(OSError)
- OS(Enum)

-----------

Functions list:

- on_windows() -> bool
- on_mac() -> bool
- on_linux() -> bool

"""

from platform import system
from enum import Enum
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


class UnknownPlatform(OSError):
    """Unknown platform - does not match 'Windows', 'Darwin', or 'Linux'."""


class OS(Enum):
    """An Enum of the values platform.system() return. Enum contents: WINDOWS, MAC, and LINUX"""
    WINDOWS = "Windows"
    MAC = "Darwin"
    LINUX = "Linux"


platform: str = system()


def on_windows() -> bool:
    """
    Returns a bool whether we are on Windows or not.

    :return: A bool whether we are on Windows or not.
    """
    logger.debug(f"We are on Windows!" if platform == OS.WINDOWS.value else f"We aren't on Windows!")
    return platform == OS.WINDOWS.value


def on_mac() -> bool:
    """
    Returns a bool whether we are on Mac OSX or not.

    :return: A bool whether we are on Mac OSX or not.
    """
    logger.debug(f"We are on Mac OSX!" if platform == OS.MAC.value else f"We aren't on Mac OSX!")
    return platform == OS.MAC.value


def on_linux() -> bool:
    """
    Returns a bool whether we are on Linux or not.

    :return: A bool whether we are on Linux or not.
    """
    logger.debug(f"We are on Linux!" if platform == OS.LINUX.value else f"We aren't on Linux!")
    return platform == OS.LINUX.value
