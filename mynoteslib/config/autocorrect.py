#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2018 Juliette Monsel <j_4321@protonmail.com>

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


Configuration window for autocorrect
"""


from tkinter import StringVar
from tkinter.ttk import Treeview, Frame, Label, Button, Entry
from mynoteslib.constants import AUTOCORRECT
from mynoteslib.autoscrollbar import AutoScrollbar


class AutoCorrectConfig(Frame):
    """Configuration window for autocorrect."""

    def __init__(self, master, app, **kwargs):
        Frame.__init__(self, master, padding=4, **kwargs)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.tree = Treeview(self, columns=('replace', 'by'), show='',
                             selectmode='browse')
        scroll_x = AutoScrollbar(self, orient='horizontal', command=self.tree.xview)
        scroll_y = AutoScrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(xscrollcommand=scroll_x.set,
                            yscrollcommand=scroll_y.set)

        self.reset()

        self.replace = StringVar(self)
        self.by = StringVar(self)

        try:
            self.replace.trace_add('write', self._trace_replace)
            self.by.trace_add('write', self._trace_by)
        except AttributeError:
            self.replace.trace_add('w', self._trace_replace)
            self.by.trace_add('w', self._trace_by)

        b_frame = Frame(self)
        self.b_add = Button(b_frame, text=_('New'), command=self.add)
        self.b_rem = Button(b_frame, text=_('Delete'), command=self.remove)
        self.b_add.state(('disabled',))
        self.b_rem.state(('disabled',))
        self.b_add.pack(pady=4, fill='x')
        self.b_rem.pack(pady=4, fill='x')
        Button(b_frame, text=_('Reset'), command=self.reset).pack(pady=8, fill='x')

        Label(self, text=_('Replace')).grid(row=0, column=0, sticky='w', pady=4)
        Label(self, text=_('By')).grid(row=0, column=1, sticky='w', pady=4)
        Entry(self, textvariable=self.replace).grid(row=1, column=0, sticky='ew', pady=4, padx=(0, 4))
        Entry(self, textvariable=self.by).grid(row=1, column=1, sticky='ew', pady=4)
        self.tree.grid(row=2, columnspan=2, sticky='ewsn', pady=(4, 0))
        scroll_x.grid(row=3, columnspan=2, sticky='ew', pady=(0, 4))
        scroll_y.grid(row=2, column=2, sticky='ns', pady=(4, 0))
        b_frame.grid(row=1, rowspan=2, padx=(4, 0), sticky='nw', column=3)

        self.tree.bind('<<TreeviewSelect>>', self._on_treeview_select)

    def _trace_by(self, *args):
        key = self.replace.get().strip()
        val = self.by.get().strip()
        self.by.set(val)
        if key in self.tree.get_children(''):
            if val != self.tree.set(key, 'by'):
                self.b_add.state(('!disabled',))
            else:
                self.b_add.state(('disabled',))
        else:
            self.b_add.state(('!disabled',))
        if not val:
            self.b_add.state(('disabled',))

    def _trace_replace(self, *args):
        key = self.replace.get().strip()
        val = self.by.get().strip()
        self.replace.set(key)
        if not key:
            self.b_add.state(('disabled',))
            self.b_rem.state(('disabled',))
        else:
            self.b_add.state(('!disabled',))
            sel = self.tree.selection()
            if key in self.tree.get_children(''):
                if key not in sel:
                    self.tree.selection_set(key)
                self.b_add.configure(text=_('Replace'))
                self.b_rem.state(('!disabled',))
                if val != self.tree.set(key, 'by'):
                    self.b_add.state(('!disabled',))
                else:
                    self.b_add.state(('disabled',))
            else:
                self.b_rem.state(('disabled',))
                self.b_add.configure(text=_('New'))
                if sel:
                    self.tree.selection_remove(*sel)
        if not val:
            self.b_add.state(('disabled',))

    def _on_treeview_select(self, event):
        sel = self.tree.selection()
        if sel:
            key, val = self.tree.item(sel[0], 'values')
            self.replace.set(key)
            self.by.set(val)

    def reset(self):
        self.tree.delete(*self.tree.get_children(''))
        keys = list(AUTOCORRECT.keys())
        keys.sort()
        for key in keys:
            self.tree.insert('', 'end', key, values=(key, AUTOCORRECT[key]))

    def add(self):
        key = self.replace.get().strip()
        val = self.by.get().strip()
        if key in self.tree.get_children(''):
            self.tree.item(key, values=(key, val))
        elif key and val:
            self.tree.insert('', 'end', key, values=(key, val))

    def remove(self):
        key = self.replace.get()
        if key in self.tree.get_children(''):
            self.tree.delete(key)

    def ok(self):
        keys = self.tree.get_children('')
        AUTOCORRECT.clear()
        for key in keys:
            AUTOCORRECT[key] = self.tree.set(key, 'by')
