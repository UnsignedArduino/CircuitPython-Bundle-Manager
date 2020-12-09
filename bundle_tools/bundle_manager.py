"""
A module that handles bundle accessing and updating.

-----------

Classes list:

No classes!

-----------

Functions list:

- list_modules_in_bundle(version: int = None) -> list
- get_module_path(version: int = None, name: str = None) -> Path:
- authenticate_with_github(user_and_pass: dict = None, access_token: str = None, url_and_token: dict = None) -> Github
- update_bundle(version: int = None) -> None

"""

from pathlib import Path
from github import Github
import requests


def list_modules_in_bundle(version: int = None) -> list:
    """
    Lists the modules in the bundle stored internally.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.

    :return: A list of strings with the module name.
    """
    pass


def get_module_path(version: int = None, name: str = None) -> Path:
    """
    Gets the path to the module in the bundle from the name.

    :param version: An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.

    :param name: The name of the module. Defaults to None, and will raise an exception if no compatible object is
     passed in.

    :return: A pathlib.Path object pointing to the requested module's path. Returns None if we can't find it.
    """
    pass


def authenticate_with_github(user_and_pass: dict = None,
                             access_token: str = None,
                             url_and_token: dict = None) -> Github:
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
     update the bundle. Check it's doc strings for more detail.
    """
    pass


def update_bundle(version: int = None, github_instance: Github = None) -> None:
    """
    Updates the bundle for the given version.

    :param version:  An integer saying what version we want, like 5 for CircuitPython 5.x and 6 for CircuitPython 6.x.
     Defaults to None, and will raise an exception if no compatible object is passed in.
    :param github_instance: An instance of github.Github. Get this from
     "bundle_tools.bundle_manager.authenticate_with_github()". Defaults to None, and will raise an exception if no
      compatible object is passed in.
    :return: Nothing
    """
    pass
