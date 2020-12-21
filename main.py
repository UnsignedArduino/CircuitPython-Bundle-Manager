import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mbox
from threading import Thread
from pathlib import Path
import traceback
from github import GithubException
import webbrowser
from time import sleep
import json
import re
from bundle_tools import drives, modules, bundle_manager


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CircuitPython Bundle Manager")
        self.resizable(False, False)
        self.config_path = Path.cwd() / "config.json"

    def __enter__(self):
        return self

    def save_key(self, key=None, value=None):
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        old_json = json.loads(self.config_path.read_text())
        old_json[key] = value
        self.config_path.write_text(json.dumps(old_json, sort_keys=True, indent=4))

    def load_key(self, key):
        if not self.config_path.exists():
            self.config_path.write_text("{}")
        try:
            return json.loads(self.config_path.read_text())[key]
        except (json.decoder.JSONDecodeError, KeyError):
            return None

    def validate_for_number(self, new):
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
        self.version_label = ttk.Label(master=self.github_auth_frame, text="Version: ")
        self.version_label.grid(row=7, column=1, padx=1, pady=1, sticky=tk.NE)
        validate_for_number_wrapper = (self.register(self.validate_for_number), '%P')
        self.version_listbox = ttk.Spinbox(master=self.github_auth_frame, width=3, from_=1, to=100,
                                           command=lambda: self.save_key("last_circuitpython_bundle_version", self.version_listbox.get()),
                                           validate="key", validatecommand=validate_for_number_wrapper)
        self.version_listbox.grid(row=7, column=2, padx=1, pady=1, sticky=tk.NW)
        self.version_listbox.set(self.load_key("last_circuitpython_bundle_version"))
        self.updating = False
        self.check_button()

    def start_update_bundle_thread(self):
        update_thread = Thread(target=self.update_bundle, daemon=True)
        update_thread.start()

    def update_bundle(self):
        self.updating = True
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
            bundle_manager.update_bundle(int(self.version_listbox.get()), github_instance)
            mbox.showinfo("CircuitPython Bundle Manager: Info", "CircuitPython bundle updated successfully!")
        except (TypeError, ValueError):
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Did you enter in the correct CircuitPython version below?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except GithubException:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! An error occurred while updating the bundle!\n"
                           "Something happened while trying to access GitHub! "
                           "Did you enter in the correct credentials?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        self.updating = False
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

    def check_button(self):
        self.after(100, self.check_button)
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

    def create_auth_method_selector(self):
        self.github_auth_method_var = tk.StringVar()
        self.github_auth_method_var.set("username and password")
        self.user_pass_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="Username and password",
            variable=self.github_auth_method_var, value="username and password",
            command=self.update_selected_auth_method
        )
        self.user_pass_radio_button.grid(row=5, column=0, padx=1, pady=1, sticky=tk.NW)
        self.access_token_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="Access token",
            variable=self.github_auth_method_var, value="access token",
            command=self.update_selected_auth_method
        )
        self.access_token_radio_button.grid(row=6, column=0, padx=1, pady=1, sticky=tk.NW)
        self.enterprise_radio_button = ttk.Radiobutton(
            master=self.github_auth_frame, text="GitHub Enterprise",
            variable=self.github_auth_method_var, value="enterprise",
            command=self.update_selected_auth_method
        )
        self.enterprise_radio_button.grid(row=7, column=0, padx=1, pady=1, sticky=tk.NW)
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
        self.enterprise_url_entry = ttk.Entry(master=self.github_auth_frame)
        self.enterprise_url_entry.grid(row=3, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_token_label = ttk.Label(master=self.github_auth_frame, text="Login or token: ")
        self.enterprise_token_label.grid(row=4, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.enterprise_token_entry = ttk.Entry(master=self.github_auth_frame)
        self.enterprise_token_entry.grid(row=4, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)

    def create_access_token_input(self):
        self.access_token_label = ttk.Label(master=self.github_auth_frame, text="Access token: ")
        self.access_token_label.grid(row=2, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.access_token_entry = ttk.Entry(master=self.github_auth_frame)
        self.access_token_entry.grid(row=2, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)

    def create_username_password_input(self):
        self.username_label = ttk.Label(master=self.github_auth_frame, text="Username: ")
        self.username_label.grid(row=0, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.password_label = ttk.Label(master=self.github_auth_frame, text="Password: ")
        self.password_label.grid(row=1, column=0, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.username_entry = ttk.Entry(master=self.github_auth_frame)
        self.username_entry.grid(row=0, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)
        self.password_entry = ttk.Entry(master=self.github_auth_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=1, pady=1, columnspan=2, sticky=tk.NW)

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
        self.update_modules_in_bundle()
        self.update_modules_in_device()

    def update_modules_in_device(self):
        try:
            self.installed_modules_listbox_var.set(modules.list_modules(Path(self.drive_combobox.get())))
        except (AttributeError, RuntimeError):
            pass

    def update_modules_in_bundle(self):
        try:
            bundles = bundle_manager.list_modules_in_bundle(int(self.version_listbox.get()))
            if bundles == None:
                bundles = []
            self.bundle_listbox_var.set(bundles)
        except (ValueError, AttributeError):
            pass

    def update_buttons(self):
        self.after(100, self.update_buttons)
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
        self.bundle_listbox = tk.Listbox(self.bundle_listbox_frame, width=19, height=10, listvariable=self.bundle_listbox_var)
        self.bundle_listbox.grid(row=0, column=0, padx=1, pady=1)
        self.bundle_listbox_scrollbar = ttk.Scrollbar(self.bundle_listbox_frame, orient=tk.VERTICAL, command=self.bundle_listbox.yview)
        self.bundle_listbox_scrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.bundle_listbox.config(yscrollcommand=self.bundle_listbox_scrollbar.set)

    def create_installed_module_list(self):
        self.installed_modules_listbox_frame = ttk.LabelFrame(master=self.bundle_manager_frame, text="Installed modules")
        self.installed_modules_listbox_frame.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NE)
        self.installed_modules_listbox_var = tk.StringVar()
        self.installed_modules_listbox = tk.Listbox(self.installed_modules_listbox_frame, width=18, height=5, listvariable=self.installed_modules_listbox_var)
        self.installed_modules_listbox.grid(row=0, column=0, padx=1, pady=1)
        self.installed_modules_listbox_scrollbar = ttk.Scrollbar(self.installed_modules_listbox_frame, orient=tk.VERTICAL, command=self.installed_modules_listbox.yview)
        self.installed_modules_listbox_scrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.installed_modules_listbox.config(yscrollcommand=self.installed_modules_listbox_scrollbar.set)

    def create_module_buttons(self):
        self.install_module_button = ttk.Button(self.bundle_manager_frame, text="Install", command=self.start_install_module_thread)
        self.install_module_button.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.uninstall_module_button = ttk.Button(self.bundle_manager_frame, text="Uninstall", command=self.start_uninstall_module_thread)
        self.uninstall_module_button.grid(row=2, column=1, padx=1, pady=1, sticky=tk.NSEW)

    def start_uninstall_module_thread(self):
        uninstall_thread = Thread(target=self.uninstall_module, daemon=True)
        uninstall_thread.start()

    def uninstall_module(self):
        self.uninstalling = True
        drive = Path(self.drive_combobox.get())
        try:
            module_path = modules.get_lib_path(drive) / modules.list_modules(drive)[self.installed_modules_listbox.curselection()[0]]
            modules.uninstall_module(module_path)
        except FileNotFoundError:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module - did you input a drive that exists?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to uninstall module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully uninstalled module!")
        self.uninstalling = False
        self.after(100, self.update_modules_in_device)

    def start_install_module_thread(self):
        install_thread = Thread(target=self.install_module, daemon=True)
        install_thread.start()

    def install_module(self):
        self.installing = True
        try:
            bundle_path = bundle_manager.get_bundle_path(int(self.version_listbox.get()))
            bundles = bundle_manager.list_modules_in_bundle(int(self.version_listbox.get()))[self.bundle_listbox.curselection()[0]]
            modules.install_module(
                bundle_path / bundles,
                Path(self.drive_combobox.get()) / "lib"
            )
        except FileNotFoundError:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module - did you input a drive that exists?\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        except RuntimeError:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Failed to install module!\n\n" + (traceback.format_exc() if self.show_traceback() else ""))
        else:
            mbox.showinfo("CircuitPython Bundle Manager: Info", "Successfully installed module!")
        self.installing = False
        self.after(100, self.update_modules_in_device)

    def create_drive_selector(self):
        self.drive_combobox_label = ttk.Label(master=self, text="Drive:")
        self.drive_combobox_label.grid(row=1, column=0, padx=1, pady=1)
        self.drive_combobox = ttk.Combobox(master=self, width=16)
        self.drive_combobox.grid(row=1, column=1, padx=1, pady=1)
        self.refresh_drives_button = ttk.Button(master=self, text="↻", width=2, command=self.update_drives)
        self.refresh_drives_button.grid(row=1, column=2, padx=1, pady=1)
        self.show_all_drives_var = tk.BooleanVar()
        self.show_all_drives_var.set(False)
        self.show_all_drives_checkbutton = ttk.Checkbutton(master=self, text="Show all drives?",
                                                           variable=self.show_all_drives_var, command=self.update_drives)
        self.show_all_drives_checkbutton.grid(row=1, column=3, padx=1, pady=1)
        self.update_drives()

    def update_drives(self):
        self.update_modules_in_bundle()
        self.update_modules_in_device()
        self.drive_combobox["values"] = drives.list_connected_drives(not self.show_all_drives_var.get())
        if len(drives.list_connected_drives()) > 0:
            self.drive_combobox.set(drives.list_connected_drives()[0])

    def copy_to_clipboard(self, string: str = ""):
        self.clipboard_clear()
        self.clipboard_append(string)
        self.update()

    def create_other_tab(self):
        self.other_frame = ttk.Frame(master=self.notebook)
        self.other_frame.grid(row=0, column=0)
        self.notebook.add(self.other_frame, text="Other")
        self.open_readme_button = ttk.Button(
            master=self.other_frame, text="Open README file",
            command=lambda: webbrowser.open(str(Path.cwd() / "README.md"))
        )
        self.open_readme_button.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.copy_readme_location_button = ttk.Button(
            master=self.other_frame, text="Copy README file location",
            command=lambda: self.copy_to_clipboard(str(Path.cwd() / "README.md"))
        )
        self.copy_readme_location_button.grid(row=1, column=0, padx=1, pady=1, sticky=tk.NW)
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.open_config_button = ttk.Button(
            master=self.other_frame, text="Open config file",
            command=lambda: webbrowser.open(str(Path.cwd() / "config.json"))
        )
        self.open_config_button.grid(row=3, column=0, padx=1, pady=1, sticky=tk.NW)
        self.copy_config_location_button = ttk.Button(
            master=self.other_frame, text="Copy config file location",
            command=lambda: self.copy_to_clipboard(str(Path.cwd() / "config.json"))
        )
        self.copy_config_location_button.grid(row=4, column=0, padx=1, pady=1, sticky=tk.NW)
        ttk.Separator(master=self.other_frame, orient=tk.HORIZONTAL).grid(row=5, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.open_github_repo_button = ttk.Button(
            master=self.other_frame, text="Open GitHub repo in browser",
            command=lambda: webbrowser.open("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.open_github_repo_button.grid(row=6, column=0, padx=1, pady=1, sticky=tk.NW)
        self.copy_github_repo_button = ttk.Button(
            master=self.other_frame, text="Copy GitHub repo link",
            command=lambda: self.copy_to_clipboard("https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager")
        )
        self.copy_github_repo_button.grid(row=7, column=0, padx=1, pady=1, sticky=tk.NW)

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

    def create_gui(self):
        self.notebook = ttk.Notebook(master=self)
        self.notebook.grid(row=0, column=0, padx=1, pady=1, columnspan=4, sticky=tk.N)
        self.create_config()
        self.create_drive_selector()
        self.create_bundle_update_tab()
        self.create_bundle_manager_tab()
        self.create_other_tab()

    def run(self):
        self.create_gui()
        self.mainloop()

    def __exit__(self, err_type=None, err_value=None, err_traceback=None):
        if err_type is not None:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! A fatal error has occurred!\n"
                           f"Error type: {err_type}\n"
                           f"Error value: {err_value}\n"
                           f"Error traceback: {err_traceback}\n\n" + traceback.format_exc())


with GUI() as gui:
    gui.run()  # Run GUI
