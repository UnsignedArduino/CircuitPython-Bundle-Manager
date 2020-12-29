import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mbox
from typing import Callable
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


class TextWithRightClick(tk.Text):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bind("<Button-3>", self.popup)

    def popup(self, event):
        logger.debug(f"Right click! Attempting to pop up context menu...")
        try:
            self.callback()
        except TypeError:
            pass
        finally:
            try:
                self.right_click_menu.tk_popup(event.x_root, event.y_root, 0)
            finally:
                self.right_click_menu.grab_release()

    def initiate_right_click_menu(self, disable: list = [], callback: Callable = None):
        self.right_click_menu = tk.Menu(self, tearoff=0)
        self.right_click_menu.add_command(label="Copy", command=self.copy, state="disabled" if "Copy" in disable else "normal")
        self.right_click_menu.add_command(label="Cut", command=self.cut, state="disabled" if "Cut" in disable else "normal")
        self.right_click_menu.add_command(label="Paste", command=self.paste, state="disabled" if "Paste" in disable else "normal")
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Delete", command=self.delete_menu, state="disabled" if "Delete" in disable else "normal")
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Select all", command=self.select_all, state="disabled" if "Select all" in disable else "normal")
        self.callback = callback

    def select_all(self):
        logger.debug(f"Select all!")
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)

    def delete_menu(self):
        if self.tag_ranges(tk.SEL):
            logger.debug(f"Deleting from {repr(tk.SEL_FIRST)} to {repr(tk.SEL_LAST)}!")
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            logger.debug(f"Deleting everything!")
            self.delete(0, tk.END)

    def paste(self):
        if self.tag_ranges(tk.SEL):
            logger.debug(f"Deleting from {repr(tk.SEL_FIRST)} to {repr(tk.SEL_LAST)}!")
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        logger.debug(f"Inserting {repr(self.clipboard_get())} at {repr(self.index(tk.INSERT))}!")
        self.insert(self.index(tk.INSERT), self.clipboard_get())

    def cut(self):
        if self.tag_ranges(tk.SEL):
            logger.debug(f"Copying {repr(self.selection_get())} to clipboard!")
            self.copy_to_clipboard(self.selection_get())
            logger.debug(f"Deleting from {repr(tk.SEL_FIRST)} to {repr(tk.SEL_LAST)}!")
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            logger.debug(f"Copying everything to clipboard!")
            self.copy_to_clipboard(self.get("1.0", tk.END))
            logger.debug(f"Deleting everything!")
            self.delete(0, tk.END)

    def copy(self):
        if self.tag_ranges(tk.SEL):
            if len(self.selection_get()) > 20000 and mbox.askokcancel("CircuitPython Bundle Manager: Warning!",
                                                                     f"You are about to copy "
                                                                     f"{len(self.get('1.0', tk.END))}"
                                                                     f" characters into the clipboard which might "
                                                                     f"crash the application - are you sure you "
                                                                     f"want to continue?", icon="warning",
                                                                     default="cancel"):
                logger.debug(f"Copying {repr(self.selection_get())} to clipboard!")
                self.copy_to_clipboard(self.selection_get())
                self.tag_remove(tk.SEL, self.tag_ranges(tk.SEL)[0], self.tag_ranges(tk.SEL)[1])
                self.update_idletasks()
        else:
            if len(self.get("1.0", tk.END)) > 20000 and mbox.askokcancel("CircuitPython Bundle Manager: Warning!",
                                                                         f"You are about to copy "
                                                                         f"{len(self.get('1.0', tk.END))}"
                                                                         f" characters into the clipboard which might "
                                                                         f"crash the application - are you sure you "
                                                                         f"want to continue?", icon="warning",
                                                                         default="cancel"):
                logger.debug(f"Copying everything to clipboard!")
                self.copy_to_clipboard(self.get("1.0", tk.END))

    def copy_to_clipboard(self, string: str = ""):
        logger.debug(f"Copying {repr(string)} to clipboard!")
        self.clipboard_clear()
        self.clipboard_append(string)
        self.update()
