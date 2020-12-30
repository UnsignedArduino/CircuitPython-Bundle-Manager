"""
A module that logs to a tk.Text using the standard logging module.

-----------

Classes list:

- Logger(logging.Handler).__init__(self, master, row: int = 0, col: int = 0, rows: int = 10, cols: int = 32, scrollback: int = 2000, *args, **kwargs)

-----------

Functions list:

No functions!

"""

import tkinter as tk
from tkinter import ttk
from gui_tools.right_click import text, spinbox
from gui_tools.idlelib_clone import tooltip
import logging
from typing import Callable


class Logger(logging.Handler):
    def __init__(self, master, row: int = 0, col: int = 0, rows: int = 10, cols: int = 32, scrollback: int = 2000,
                 save_scrollback_callback: Callable = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLevel(logging.DEBUG)
        self.setFormatter(fmt=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.frame = ttk.Frame(master=master)
        self.frame.grid(row=row, column=col, padx=1, pady=1, sticky=tk.NW)
        self.log = text.TextWithRightClick(master=self.frame, width=cols, height=rows, wrap=tk.NONE, state=tk.DISABLED)
        self.log.initiate_right_click_menu(disable=["Cut", "Paste", "Delete"])
        self.log.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.log, text="The log for the application. Please see the console for the complete log.")
        self.yscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.VERTICAL, command=self.log.yview)
        self.yscrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.xscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.HORIZONTAL, command=self.log.xview)
        self.xscrollbar.grid(row=1, column=0, columnspan=2, padx=1, pady=1, sticky=tk.NSEW)
        self.log.config(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)
        self.bottom_frame = ttk.Frame(master=self.frame)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, padx=1, pady=1)
        self.rows = rows
        self.scrollback = scrollback
        self.save_scrollback_callback = save_scrollback_callback
        self.make_scrollback_widgets()
        self.make_autoscroll_widgets()

    def make_autoscroll_widgets(self):
        self.autoscroll_checkbutton_var = tk.BooleanVar(value=True)
        self.autoscroll_checkbutton = ttk.Checkbutton(master=self.bottom_frame, text="Autoscroll?",
                                                      variable=self.autoscroll_checkbutton_var)
        self.autoscroll_checkbutton.grid(row=0, column=3, padx=1, pady=1, sticky=tk.NW)
        tooltip.Hovertip(self.autoscroll_checkbutton, text="Whether to autoscroll the log when new logs are added.")

    def validate_for_number(self, new):
        return new.isdigit()

    def clear_scrollback(self):
        delete_rows = self.log.get("1.0", tk.END).count("\n") - self.rows
        self.log.config(state=tk.NORMAL)
        self.log.delete("1.0", f"{delete_rows + 1}.0")
        self.log.config(state=tk.DISABLED)

    def save_scrollback(self):
        self.scrollback_spinbox.after(100, self.save_scrollback)
        if not self.scrollback_spinbox.last_scrollback == self.scrollback_spinbox.get():
            self.scrollback_spinbox.last_scrollback = self.scrollback_spinbox.get()
            try:
                self.save_scrollback_callback(self.scrollback_spinbox.get())
            except AttributeError:
                pass

    def make_scrollback_widgets(self):
        ttk.Label(master=self.bottom_frame, text="Scrollback:").grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.check_num_wrapper = (self.frame.register(self.validate_for_number), "%P")
        self.scrollback_spinbox = spinbox.SpinboxWithRightClick(master=self.bottom_frame, from_=self.rows, to=10000,
                                                                width=7, validate="key", increment=10,
                                                                validatecommand=self.check_num_wrapper)
        self.scrollback_spinbox.initiate_right_click_menu()
        self.scrollback_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        self.scrollback_spinbox.set(self.scrollback)
        self.scrollback_spinbox.last_scrollback = self.scrollback_spinbox.get()
        self.save_scrollback()
        tooltip.Hovertip(self.scrollback_spinbox, text="How many lines to keep in the logs.")
        self.clear_scrollback_button = ttk.Button(master=self.bottom_frame, text="Clear", width=9,
                                                  command=self.clear_scrollback)
        self.clear_scrollback_button.grid(row=0, column=2, padx=1, pady=0, sticky=tk.NW)
        tooltip.Hovertip(self.clear_scrollback_button, text="Clear the scrollback.")

    def emit(self, record):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, self.format(record) + "\n")
        if self.autoscroll_checkbutton_var.get():
            self.log.see(tk.END)
        while self.log.get("1.0", tk.END).count("\n") > int(self.scrollback_spinbox.get()):
            self.log.delete("1.0", "2.0")
        self.log.config(state=tk.DISABLED)
