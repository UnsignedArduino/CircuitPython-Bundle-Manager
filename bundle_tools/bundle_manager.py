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


def list_modules_in_bundle(version: int = None) -> list:
    """
    Lists the modules in the bundle stored internally.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.

    :return: A list of strings with the module name. Returns an empty list if no bundle was downloaded.
    """
    modules = []
    module_path = Path.cwd() / "bundles" / str(version)
    for module in module_path.glob("*"):
        modules.append(module.name)
    return modules


def get_module_path(version: int = None, name: str = None) -> Path:
    """
    Gets the path to the module in the bundle from the name.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.

    :param name: The name of the module. Defaults to None, and will raise an exception if no compatible object is
     passed in.

    :return: A pathlib.Path object pointing to the requested module's path. Returns None if we can't find it.
    """
    module_path = Path.cwd() / "bundles" / str(version) / name
    return module_path if module_path.exists() else None


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

    :param user_and_pass: A dictionary with the keys "username" and "password". Defaults to None, and will raise an
     exception if no compatible object is passed in.
    :param access_token: A string with your access token. Defaults to None, and will raise an exception if no compatible
     object is passed in.
    :param url_and_token: A dictionary with the keys "base_url" and "login_or_token". Defaults to None, and will raise
     an exception if no compatible object is passed in.
    :return: A github.Github instance. Pass this into "bundle_tools.bundle_manager.update_bundle()" when you need to
     update the bundle. Check it's doc strings for more detail. If no parameters were provided, then None is returned.
    """
    if type(user_and_pass) == dict:
        return Github(user_and_pass["username"], user_and_pass["password"])
    elif type(access_token) == str:
        return Github(access_token)
    elif type(url_and_token) == dict:
        return Github(base_url=url_and_token["base_url"], login_or_token=url_and_token["login_or_token"])
    return None


def update_bundle(version: int = None, github_instance: Github = None) -> Path:
    """
    Updates the bundle for the given version.

    :param version:  An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.
    :param github_instance: An instance of github.Github. Get this from
     "bundle_tools.bundle_manager.authenticate_with_github()". Defaults to None, and will raise an exception if no
      compatible object is passed in.
    :return: A pathlib.Path object that contains the path of the bundle.
    """
    assets = github_instance.get_repo("adafruit/Adafruit_CircuitPython_Bundle").get_latest_release().get_assets()
    name = f"adafruit-circuitpython-bundle-{version}.x-mpy"
    bundle_url = None
    bundle_name = None
    for asset in assets:
        if name in asset.name:
            bundle_url = asset.browser_download_url
            bundle_name = asset.name
            break
    download_path = Path.cwd() / "bundles_zip" / str(version) / bundle_name
    download_path.parent.mkdir(parents=True, exist_ok=True)
    with download_path.open(mode="wb") as file:
        response = requests.get(bundle_url)
        file.write(response.content)
    unzip_path = Path.cwd() / "bundles" / str(version) / str(unix())
    unzip_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(download_path, "r") as zip_file:
        zip_file.extractall(unzip_path)
    rmtree(download_path.parent)
    while len(list(unzip_path.parent.glob("*"))) > 5:
        bundles = list(unzip_path.parent.glob("*"))
        bundles.sort()
        rmtree(bundles[0])
    return unzip_path / bundle_name[:-4] / "lib"
