from platform import system
from enum import Enum


class UnknownPlatform(OSError):
    """Unknown platform - does not match 'Windows', 'Darwin', or 'Linux'."""


class OS(Enum):
    WINDOWS = "Windows"
    MAC = "Darwin"
    LINUX = "Linux"


platform: str = system()


def on_windows() -> bool:
    return platform == OS.WINDOWS.value


def on_mac() -> bool:
    return platform == OS.MAC.value


def on_linux() -> bool:
    return platform == OS.LINUX.value
