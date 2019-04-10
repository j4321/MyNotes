#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2018-2019 Juliette Monsel <j_4321@protonmail.com>

MyNotes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MyNotes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Font settings
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from mynoteslib.constants import add_trace
from mynoteslib.autocomplete import AutoCompleteCombobox


class FontFrame(ttk.Frame):
    def __init__(self, master, font, size=True, style=False,
                 sample_text=_("Sample text"), font_list=[]):
        ttk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)

        # --- entry validation
        self._validate = self.register(self._validate_entry_nb)
        self._validate_size = self.register(self._validate_font_size)

        # --- chooser
        self.font = tkfont.Font(self, font=font)
        prop = self.font.actual()

        # --- --- Preview
        sample = ttk.Label(self, text=sample_text,
                           anchor="center", font=self.font,
                           style="prev.TLabel", relief="groove")

        sample.grid(row=2, columnspan=2, padx=4, pady=6,
                    ipadx=4, ipady=4, sticky="eswn")

        # --- --- Family
        if not font_list:
            self.fonts = list(set(tkfont.families()))
            self.fonts.append("TkDefaultFont")
            self.fonts.sort()
        else:
            self.fonts = sorted(font_list)

        self.font_family = tk.StringVar(self, value=prop['family'])
        add_trace(self.font_family, 'write',
                  lambda *args: self.font.configure(family=self.font_family.get()))
        w = max([len(f) for f in self.fonts])

        self.choose_family = AutoCompleteCombobox(self, values=self.fonts,
                                                  width=(w * 2) // 3,
                                                  textvariable=self.font_family,
                                                  exportselection=False)
        self.choose_family.current(self.fonts.index(prop['family']))
        self.choose_family.grid(row=0, column=0, padx=4, pady=4, sticky='ew')

        # --- --- Size
        if size:
            self.font_size = tk.StringVar(self, value=prop['size'])
            add_trace(self.font_size, 'write',
                      lambda *args: self._config_size(self.font_size, self.font))
            sizes = list(range(6, 17)) + list(range(18, 32, 2))
            if not prop['size'] in sizes:
                sizes.append(prop['size'])
            sizes.sort()
            self.sizes = ["%i" % i for i in sizes]

            self.choose_size = ttk.Combobox(self, values=self.sizes, width=5,
                                            exportselection=False,
                                            textvariable=self.font_size,
                                            validate="key",
                                            validatecommand=(self._validate_size, "%d", "%P", "%V"))
            self.choose_size.current(self.sizes.index(str(prop['size'])))
            self.choose_size.grid(row=0, column=1, padx=4, pady=4)

        # --- --- Style (bold, italic, underlined)
        if style:
            frame_style = ttk.Frame(self)
            frame_style.grid(row=1, columnspan=2, pady=6)
            self.bold = tk.StringVar(self, value=prop['weight'])
            add_trace(self.bold, 'write',
                      lambda *args: self.font.configure(weight=self.bold.get()))
            self.italic = tk.StringVar(self, value=prop['slant'])
            add_trace(self.italic, 'write',
                      lambda *args: self.font.configure(slant=self.italic.get()))
            self.underline = tk.BooleanVar(self, value=prop['underline'])
            add_trace(self.underline, 'write',
                      lambda *args: self.font.configure(underline=self.underline.get()))
            ttk.Checkbutton(frame_style, text=_("Bold"),
                            onvalue='bold', offvalue='normal',
                            variable=self.bold).pack(side='left', padx=4)
            ttk.Checkbutton(frame_style, text=_("Italic"),
                            onvalue='italic', offvalue='roman',
                            variable=self.italic).pack(side='left', padx=4)
            ttk.Checkbutton(frame_style, text=_("Underline"),
                            variable=self.underline).pack(side='left', padx=4)

    def get_font(self):
        return self.font.actual()

    @staticmethod
    def _config_size(variable, font):
        size = variable.get()
        if size:
            font.configure(size=size)

    @staticmethod
    def _validate_entry_nb(P):
        """ Allow only to enter numbers"""
        parts = P.split(".")
        b = len(parts) < 3 and P != "."
        for p in parts:
            b = b and (p == "" or p.isdigit())
        return b

    def _validate_font_size(self, d, ch, V):
        """Validation of the size entry content."""
        if d == '1':
            l = [i for i in self.sizes if i[:len(ch)] == ch]
            if l:
                i = self.sizes.index(l[0])
                self.choose_size.current(i)
                index = self.choose_size.index("insert")
                self.choose_size.selection_range(index + 1, "end")
                self.choose_size.icursor(index + 1)
            return ch.isdigit()
        else:
            return True
