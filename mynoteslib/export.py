#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
My Notes - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

My Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

My Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Export dialog
"""


from tkinter import Toplevel
from tkinter.ttk import Checkbutton, Frame, Button, Separator
from mynoteslib.constantes import CONFIG


class Export(Toplevel):
    """Category export dialog."""
    def __init__(self, master):
        """Create export dialog."""
        Toplevel.__init__(self, master)
        self.title(_("Export"))
        self.resizable(False, False)
        self.grab_set()
#        self.columnconfigure(0, weight=1)
        self.categories = CONFIG.options("Categories")
        self.categories.sort()
        self.categories_to_export = []
        self.only_visible = False

        # select all checkbutton
        self.ch_all = Checkbutton(self, text=_("Select all"),
                                  command=self.select_all)
        # export only visible notes checkbutton
        self.ch_only_visible = Checkbutton(self, text=_("Only visible notes"))
        self.ch_all.grid(sticky="w", padx=4, pady=4)
        self.ch_only_visible.grid(sticky="w", padx=4, pady=4)
        Separator(self).grid(sticky="ew", padx=4, pady=4)
        self.checkbuttons = []
        # one checkbutton by category
        for cat in self.categories:
            self.checkbuttons.append(Checkbutton(self, text=cat.capitalize(),
                                                 command=self.toggle_select_all))
            self.checkbuttons[-1].grid(sticky="w", padx=4, pady=4)

        frame = Frame(self)
        frame.grid()

        Button(frame, text="Ok",
               command=self.ok).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        Button(frame, text=_("Cancel"),
               command=self.destroy).grid(row=0, column=1, sticky="e", padx=4, pady=4)
        self.ch_all.state(("selected",))
        self.select_all()

    def ok(self):
        """Validate choice."""
        for ch, cat in zip(self.checkbuttons, self.categories):
            if "selected" in ch.state():
                self.categories_to_export.append(cat)
        self.only_visible = "selected" in self.ch_only_visible.state()
        self.destroy()

    def select_all(self):
        """Select all categories."""
        if ("selected" in self.ch_all.state()):
            state = "selected"
        else:
            state = "!selected"
        for ch in self.checkbuttons:
            ch.state((state,))

    def toggle_select_all(self):
        """Change select all checkbutton state when another checkbutton is clicked."""
        b = 0
        for ch in self.checkbuttons:
            if "selected" in ch.state():
                b += 1
        if b == len(self.checkbuttons):
            self.ch_all.state(("selected",))
        else:
            self.ch_all.state(("!selected",))

    def get_export(self):
        return self.categories_to_export, self.only_visible
