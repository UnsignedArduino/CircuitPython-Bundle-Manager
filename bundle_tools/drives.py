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


def list_connected_drives(circuitpython_only: bool = True, drive_mount_point: Path = Path("/media")) -> list:
    """
    Returns a list of connected drives. On Windows, this will be something like `[WindowsPath('C:'), ...]`.

    :param circuitpython_only: A bool telling whether to filter out non-CircuitPython drives. Defaults to True.

    :param drive_mount_point: A pathlib.Path object pointing to where drives are mounted. Applies only to unix-based
     systems.

    :return: A list of pathlib.Path objects that contain the drives.
    """
    connected_drives: list = []
    if os_detect.on_windows():
        # Since you only can have up to 26 drive letters, then just loop over all the letters
        for letter in ascii_uppercase:
            # If we are looking for CircuitPython drives, also look for boot_out.txt
            drive_path = Path(f"{letter}:") / "boot_out.txt" if circuitpython_only else Path(f"{letter}:")
            if drive_path.exists():
                connected_drives.append(drive_path.parent)
    elif os_detect.on_mac():
        # TODO: Someone test this!
        for path in drive_mount_point.glob("*"):
            if circuitpython_only and (path / "boot_out.txt").exists():
                connected_drives.append(path)
            else:
                connected_drives.append(path)
    elif os_detect.on_linux():
        for path in drive_mount_point.glob("*"):
            if circuitpython_only and (path / "boot_out.txt").exists():
                connected_drives.append(path)
            else:
                connected_drives.append(path)
    else:
        raise os_detect.UnknownPlatform("Unknown platform - does not know how to search for drives")
    return connected_drives
