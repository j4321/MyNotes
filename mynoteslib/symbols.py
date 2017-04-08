# -*- coding: utf-8 -*-

from tkinter import Tk, Toplevel, Canvas, Menu, TclError
from tkinter.ttk import Frame, Button, Label, Entry, Scrollbar, Menubutton, Style
from mynoteslib.constantes import SYMBOLS


class Palette(Toplevel):
    def __init__(self, master, font, symbols, **kwargs):
        Toplevel.__init__(self, master, **kwargs)
        self.title("Symbols")
        self.grab_set()
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)

        style = Style(self)
        self.activebg = style.lookup("TEntry", "selectbackground", ("focus",))

        self.text_to_insert = ""

        l = len(symbols)
        self.canvas = Canvas(self, background="white",
                             width=240, height=(l//12 + 1)*20)
        self.canvas.grid(row=0, column=0, columnspan=2, sticky="eswn")

        for i,s in enumerate(symbols):
            x = i % 12
            y = i//12
            self.canvas.create_rectangle(x*20, y*20, (x + 1)*20, (y + 1)*20,
                                         activefill=self.activebg, fill="white",
                                         width=0, tags="square")
            self.canvas.create_text(x*20 + 10, y*20 + 10, text=s,
                                    activefill="white", font="%s 11" % font,
                                    tags="char")

        self.canvas.tag_bind("square", "<Button-1>", self.add_square)
        self.canvas.tag_bind("square", "<Enter>", self.enter_square)
        self.canvas.tag_bind("square", "<Leave>", self.leave_square)
        self.canvas.tag_bind("char", "<Button-1>", self.add_char)
        self.canvas.tag_bind("char", "<Enter>", self.enter_char)
        self.canvas.tag_bind("char", "<Leave>", self.leave_char)

        self.entry = Entry(self)
        self.entry.grid(row=1, column=0, sticky="ew")
        self.entry.focus_set()
        self.entry.bind("<Return>", self.ok)

        Button(self, text=_("Insert"), width=len(_("Insert")) + 1,
               command=self.ok).grid(row=1, column=1)


    def enter_square(self, event):
        c = self.canvas.find_withtag("current")
        char = self.canvas.find_above(c)
        self.canvas.itemconfigure(char, fill="white")

    def leave_square(self, event):
        c = self.canvas.find_withtag("current")
        char = self.canvas.find_above(c)
        self.canvas.itemconfigure(char, fill="black")

    def enter_char(self, event):
        c = self.canvas.find_withtag("current")
        square = self.canvas.find_below(c)
        self.canvas.itemconfigure(square, fill=self.activebg)

    def leave_char(self, event):
        c = self.canvas.find_withtag("current")
        square = self.canvas.find_below(c)
        self.canvas.itemconfigure(square, fill="white")

    def add_square(self, event):
        c = self.canvas.find_withtag("current")
        char = self.canvas.find_above(c)
        self.entry.insert("end", self.canvas.itemcget(char, "text"))

    def add_char(self, event):
        char = self.canvas.find_withtag("current")
        self.entry.insert("end", self.canvas.itemcget(char, "text"))

    def ok(self, event=None):
        self.text_to_insert = self.entry.get()
        self.destroy()

    def get_text(self):
        return self.text_to_insert


def pick_symbol(master, font, symbols, **kwargs):
    picker = Palette(master, font, symbols, **kwargs)
    master.wait_window(picker)
    return picker.get_text()
