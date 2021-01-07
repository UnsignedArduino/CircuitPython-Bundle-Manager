import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mbox
from gui_tools.right_click.entry import EntryWithRightClick
from gui_tools.right_click.spinbox import SpinboxWithRightClick
from gui_tools.right_click.combobox import ComboboxWithRightClick
from gui_tools.right_click.listbox import ListboxWithRightClick
from gui_tools.idlelib_clone import tooltip
from gui_tools import gui_log
from threading import Thread
from pathlib import Path
import traceback
from github import GithubException
import requests
import webbrowser
from time import sleep
import json
from bundle_tools import drives, modules, bundle_manager, os_detect
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CircuitPython Bundle Manager")
        self.resizable(False, False)
        self.config_path = Path.cwd() / "config.json"
        self.disable_closing = False
        self.protocol("WM_DELETE_WINDOW", self.try_to_close)

    def __enter__(self):
        return self

    def try_to_close(self):
        logger.debug(f"User requested closing window...")
        if self.disable_closing:
            logger.warning(f"Currently in the middle of doing something!")
            if mbox.askokcancel("CircuitPython Bundle Manager: Confirmation",
                                "Something is happening right now!\n"
                                "If you close out now, this will immediately stop what we are doing and may cause a "
                                "corrupt directory hierarchy, broken files and/or broken directories. "
                                "Are you sure you want to exit?",
                                icon="warning", default="cancel"):
                logger.debug(f"User continued to close window!")
                self.destroy()
        else:
            logger.debug(f"Destroying main window!")
            self.destroy()

    def save_key(self, key=None, value=None):
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        old_json = json.loads(self.config_path.read_text())
        logger.debug(f"Setting {repr(key)} to {repr(value)}!")
        old_json[key] = value
        self.config_path.write_text(json.dumps(old_json, sort_keys=True, indent=4))

    def load_key(self, key, log: bool = True):
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        try:
            value = json.loads(self.config_path.read_text())[key]
            if log:
                logger.debug(f"{repr(key)} = {repr(value)}")
            return value
        except (json.decoder.JSONDecodeError, KeyError):
            logger.warning(f"Could not find {repr(key)} in config!")
            return None

    def validate_for_number(self, new):
        logger.debug(f"{repr(new)} did " + ("" if new.isdigit() and len(new) <= 3 else "not ") + "pass validation!")
        return new.isdigit() and len(new) <= 3

    def create_bundle_update_tab(self):
        self.github_auth_frame = ttk.Frame(master=self.notebook)
        self.github_auth_frame.grid(row=0, column=0, padx=1, pady=1)
        self.notebook.add(self.github_auth_frame, text="Update Bundle")
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
                                                     command=lambda: self.save_key("last_circuitpython_bundle_version", self.version_listbox.get()),
                                                     validate="key", validatecommand=validate_for_number_wrapper)
        self.version_listbox.grid(row=7, column=2, padx=1, pady=1, sticky=tk.NW)
        self.version_listbox.set(self.load_key("last_circuitpython_bundle_version"))
        self.version_listbox.initiate_right_click_menu(disable=["Cut", "Delete"])
        tooltip.Hovertip(self.version_listbox, text="The major CircuitPython version used when updating the bundle.")
        self.updating = False
        self.check_update_button()

    def start_update_bundle_thread(self):
        logger.debug(f"Starting update bundle thread!")
        update_thread = Thread(target=self.update_bundle, daemon=True)
        update_thread.start()

    def update_bundle(self):
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
            logger.debug(f"Attempting to update bundle...")
            bundle_manager.update_bundle(int(self.version_listbox.get()), github_instance)
            mbox.showinfo("CircuitPython Bundle Manager: Info", "CircuitPython bundle updated successfully!")
        except (TypeError, ValueError):
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Did you enter in the correct CircuitPython version below?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except GithubException:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access GitHub! "
                           "Did you enter in the correct credentials?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except requests.exceptions.ConnectionError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access the internet! "
                           "Do you have a working internet connection?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except requests.exceptions.ChunkedEncodingError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access the internet! "
                           "Did you internet connection break?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except Exception as _:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!"
                           "\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.info(f"Successfully updated bundle!")
        self.updating = False
        self.disable_closing = False
        self.enable_github_auth_inputs(True)

    def enable_github_auth_inputs(self, enable: bool = True):
        self.enable_username_password(self.github_auth_method_var.get() == "username and password" if enable else False)
        self.enable_access_token(self.github_auth_method_var.get() == "access token" if enable else False)
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise" if enable else False)
        self.user_pass_radio_button.config(state="normal" if enable else "disabled")
        self.access_token_radio_button.config(state="normal" if enable else "disabled")
        self.enterprise_radio_button.config(state="normal" if enable else "disabled")
        self.version_label.config(state="normal" if enable else "disabled")
        self.version_listbox.config(state="normal" if enable else "disabled")

    def check_update_button(self):
        self.after(500, self.check_update_button)
        if self.updating:
            self.update_bundle_button.config(state="disabled", text="Updating bundle...")
            return
        else:
            self.update_bundle_button.config(state="enabled", text="Update bundle")
        if self.version_listbox.get() == "":
            self.update_bundle_button.config(state="disabled")
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
            self.update_bundle_button.config(state="disabled")

    def update_selected_auth_method(self):
        self.enable_username_password(self.github_auth_method_var.get() == "username and password")
        self.enable_access_token(self.github_auth_method_var.get() == "access token")
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise")
        self.save_key("last_auth_method_used", self.github_auth_method_var.get())

    def enable_enterprise(self, enable: bool = True):
        self.enterprise_url_label.config(state="normal" if enable else "disabled")
        self.enterprise_url_entry.config(state="normal" if enable else "disabled")
        self.enterprise_token_label.config(state="normal" if enable else "disabled")
        self.enterprise_token_entry.config(state="normal" if enable else "disabled")

    def enable_access_token(self, enable: bool = True):
        self.access_token_label.config(state="normal" if enable else "disabled")
        self.access_token_entry.config(state="normal" if enable else "disabled")

    def enable_username_password(self, enable: bool = True):
        self.username_label.config(state="normal" if enable else "disabled")
        self.username_entry.config(state="normal" if enable else "disabled")
        self.password_label.config(state="normal" if enable else "disabled")
        self.password_entry.config(state="normal" if enable else "disabled")
        self.show_password_button.config(state="normal" if enable else "disabled")

    def create_auth_method_selector(self):
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

    def create_github_enterprise_input(self):
        self.enterprise_url_label = ttk.Label(master=self.github_auth_frame, text="GitHub Enterprise URL: ")
        self.enterprise_url_label.grid(row=3, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_url_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.enterprise_url_entry.grid(row=3, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_url_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.enterprise_url_entry, text="Input a GitHub Enterprise URl that matches with the login or token below.")
        self.enterprise_token_label = ttk.Label(master=self.github_auth_frame, text="Login or token: ")
        self.enterprise_token_label.grid(row=4, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_token_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.enterprise_token_entry.grid(row=4, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_token_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.enterprise_token_entry, text="Input a GitHub Enterprise login or token that matches with the URL above.")

    def create_access_token_input(self):
        self.access_token_label = ttk.Label(master=self.github_auth_frame, text="Access token: ")
        self.access_token_label.grid(row=2, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.access_token_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.access_token_entry.grid(row=2, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.access_token_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.access_token_entry, text="Input an GitHub access token. Scopes need are:\n - public access")

    def create_username_password_input(self):
        self.username_label = ttk.Label(master=self.github_auth_frame, text="Username: ")
        self.username_label.grid(row=0, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.password_label = ttk.Label(master=self.github_auth_frame, text="Password: ")
        self.password_label.grid(row=1, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.username_entry = EntryWithRightClick(master=self.github_auth_frame)
        self.username_entry.grid(row=0, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.username_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.username_entry, text="Input a GitHub username that matches the password below.")
        self.password_frame = ttk.Frame(master=self.github_auth_frame)
        self.password_frame.grid(row=1, column=1, padx=0, pady=1, columnspan=2, sticky=tk.NW)
        self.password_entry = EntryWithRightClick(master=self.password_frame, width=13, show="*")
        self.password_entry.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.password_entry.initiate_right_click_menu()
        tooltip.Hovertip(self.password_entry, text="Input a GitHub password that matches the username above.")
        self.show_password_button = ttk.Button(master=self.password_frame, width=5, text="Show", command=self.toggle_password_visibility)
        self.show_password_button.grid(row=0, column=1, padx=1, pady=0, sticky=tk.NW)
        tooltip.Hovertip(self.show_password_button, text="Show or hide the password")

    def toggle_password_visibility(self):
        if self.show_password_button["text"] == "Show":
            self.show_password_button.config(text="Hide")
            self.password_entry.config(show="")
        else:
            self.show_password_button.config(text="Show")
            self.password_entry.config(show="*")

    def create_bundle_manager_tab(self):
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

    def update_modules_in_device(self):
        try:
            try:
                installed_modules = modules.list_modules(Path(self.drive_combobox.get()))
            except RuntimeError:
                logger.exception(f"Uh oh! Something happened!")
                installed_modules = []
            installed_modules.sort()
            logger.debug(f"Installed modules: {repr(installed_modules)}")
            self.installed_modules_listbox_var.set(installed_modules)
        except (AttributeError, RuntimeError):
            logger.exception(f"Uh oh! Something happened!")

    def update_modules_in_bundle(self):
        try:
            bundles = bundle_manager.list_modules_in_bundle(int(self.version_listbox.get()))
            if bundles == None:
                bundles = []
            bundles.sort()
            logger.debug(f"Modules in bundle: {repr(bundles)}")
            self.bundle_listbox_var.set(bundles)
        except (ValueError, AttributeError):
            logger.exception(f"Uh oh! Something happened!")

    def update_buttons(self):
        self.after(100, self.update_buttons)
        try:
            if self.updating:
                self.install_module_button.config(state="disabled", text="Updating bundle...\nCannot install!")
                return
            else:
                self.install_module_button.config(text="Install")
        except AttributeError:
            logger.exception(f"Uh oh! Something happened!")
        if self.installing:
            self.install_module_button.config(state="disabled", text="Installing...")
            self.uninstall_module_button.config(state="disabled")
            self.bundle_listbox.config(state="disabled")
            self.installed_modules_listbox.config(state="disabled")
            return
        else:
            self.install_module_button.config(text="Install")
            self.bundle_listbox.config(state="normal")
            self.installed_modules_listbox.config(state="normal")
        if self.uninstalling:
            self.install_module_button.config(state="disabled")
            self.uninstall_module_button.config(state="disabled", text="Uninstalling...")
            self.bundle_listbox.config(state="disabled")
            self.installed_modules_listbox.config(state="disabled")
            return
        else:
            self.uninstall_module_button.config(text="Uninstall")
            self.bundle_listbox.config(state="normal")
            self.installed_modules_listbox.config(state="normal")
        self.install_module_button.config(state="normal" if len(self.bundle_listbox.curselection()) > 0 else "disabled")
        self.uninstall_module_button.config(state="normal" if len(self.installed_modules_listbox.curselection()) > 0 else "disabled")
        if self.drive_combobox.get() == "":
            self.install_module_button.config(state="disabled")
            self.uninstall_module_button.config(state="disabled")

    def create_bundle_list(self):
        self.bundle_listbox_frame = ttk.LabelFrame(master=self.bundle_manager_frame, text="Bundle")
        self.bundle_listbox_frame.grid(row=0, column=0, padx=1, pady=1, rowspan=3)
        self.bundle_listbox_var = tk.StringVar()
        self.bundle_listbox = ListboxWithRightClick(self.bundle_listbox_frame, width=19, height=10, listvariable=self.bundle_listbox_var)
        self.bundle_listbox.grid(row=0, column=0, padx=1, pady=1)
        self.bundle_listbox.initiate_right_click_menu(["Copy", "Cut", "Paste", "Select all", "Delete"])
        self.bundle_listbox.right_click_menu.add_separator()
        self.bundle_listbox.right_click_menu.add_command(label="Refresh bundle", command=self.update_modules_in_bundle)
        tooltip.Hovertip(self.bundle_listbox, text="A list of modules from the CircuitPython bundle.\n"
                                                   "Select a module and press install to install the module to the selected device.")
        self.bundle_listbox_scrollbar = ttk.Scrollbar(self.bundle_listbox_frame, orient=tk.VERTICAL, command=self.bundle_listbox.yview)
        self.bundle_listbox_scrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.bundle_listbox.config(yscrollcommand=self.bundle_listbox_scrollbar.set)

    def create_installed_module_list(self):
        self.installed_modules_listbox_frame = ttk.LabelFrame(master=self.bundle_manager_frame, text="Installed modules")
        self.installed_modules_listbox_frame.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NE)
        self.installed_modules_listbox_var = tk.StringVar()
        self.installed_modules_listbox = ListboxWithRightClick(self.installed_modules_listbox_frame, width=18, height=5, listvariable=self.installed_modules_listbox_var)
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

    def check_for_lib_path(self):
        self.installed_modules_listbox.right_click_menu.delete(9)
        self.installed_modules_listbox.right_click_menu.add_command(
            label="Open in file manager",
            state="normal" if modules.get_lib_path(Path(self.drive_combobox.get())).exists() else "disabled",
            command=lambda: webbrowser.open(str(modules.get_lib_path(Path(self.drive_combobox.get()))))
        )

    def create_module_buttons(self):
        self.install_module_button = ttk.Button(self.bundle_manager_frame, text="Install", command=self.start_install_module_thread)
        self.install_module_button.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NSEW)
        tooltip.Hovertip(self.install_module_button, text="Install the selected module to the selected device.")
        self.uninstall_module_button = ttk.Button(self.bundle_manager_frame, text="Uninstall", command=self.start_uninstall_module_thread)
        self.uninstall_module_button.grid(row=2, column=1, padx=1, pady=1, sticky=tk.NSEW)
        tooltip.Hovertip(self.uninstall_module_button, text="Uninstall the selected module from the selected device.")

    def start_uninstall_module_thread(self):
        logger.debug(f"Starting uninstall module thread!")
        uninstall_thread = Thread(target=self.uninstall_module, daemon=True)
        uninstall_thread.start()

    def uninstall_module(self):
        self.uninstalling = True
        self.disable_closing = True
        drive = Path(self.drive_combobox.get())
        logger.debug(f"Selected drive is {repr(drive)}")
        try:
            module_path = modules.get_lib_path(drive) / modules.list_modules(drive)[self.installed_modules_listbox.curselection()[0]]
            logger.debug(f"Attempting to uninstall module at {repr(module_path)}")
            modules.uninstall_module(module_path)
        except FileNotFoundError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module - did you input a drive that exists?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.debug(f"Successfully uninstalled module!")
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully uninstalled module!")
        self.uninstalling = False
        self.disable_closing = False
        self.after(100, self.update_modules_in_device)

    def start_install_module_thread(self):
        logger.debug(f"Starting install module thread!")
        install_thread = Thread(target=self.install_module, daemon=True)
        install_thread.start()

    def install_module(self):
        self.installing = True
        self.disable_closing = True
        try:
            bundle_path = bundle_manager.get_bundle_path(int(self.version_listbox.get()))
            logger.debug(f"Attempting to install module at {repr(bundle_path)}")
            bundles = bundle_manager.list_modules_in_bundle(int(self.version_listbox.get()))
            bundles.sort()
            bundles = bundles[self.bundle_listbox.curselection()[0]]
            modules.install_module(
                bundle_path / bundles,
                Path(self.drive_combobox.get()) / "lib"
            )
        except FileNotFoundError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module - did you input a drive that exists?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            logger.exception(f"Uh oh! Something happened!")
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            logger.debug(f"Successfully installed module!")
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully installed module!")
        self.installing = False
        self.disable_closing = False
        self.after(100, self.update_modules_in_device)

    def create_drive_selector(self):
        self.drive_combobox_label = ttk.Label(master=self, text="Drive:")
        self.drive_combobox_label.grid(row=1, column=0, padx=1, pady=1)
        self.drive_combobox = ComboboxWithRightClick(master=self, width=16)
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

    def update_everything(self):
        self.update_drives()
        self.update_modules()

    def update_modules(self):
        self.update_modules_in_bundle()
        self.update_modules_in_device()

    def update_drives(self):
        connected_drives = drives.list_connected_drives(not self.show_all_drives_var.get(),
                                                        Path(self.load_key("unix_drive_mount_point")))
        logger.debug(f"Connected drives: {repr(connected_drives)}")
        self.drive_combobox["values"] = connected_drives
        if self.drive_combobox.get() == "" and len(drives.list_connected_drives(not self.show_all_drives_var.get(), Path(self.load_key("unix_drive_mount_point")))) > 0:
            selected_drive = drives.list_connected_drives(not self.show_all_drives_var.get(), Path(self.load_key("unix_drive_mount_point")))[0]
            logger.debug(f"Setting selected drive to {repr(selected_drive)}!")
            self.drive_combobox.set(selected_drive)

    def copy_to_clipboard(self, string: str = ""):
        logger.debug(f"Copying {repr(string)} to clipboard!")
        self.clipboard_clear()
        self.clipboard_append(string)
        self.update()

    def create_other_tab(self):
        self.other_frame = ttk.Frame(master=self.notebook)
        self.other_frame.grid(row=0, column=0)
        self.notebook.add(self.other_frame, text="Other")
        self.readme_frame = ttk.Frame(master=self.other_frame)
        self.readme_frame.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_readme_button = ttk.Button(
            master=self.readme_frame, text="Open README file",
            command=lambda: webbrowser.open(str(Path.cwd() / "README.md"))
        )
        self.open_readme_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_readme_button, text="Open the README file in the default markdown editor.")
        self.open_readme_button_location = ttk.Button(
            master=self.readme_frame, text="Open README file location",
            command=lambda: webbrowser.open(str(Path.cwd()))
        )
        self.open_readme_button_location.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_readme_button_location, text="Open the README file location in the default file manager.")
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.config_frame = ttk.Frame(master=self.other_frame)
        self.config_frame.grid(row=2, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_config_button = ttk.Button(
            master=self.config_frame, text="Open config file",
            command=lambda: webbrowser.open(str(Path.cwd() / "config.json"))
        )
        self.open_config_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_config_button, text="Open the config file in the default json editor.")
        self.open_config_button_location = ttk.Button(
            master=self.config_frame, text="Open config file location",
            command=lambda: webbrowser.open(str(Path.cwd()))
        )
        self.open_config_button_location.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_config_button_location, text="Open the config file location in the default file manager.")
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.github_repo_frame = ttk.Frame(master=self.other_frame)
        self.github_repo_frame.grid(row=4, column=0, padx=1, pady=1, sticky=tk.NW)
        self.open_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Open GitHub repo link",
            command=lambda: webbrowser.open("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.open_github_repo_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.open_github_repo_button, text="Open the GitHub repo for this project in the default browser.")
        self.copy_github_repo_button = ttk.Button(
            master=self.github_repo_frame, text="Copy GitHub repo link",
            command=lambda: self.copy_to_clipboard("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.copy_github_repo_button.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.copy_github_repo_button, text="Copy the link to the GitHub repo for this project to the clipboard.")

    def show_traceback(self):
        try:
            return self.load_key("show_traceback_in_error_messages").lower() in ("yes", "true", "1")
        except AttributeError:
            return False

    def create_config(self):
        if not self.load_key("last_circuitpython_bundle_version"):
            self.save_key("last_circuitpython_bundle_version", "6")
        if not self.load_key("last_auth_method_used"):
            self.save_key("last_auth_method_used", "username and password")
        if not self.load_key("show_traceback_in_error_messages"):
            self.save_key("show_traceback_in_error_messages", "false")
        if not self.load_key("unix_drive_mount_point"):
            self.save_key("unix_drive_mount_point", "/media")
        if not self.load_key("gui_log_scrollback"):
            self.save_key("gui_log_scrollback", "2000")

    def save_scrollback(self, scrollback):
        self.save_key("gui_log_scrollback", scrollback)

    def create_gui(self, log_level: int = logging.DEBUG, handlers_to_add: list = []):
        logger.debug(f"Creating GUI...")
        self.notebook = ttk.Notebook(master=self)
        self.notebook.grid(row=0, column=0, padx=1, pady=1, columnspan=4, sticky=tk.N)
        self.create_config()
        self.create_drive_selector()
        self.create_bundle_update_tab()
        self.create_bundle_manager_tab()
        self.create_other_tab()
        self.notebook.select(0)

    def run(self, log_level: int = logging.DEBUG, handlers_to_add: list = []):
        self.create_gui(log_level=log_level, handlers_to_add=handlers_to_add)
        self.mainloop()

    def __exit__(self, err_type=None, err_value=None, err_traceback=None):
        if err_type is not None:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! A fatal error has occurred!\n"
                           f"Error type: {err_type}\n"
                           f"Error value: {err_value}\n"
                           f"Error traceback: {err_traceback}\n\n" + traceback.format_exc())
            logger.fatel("Uh oh, a fatel error has occurred!", exc_info=True)
