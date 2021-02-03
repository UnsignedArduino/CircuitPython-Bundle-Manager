"""
A module that handles drives.

-----------

Classes list:

No classes!

-----------

Functions list:

- list_connected_drives(circuitpython_only: bool = True, drive_mount_point: Path = "/media") -> list

"""

from pathlib import Path
from string import ascii_uppercase
from bundle_tools import os_detect
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


def list_connected_drives(circuitpython_only: bool = True, drive_mount_point: Path = Path("/media")) -> list[Path]:
    """
    Returns a list of connected drives. On Windows, this will be something like `[WindowsPath('C:'), ...]`.

    :param circuitpython_only: A bool telling whether to filter out non-CircuitPython drives. Defaults to True.

    :param drive_mount_point: A pathlib.Path object pointing to where drives are mounted. Applies only to unix-based
     systems.

    :return: A list of pathlib.Path objects that contain the drives.
    """
    connected_drives: list = []
    logger.debug("Testing for CircuitPython drives" if circuitpython_only else "Not testing for CircuitPython drives!")
    logger.debug(f"Drive mount point is {repr(drive_mount_point)}")
    if os_detect.on_windows():
        logger.debug(f"Platform is Windows!")
        # Since you only can have up to 26 drive letters, then just loop over all the letters
        for letter in ascii_uppercase:
            # If we are looking for CircuitPython drives, also look for boot_out.txt
            drive_path = Path(f"{letter}:") / "boot_out.txt" if circuitpython_only else Path(f"{letter}:")
            if drive_path.exists():
                connected_drives.append(drive_path.parent)
    elif os_detect.on_mac():
        logger.debug("Platform is Mac OSX!")
        logger.info("Hey, if this works, please tell me at "
                    "https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/issues!")
        logger.info(f"If it doesn't, still tell me please!")
        # TODO: Someone test this!
        for path in drive_mount_point.glob("*"):
            if circuitpython_only and (path / "boot_out.txt").exists():
                connected_drives.append(path)
            else:
                connected_drives.append(path)
    elif os_detect.on_linux():
        logger.debug("Platform is Linux!")
        for path in drive_mount_point.glob("*"):
            try:
                if circuitpython_only and (path / "boot_out.txt").exists():
                    connected_drives.append(path)
                else:
                    connected_drives.append(path)
            except PermissionError:
                if not circuitpython_only:
                    connected_drives.append(path)
    else:
        logger.error("Unknown platform!")
        raise os_detect.UnknownPlatform("Unknown platform - does not know how to search for drives")
    logger.info(f"Connected drives are {repr(connected_drives)}" + (" (CircuitPython only!)" if circuitpython_only else ""))
    return connected_drives
