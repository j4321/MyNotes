#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

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


Dialog to delete notes
"""


from PIL.ImageTk import PhotoImage
from tkinter import Toplevel, Text, Menu, StringVar, BooleanVar
from tkinter.ttk import Label, Frame, Button, Notebook, Checkbutton, Menubutton
from mynoteslib.constants import CONFIG, IM_DELETE, IM_CHANGE, IM_VISIBLE_24, IM_HIDDEN_24
from mynoteslib.autoscrollbar import AutoScrollbar as Scrollbar
from mynoteslib.messagebox import askokcancel
from mynoteslib.tooltip import TooltipWrapper


class Heading(Label):

    _initialized = False

    def __init__(self, master, category, column, anchor='center', command=None,
                 style='heading.TLabel', compound='right', **kwargs):
        Label.__init__(self, master, class_='ManagerHeading', style=style,
                       anchor=anchor, compound=compound, **kwargs)
        self.category = category
        self.column = column
        self.reverse = False
        self.state(['alternate'])

        if command is not None:
            self.bind('<Button-1>', command)

        if not Heading._initialized:
            for seq in self.bind_class('TButton'):
                self.bind_class('ManagerHeading', seq, self.bind_class('TButton', seq))
            Heading._initialized = True


class ManagerItem(Frame):
    def __init__(self, master, note_data, toggle_visibility_cmd):
        Frame.__init__(self, master, class_='ManagerItem', style='manager.TFrame')
        self.columnconfigure(0, weight=0, minsize=18)
        self.columnconfigure(1, weight=1, minsize=198)
        self.columnconfigure(2, weight=1, minsize=198)
        self.columnconfigure(3, weight=0, minsize=85)
        self.columnconfigure(4, weight=0, minsize=22)
        self.toggle_visibility_cmd = toggle_visibility_cmd
        title = note_data['title']
        if title:
            title = title[:17] + (len(title) > 17) * '...'
        title = title.replace('\t', ' ')
        date = note_data.get('date', '??')
        txt = note_data['txt'].splitlines()
        if txt:
            txt = txt[0][:17] + (len(txt[0]) > 17 or len(txt) > 1) * '...'
        else:
            txt = ''
        txt = txt.replace('\t', ' ')
        self._data = {'title': title, 'text': txt, 'date': date}
        self.title = Label(self, text=title, anchor='w', style='manager.TLabel')
        self.text = Label(self, text=txt, anchor='w', style='manager.TLabel')
        self.date = Label(self, text=date, anchor='center', style='manager.TLabel')
        self.checkbutton = Checkbutton(self, style='manager.TCheckbutton')
        self.visibility = BooleanVar(self, note_data['visible'])
        self.toggle_visibility = Checkbutton(self, style='manager.Toggle', variable=self.visibility,
                                             command=self.toggle_visibility)
        self.checkbutton.grid(row=0, column=0, padx=(2, 0), pady=4, sticky='nsew')
        self.title.grid(row=0, column=1, padx=4, pady=4, sticky='ew')
        self.text.grid(row=0, column=2, padx=4, pady=4, sticky='ew')
        self.date.grid(row=0, column=3, padx=4, pady=4, sticky='ew')
        self.toggle_visibility.grid(row=0, column=4, padx=(0, 2), pady=4, sticky='wens')
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.checkbutton.bind('<Enter>', self._on_enter)  # override class binding
        self.checkbutton.bind('<Leave>', self._on_leave)  # override class binding
        self.toggle_visibility.bind('<Enter>', self._on_enter)  # override class binding
        self.toggle_visibility.bind('<Leave>', self._on_leave)  # override class binding
        self.bind('<ButtonRelease-1>', self._on_click)
        self.text.bind('<ButtonRelease-1>', self._on_click)
        self.title.bind('<ButtonRelease-1>', self._on_click)
        self.date.bind('<ButtonRelease-1>', self._on_click)

    def state(self, statespec=None):
        return self.checkbutton.state(statespec)

    def toggle_visibility(self):
        self.toggle_visibility_cmd(self.visibility.get())

    def get(self, key):
        if key is 'visibility':
            return self.visibility.get()
        else:
            return self._data[key]

    def get_values(self):
        return (self._data['title'], self._data['text'], self._data['date'], self.visibility.get())

    def _on_enter(self, event):
        self.title.state(('active',))
        self.text.state(('active',))
        self.date.state(('active',))
        self.checkbutton.state(('active',))
        self.toggle_visibility.state(('active',))
        Frame.state(self, ('active',))
        return "break"

    def _on_leave(self, event):
        self.title.state(('!active',))
        self.text.state(('!active',))
        self.date.state(('!active',))
        self.checkbutton.state(('!active',))
        self.toggle_visibility.state(('!active',))
        Frame.state(self, ('!active',))
        return "break"

    def _on_click(self, event):
        self.checkbutton.invoke()
        return "break"


class Manager(Toplevel):
    """Note manager."""
    def __init__(self, master):
        """Create note manager to easily delete multiple notes."""
        Toplevel.__init__(self, master, class_='MyNotes')
        self.title(_("Note Manager"))
        self.minsize(width=546, height=200)
        self.grab_set()
        categories = CONFIG.options("Categories")
        categories.sort()

        self.im_del = PhotoImage(file=IM_DELETE, master=self)
        self.im_change = PhotoImage(file=IM_CHANGE, master=self)
        self.im_visible = PhotoImage(file=IM_VISIBLE_24, master=self)
        self.im_hidden = PhotoImage(file=IM_HIDDEN_24, master=self)

        tooltipwrapper = TooltipWrapper(self)

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
                                     command=self.change_cat_selection)
            self.notes[cat] = {}
            frame = Frame(self.notebook, padding=2)
            self.texts[cat] = Text(frame, width=1, height=1, bg=self.cget('bg'),
                                   relief='flat', highlightthickness=0,
                                   padx=0, pady=0, cursor='arrow')
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(1, weight=1)

            self.texts[cat].grid(row=1, column=0, sticky='ewsn')
            scrolly = Scrollbar(frame, orient='vertical',
                                command=self.texts[cat].yview)
            scrolly.grid(row=1, column=1, sticky='ns', pady=(2, 0))
            scrollx = Scrollbar(frame, orient='horizontal',
                                command=self.texts[cat].xview)
            scrollx.grid(row=2, column=0, sticky='ew')
            self.texts[cat].configure(xscrollcommand=scrollx.set,
                                      yscrollcommand=scrolly.set)
            self.frames[cat] = Frame(self.texts[cat], style='bg.TFrame',
                                     padding=1, height=29, width=523)
            self.frames[cat].columnconfigure(0, weight=1, minsize=170)
            headings = Frame(frame, padding=(1, 0, 1, 0))
            headings.columnconfigure(0, weight=0, minsize=20)
            headings.columnconfigure(1, weight=1, minsize=198)
            headings.columnconfigure(2, weight=1, minsize=198)
            headings.columnconfigure(3, weight=0, minsize=84)
            headings.columnconfigure(4, weight=0, minsize=22)
            Heading(headings, cat, 'title', command=self.sort_column,
                    text=_('Title')).grid(row=0, column=1, sticky='ew')
            Heading(headings, cat, 'text', command=self.sort_column,
                    text=_('Text')).grid(row=0, column=2, sticky='ew')
            Heading(headings, cat, 'date', command=self.sort_column,
                    text=_('Date')).grid(row=0, column=3, sticky='ew')
            Heading(headings, cat, 'select_all', style='select.heading.TLabel', padding=0,
                    command=self.toggle_selectall).place(x=0, y=0, anchor='nw',
                                                         relheight=1, width=20)
            Heading(headings, cat, 'visibility',
                    command=self.sort_column).place(relx=1, y=0, anchor='ne',
                                                    bordermode='outside',
                                                    width=23, relheight=1)
            headings.place(x=0, y=2, anchor='nw')
            self.update_idletasks()
            frame.rowconfigure(0, minsize=headings.winfo_reqheight())
            self.texts[cat].window_create('1.0', window=self.frames[cat])
            b_frame = Frame(frame)
            b_frame.grid(row=3, columnspan=2)
            m = Menubutton(b_frame, image=self.im_change, text=_('Change category'),
                           compound='right', menu=menu_cat,
                           padding=1)
            m.pack(side='left', padx=4, pady=4, fill='y')
            tooltipwrapper.add_tooltip(m, _('Change category of selected notes'))
            b_show = Button(b_frame, image=self.im_visible, padding=1,
                            command=self.show_selection)
            b_show.pack(side='left', padx=4, pady=4)
            tooltipwrapper.add_tooltip(b_show, _('Show selected notes'))
            b_hide = Button(b_frame, image=self.im_hidden, padding=1,
                            command=self.hide_selection)
            b_hide.pack(side='left', padx=4, pady=4)
            tooltipwrapper.add_tooltip(b_hide, _('Hide selected notes'))
            b_del = Button(b_frame, image=self.im_del, command=self.del_selection,
                           padding=1)
            b_del.pack(side='left', padx=4, pady=4, fill='y')
            tooltipwrapper.add_tooltip(b_del, _('Delete selected notes'))

            self.notebook.add(frame, text=cat.capitalize(), sticky="ewsn",
                              padding=0)
        # display notes by category
        for key, note_data in self.master.note_data.items():
            self.display_note(key, note_data)

        for txt in self.texts.values():
            txt.configure(state='disabled')
        self.geometry('410x450')
        self.bind("<Button-4>", lambda e: self.scroll(-1))
        self.bind("<Button-5>", lambda e: self.scroll(1))
        self.notebook.bind('<<NotebookTabChanged>>', self.on_change_tab)

    def toggle_selectall(self, event):
        heading = event.widget
        cat = heading.category
        sel = self.get_selection(cat)
        if len(sel) == len(self.notes[cat]):
            for widget in self.notes[cat].values():
                widget.state(('!selected',))
        else:
            for widget in self.notes[cat].values():
                widget.state(('selected',))

    def show_selection(self):
        cat = self.notebook.tab('current', 'text').lower()
        sel = self.get_selection(cat)
        if sel:
            for key in sel:
                self.notes[cat][key].visibility.set(True)
                self.toggle_visibility(key, True)

    def hide_selection(self):
        cat = self.notebook.tab('current', 'text').lower()
        sel = self.get_selection(cat)
        if sel:
            for key in sel:
                self.notes[cat][key].visibility.set(False)
                self.toggle_visibility(key, False)

    def select_all(self):
        cat = self.notebook.tab('current', 'text').lower()
        for widget in self.notes[cat].values():
            widget.state(('selected',))

    def deselect_all(self):
        cat = self.notebook.tab('current', 'text').lower()
        for widget in self.notes[cat].values():
            widget.state(('!selected',))

    def sort_column(self, event):
        """Sort column."""
        heading = event.widget
        notes = [(item.get(heading.column), item.get_values(), item) for item in self.notes[heading.category].values()]
        notes.sort(reverse=heading.reverse, key=lambda x: x[:-1])
        for i, (val, values, item) in enumerate(notes):
            item.grid_configure(row=i)
        heading.reverse = not heading.reverse
        heading.state(['!' * heading.reverse + 'alternate'])

    def toggle_visibility(self, key, visible):
        if visible:
            if key not in self.master.notes:
                self.master.show_note(key)
        else:
            if key in self.master.notes:
                self.master.notes[key].hide()
        self.after(2, self.focus_set)
        self.after(4, self.grab_set)

    def display_note(self, key, note_data):
        """Display note in note manager."""
        cat = note_data["category"]
        c, r = self.frames[cat].grid_size()
        self.notes[cat][key] = ManagerItem(self.frames[cat], note_data,
                                           lambda vis: self.toggle_visibility(key, vis))
        self.notes[cat][key].grid(row=r, sticky='ew')

    def on_change_tab(self, event):
        self.category.set(self.notebook.tab("current", "text").lower())

    def del_selection(self):
        """Delete selected notes."""
        cat = self.notebook.tab('current', 'text').lower()
        sel = self.get_selection(cat)
        if sel:
            rep = askokcancel(_("Confirmation"), _("Delete the selected notes?"))
            if rep:
                for key in sel:
                    self.master.delete_note(key)
                    self.notes[cat][key].destroy()
                    del self.notes[cat][key]
                    self.update_idletasks()

    def change_cat_selection(self):
        """Change selected notes category."""
        cat = self.notebook.tab('current', 'text').lower()
        new_cat = self.category.get()
        sel = self.get_selection(cat)
        if sel and new_cat != cat:
            rep = askokcancel(_("Confirmation"), _("Change the category of the selected notes?"))
            if rep:
                for key in sel:
                    self.master.change_note_category(key, new_cat)
                    self.notes[cat][key].destroy()
                    del self.notes[cat][key]
                    self.display_note(key, self.master.note_data[key])
                    self.update_idletasks()
        self.category.set(cat)
        self.grab_set()

    def get_selection(self, cat):
        sel = []
        for key, widget in self.notes[cat].items():
            if 'selected' in widget.state():
                sel.append(key)
        return sel

    def scroll(self, delta):
        cat = self.notebook.tab("current", "text").lower()
        top, bottom = self.texts[cat].yview()
        top += delta * 0.05
        top = min(max(top, 0), 1)
        self.texts[cat].yview_moveto(top)
