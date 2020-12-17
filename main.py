import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mbox
from threading import Thread
from time import sleep
from bundle_tools import drives, modules, bundle_manager


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CircuitPython Bundle Manager")
        self.resizable(False, False)

    def __enter__(self):
        return self

    def create_bundle_update_frame(self):
        self.github_auth_frame = ttk.LabelFrame(master=self, text="Authenticate with GitHub")
        self.github_auth_frame.grid(row=0, column=0, padx=1, pady=1)
        self.create_username_password_input()
        self.create_access_token_input()
        self.create_github_enterprise_input()
        self.create_auth_method_selector()
        self.update_bundle_button = ttk.Button(master=self.github_auth_frame, text="Update bundle", command=self.update_bundle)
        self.update_bundle_button.grid(row=5, column=1, rowspan=2, padx=1, pady=1)
        self.updating = False
        self.check_button()

    def update_bundle(self):
        update_thread = Thread(target=self._update_bundle, daemon=True)
        update_thread.start()

    def _update_bundle(self):
        self.updating = True
        self.enable_github_auth_inputs(False)
        sleep(1)
        self.updating = False
        self.enable_github_auth_inputs(True)

    def enable_github_auth_inputs(self, enable: bool = True):
        self.enable_username_password(self.github_auth_method_var.get() == "username and password" if enable else False)
        self.enable_access_token(self.github_auth_method_var.get() == "access token" if enable else False)
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise" if enable else False)
        self.user_pass_radio_button.config(state="normal" if enable else "disabled")
        self.access_token_radio_button.config(state="normal" if enable else "disabled")
        self.enterprise_radio_button.config(state="normal" if enable else "disabled")

    def check_button(self):
        if self.updating:
            self.update_bundle_button.config(state="disabled", text="Updating bundle...")
            self.after(100, self.check_button)
            return
        else:
            self.update_bundle_button.config(state="enabled", text="Update bundle")
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
        self.after(100, self.check_button)

    def update_selected_auth_method(self):
        self.enable_username_password(self.github_auth_method_var.get() == "username and password")
        self.enable_access_token(self.github_auth_method_var.get() == "access token")
        self.enable_enterprise(self.github_auth_method_var.get() == "enterprise")

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
        self.update_selected_auth_method()

    def create_github_enterprise_input(self):
        self.enterprise_url_label = ttk.Label(master=self.github_auth_frame, text="GitHub Enterprise URL: ")
        self.enterprise_url_label.grid(row=3, column=0, padx=1, pady=1, sticky=tk.NW)
        self.enterprise_url_entry = ttk.Entry(master=self.github_auth_frame)
        self.enterprise_url_entry.grid(row=3, column=1, padx=1, pady=1, sticky=tk.NW)
        self.enterprise_token_label = ttk.Label(master=self.github_auth_frame, text="Login or token: ")
        self.enterprise_token_label.grid(row=4, column=0, padx=1, pady=1, sticky=tk.NW)
        self.enterprise_token_entry = ttk.Entry(master=self.github_auth_frame)
        self.enterprise_token_entry.grid(row=4, column=1, padx=1, pady=1, sticky=tk.NW)

    def create_access_token_input(self):
        self.access_token_label = ttk.Label(master=self.github_auth_frame, text="Access token: ")
        self.access_token_label.grid(row=2, column=0, padx=1, pady=1, sticky=tk.NW)
        self.access_token_entry = ttk.Entry(master=self.github_auth_frame)
        self.access_token_entry.grid(row=2, column=1, padx=1, pady=1, sticky=tk.NW)

    def create_username_password_input(self):
        self.username_label = ttk.Label(master=self.github_auth_frame, text="Username: ")
        self.username_label.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.password_label = ttk.Label(master=self.github_auth_frame, text="Password: ")
        self.password_label.grid(row=1, column=0, padx=1, pady=1, sticky=tk.NW)
        self.username_entry = ttk.Entry(master=self.github_auth_frame)
        self.username_entry.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        self.password_entry = ttk.Entry(master=self.github_auth_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NW)

    def create_gui(self):
        self.create_bundle_update_frame()

    def run(self):
        self.create_gui()
        self.mainloop()

    def __exit__(self, err_type=None,
                 err_value=None,
                 err_traceback=None):
        if err_type is not None:
            mbox.showerror("CircuitPython Bundle Manager: ERROR!",
                           "Oh no! A fatal error has occurred!\n"
                           f"Error type: {err_type}\n"
                           f"Error value: {err_value}\n"
                           f"Error traceback: {err_traceback}")


with GUI() as gui:
    gui.run()  # Run GUI
