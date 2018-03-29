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


Dialog to delete notes
"""


from tkinter import Toplevel, PhotoImage, Text, Menu, StringVar
from tkinter.ttk import Label, Frame, Button, Notebook, Checkbutton, Menubutton
from mynoteslib.constantes import CONFIG, IM_DELETE, IM_CHANGE
from mynoteslib.autoscrollbar import AutoScrollbar as Scrollbar
from mynoteslib.messagebox import askokcancel


class Manager(Toplevel):
    """Note manager."""
    def __init__(self, master):
        """Create note manager to easily delete multiple notes."""
        Toplevel.__init__(self, master, class_='MyNotes')
        self.title(_("Notes Manager"))
        self.grab_set()
        categories = CONFIG.options("Categories")
        categories.sort()

        self.im_del = PhotoImage(file=IM_DELETE, master=self)
        self.im_change = PhotoImage(file=IM_CHANGE, master=self)

        self.notebook = Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.texts = {}
        self.frames = {}
        self.notes = {}

        # to change notes category
        menu_cat = Menu(self, tearoff=False)
        self.category = StringVar(self)

        # create one tab per category
        for cat in categories:
            menu_cat.add_radiobutton(label=cat.capitalize(), value=cat,
                                     variable=self.category,
                                     command=self.move_selection)
            self.notes[cat] = {}
            frame = Frame(self.notebook)
            self.texts[cat] = Text(frame, width=1, height=1, bg=self.cget('bg'),
                                   relief='flat', highlightthickness=0,
                                   padx=4, pady=4, cursor='arrow')
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

            self.texts[cat].grid(row=0, column=0, sticky='ewsn', padx=(0, 2))
            scrolly = Scrollbar(frame, orient='vertical',
                                command=self.texts[cat].yview)
            scrolly.grid(row=0, column=1, sticky='ns')
            scrollx = Scrollbar(frame, orient='horizontal',
                                command=self.texts[cat].xview)
            scrollx.grid(row=1, column=0, sticky='ew')
            self.texts[cat].configure(xscrollcommand=scrollx.set,
                                      yscrollcommand=scrolly.set)
            self.frames[cat] = Frame(self.texts[cat])
            self.frames[cat].columnconfigure(1, weight=1, minsize=170)
            self.frames[cat].columnconfigure(2, weight=1, minsize=170)
            self.frames[cat].columnconfigure(0, minsize=20)
            self.texts[cat].window_create('1.0', window=self.frames[cat])
            b_frame = Frame(frame)
            b_frame.grid(row=2, columnspan=2)
            Button(b_frame, image=self.im_del, command=self.del_selection,
                   padding=1).grid(row=0, column=1, padx=4, pady=4, sticky='w')

            Menubutton(b_frame, image=self.im_change, text=_('Change category'),
                       compound='right', menu=menu_cat,
                       padding=1).grid(row=0, column=0, padx=4, pady=4, sticky='nse')

            self.notebook.add(frame, text=cat.capitalize(), sticky="ewsn",
                              padding=0)
        # display notes by category
        for key, note_data in self.master.note_data.items():
            self.display_note(key, note_data)
#            cat = note_data["category"]
#            c, r = self.frames[cat].grid_size()
#            self.notes[cat][key] = []
#            title = note_data['title'][:20]
#            title = title.replace('\t', ' ') + ' ' * (20 - len(title))
#            self.notes[cat][key].append(Checkbutton(self.frames[cat], text=title,
#                                                    style='manager.TCheckbutton'))
#            txt = note_data['txt'].splitlines()
#            if txt:
#                txt = txt[0][:17] + (len(txt[0]) > 17 or len(txt) > 1) * '...'
#            else:
#                txt = ''
#            txt = txt.replace('\t', ' ') + ' ' * (20 - len(txt))
#            self.notes[cat][key].append(Label(self.frames[cat], text=txt))
#            for i, widget in enumerate(self.notes[cat][key]):
#                widget.grid(row=r, column=i, sticky='w', padx=4, pady=4)

        for txt in self.texts.values():
            txt.configure(state='disabled')
        self.geometry('410x450')
        self.bind("<Button-4>", lambda e: self.scroll(-1))
        self.bind("<Button-5>", lambda e: self.scroll(1))
        self.notebook.bind('<<NotebookTabChanged>>', self.on_change_tab)

    def display_note(self, key, note_data):
        """Display note in note manager."""
        cat = note_data["category"]
        c, r = self.frames[cat].grid_size()
        self.notes[cat][key] = []
        title = note_data['title'][:20]
        title = title.replace('\t', ' ') + ' ' * (20 - len(title))
        self.notes[cat][key].append(Checkbutton(self.frames[cat], text=title,
                                                style='manager.TCheckbutton'))
        txt = note_data['txt'].splitlines()
        if txt:
            txt = txt[0][:17] + (len(txt[0]) > 17 or len(txt) > 1) * '...'
        else:
            txt = ''
        txt = txt.replace('\t', ' ') + ' ' * (20 - len(txt))
        self.notes[cat][key].append(Label(self.frames[cat], text=txt))
        for i, widget in enumerate(self.notes[cat][key]):
            widget.grid(row=r, column=i, sticky='w', padx=4, pady=4)

    def on_change_tab(self, event):
        self.category.set(self.notebook.tab("current", "text").lower())

    def del_selection(self):
        """Delete selected notes."""
        rep = askokcancel(_("Confirmation"), _("Delete the selected notes?"))
        if rep:
            cat = self.notebook.tab('current', 'text').lower()
            sel = self.get_selection(cat)
            for key in sel:
                self.master.delete_note(key)
                for widget in self.notes[cat][key]:
                    widget.destroy()

    def move_selection(self):
        """Change selected notes category."""
        cat = self.notebook.tab('current', 'text').lower()
        new_cat = self.category.get()
        if new_cat != cat:
            rep = askokcancel(_("Confirmation"), _("Change the category of the selected notes?"))
            if rep:
                sel = self.get_selection(cat)
                for key in sel:
                    self.master.change_note_category(key, new_cat)
                    for widget in self.notes[cat][key]:
                        widget.destroy()
                    self.display_note(key, self.master.note_data[key])

            self.category.set(cat)

    def get_selection(self, cat):
        sel = []
        for key, widgets in self.notes[cat].items():
            if 'selected' in widgets[0].state():
                sel.append(key)
        return sel

#    def delete_note(self, note_id):
#        self.master.delete_note(note_id)
#        for widget in self.notes[note_id]:
#            widget.destroy()

    def scroll(self, delta):
        cat = self.notebook.tab("current", "text").lower()
        top, bottom = self.texts[cat].yview()
        top += delta * 0.05
        top = min(max(top, 0), 1)
        self.texts[cat].yview_moveto(top)
