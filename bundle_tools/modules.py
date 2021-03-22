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
from shutil import copy2, copytree, rmtree
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


def get_lib_path(device_drive: Path = None) -> Path:
    """
    Passing in the device path (ex. "I:") will return the path of the lib directory

    :param device_drive: A pathlib.Path object that points to the device. Example: "I:" on Windows.
    :return: A pathlib.Path object pointing to the lib directory on a CircuitPython device.
    """
    logger.debug(f"Lib path is {repr(device_drive / 'lib')}")
    return device_drive / "lib"


def list_modules(start_path: Path = None) -> list[str]:
    """
    Passing in the device path (ex. "I:") will return a list of strings containing the names of the modules.

    :param start_path: A pathlib.Path object that points to the device. Example: "I:" on Windows.
    :return: A list of strings with the name of the modules.
    """
    lib_directory: Path = get_lib_path(start_path)
    logger.debug(f"Lib path is {repr(lib_directory)}")
    if not lib_directory.exists():
        logger.error(f"The lib directory '{lib_directory}' does not exist on the CircuitPython device!")
        raise RuntimeError(f"The lib directory '{lib_directory}' does not exist on the CircuitPython device!")
    libs = [
        lib.name
        for lib in list(lib_directory.glob("*"))
        if lib.name[0] != "." # ignore hidden files
    ]
    logger.debug(f"Modules found: {repr(libs)}")
    # sort the modules here, so we have a stable list
    libs.sort()
    return libs


def list_modules_in_bundle(start_path: Path) -> list[str]:
    """
    Passing in a path to the bundle (ex.
    E:/CircuitPython Bundle Manager/bundles/6/1608213643.5342305/adafruit-circuitpython-bundle-6.x-mpy-20201217/lib/)
    will return a list of strings containing the names of the modules inside.

    :param start_path: A pathlib.Path object that points to the device. Example:
      "adafruit-circuitpython-bundle-6.x-mpy-20201217/lib/".
    :return: A list of strings with the name of the modules.
    """
    libs = list(start_path.glob("*"))
    for index, lib in enumerate(libs):
        libs[index] = lib.name
    logger.debug(f"Modules found in bundle: {repr(libs)}")
    return libs


def install_module(module_path: Path = None, device_path: Path = None) -> None:
    """
    Pass in the path to the module (ex. ".../adafruit-circuitpython-bundle-6.x-mpy-20201126/lib/adafruit_bus_device")
    and the device path (ex. "I:lib") will copy the directory/file to the device.

    :param module_path: A pathlib.Path object that points to the path of the module.
    :param device_path: A pathlib.Path object that points to the path of the device's lib directory.
    :return: None
    """
    if not module_path.exists():
        logger.error(f"{module_path} does not exist!")
        raise FileNotFoundError(f"{module_path} does not exist!")
    if not device_path.exists():
        logger.error(f"{device_path} does not exist!")
        raise FileNotFoundError(f"{device_path} does not exist!")
    if module_path.is_file():
        logger.debug(f"Installing {repr(module_path)} to {repr(device_path)}...")
        copy2(module_path, device_path)
    else:
        logger.debug(f"Installing {repr(module_path)} to {repr(device_path / module_path.stem)}...")
        copytree(module_path, device_path / module_path.stem)
    logger.info(f"Successfully installed {repr(module_path)}!")


def uninstall_module(module_path: Path = None) -> None:
    """
    Pass in the path to the module (ex. "I:lib/adafruit_bus_device") on
    the device will delete the directory/file on the device.

    :param module_path: A pathlib.Path object that points to the path of the module **ON THE DEVICE**.
    :return: None
    """
    if not module_path.exists():
        logger.error(f"{module_path} does not exist!")
        raise FileNotFoundError(f"{module_path} does not exist!")
    logger.debug(f"Uninstalling {repr(module_path)}...")
    if module_path.is_file():
        module_path.unlink()
    else:
        rmtree(module_path)
    logger.info(f"Successfully uninstalled {repr(module_path)}!")
