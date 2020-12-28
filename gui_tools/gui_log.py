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
    def __init__(self, master, row, col, rows, cols, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLevel(logging.DEBUG)
        self.setFormatter(fmt=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.frame = ttk.Frame(master=master)
        self.frame.grid(row=row, column=col, padx=1, pady=1, sticky=tk.NW)
        self.log = text.TextWithRightClick(master=self.frame, width=cols, height=rows, wrap=tk.NONE)
        self.log.initiate_right_click_menu(disable=["Cut", "Paste", "Delete"])
        self.log.grid(row=0, column=0, padx=1, pady=1, sticky=tk.NW)
        self.yscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.VERTICAL, command=self.log.yview)
        self.yscrollbar.grid(row=0, column=1, padx=1, pady=1, sticky=tk.NSEW)
        self.xscrollbar = ttk.Scrollbar(master=self.frame, orient=tk.HORIZONTAL, command=self.log.xview)
        self.xscrollbar.grid(row=1, column=0, columnspan=2, padx=1, pady=1, sticky=tk.NSEW)
        self.log.config(state=tk.DISABLED, yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)

    def emit(self, record):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, self.format(record) + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
