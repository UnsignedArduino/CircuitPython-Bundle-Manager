import tkinter as tk
from tkinter import ttk


class EntryWithRightClick(ttk.Entry):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.initiate_right_click_menu()
        self.bind("<Button-3>", self.popup)

    def popup(self, event):
        if str(self["state"]) == "normal":
            try:
                self.right_click_menu.tk_popup(event.x_root, event.y_root, 0)
            finally:
                self.right_click_menu.grab_release()

    def initiate_right_click_menu(self):
        self.right_click_menu = tk.Menu(self, tearoff=0)
        self.right_click_menu.add_command(label="Copy", command=self.copy)
        self.right_click_menu.add_command(label="Cut", command=self.cut)
        self.right_click_menu.add_command(label="Paste", command=self.paste)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Delete", command=self.delete_menu)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Select all", command=self.select_all)

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
