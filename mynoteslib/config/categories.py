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


Category Manager
"""

from tkinter import StringVar, PhotoImage, Toplevel, Text
from mynoteslib.constants import CONFIG, COLORS, INV_COLORS, IM_PLUS, IM_DELETE
from mynoteslib.constants import save_config, fill, optionmenu_patch
from tkinter.ttk import Label, Button, OptionMenu, Style, Separator, Entry, Frame
from mynoteslib.messagebox import askyesnocancel
from mynoteslib.autoscrollbar import AutoScrollbar


class CategoryManager(Frame):
    """Category manager for the sticky notes."""

    def __init__(self, master, app, **kwargs):
        """Create category manager."""
        Frame.__init__(self, master, padding=4, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.app = app

        self.style = Style(self)
        self.style.theme_use("clam")

        self.im_plus = PhotoImage(file=IM_PLUS)
        self.im_delete = PhotoImage(file=IM_DELETE)

        # --- Default category
        self.frame_def_cat = Frame(self)
        self.default_category = StringVar(self.frame_def_cat,
                                          CONFIG.get("General",
                                                     "default_category").capitalize())
        Label(self.frame_def_cat, text=_("Default category ")).grid(row=0, column=0,
                                                                    sticky="e",
                                                                    padx=(4, 0))
        self.categories = CONFIG.options("Categories")
        self.categories.sort()
        categories = [cat.capitalize() for cat in self.categories]
        self.def_cat_menu = OptionMenu(self.frame_def_cat, self.default_category,
                                       CONFIG.get("General",
                                                  "default_category").capitalize(),
                                       *categories)
        optionmenu_patch(self.def_cat_menu, self.default_category)
        self.def_cat_menu.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        # --- Category colors, names ...
        style = Style(self)
        style.configure('txt.TFrame', relief='ridge', border=2)
        bg = style.lookup('TFrame', 'background')
        frame = Frame(self, style='txt.TFrame', padding=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        txt = Text(frame, width=1, height=1, bg=bg, relief='flat',
                   highlightthickness=0, padx=6, pady=6, cursor='arrow')
        scroll_x = AutoScrollbar(frame, orient='horizontal', command=txt.xview)
        scroll_y = AutoScrollbar(frame, orient='vertical', command=txt.yview)
        txt.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        txt.grid(row=0, column=0, sticky='ewns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        scroll_y.grid(row=0, column=1, sticky='ns')

        self.frame_cat = Frame(txt)
        txt.window_create('1.0', window=self.frame_cat)
        self.colors = list(COLORS.keys())
        self.colors.sort()
        self.images = []
        for key in self.colors:
            self.images.append(PhotoImage(key, master=self, width=16, height=16))
            fill(self.images[-1], COLORS[key])
        self.cat_colors = {}
        self.cat_labels = {}
        self.cat_menus = {}
        self.cat_buttons = {}
        for i, cat in enumerate(self.categories):
            self.cat_labels[cat] = Label(self.frame_cat,
                                         text="%s" % cat.capitalize(),
                                         anchor='e')
            self.cat_labels[cat].grid(row=i + 2, column=0, sticky="ew", padx=2)
            self.cat_labels[cat].bind('<Double-Button-1>', self.change_name)
            self.cat_colors[cat] = StringVar(self)
            color = CONFIG.get("Categories", cat)
            self.cat_menus[cat] = OptionMenu(self.frame_cat, self.cat_colors[cat],
                                             INV_COLORS[color], *self.colors,
                                             command=lambda color, c=cat: self.change_menubutton_color(color, c),
                                             style="%s.TMenubutton" % cat)
            optionmenu_patch(self.cat_menus[cat], self.cat_colors[cat])
            self.style.configure("%s.TMenubutton" % cat, background=color)
            self.cat_menus[cat].grid(row=i + 2, column=1, sticky="w", padx=4, pady=4)
            self.cat_buttons[cat] = Button(self.frame_cat, image=self.im_delete,
                                           padding=1,
                                           command=lambda c=cat: self.del_cat(c))
            self.cat_buttons[cat].grid(row=i + 2, column=2, padx=4, pady=4)

        if len(self.categories) == 1:
            self.cat_buttons[self.categories[0]].configure(state="disabled")

        # --- placement
        self.frame_def_cat.grid(row=0, column=0, sticky="eswn", pady=4)
        frame.grid(row=1, column=0, sticky="eswn")
        Button(self, image=self.im_plus,
               command=self.add_cat).grid(row=2, column=0, sticky='w', pady=8)

    def change_name(self, event):
        """Change category name."""
        def ok(event):
            cats = [l.cget('text').lower() for l in self.cat_labels.values()]
            cat = name.get().strip().lower()
            if cat and cat not in cats:
                label.configure(text=cat.capitalize())
                if old_cat == self.default_category.get():
                    self.default_category.set(cat.capitalize())
                self.update_def_cat_menu()

            name.destroy()
        label = event.widget
        old_cat = label.cget('text')
        name = Entry(self, justify='center')
        name.insert(0, label.cget('text'))
        name.place(in_=label, relx=0, rely=0, anchor='nw', relwidth=1, relheight=1)
        name.bind('<FocusOut>', lambda e: name.destroy())
        name.bind('<Escape>', lambda e: name.destroy())
        name.bind('<Return>', ok)
        name.selection_range(0, 'end')
        name.focus_set()

    def get_color(self, category):
        """Return color of category."""
        return self.cat_colors[category].get()

    def get_name(self, category):
        return self.cat_labels[category].cget('text').lower()

    def change_menubutton_color(self, color, cat):
        """
        Change the color of the menubutton of the category cat when its
        default color is changed.
        """
        self.style.configure("%s.TMenubutton" % cat, background=COLORS[color])

    def del_cat(self, category):
        """Remove category."""
        rep = askyesnocancel(_("Question"),
                             _("Do you want to delete all notes belonging to \
the category %(category)s? If you answer 'No', the category will be deleted but \
the notes will belong to the default category. Be careful, the change will take \
effect immediately and cannot be undone.") % {"category": category})
        if rep is not None:
            del(self.cat_colors[category])
            self.cat_buttons[category].grid_forget()
            del(self.cat_buttons[category])
            self.cat_labels[category].grid_forget()
            cat = self.cat_labels[category].cget('text')
            del(self.cat_labels[category])
            self.cat_menus[category].grid_forget()
            del(self.cat_menus[category])
            self.categories.remove(category)
            CONFIG.remove_option("Categories", category)
            if self.default_category.get() == cat:
                default = list(self.cat_labels.values())[0].cget('text')
                self.default_category.set(default)
                CONFIG.set("General", "default_category", default.lower())
                self.update_def_cat_menu()
            if len(self.categories) == 1:
                self.cat_buttons[self.categories[0]].configure(state="disabled")
            if rep:
                self.app.delete_cat(category)
            self.app.update_notes()
            self.app.update_menu()
            save_config()

    def update_def_cat_menu(self):
        """Update default caregory menu."""
        self.def_cat_menu.destroy()
        categories = [l.cget('text') for l in self.cat_labels.values()]
        self.def_cat_menu = OptionMenu(self.frame_def_cat, self.default_category,
                                       None, *categories)
        optionmenu_patch(self.def_cat_menu, self.default_category)
        self.def_cat_menu.grid(row=0, column=1, sticky="w", padx=4, pady=4)

    def add_cat(self):
        """Add a category."""
        top = Toplevel(self, class_='MyNotes')
        top.transient(self)
        top.grab_set()
        top.resizable(False, False)
        top.title(_("New Category"))

        def valide(event=None):
            cats = [l.cget('text').lower() for l in self.cat_labels.values()]
            cat = name.get().strip().lower()
            if cat and cat not in cats:
                c, i = self.frame_cat.grid_size()
                self.cat_labels[cat] = Label(self.frame_cat,
                                             text="%s" % cat.capitalize())
                self.cat_labels[cat].grid(row=i, column=0, sticky="e")
                self.cat_colors[cat] = StringVar(self, _("Yellow"))
                self.cat_menus[cat] = OptionMenu(self.frame_cat, self.cat_colors[cat],
                                                 _("Yellow"), *self.colors,
                                                 command=lambda color, c=cat: self.change_menubutton_color(color, c),
                                                 style="%s.TMenubutton" % cat)
                self.style.configure("%s.TMenubutton" % cat, background=COLORS[_("Yellow")])
                optionmenu_patch(self.cat_menus[cat], self.cat_colors[cat])
                self.cat_menus[cat].grid(row=i, column=1, padx=4, pady=4)
                self.cat_buttons[cat] = Button(self.frame_cat, image=self.im_delete,
                                               padding=1,
                                               command=lambda c=cat: self.del_cat(c))
                self.cat_buttons[cat].grid(row=i, column=2, padx=4, pady=4)
                self.cat_buttons[self.categories[0]].configure(state="normal")
                self.categories.append(cat)
                self.categories.sort()
                self.update_def_cat_menu()
                top.destroy()

        name = Entry(top, justify="center")
        name.grid(row=0, column=0, columnspan=2, sticky="ew")
        name.bind("<Return>", valide)
        name.bind("<Escape>", lambda e: top.destroy())
        name.focus_set()
        Button(top, text="Ok", command=valide).grid(row=1, column=0, sticky="nswe")
        Button(top, text=_("Cancel"),
               command=top.destroy).grid(row=1, column=1, sticky="nswe")
