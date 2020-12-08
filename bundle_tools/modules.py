"""
A module that handles modules on a CircuitPython device.

-----------

Classes list:

No classes!

-----------

Functions list:

- get_lib_path(device_drive: Path = None) -> Path
- list_modules(start_path: Path = None) -> list
- install_module(module_path: Path = None, device_path: Path = None) -> None
- uninstall_module(module_path: Path = None) -> None

"""

from pathlib import Path
from shutil import copy2, copytree


def get_lib_path(device_drive: Path = None) -> Path:
    """
    Passing in the device path (ex. "I:") will return the path of the lib directory

    :param device_drive: A pathlib.Path object that points to the device. Example: "I:" on Windows.
    Defaults to None, and will raise an exception if no compatible object is passed in.

    :return: A pathlib.Path object pointing to the lib directory on a CircuitPython device.
    """
    return device_drive / "lib"


def list_modules(start_path: Path = None) -> list:
    """
    Passing in the device path (ex. "I:") will return a list of pathlib.Path objects pointing to the module paths
    - stringify them to get the module names.

    :param start_path: A pathlib.Path object that points to the device. Example: "I:" on Windows.
    Defaults to None, and will raise an exception if no compatible object is passed in.

    :return: A list of pathlib.Path objects pointing to the path of the modules.
    """
    lib_directory: Path = get_lib_path(start_path)
    if not lib_directory.exists():
        raise RuntimeError(f"The lib directory '{lib_directory}' does not exist on the CircuitPython device!")
    return list(lib_directory.glob("*"))


def install_module(module_path: Path = None, device_path: Path = None) -> None:
    """
    Pass in the path to the module (ex. ".../adafruit-circuitpython-bundle-6.x-mpy-20201126/lib/adafruit_bus_device")
    and the device path (ex. "I:lib") will copy the directory/file to the device.

    :param module_path: A pathlib.Path object that points to the path of the module. Defaults to None, and will raise
    an exception if no compatible object is passed in.

    :param device_path: A pathlib.Path object that points to the path of the device's lib directory. Defaults to None,
    and will raise an exception if no compatible object is passed in.

    :return: None
    """
    if module_path.is_file():
        copy2(module_path, device_path)
    else:
        copytree(module_path, device_path / module_path.stem)


def uninstall_module(module_path: Path = None) -> None:
    """
    Pass in the path to the module (ex. "I:lib/adafruit_bus_device") on
    the device will delete the directory/file on the device.

    :param module_path: A pathlib.Path object that points to the path of the module ON THE DEVICE. Defaults to None,
    and will raise an exception if no compatible object is passed in.

    :return: None
    """
    if module_path.is_file():
        module_path.unlink()
    else:
        module_path.rmdir()
