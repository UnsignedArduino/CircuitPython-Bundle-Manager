import tkinter as tk
from tkinter import ttk
from typing import Callable


class ListboxWithRightClick(tk.Listbox):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bind("<Button-3>", self.popup)

    def popup(self, event):
        try:
            self.callback()
        except TypeError:
            pass
        if str(self["state"]) == "normal":
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
        self.select_range(0, tk.END)

    def delete_menu(self):
        if self.selection_present():
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            self.delete(0, tk.END)

    def paste(self):
        if self.selection_present():
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.insert(self.index(tk.INSERT), self.clipboard_get())

    def cut(self):
        if self.selection_present():
            self.copy_to_clipboard(self.selection_get())
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.select_clear()
        else:
            self.copy_to_clipboard(self.get())
            self.delete(0, tk.END)

    def copy(self):
        if self.selection_present():
            self.copy_to_clipboard(self.selection_get())
            self.select_clear()
        else:
            self.copy_to_clipboard(self.get())

    def copy_to_clipboard(self, string: str = ""):
        self.clipboard_clear()
        self.clipboard_append(string)
        self.update()
