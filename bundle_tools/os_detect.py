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
    return platform == OS.WINDOWS.value


def on_mac() -> bool:
    """
    Returns a bool whether we are on Mac OSX or not.
    :return: A bool whether we are on Mac OSX or not.
    """
    return platform == OS.MAC.value


def on_linux() -> bool:
    """
    Returns a bool whether we are on Linux or not.
    :return: A bool whether we are on Linux or not.
    """
    return platform == OS.LINUX.value
