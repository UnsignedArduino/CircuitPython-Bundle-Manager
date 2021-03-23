"""
The main GUI program.

-----------

Classes list:

- GUI(tk.Tk).__init__()

-----------

Functions list:

No functions!

"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mbox
from gui_tools.right_click.entry import EntryWithRightClick
from gui_tools.right_click.spinbox import SpinboxWithRightClick
from gui_tools.right_click.combobox import ComboboxWithRightClick
from gui_tools.right_click.listbox import ListboxWithRightClick
from gui_tools.idlelib_clone import tooltip
from gui_tools import download_dialog
from threading import Thread
from pathlib import Path
import traceback
from github import GithubException
import requests
from markdown import markdown as markdown_to_html
import webbrowser
import json
from bundle_tools import drives, modules, bundle_manager, os_detect, imported
from typing import Union
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


class GUI(tk.Tk):
    """
    The GUI for the CircuitPython Bundle Manager.
    """
    def __init__(self):
        super().__init__()
        self.title("CircuitPython Bundle Manager")
        self.resizable(False, False)
        self.config_path = Path.cwd() / "config.json"
        self.disable_closing = False
        self.protocol("WM_DELETE_WINDOW", self.try_to_close)

    def __enter__(self):
        return self

    def try_to_close(self) -> None:
        """
        Try to close the application - checks if we are not busy and displays dialogs appropriately.

        :return: None.
        """
        logger.debug("User requested closing window...")
        if self.disable_closing:
            logger.warning("Currently in the middle of doing something!")
            if mbox.askokcancel("CircuitPython Bundle Manager: Confirmation",
                                "Something is happening right now!\n"
                                "If you close out now, this will immediately stop what we are doing and may cause a "
                                "corrupt directory hierarchy, broken files and/or broken directories. "
                                "Are you sure you want to exit?",
                                icon="warning", default="cancel"):
                logger.debug("User continued to close window!")
                self.destroy()
        else:
            logger.debug("Destroying main window!")
            self.destroy()

    def save_key(self, key: str = None, value: str = None) -> None:
        """
        Save a key to the config file.

        :param key: A string.
        :param value: A string.
        :return: None.
        """
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        old_json = json.loads(self.config_path.read_text())
        logger.debug(f"Setting {repr(key)} to {repr(value)}!")
        old_json[key] = value
        self.config_path.write_text(json.dumps(old_json, sort_keys=True, indent=4))

    def load_key(self, key: str) -> Union[str, None]:
        """
        Retrieves a key from the config file.

        :param key: A string.
        :return: A string of the value of the key, or None if it was not found.
        """
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        try:
            value = json.loads(self.config_path.read_text())[key]
            return value
        except (json.decoder.JSONDecodeError, KeyError):
            logger.warning(f"Could not find {repr(key)} in config!")
            return None

    def validate_for_number(self, new: str = "") -> bool:
        """
        Checks a string to see whether it's a number and within 3 digits.

        :param new: The string to validate.
        :return: A bool telling whether it passed validation.
        """
        logger.debug(f"{repr(new)} did " + ("" if new.isdigit() and len(new) <= 3 else "not ") + "pass validation!")
        return new.isdigit() and len(new) <= 3

    def create_bundle_update_tab(self) -> None:
        """
        Create the bundle update tab.

        :return: None.
        """
        self.github_auth_frame = ttk.Frame(master=self.notebook)
        self.github_auth_frame.grid(row=0, column=0, padx=1, pady=1)
        self.notebook.add(self.github_auth_frame, text="Update" if os_detect.on_linux() else "Update Bundle")
        self.create_username_password_input()
        self.create_access_token_input()
        self.create_github_enterprise_input()
        self.create_auth_method_selector()
        self.update_bundle_button = ttk.Button(master=self.github_auth_frame, text="Update bundle", command=self.start_update_bundle_thread)
        self.update_bundle_button.grid(row=5, column=1, rowspan=2, columnspan=2, padx=1, pady=1)
        tooltip.Hovertip(self.update_bundle_button, text="Update the bundle used for installing modules.")
        self.version_label = ttk.Label(master=self.github_auth_frame, text="Version: ")
        self.version_label.grid(row=7, column=1, padx=1, pady=1, sticky=tk.NE)
        validate_for_number_wrapper = (self.register(self.validate_for_number), '%P')
        self.version_listbox = SpinboxWithRightClick(master=self.github_auth_frame, width=3, from_=1, to=100,
                                                     command=lambda: self.save_key("last_circuit_python_bundle_version", self.version_listbox.get()),
                                                     validate="key", validatecommand=validate_for_number_wrapper)
        self.version_listbox.grid(row=7, column=2, padx=1, pady=1, sticky=tk.NW)
        self.version_listbox.set(self.load_key("last_circuit_python_bundle_version"))
        self.version_listbox.initiate_right_click_menu(disable=["Cut", "Delete"])
        tooltip.Hovertip(self.version_listbox, text="The major CircuitPython version used when updating the bundle.")
        self.updating = False
        self.check_update_button()

    def start_update_bundle_thread(self) -> None:
        """
        Start the bundle update thread.

        :return: None.
        """
        logger.debug("Starting update bundle thread!")
        update_thread = Thread(target=self.update_bundle, daemon=True)
        update_thread.start()

    def update_bundle(self) -> None:
        """
        Update the bundle, this will block. Better to call GUI.start_update_bundle_thread instead.

        :return: None.
        """
        self.updating = True
        self.disable_closing = True
        self.enable_github_auth_inputs(False)
        github_instance = bundle_manager.authenticate_with_github(
            user_and_pass={
                "username": self.username_entry.get(),
                "password": self.password_entry.get()
            } if self.github_auth_method_var.get() == "username and password" else None,
            access_token=self.access_token_entry.get() if self.github_auth_method_var.get() == "access token" else None,
            url_and_token={
                "base_url": self.enterprise_url_entry.get(),
                "login_or_tokin": self.enterprise_token_entry.get()
            } if self.github_auth_method_var.get() == "enterprise" else None
        )
        try:
            logger.debug("Attempting to update bundle...")
            bundle_manager.update_bundle(int(self.version_listbox.get()), github_instance)
            mbox.showinfo("CircuitPython Bundle Manager: Info", "CircuitPython bundle updated successfully!")
        except (TypeError, ValueError):
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Did you enter in the correct CircuitPython version below?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except GithubException:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access GitHub! "
                           "Did you enter in the correct credentials?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except requests.exceptions.ConnectionError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access the internet! "
                           "Do you have a working internet connection?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except requests.exceptions.ChunkedEncodingError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access the internet! "
                           "Did you internet connection break?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except Exception as _:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!"
                           "\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.info("Successfully updated bundle!")
        self.updating = False
        self.disable_closing = False
        self.enable_github_auth_inputs(True)

    def enable_github_auth_inputs(self, enable: bool = True) -> None:
        """
        Enable of disable the GitHub authentication inputs.

        :param enable: Whether to enable or disable the GitHub authentication inputs.
        :return: None.
        """
        self.enable_username_password(self.github_auth_method_var.get() == "username and password" if enable else False)
        self.enable_access_token(self.github_auth_method_var.get() == "access token" if enable else False)
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise" if enable else False)
        self.user_pass_radio_button.config(state=tk.NORMAL if enable else "disabled")
        self.access_token_radio_button.config(state=tk.NORMAL if enable else "disabled")
        self.enterprise_radio_button.config(state=tk.NORMAL if enable else "disabled")
        self.version_label.config(state=tk.NORMAL if enable else "disabled")
        self.version_listbox.config(state=tk.NORMAL if enable else "disabled")

    def check_update_button(self) -> None:
        """
        Update the button to reflect the current operations. Also disable or enable it depending on the current
        situation. Note you should only call this function once because it will automatically reschedule itself in the
        Tk event loop.

        :return: None.
        """
        self.after(100, self.check_update_button)
        if self.updating:
            self.update_bundle_button.config(state=tk.DISABLED, text="Updating bundle...")
            return
        else:
            self.update_bundle_button.config(state="enabled", text="Update bundle")
        if self.version_listbox.get() == "":
            self.update_bundle_button.config(state=tk.DISABLED)
            return
        if self.github_auth_method_var.get() == "username and password":
            self.update_bundle_button.config(
                state="normal" if self.username_entry.get() != "" and self.password_entry.get() != "" else "disabled"
            )
        elif self.github_auth_method_var.get() == "access token":
            self.update_bundle_button.config(
                state="normal" if self.access_token_entry.get() != "" else "disabled"
            )
        elif self.github_auth_method_var.get() == "enterprise":
            self.update_bundle_button.config(
                state="normal" if self.enterprise_url_entry.get() != "" and self.enterprise_token_entry.get() != "" else "disabled"
            )
        else:
            self.update_bundle_button.config(state=tk.DISABLED)

    def update_selected_auth_method(self) -> None:
        """
        Update the GUI with the selected authentication method by disabling or enabling certain GitHub authentication
        methods.

        :return: None.
        """
        self.enable_username_password(self.github_auth_method_var.get() == "username and password")
        self.enable_access_token(self.github_auth_method_var.get() == "access token")
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise")
        self.save_key("last_auth_method_used", self.github_auth_method_var.get())

    def enable_enterprise(self, enable: bool = True) -> None:
        """
        Enable or disable the GitHub Enterprise authentication inputs.

        :param enable: Whether to enable or disable the GitHub Enterprise authentication inputs.
        :return: None.
        """
        self.enterprise_url_label.config(state=tk.NORMAL if enable else "disabled")
        self.enterprise_url_entry.config(state=tk.NORMAL if enable else "disabled")
        self.enterprise_token_label.config(state=tk.NORMAL if enable else "disabled")
        self.enterprise_token_entry.config(state=tk.NORMAL if enable else "disabled")

    def enable_access_token(self, enable: bool = True) -> None:
        """
        Enable or disable the access token authentication input.

        :param enable: Whether to enable or disable the GitHub access token authentication input.
        :return: None.
        """
        self.access_token_label.config(state=tk.NORMAL if enable else "disabled")
        self.access_token_entry.config(state=tk.NORMAL if enable else "disabled")

    def enable_username_password(self, enable: bool = True) -> None:
        """
        Enable or disable the username and password authentication input.

        :param enable: Whether to enable or disable the username and password authentication input.
        :return: None.
        """
        self.username_label.config(state=tk.NORMAL if enable else "disabled")
        self.username_entry.config(state=tk.NORMAL if enable else "disabled")
        self.password_label.config(state=tk.NORMAL if enable else "disabled")
        self.password_entry.config(state=tk.NORMAL if enable else "disabled")
        self.show_password_button.config(state=tk.NORMAL if enable else "disabled")

    def create_auth_method_selector(self) -> None:
        """
        Creates the GitHub authentcation method selector.

        :return: None.
        """
        self.github_auth_method_var = tk.StringVar()
        self.github_auth_method_var.set("username and password")
        self.user_pass_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="Username and password",
            variable=self.github_auth_method_var, value="username and password",
            command=self.update_selected_auth_method
        )
        self.user_pass_radio_button.grid(row=5, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.user_pass_radio_button, text="Use a username and password to authenticate with GitHub.")
        self.access_token_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="Access token",
            variable=self.github_auth_method_var, value="access token",
            command=self.update_selected_auth_method
        )
        self.access_token_radio_button.grid(row=6, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.access_token_radio_button, text="Use an access token and password to authenticate with GitHub.")
        self.enterprise_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="GitHub Enterprise",
            variable=self.github_auth_method_var, value="enterprise",
            command=self.update_selected_auth_method
        )
        self.enterprise_radio_button.grid(row=7, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.enterprise_radio_button, text="Use a GitHub Enterprise URL and a token or login to authenticate with GitHub.")
        try:
            auth_method = self.load_key("last_auth_method_used")
            if not auth_method == None:
                self.github_auth_method_var.set(auth_method)
        except FileNotFoundError:
            pass
        self.update_selected_auth_method()

    def create_github_enterprise_input(self) -> None:
        """
        Create the GitHub Enterprise authentication input.

        :return: None.
        """
        self.enterprise_url_label = ttk.Label(master=self.github_auth_frame, text="GitHub Enterprise URL: ")
        self.enterprise_url_label.grid(row=3, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        if os_detect.on_linux():
            self.enterprise_url_entry = EntryWithRightClick(master=self.github_auth_frame, width=18)
        else:
            self.enterprise_url_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.enterprise_url_entry.grid(row=3, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_url_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.enterprise_url_entry, text="Input a GitHub Enterprise URl that matches with the login or token below.")
        self.enterprise_token_label = ttk.Label(master=self.github_auth_frame, text="Login or token: ")
        self.enterprise_token_label.grid(row=4, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        if os_detect.on_linux():
            self.enterprise_token_entry = EntryWithRightClick(master=self.github_auth_frame, width=18)
        else:
            self.enterprise_token_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.enterprise_token_entry.grid(row=4, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_token_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.enterprise_token_entry, text="Input a GitHub Enterprise login or token that matches with the URL above.")

    def create_access_token_input(self) -> None:
        """
        Create the GitHub access token authentication input.

        :return: None.
        """
        self.access_token_label = ttk.Label(master=self.github_auth_frame, text="Access token: ")
        self.access_token_label.grid(row=2, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        if os_detect.on_linux():
            self.access_token_entry = EntryWithRightClick(master=self.github_auth_frame, width=18)
        else:
            self.access_token_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.access_token_entry.grid(row=2, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.access_token_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.access_token_entry, text="Input an GitHub access token. Scopes need are:\n - public access")

    def create_username_password_input(self) -> None:
        """
        Create the username and password authentication input.

        :return: None.
        """
        self.username_label = ttk.Label(master=self.github_auth_frame, text="Username: ")
        self.username_label.grid(row=0, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.password_label = ttk.Label(master=self.github_auth_frame, text="Password: ")
        self.password_label.grid(row=1, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        if os_detect.on_linux():
            self.username_entry = EntryWithRightClick(master=self.github_auth_frame, width=18)
        else:
            self.username_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.username_entry.grid(row=0, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.username_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.username_entry, text="Input a GitHub username that matches the password below.")
        self.password_frame = ttk.Frame(master=self.github_auth_frame)
        self.password_frame.grid(row=1, column=1, padx=0, pady=1, columnspan=2, sticky=tk.NW)
        if os_detect.on_linux():
            self.password_entry = EntryWithRightClick(master=self.password_frame, width=11, show="*")
        else:
            self.password_entry = EntryWithRightClick(master=self.password_frame, width=13, show="*")
        self.password_entry.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.password_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.password_entry, text="Input a GitHub password that matches the username above.")
        self.show_password_button = ttk.Button(master=self.password_frame, width=5, text="Show", command=self.toggle_password_visibility)
        self.show_password_button.grid(row=0, column=1, padx=1, pady=0, sticky=tk.NW)
        tooltip.Hovertip(self.show_password_button, text="Show or hide the password")

    def toggle_password_visibility(self) -> None:
        """
        Toggle whether to show or hide the password depending on the button's text.

        :return: None.
        """
        if self.show_password_button["text"] == "Show":
            self.show_password_button.config(text="Hide")
            self.password_entry.config(show="")
        else:
            self.show_password_button.config(text="Show")
            self.password_entry.config(show="*")

    def create_bundle_manager_tab(self) -> None:
        """
        Create the bundle manager tab.

        :return: None.
        """
        self.bundle_manager_frame = ttk.Frame(master=self.notebook)
        self.bundle_manager_frame.grid(row=0, column=0, padx=1, pady=1)
        self.notebook.add(self.bundle_manager_frame, text="Bundle Manager")
        self.installing = False
        self.uninstalling = False
        self.create_bundle_list()
        self.create_installed_module_list()
        self.create_module_buttons()
        self.update_buttons()
        self.after(100, self.update_modules)

    def update_modules_in_device(self) -> None:
        """
        Update the modules on the device.

        :return: None.
        """
        try:
            try:
                installed_modules = modules.list_modules(Path(self.drive_combobox.get()))
            except RuntimeError:
                logger.exception("Uh oh! Something happened!")
                installed_modules = []
            installed_modules.sort()
            logger.debug(f"Installed modules: {repr(installed_modules)}")
            self.installed_modules_listbox_var.set(installed_modules)
        except (AttributeError, RuntimeError):
            logger.exception("Uh oh! Something happened!")

    def update_modules_in_bundle(self) -> None:
        """
        Update the modules shown on the bundle.

        :return: None.
        """
        try:
            bundles = bundle_manager.list_modules_in_bundle(int(self.version_listbox.get()))
            if bundles == None:
                bundles = []
            bundles.sort()
            logger.debug(f"Modules in bundle: {repr(bundles)}")
            search_query = self.search_bar_var.get()
            if not search_query == "":
                sorted_bundles = []
                for bundle in bundles:
                    if search_query in bundle:
                        sorted_bundles.append(bundle)
                logger.debug(f"Sorted bundles: {repr(sorted_bundles)}")
                self.bundle_listbox_var.set(sorted_bundles)
            else:
                self.bundle_listbox_var.set(bundles)
            self.bundles = bundles
        except (ValueError, AttributeError):
            logger.exception("Uh oh! Something happened!")

    def update_buttons(self) -> None:
        """
        Enable or disable the install/uninstall buttons.

        :return: None
        """
        self.after(100, self.update_buttons)
        try:
            if self.updating:
                self.install_module_button.config(state=tk.DISABLED, text="Updating bundle...\nCannot install!")
                return
            else:
                self.install_module_button.config(text="Install")
        except AttributeError:
            logger.exception("Uh oh! Something happened!")
        if self.installing:
            self.install_module_button.config(state=tk.DISABLED, text="Installing...")
            self.uninstall_module_button.config(state=tk.DISABLED)
            self.bundle_listbox.config(state=tk.DISABLED)
            self.installed_modules_listbox.config(state=tk.DISABLED)
            self.search_bar.config(state=tk.DISABLED)
            return
        else:
            self.install_module_button.config(text="Install")
            self.bundle_listbox.config(state=tk.NORMAL)
            self.installed_modules_listbox.config(state=tk.NORMAL)
            self.search_bar.config(state=tk.NORMAL)
        if self.uninstalling:
            self.install_module_button.config(state=tk.DISABLED)
            self.uninstall_module_button.config(state=tk.DISABLED, text="Uninstalling...")
            self.bundle_listbox.config(state=tk.DISABLED)
            self.installed_modules_listbox.config(state=tk.DISABLED)
            self.search_bar.config(state=tk.DISABLED)
            return
        else:
            self.uninstall_module_button.config(text="Uninstall")
            self.bundle_listbox.config(state=tk.NORMAL)
            self.installed_modules_listbox.config(state=tk.NORMAL)
            self.search_bar.config(state=tk.NORMAL)
        self.install_module_button.config(state=tk.NORMAL if len(self.bundle_listbox.curselection()) > 0 else "disabled")
        self.uninstall_module_button.config(state=tk.NORMAL if len(self.installed_modules_listbox.curselection()) > 0 else "disabled")
        if self.drive_combobox.get() == "":
            self.install_module_button.config(state=tk.DISABLED)
            self.uninstall_module_button.config(state=tk.DISABLED)

    def update_search_bar(self, *args) -> None:
        """
        Update the results from the search bar.

        :param args: Something to do with Tk's tracing method.
        :return: None.
        """
        logger.debug(f"Search query is {repr(self.search_bar_var.get())}")
        self.update_modules_in_bundle()

    def create_bundle_list(self) -> None:
        """
        Create the list of modules in the bundle.

        :return: None.
        """
        self.bundle_listbox_frame = ttk.LabelFrame(master=self.bundle_manager_frame, text="Bundle")
        self.bundle_listbox_frame.grid(row=0, column=0, padx=1, pady=1, rowspan=3)
        self.search_bar_var = tk.StringVar()
        self.search_bar_var.set("")
        self.search_bar_var.trace_add("write", self.update_search_bar)
        if os_detect.on_windows():
            self.search_bar = EntryWithRightClick(master=self.bundle_listbox_frame, textvariable=self.search_bar_var, width=22)
        else:
            self.search_bar = EntryWithRightClick(master=self.bundle_listbox_frame, textvariable=self.search_bar_var, width=20)
        self.search_bar.initiate_right_click_menu()
        self.search_bar.grid(row=0, column=0, columnspan=2, padx=1, pady=1)
        tooltip.Hovertip(self.search_bar, text="Enter your search query here.")
        self.bundle_listbox_var = tk.StringVar()
        if os_detect.on_windows():
            self.bundle_listbox = ListboxWithRightClick(self.bundle_listbox_frame, width=19, height=9, listvariable=self.bundle_listbox_var)
        else:
            self.bundle_listbox = ListboxWithRightClick(self.bundle_listbox_frame, width=18, height=9, listvariable=self.bundle_listbox_var)
        self.bundle_listbox.grid(row=1, column=0, padx=1, pady=1)
        self.bundle_listbox.initiate_right_click_menu(["Copy", "Cut", "Paste", "Select all", "Delete"])
        self.bundle_listbox.right_click_menu.add_separator()
        self.bundle_listbox.right_click_menu.add_command(label="Refresh bundle", command=self.update_modules_in_bundle)
        tooltip.Hovertip(self.bundle_listbox, text="A list of modules from the CircuitPython bundle.\n"
                                                   "Select a module and press install to install the module to the selected device.")
        self.bundle_listbox_scrollbar = ttk.Scrollbar(self.bundle_listbox_frame, orient=tk.VERTICAL, command=self.bundle_listbox.yview)
        self.bundle_listbox_scrollbar.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.bundle_listbox.config(yscrollcommand=self.bundle_listbox_scrollbar.set)

    def create_installed_module_list(self) -> None:
        """
        Create the list of installed modules.

        :return: None.
        """
        self.installed_modules_listbox_frame = ttk.LabelFrame(master=self.bundle_manager_frame, text="Installed modules")
        self.installed_modules_listbox_frame.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NE)
        self.installed_modules_listbox_var = tk.StringVar()
        if os_detect.on_windows():
            self.installed_modules_listbox = ListboxWithRightClick(self.installed_modules_listbox_frame, width=18, height=5, listvariable=self.installed_modules_listbox_var)
        else:
            self.installed_modules_listbox = ListboxWithRightClick(self.installed_modules_listbox_frame, width=17, height=5, listvariable=self.installed_modules_listbox_var)
        self.installed_modules_listbox.grid(row=0, column=0, padx=1, pady=1)
        self.installed_modules_listbox.initiate_right_click_menu(["Copy", "Cut", "Paste", "Select all", "Delete"], callback=self.check_for_lib_path)
        self.installed_modules_listbox.right_click_menu.add_separator()
        self.installed_modules_listbox.right_click_menu.add_command(label="Refresh modules", command=self.update_modules_in_device)
        self.installed_modules_listbox.right_click_menu.add_command(label="Open in file manager",
                                                                    command=lambda: webbrowser.open(str(modules.get_lib_path(Path(self.drive_combobox.get())))))
        tooltip.Hovertip(self.installed_modules_listbox, text="A list of modules installed on the selected device.\n"
                                                              "Select a module and press uninstall to uninstall the module from the selected device.")
        self.installed_modules_listbox_scrollbar = ttk.Scrollbar(self.installed_modules_listbox_frame, orient=tk.VERTICAL, command=self.installed_modules_listbox.yview)
        self.installed_modules_listbox_scrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.installed_modules_listbox.config(yscrollcommand=self.installed_modules_listbox_scrollbar.set)

    def check_for_lib_path(self) -> None:
        """
        Check whether we can open the device in the file manager via context menu.

        :return: None.
        """
        self.installed_modules_listbox.right_click_menu.delete(9)
        self.installed_modules_listbox.right_click_menu.add_command(
            label="Open in file manager",
            state="normal" if modules.get_lib_path(Path(self.drive_combobox.get())).exists() else "disabled",
            command=lambda: webbrowser.open(str(modules.get_lib_path(Path(self.drive_combobox.get()))))
        )

    def create_module_buttons(self) -> None:
        """
        Create the install and uninstall buttons.

        :return: None.
        """
        self.install_module_button = ttk.Button(self.bundle_manager_frame, text="Install", command=self.start_install_module_thread)
        self.install_module_button.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NSEW)
        tooltip.Hovertip(self.install_module_button, text="Install the selected module to the selected device.")
        self.uninstall_module_button = ttk.Button(self.bundle_manager_frame, text="Uninstall", command=self.start_uninstall_module_thread)
        self.uninstall_module_button.grid(row=2, column=1, padx=1, pady=1, sticky=tk.NSEW)
        tooltip.Hovertip(self.uninstall_module_button, text="Uninstall the selected module from the selected device.")

    def start_uninstall_module_thread(self) -> None:
        """
        Start the module uninstall thread.

        :return: None.
        """
        logger.debug("Starting uninstall module thread!")
        uninstall_thread = Thread(target=self.uninstall_module, daemon=True)
        uninstall_thread.start()

    def uninstall_module(self) -> None:
        """
        Uninstall the selected module from the selected device, this will block. Better to call
        GUI.start_uninstall_module_thread instead.

        :return: None.
        """
        self.uninstalling = True
        self.disable_closing = True
        drive = Path(self.drive_combobox.get())
        logger.debug(f"Selected drive is {repr(drive)}")
        try:
            module_path = modules.get_lib_path(drive) / self.installed_modules_listbox.get(self.installed_modules_listbox.curselection())
            logger.debug(f"Attempting to uninstall module at {repr(module_path)}")
            modules.uninstall_module(module_path)
        except FileNotFoundError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module - did you input a drive that exists?\n"
                           "Try reloading the list of installed modules before uninstall again!\n"
                           "\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.debug("Successfully uninstalled module!")
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully uninstalled module!")
        self.uninstalling = False
        self.disable_closing = False
        self.after(100, self.update_modules_in_device)

    def start_install_module_thread(self) -> None:
        """
        Start the module install thread.

        :return: None.
        """
        logger.debug("Starting install module thread!")
        install_thread = Thread(target=self.install_module, daemon=True)
        install_thread.start()

    def install_module(self) -> None:
        """
        Install the selected module to the selected device, this will block. Better to call
        GUI.start_install_module_thread instead.

        :return: None.
        """
        self.installing = True
        self.disable_closing = True
        try:
            bundle_path = bundle_manager.get_bundle_path(int(self.version_listbox.get()))
            logger.debug(f"Attempting to install module at {repr(bundle_path)}")
            selected = self.bundle_listbox.get(self.bundle_listbox.curselection())
            logger.debug(f"Selected in listbox is {repr(selected)}")
            logger.debug(f"Installing module {repr(selected)}")
            modules.install_module(
                bundle_path / selected,
                Path(self.drive_combobox.get()) / "lib"
            )
        except FileNotFoundError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module - did you input a drive that exists?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            logger.exception("Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.debug("Successfully installed module!")
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully installed module!")
        self.installing = False
        self.disable_closing = False
        self.after(100, self.update_modules_in_device)

    def create_drive_selector(self) -> None:
        """
        Create the drive selector.

        :return: None.
        """
        self.drive_combobox_label = ttk.Label(master=self, text="Drive:")
        self.drive_combobox_label.grid(row=1, column=0, padx=1, pady=1)
        if os_detect.on_windows():
            self.drive_combobox = ComboboxWithRightClick(master=self, width=16)
        else:
            self.drive_combobox = ComboboxWithRightClick(master=self, width=15)
        self.drive_combobox.grid(row=1, column=1, padx=1, pady=1)
        self.drive_combobox.initiate_right_click_menu()
        self.drive_combobox.right_click_menu.add_separator()
        self.drive_combobox.right_click_menu.add_command(label="Refresh drives", command=self.update_drives)
        tooltip.Hovertip(self.drive_combobox, text="Select the drive that represents the CircuitPython device.")
        self.refresh_drives_button = ttk.Button(master=self, text="↻", width=2, command=self.update_everything)
        self.refresh_drives_button.grid(row=1, column=2, padx=1, pady=1)
        tooltip.Hovertip(self.refresh_drives_button, text="Refresh:\n"
                                                          " - Connected drives\n"
                                                          " - Modules in the last downloaded bundle\n"
                                                          " - Modules installed on the device\n")
        self.show_all_drives_var = tk.BooleanVar()
        self.show_all_drives_var.set(False)
        self.show_all_drives_checkbutton = ttk.Checkbutton(master=self, text="Show all drives?",
                                                           variable=self.show_all_drives_var, command=self.update_drives)
        self.show_all_drives_checkbutton.grid(row=1, column=3, padx=1, pady=1)
        tooltip.Hovertip(self.show_all_drives_checkbutton, text="Whether to list all drives or CircuitPython drives in the combobox.")
        self.update_drives()

    def update_everything(self) -> None:
        """
        Update the modules and the drives.

        :return: None.
        """
        self.update_drives()
        self.update_modules()

    def update_modules(self) -> None:
        """
        Update the displayed modules.

        :return: None.
        """
        self.update_modules_in_bundle()
        self.update_modules_in_device()

    def update_drives(self) -> None:
        """
        Update the displayed list of drives.

        :return: None.
        """
        try:
            connected_drives = drives.list_connected_drives(not self.show_all_drives_var.get(),
                                                            Path(self.load_key("unix_drive_mount_point")))
        except OSError:
            logger.error(f"Could not get connected drives!\n\n{traceback.format_exc()}")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while getting a list of connected drives!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
            return
        logger.debug(f"Connected drives: {repr(connected_drives)}")
        self.drive_combobox["values"] = connected_drives
        if self.drive_combobox.get() == "" and len(drives.list_connected_drives(not self.show_all_drives_var.get(), Path(self.load_key("unix_drive_mount_point")))) > 0:
            selected_drive = drives.list_connected_drives(not self.show_all_drives_var.get(), Path(self.load_key("unix_drive_mount_point")))[0]
            logger.debug(f"Setting selected drive to {repr(selected_drive)}!")
            self.drive_combobox.set(selected_drive)

    def copy_to_clipboard(self, string: str = "") -> None:
        """
        Copy the string to the clipboard.

        :param string: A string to copy to the clipboard.
        :return: None.
        """
        logger.debug(f"Copying {repr(string)} to clipboard!")
        self.clipboard_clear()
        self.clipboard_append(string)
        self.update()

    def open_file(self, path: Union[Path, str], download_url: str = None) -> None:
        """
        Open a file or a web page.

        :param path: A string or a path representing the web page or the path of the file/directory.
        :param download_url: If a file, the link to where we can download the file if it is missing.
        :return: None.
        """
        logger.debug(f"Opening {repr(path)}...")
        if isinstance(path, Path):
            if path.exists():
                webbrowser.open(str(path))
            else:
                mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                               "Oh no! An error occurred while opening this file!\n"
                               f"The file {repr(path)} does not exist!")
                if download_url and mbox.askokcancel("CircuitPython Bundle Manager: Confirm",
                                                     "It looks like this file is available on GitHub!\n"
                                                     "Would you like to download it?"):
                    if download_dialog.download(master=self, url=download_url, path=path,
                                                show_traceback=self.show_traceback()):
                        webbrowser.open(str(path))
        else:
            webbrowser.open(path)

    def open_markdown(self, path: Union[str, Path], download_url: str = None) -> None:
        """
        Open a file or a web page.

        :param path: A string or a path to the markdown file.
        :param download_url: If a file, the link to where we can download the file if it is missing.
        :return: None.
        """
        logger.debug(f"Opening markdown file {repr(path)}...")
        if isinstance(path, Path):
            path = Path(path)
        if path.exists():
            logger.debug(f"Converting markdown to HTML...")
            html_path = Path.cwd() / (path.stem + ".html")
            html_path.write_text(markdown_to_html(text=path.read_text(), extensions=["pymdownx.tilde"]))
            logger.debug(f"Opening HTML in browser...")
            webbrowser.open(url=html_path.as_uri())
        else:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while opening this file!\n"
                           f"The file {repr(path)} does not exist!")
            if download_url and mbox.askokcancel("CircuitPython Bundle Manager: Confirm",
                                                 "It looks like this file is available on GitHub!\n"
                                                 "Would you like to download it?"):
                if download_dialog.download(master=self, url=download_url, path=path,
                                            show_traceback=self.show_traceback()):
                    self.open_markdown(path=path)

    def make_open_readme_buttons(self) -> None:
        """
        Make the open README.md buttons.

        :return: None.
        """
        self.readme_frame = ttk.Frame(master=self.other_frame)
        self.readme_frame.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_readme_button = ttk.Button(
            master=self.readme_frame, text="Open README file",
            command=lambda: self.open_markdown(
                Path.cwd() / "README.md",
                download_url="https://raw.githubusercontent.com/UnsignedArduino/CircuitPython-Bundle-Manager/main/README.md"
            )
        )
        self.open_readme_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_readme_button, text="Open the README file in the default markdown editor.")
        self.open_readme_button_location = ttk.Button(
            master=self.readme_frame, text="Open README file location",
            command=lambda: self.open_file(Path.cwd())
        )
        self.open_readme_button_location.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_readme_button_location, text="Open the README file location in the default file manager.")

    def make_open_config_buttons(self) -> None:
        """
        Make the open config buttons.

        :return: None.
        """
        self.config_frame = ttk.Frame(master=self.other_frame)
        self.config_frame.grid(row=2, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_config_button = ttk.Button(
            master=self.config_frame, text="Open config file",
            command=lambda: self.open_file(Path.cwd() / "config.json")
        )
        self.open_config_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_config_button, text="Open the config file in the default json editor.")
        self.open_config_button_location = ttk.Button(
            master=self.config_frame, text="Open config file location",
            command=lambda: self.open_file(Path.cwd())
        )
        self.open_config_button_location.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_config_button_location, text="Open the config file location in the default file manager.")

    def make_open_log_buttons(self) -> None:
        """
        Make the open log buttons.

        :return: None.
        """
        self.log_frame = ttk.Frame(master=self.other_frame)
        self.log_frame.grid(row=4, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_log_button = ttk.Button(
            master=self.log_frame, text="Open log file",
            command=lambda: self.open_file(Path.cwd() / "log.log")
        )
        self.open_log_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_config_button, text="Open the log file in the default log editor.")
        self.open_log_button_location = ttk.Button(
            master=self.log_frame, text="Open log file location",
            command=lambda: self.open_file(Path.cwd())
        )
        self.open_log_button_location.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_log_button_location, text="Open the log file location in the default file manager.")

    def make_open_github_repo_buttons(self) -> None:
        """
        Make the open GitHub repo buttons.

        :return: None.
        """
        self.github_repo_frame = ttk.Frame(master=self.other_frame)
        self.github_repo_frame.grid(row=6, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Open GitHub repo link",
            command=lambda: self.open_file("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.open_github_repo_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_github_repo_button, text="Open the GitHub repo for this project in the default browser.")
        self.copy_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Copy GitHub repo link",
            command=lambda: self.copy_to_clipboard("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.copy_github_repo_button.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.copy_github_repo_button, text="Copy the link to the GitHub repo for this project to the clipboard.")

    def make_open_issue_buttons(self) -> None:
        """
        Make the open new issue buttons.

        :return: None.
        """
        self.github_repo_frame = ttk.Frame(master=self.other_frame)
        self.github_repo_frame.grid(row=8, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Open an issue",
            command=lambda: self.open_file("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/issues/new")
        )
        self.open_github_repo_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_github_repo_button, text="Open a new issue panel for this project in the default browser.")
        self.copy_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Copy link to open issue",
            command=lambda: self.copy_to_clipboard("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/issues/new")
        )
        self.copy_github_repo_button.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.copy_github_repo_button, text="Copy the link to open a new issue panel for this project to the clipboard.")

    def create_other_tab(self) -> None:
        """
        Create the other tab.

        :return: None.
        """
        self.other_frame = ttk.Frame(master=self.notebook)
        self.other_frame.grid(row=0, column=0)
        self.notebook.add(self.other_frame, text="Other")
        self.make_open_readme_buttons()
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.make_open_config_buttons()
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.make_open_log_buttons()
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=5, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.make_open_github_repo_buttons()
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=7, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.make_open_issue_buttons()

    def show_traceback(self) -> bool:
        """
        Whether to show the traceback or not depending on the config file.

        :return: None.
        """
        try:
            return self.load_key("show_traceback_in_error_messages").lower() in ("yes", "true", "1")
        except AttributeError:
            return False

    def create_config(self) -> None:
        """
        Re-create the config keys if they do not exist.

        :return: None.
        """
        if not self.load_key("last_circuit_python_bundle_version"):
            self.save_key("last_circuit_python_bundle_version", "6")
        if not self.load_key("last_auth_method_used"):
            self.save_key("last_auth_method_used", "username and password")
        if not self.load_key("show_traceback_in_error_messages"):
            self.save_key("show_traceback_in_error_messages", "false")
        if not self.load_key("unix_drive_mount_point"):
            self.save_key("unix_drive_mount_point", "/media")

    def get_code(self) -> Union[Path, None]:
        """
        Return the path to the code file from the selected device.

        :return: A pathlib.Path object pointing to the code file or None if we could not find it.
        """
        codes = ["code.txt", "code.py", "main.txt", "main.py"]
        if not self.drive_combobox.get() or not Path(self.drive_combobox.get()).exists():
            return None
        for code_path in codes:
            path = Path(self.drive_combobox.get()) / code_path
            if path.exists():
                return path
        return None

    def update_detect_button(self) -> None:
        """
        Update the detect button depending on the current situation.

        :return: None.
        """
        self.after(ms=100, func=self.update_detect_button)
        enable = not (not self.drive_combobox.get() or not Path(self.drive_combobox.get()).exists() or not self.get_code())
        self.detect_refresh_button.config(state=tk.NORMAL if enable else tk.DISABLED)
        if hasattr(self, "detected_modules_listbox_var") and not enable:
            self.detected_modules_listbox_var.set([])

    def update_detected_modules_listbox_right_click(self) -> None:
        """
        Update the right click for the detected modules.

        :return: None.
        """
        enable = not (not self.drive_combobox.get() or not Path(self.drive_combobox.get()).exists() or not self.get_code())
        if enable:
            self.detected_modules_listbox.right_click_menu.delete(8)
            self.detected_modules_listbox.right_click_menu.add_command(label="Detect again",
                                                                       command=self.update_detect, state=tk.NORMAL)
        else:
            self.detected_modules_listbox.right_click_menu.delete(8)
            self.detected_modules_listbox.right_click_menu.add_command(label="Detect again",
                                                                       command=self.update_detect, state=tk.DISABLED)

    def update_detect(self) -> None:
        """
        Update the detected modules.

        :return: None.
        """
        self.detected_modules_listbox_var.set([])
        code_path = self.get_code()
        if not code_path:
            return
        self.modules_imported, self.module_lines = imported.get_imported(code_path.read_text())
        self.modules_imported = [module.split(".")[0] for module in self.modules_imported]
        logger.debug(f"Modules imported: {repr(self.modules_imported)}")
        self.detected_modules_listbox_var.set(self.modules_imported)

    def update_find_in_bundle_button(self) -> None:
        """
        Update the find in bundle button depending on the current situation.

        :return: None.
        """
        self.after(ms=100, func=self.update_find_in_bundle_button)
        if not hasattr(self, "detected_modules_listbox"):
            return
        if not hasattr(self, "bundles"):
            return
        if not self.detected_modules_listbox.curselection():
            return
        selected = self.detected_modules_listbox.get(self.detected_modules_listbox.curselection())
        if selected in self.bundles:
            self.detect_find_in_bundle_button.config(state=tk.NORMAL)
        elif f"{selected}.mpy" in self.bundles:
            self.detect_find_in_bundle_button.config(state=tk.NORMAL)
        else:
            self.detect_find_in_bundle_button.config(state=tk.DISABLED)

    def find_in_bundle(self) -> None:
        """
        Find the selected module in the list of detected modules in the bundle.

        :return: None.
        """
        selected = self.detected_modules_listbox.get(self.detected_modules_listbox.curselection())
        self.search_bar_var.set("")
        self.bundle_listbox.selection_clear(0, tk.END)
        if selected in self.bundles:
            self.bundle_listbox.selection_set(self.bundles.index(selected))
            self.bundle_listbox.see(self.bundles.index(selected))
        selected = f"{selected}.mpy"
        if selected in self.bundles:
            self.bundle_listbox.selection_set(self.bundles.index(selected))
            self.bundle_listbox.see(self.bundles.index(selected))
        self.notebook.select(self.bundle_manager_frame)

    def create_detect_top_ui(self) -> None:
        """
        Create the detect tab's top UI. (The two buttons)

        :return: None.
        """
        self.detect_top_frame = ttk.Frame(master=self.detect_frame)
        self.detect_top_frame.grid(row=0, column=0, padx=1, pady=1, sticky=tk.EW + tk.N)
        self.detect_refresh_button = ttk.Button(master=self.detect_top_frame, text="Detect", command=self.update_detect)
        self.detect_refresh_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.detect_refresh_button, text="Check again for imported modules.")
        self.detect_find_in_bundle_button = ttk.Button(master=self.detect_top_frame, text="Find in bundle",
                                                       command=self.find_in_bundle, state=tk.DISABLED)
        self.detect_find_in_bundle_button.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.detect_find_in_bundle_button, text="Find the selected module in the bundle list.")
        self.update_detect_button()
        self.update_find_in_bundle_button()

    def create_detected_listbox_frame(self) -> None:
        """
        Created the detected listbox frame.

        :return: None.
        """
        self.detected_listbox_frame = ttk.LabelFrame(master=self.detected_frame, text="Imported modules")
        self.detected_listbox_frame.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NSEW)
        self.detected_modules_listbox_var = tk.StringVar(value=[])
        if os_detect.on_windows():
            self.detected_modules_listbox = ListboxWithRightClick(master=self.detected_listbox_frame, height=8, width=42,
                                                                  listvariable=self.detected_modules_listbox_var)
        else:
            self.detected_modules_listbox = ListboxWithRightClick(master=self.detected_listbox_frame, height=8, width=38,
                                                                  listvariable=self.detected_modules_listbox_var)
        self.detected_modules_listbox.initiate_right_click_menu(["Copy", "Cut", "Paste", "Select all", "Delete"],
                                                                callback=self.update_detected_modules_listbox_right_click)
        self.detected_modules_listbox.right_click_menu.add_separator()
        self.detected_modules_listbox.right_click_menu.add_command(label="Detect again", command=self.update_detect)
        self.detected_modules_listbox.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.detected_modules_listbox, text="Modules that you imported in your code.")
        self.detected_modules_listbox_scrollbar = ttk.Scrollbar(self.detected_listbox_frame, orient=tk.VERTICAL,
                                                                command=self.detected_modules_listbox.yview)
        self.detected_modules_listbox_scrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.detected_modules_listbox.config(yscrollcommand=self.detected_modules_listbox_scrollbar.set)

    def create_detected_frame(self) -> None:
        """
        Create the detected fram inside the detect tab.

        :return: None.
        """
        self.detected_frame = ttk.Frame(master=self.detect_frame)
        self.detected_frame.grid(row=1, column=0, padx=1, pady=1, sticky=tk.NSEW)
        self.create_detected_listbox_frame()

    def create_detect_tab(self) -> None:
        """
        Create the detect tab.

        :return: None.
        """
        self.detect_frame = ttk.Frame(master=self.notebook)
        self.detect_frame.grid(row=0, column=0)
        self.notebook.add(child=self.detect_frame, text="Detect")
        # TODO: Test on macOS
        self.create_detect_top_ui()
        self.create_detected_frame()
        self.update_detect()

    def create_gui(self) -> None:
        """
        Create the GUI.

        :return: None.
        """
        logger.debug("Creating GUI...")
        if os_detect.on_linux():
            self.global_style = ttk.Style()
            self.global_style.theme_use("clam")
        self.notebook = ttk.Notebook(master=self)
        self.notebook.grid(row=0, column=0, padx=1, pady=1, columnspan=4, sticky=tk.N)
        self.create_config()
        self.create_drive_selector()
        self.create_bundle_update_tab()
        self.create_bundle_manager_tab()
        self.create_detect_tab()
        self.create_other_tab()

    def run(self) -> None:
        """
        Run the GUI, this will block.

        :return: None.
        """
        self.create_gui()
        self.lift()
        self.mainloop()

    def __exit__(self, err_type=None, err_value=None, err_traceback=None):
        if err_type is not None:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! A fatal error has occurred!\n"
                           f"Error type: {err_type}\n"
                           f"Error value: {err_value}\n"
                           f"Error traceback: {err_traceback}\n\n" + traceback.format_exc())
            logger.exception("Uh oh, a fatal error has occurred!", exc_info=True)
