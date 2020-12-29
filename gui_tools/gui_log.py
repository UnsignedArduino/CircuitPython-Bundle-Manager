"""
A module that logs to a tk.Text using the standard logging module.

-----------

Classes list:

- WidgetLogger(logging.Handler)

-----------

Functions list:

No functions!

"""

import tkinter as tk
from tkinter import ttk
from gui_tools.right_click import text
import logging


class Logger(logging.Handler):
    def __init__(self, master, row: int = 0, col: int = 0, rows: int = 10, cols: int = 32, scrollback: int = 2000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLevel(logging.DEBUG)
        self.setFormatter(fmt=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.frame = ttk.Frame(master=master)
        self.frame.grid(row=row, column=col, padx=1, pady=1, sticky=tk.NW)
        self.log = text.TextWithRightClick(master=self.frame, width=cols, height=rows, wrap=tk.NONE, state=tk.DISABLED)
        self.log.initiate_right_click_menu(disable=["Cut", "Paste", "Delete"])
        self.log.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.yscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.VERTICAL, command=self.log.yview)
        self.yscrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.xscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.HORIZONTAL, command=self.log.xview)
        self.xscrollbar.grid(row=1, column=0, columnspan=2, padx=1, pady=1, sticky=tk.NSEW)
        self.log.config(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)
        self.bottom_frame = ttk.Frame(master=self.frame)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, padx=1, pady=1)
        self.scrollback = scrollback
        self.rows = rows
        self.make_scrollback_widgets()

    def validate_for_number(self, new):
        return new.isdigit()

    def make_scrollback_widgets(self):
        ttk.Label(master=self.bottom_frame, text="Scrollback:").grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.check_num_wrapper = (self.frame.register(self.validate_for_number), "%P")
        self.scrollback_spinbox = ttk.Spinbox(master=self.bottom_frame, from_=self.rows, to=10000, width=5,
                                              validate="key", validatecommand=self.check_num_wrapper)
        self.scrollback_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NW)
        self.scrollback_spinbox.set(self.scrollback)

    def emit(self, record):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, self.format(record) + "\n")
        self.log.see(tk.END)
        while self.log.get("1.0", tk.END).count("\n") > int(self.scrollback_spinbox.get()):
            self.log.delete("1.0", "2.0")
        self.log.config(state=tk.DISABLED)
