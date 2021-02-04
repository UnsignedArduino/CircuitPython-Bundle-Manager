"""
A module that handles bundle accessing and updating.

-----------

Classes list:

No classes!

-----------

Functions list:

- list_modules_in_bundle(version: int = None) -> list
- get_module_path(version: int = None, name: str = None) -> Path:
- authenticate_with_github(user_and_pass: dict = None,
                           access_token: str = None,
                           url_and_token: dict = None) -> Union[Github, None]
- update_bundle(version: int = None) -> None

"""

from pathlib import Path
from shutil import rmtree
from github import Github
import requests
from zipfile import ZipFile
from time import time as unix
from typing import Union
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


def list_modules_in_bundle(version: int) -> Union[list[str], None]:
    """
    Lists the modules in the bundle stored internally.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
    :return: A list of strings with the module name. Returns an empty list if no bundle was downloaded or None if it
      couldn't find it.
    """
    modules = []
    modules_path = Path.cwd() / "bundles" / str(version)
    bundles = [str(path) for path in list(modules_path.glob("*"))]
    bundles.sort()
    logger.debug(f"Modules found are {repr(bundles)}")
    try:
        bundles = bundles[-1:][0]
    except IndexError:
        return None
    module_path = (list(Path(bundles).glob("*"))[0] / "lib")
    logger.debug(f"Module path is {repr(module_path)}")
    for module in module_path.glob("*"):
        modules.append(module.name)
    logger.debug(f"Modules found: {repr(modules)}")
    return modules


def get_bundle_path(version: int) -> Union[Path, None]:
    """
    Gets that path of the bundle stored internally.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
    :return: A pathlib.Path object pointing to the path of the bundle or None if we can't find it.
    """
    modules_path = Path.cwd() / "bundles" / str(version)
    bundles = [str(path) for path in list(modules_path.glob("*"))]
    bundles.sort()
    logger.debug(f"Modules found are {repr(bundles)}")
    try:
        bundles = bundles[-1:][0]
    except IndexError:
        return None
    bundle_path = (list(Path(bundles).glob("*"))[0] / "lib")
    logger.debug(f"Bundle path is {repr(bundle_path)}")
    return bundle_path


def authenticate_with_github(user_and_pass: dict = None,
                             access_token: str = None,
                             url_and_token: dict = None) -> Union[Github, None]:
    """
    To authenticate with:

    -----------

    # Username and password

    bundle_manager.authenticate_with_github(user_and_pass={"username": "your_username", "password": "your_password"})

    # Access token

    bundle_manager.authenticate_with_github(access_token="your_access_token")

    # Github Enterprise

    bundle_manager.authenticate_with_github(url_and_token={
        "base_url": "your_base_url", # Note that your base URL should be like https://{hostname}/api/v3

        "login_or_token": "your_access_token"
    })

    -----------

    https://pygithub.readthedocs.io/en/latest/introduction.html#very-short-tutorial will have a better description of
    what you need to authenticate.

    :param user_and_pass: A dictionary with the keys "username" and "password".
    :param access_token: A string with your access token.
    :param url_and_token: A dictionary with the keys "base_url" and "login_or_token".
    :return: A github.Github instance. Pass this into "bundle_tools.bundle_manager.update_bundle()" when you need to
     update the bundle. Check it's doc strings for more detail. If no parameters were provided, then None is returned.
    """
    if type(user_and_pass) == dict:
        logger.debug(f"Using username and password!")
        return Github(user_and_pass["username"], user_and_pass["password"])
    elif type(access_token) == str:
        logger.debug(f"Using access token!")
        return Github(access_token)
    elif type(url_and_token) == dict:
        logger.debug(f"Using url and token/login!")
        return Github(base_url=url_and_token["base_url"], login_or_token=url_and_token["login_or_token"])
    return None


def update_bundle(version: int = None, github_instance: Github = None) -> Path:
    """
    Updates the bundle for the given version.

    :param version:  An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
    :param github_instance: An instance of github.Github. Get this from
      "bundle_tools.bundle_manager.authenticate_with_github()".
    :return: A pathlib.Path object that contains the path of the bundle.
    """
    logger.info(f"Updating bundle...")
    assets = github_instance.get_repo("adafruit/Adafruit_CircuitPython_Bundle").get_latest_release().get_assets()
    logger.debug(f"Assets found: {repr(assets)}")
    name = f"adafruit-circuitpython-bundle-{version}.x-mpy"
    bundle_url = None
    bundle_name = None
    for asset in assets:
        if name in asset.name:
            bundle_url = asset.browser_download_url
            bundle_name = asset.name
            logger.debug(f"Found bundle! Name: {repr(bundle_name)} URL: {repr(bundle_url)}")
            break
    download_path = Path.cwd() / "bundles_zip" / str(version) / bundle_name
    download_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Download path is {repr(download_path)}")
    with download_path.open(mode="wb") as file:
        logger.debug(f"Downloading {repr(bundle_url)}...")
        response = requests.get(bundle_url)
        file.write(response.content)
    unzip_path = Path.cwd() / "bundles" / str(version) / str(unix())
    unzip_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Unzip path is {repr(unzip_path)}")
    with ZipFile(download_path, "r") as zip_file:
        logger.debug(f"Extracting {repr(download_path)}...")
        zip_file.extractall(unzip_path)
    logger.debug(f"Deleting {repr(download_path.parent)}...")
    rmtree(download_path.parent)
    logger.debug(f"Found {len(list(unzip_path.parent.glob('*')))} bundles!")
    while len(list(unzip_path.parent.glob("*"))) > 5:
        bundles = list(unzip_path.parent.glob("*"))
        bundles.sort()
        logger.debug(f"Deleting {repr(bundles[0])}...")
        rmtree(bundles[0])
    logger.debug(f"Path to latest bundle is {repr(unzip_path / bundle_name[:-4] / 'lib')}")
    logger.info(f"Finished updating bundle!")
    return unzip_path / bundle_name[:-4] / "lib"
