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


Sticky note class
"""


from tkinter import Text,  Toplevel, PhotoImage, StringVar, Menu, TclError
from tkinter.ttk import  Style, Sizegrip, Entry, Checkbutton, Label
import os
import re
from time import strftime
import ewmh
from mynoteslib.constantes import CONFIG, COLORS, IM_LOCK, askopenfilename
from mynoteslib.constantes import TEXT_COLORS, sorting, SYMBOLS
from mynoteslib.symbols import pick_symbol
from mynoteslib.messagebox import showerror, askokcancel

class Sticky(Toplevel):
    """ Sticky note class """

    def __init__(self, master, key, **kwargs):
        """ Create a new sticky note.
            master: main app
            key: key identifying this note in master.note_data
            kwargs: dictionnary of the other arguments
            (title, txt, category, color, tags, geometry, locked, checkboxes,
             images, rolled)
        """
        Toplevel.__init__(self, master)
        ### window properties
        self.id = key
        self.is_locked = not (kwargs.get("locked", False))
        self.images = []
        self.title('mynotes%s' % key)
        self.attributes("-type", "splash")
        self.attributes("-alpha", CONFIG.getint("General", "opacity")/100)
        self.focus_force()
        # window geometry
        self.update_idletasks()
        self.geometry(kwargs.get("geometry", '220x235'))
        self.save_geometry = kwargs.get("geometry", '220x235')
        self.update()
        self.rowconfigure(1, weight=1)
        self.minsize(10,10)
        self.protocol("WM_DELETE_WINDOW", self.hide)

        ### style
        self.style = Style(self)
        self.style.configure(self.id + ".TCheckbutton", selectbackground="red")
        self.style.map('TEntry', selectbackground=[('!focus', '#c3c3c3')])

        ### note elements
        # title
        font_title = "%s %s" %(CONFIG.get("Font", "title_family").replace(" ", "\ "),
                               CONFIG.get("Font", "title_size"))
        style = CONFIG.get("Font", "title_style").split(",")
        if style:
            font_title += " "
            font_title += " ".join(style)

        self.title_var = StringVar(master=self,
                                   value=kwargs.get("title", _("Title")))
        self.title_label = Label(self,
                                 textvariable=self.title_var,
                                 anchor="center",
                                 style=self.id + ".TLabel",
                                 font=font_title)
        self.title_entry = Entry(self, textvariable=self.title_var,
                                 exportselection=False,
                                 justify="center", font=font_title)
        # buttons/icons
        self.roll = Label(self, image="img_roll", style=self.id + ".TLabel")
        self.close = Label(self, image="img_close", style=self.id + ".TLabel")
        self.im_lock = PhotoImage(master=self, file=IM_LOCK)
        self.cadenas = Label(self, style=self.id + ".TLabel")
        # corner grip
        self.corner = Sizegrip(self, style=self.id + ".TSizegrip")
        # texte
        font_text = "%s %s" %(CONFIG.get("Font", "text_family").replace(" ", "\ "),
                              CONFIG.get("Font", "text_size"))
        selectbg = self.style.lookup('TEntry', 'selectbackground', ('focus',))
        self.txt = Text(self, wrap='word', undo=True,
                        selectforeground='white',
                        inactiveselectbackground=selectbg,
                        selectbackground=selectbg,
                        tabs=("10", 'right', '20', 'left'),
                        relief="flat", borderwidth=0,
                        highlightthickness=0, font=font_text)
        # tags
        self.txt.tag_configure("bold", font="%s bold" % font_text)
        self.txt.tag_configure("italic", font="%s italic" % font_text)
        self.txt.tag_configure("bold-italic", font="%s bold italic" % font_text)
        self.txt.tag_configure("underline", underline=True)
        self.txt.tag_configure("overstrike", overstrike=True)
        self.txt.tag_configure("center", justify="center")
        self.txt.tag_configure("left", justify="left")
        self.txt.tag_configure("right", justify="right")
        self.txt.tag_configure("list", lmargin1=0, lmargin2='20')
        self.txt.tag_configure("todolist", lmargin1=0, lmargin2='20')
        self.txt.tag_configure("enum", lmargin1=0, lmargin2='20')

        for coul in TEXT_COLORS.values():
            self.txt.tag_configure(coul, foreground=coul, selectforeground="white")
        ### menus
        ### * menu on title
        self.menu = Menu(self, tearoff=False)
        # note color
        menu_note_color = Menu(self.menu, tearoff=False)
        colors = list(COLORS.keys())
        colors.sort()
        for coul in colors:
            menu_note_color.add_command(label=coul,
                                           command=lambda key=coul: self.change_color(key))
        # category
        self.category = StringVar(self, kwargs.get("category",
                                                   CONFIG.get("General",
                                                              "default_category")))
        self.menu_categories = Menu(self.menu, tearoff=False)
        categories = CONFIG.options("Categories")
        categories.sort()
        for cat in categories:
            self.menu_categories.add_radiobutton(label=cat.capitalize(),
                                                 value=cat,
                                                 variable=self.category,
                                                 command=self.change_category)
        # position: normal, always above, always below
        self.position = StringVar(self,
                                  kwargs.get("position",
                                             CONFIG.get("General", "position")))
        menu_position = Menu(self.menu, tearoff=False)
        menu_position.add_radiobutton(label=_("Always above"),
                                      value="above",
                                      variable=self.position,
                                      command=self.set_position_above)
        menu_position.add_radiobutton(label=_("Always below"),
                                      value="below",
                                      variable=self.position,
                                      command=self.set_position_below)
        menu_position.add_radiobutton(label=_("Normal"),
                                      value="normal",
                                      variable=self.position,
                                      command=self.set_position_normal)
        # mode: note, list, todo list
#        menu_mode = Menu(self.menu, tearoff=False)
#        self.mode = StringVar(self,
#                              kwargs.get("mode", "note"))
#        menu_mode.add_radiobutton(label=_("Note"), value="note",
#                                  command=self.set_mode_note,
#                                  variable=self.mode)
#        menu_mode.add_radiobutton(label=_("List"), value="list",
#                                  command=self.set_mode_list,
#                                  variable=self.mode)
#        menu_mode.add_radiobutton(label=_("ToDo List"), value="todolist",
#                                  command=self.set_mode_todolist,
#                                  variable=self.mode)

        self.menu.add_command(label=_("Delete"), command=self.delete)
        self.menu.add_cascade(label=_("Category"), menu=self.menu_categories)
        self.menu.add_cascade(label=_("Color"), menu=menu_note_color)
        self.menu.add_command(label=_("Lock"), command=self.lock)
        self.menu.add_cascade(label=_("Position"), menu=menu_position)
#        self.menu.add_cascade(label=_("Mode"), menu=menu_mode)

        ### * menu on main text
        self.menu_txt = Menu(self.txt, tearoff=False)
        # style
        menu_style = Menu(self.menu_txt, tearoff=False)
        menu_style.add_command(label=_("Bold"), command=lambda: self.toggle_text_style("bold"))
        menu_style.add_command(label=_("Italic"), command=lambda: self.toggle_text_style("italic"))
        menu_style.add_command(label=_("Underline"), command=lambda: self.toggle_text_style("underline"))
        menu_style.add_command(label=_("Overstrike"), command=lambda: self.toggle_text_style("overstrike"))
        # text alignment
        menu_align = Menu(self.menu_txt, tearoff=False)
        menu_align.add_command(label=_("Left"), command=lambda: self.set_align("left"))
        menu_align.add_command(label=_("Right"), command=lambda: self.set_align("right"))
        menu_align.add_command(label=_("Center"), command=lambda: self.set_align("center"))
        # text color
        menu_colors = Menu(self.menu_txt, tearoff=False)
        colors = list(TEXT_COLORS.keys())
        colors.sort()
        for coul in colors:
            menu_colors.add_command(label=coul,
                                    command=lambda key=coul: self.change_sel_color(TEXT_COLORS[key]))
        # insert
        menu_insert = Menu(self.menu_txt, tearoff=False)
        menu_insert.add_command(label=_("Symbols"), command=self.add_symbols)
        menu_insert.add_command(label=_("Checkbox"), command=self.add_checkbox)
        menu_insert.add_command(label=_("Image"), command=self.add_image)
        menu_insert.add_command(label=_("Date"), command=self.add_date)

        # lists
        menu_lists = Menu(self.menu_txt, tearoff=False)
        menu_lists.add_command(label=_("List"),
                                  command=self.toggle_bullets)
        menu_lists.add_command(label=_("ToDo List"),
                                  command=self.toggle_checkboxes)
        menu_lists.add_command(label=_("Enumeration"),
                                  command=self.toggle_enum)

        self.menu_txt.add_cascade(label=_("Style"), menu=menu_style)
        self.menu_txt.add_cascade(label=_("Align"), menu=menu_align)
        self.menu_txt.add_cascade(label=_("Color"), menu=menu_colors)
        self.menu_txt.add_cascade(label=_("Insert"), menu=menu_insert)
        self.menu_txt.add_cascade(label=_("List"), menu=menu_lists)
        ### restore note content/appearence
        self.color = kwargs.get("color",
                                CONFIG.get("Categories", self.category.get()))
        self.txt.insert('1.0', kwargs.get("txt",""))
        self.txt.edit_reset()  # clear undo stack
        # restore inserted objects (images and checkboxes)
        # we need to restore objects with increasing index to avoid placment errors
        indexes = list(kwargs.get("inserted_objects", {}).keys())
        indexes.sort(key=sorting)
        for index in indexes:
            kind, val = kwargs["inserted_objects"][index]
            if kind == "checkbox":
                ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
                if val:
                    ch.state(("selected",))
                self.txt.window_create(index, window=ch)

            elif kind == "image":
                if os.path.exists(val):
                    self.images.append(PhotoImage(master=self.txt, file=val))
                    self.txt.image_create(index, image=self.images[-1], name=val)
        # restore tags
        for tag in kwargs.get("tags", []):
            indices = kwargs["tags"][tag]
            if indices:
                self.txt.tag_add(tag, *indices)
        self.txt.focus_set()
        self.lock()
        if kwargs.get("rolled", False):
            self.rollnote()
        if self.position.get() == "above":
            self.set_position_above()
        elif self.position.get() == "below":
            self.set_position_below()

        ### placement
        # titlebar
        if CONFIG.get("General", "buttons_position") == "right":
            # right = lock icon - title - roll - close
            self.columnconfigure(1, weight=1)
            self.roll.grid(row=0, column=2, sticky="e")
            self.close.grid(row=0, column=3, sticky="e", padx=(0,2))
            self.cadenas.grid(row=0,column=0, sticky="w")
            self.title_label.grid(row=0, column=1, sticky="ew", pady=(1,0))
        else:
            # left = close - roll - title - lock icon
            self.columnconfigure(2, weight=1)
            self.roll.grid(row=0, column=1, sticky="w")
            self.close.grid(row=0, column=0, sticky="w", padx=(2,0))
            self.cadenas.grid(row=0,column=3, sticky="e")
            self.title_label.grid(row=0, column=2, sticky="ew", pady=(1,0))
        # body
        self.txt.grid(row=1, columnspan=4, column=0, sticky="ewsn",
                      pady=(1,4), padx=4)
        self.corner.lift(self.txt)
        self.corner.place(relx=1.0, rely=1.0, anchor="se")

        ### bindings
        self.bind("<FocusOut>", self.save_note)
        self.bind('<Configure>', self.bouge)
        self.bind('<Button-1>', self.change_focus, True)
        self.close.bind("<Button-1>", self.hide)
        self.close.bind("<Enter>", self.enter_close)
        self.close.bind("<Leave>", self.leave_close)
        self.roll.bind("<Button-1>", self.rollnote)
        self.roll.bind("<Enter>", self.enter_roll)
        self.roll.bind("<Leave >", self.leave_roll)
        self.title_label.bind("<Double-Button-1>", self.edit_title)
        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<ButtonRelease-1>", self.stop_move)
        self.title_label.bind("<B1-Motion>", self.move)
        self.title_label.bind('<Button-3>', self.show_menu)
        self.title_entry.bind("<Return>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<FocusOut>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<Escape>", lambda e: self.title_entry.place_forget())
        self.txt.bind('<Button-3>', self.show_menu_txt)
        # add binding to the existing class binding so that the selected text
        # is erased on pasting
        self.txt.bind("<Control-v>", self.paste)
        self.corner.bind('<ButtonRelease-1>', self.resize)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == "color":
            self.style.configure(self.id + ".TSizegrip",
                                 background=self.color)
            self.style.configure(self.id +  ".TLabel",
                                 background=self.color)
            self.style.configure("close" + self.id +  ".TLabel",
                                 background=self.color)
            self.style.configure("roll" + self.id +  ".TLabel",
                                 background=self.color)
            self.style.map(self.id +  ".TLabel",
                           background=[("active", self.color)])
            self.style.configure(self.id + ".TCheckbutton",
                                 background=self.color)
            self.style.map(self.id + ".TCheckbutton",
                           background=[("active", self.color),
                                       ("disabled", self.color)])
            self.style.map("close" + self.id +  ".TLabel",
                           background=[("active", self.color)])
            self.style.map("roll" + self.id +  ".TLabel",
                           background=[("active", self.color)])
            self.configure(bg=self.color)
            self.txt.configure(bg=self.color)

    def paste(self, event):
        """ delete selected text before pasting """
        if self.txt.tag_ranges("sel"):
            self.txt.delete("sel.first", "sel.last")

    def delete(self, confirmation=True):
        """ Delete this note """
        if confirmation:
            rep = askokcancel(_("Confirmation"), _("Delete the note?"))
        else:
            rep = True
        if rep:
            del(self.master.note_data[self.id])
            del(self.master.notes[self.id])
            self.master.save()
            self.destroy()

    def lock(self):
        """ Put note in read-only mode to avoid unwanted text insertion """
        if self.is_locked:
            selectbg = self.style.lookup('TEntry', 'selectbackground', ('focus',))
            self.txt.configure(state="normal",
                               selectforeground='white',
                               selectbackground=selectbg,
                               inactiveselectbackground=selectbg)
            self.is_locked = False
            for checkbox in self.txt.window_names():
                ch = self.txt.children[checkbox.split(".")[-1]]
                ch.configure(state="normal")
            self.cadenas.configure(image="")
            self.menu.entryconfigure(3, label=_("Lock"))
            self.title_label.bind("<Double-Button-1>", self.edit_title)
            self.txt.bind('<Button-3>', self.show_menu_txt)
        else:
            self.txt.configure(state="disabled",
                               selectforeground='black',
                               inactiveselectbackground='#c3c3c3',
                               selectbackground='#c3c3c3')
            self.cadenas.configure(image=self.im_lock)
            for checkbox in self.txt.window_names():
                ch = self.txt.children[checkbox.split(".")[-1]]
                ch.configure(state="disabled")
            self.is_locked = True
            self.menu.entryconfigure(3, label=_("Unlock"))
            self.title_label.unbind("<Double-Button-1>")
            self.txt.unbind('<Button-3>')
        self.save_note()

    def save_info(self):
        """ Return the dictionnary containing all the note data """
        data = {}
        data["txt"] = self.txt.get("1.0","end")[:-1]
        data["tags"] = {}
        for tag in self.txt.tag_names():
            if tag != "sel":
                data["tags"][tag] = [index.string for index in self.txt.tag_ranges(tag)]
        data["title"] = self.title_var.get()
        data["geometry"] = self.save_geometry
        data["category"] = self.category.get()
        data["color"] = self.color
        data["locked"] = self.is_locked
#        data["mode"] = self.mode.get()
        data["inserted_objects"] = {}
        data["rolled"] = not self.txt.winfo_ismapped()
        data["position"] = self.position.get()

        for image in self.txt.image_names():
            data["inserted_objects"][self.txt.index(image)] = ("image",
                                                               image.split('#')[0])
        for checkbox in self.txt.window_names():
            ch = self.txt.children[checkbox.split(".")[-1]]
            data["inserted_objects"][self.txt.index(checkbox)] = ("checkbox", "selected" in ch.state())
        return data

    def change_color(self, key):
        self.color = COLORS[key]
        self.save_note()

    def change_category(self, category=None):
        if category:
            self.category.set(category)
        self.color = CONFIG.get("Categories", self.category.get())
        self.save_note()

#    def set_mode_note(self):
#        self.txt.tag_remove("list", "1.0", "end")
#        self.txt.tag_remove("todolist", "1.0", "end")
#        self.save_note()
#
#    def set_mode_list(self):
#        index = self.txt.index("insert")
#        if index.split(".")[-1] == "0":
#            self.txt.insert("insert", "\t•\t")
#        else:
#            self.txt.insert("insert", "\n\t•\t")
#        self.txt.tag_add("list", "1.0", "end")
#        self.save_note()
#
#    def set_mode_todolist(self):
#        index = self.txt.index("insert")
#        if index.split(".")[-1] == "0":
#            ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
#            self.txt.window_create("insert", window=ch)
#        else:
#            self.txt.insert("insert", "\n")
#            ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
#            self.txt.window_create("insert", window=ch)
#        self.txt.tag_add("todolist", "1.0", "end")
#        self.save_note()

    def set_position_above(self):
        e = ewmh.EWMH()
        for w in e.getClientList():
            if w.get_wm_name() == 'mynotes%s' % self.id:
                e.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                e.setWmState(w, 0, '_NET_WM_STATE_BELOW')
        e.display.flush()
        self.save_note()

    def set_position_below(self):
        e = ewmh.EWMH()
        for w in e.getClientList():
            if w.get_wm_name() == 'mynotes%s' % self.id:
                e.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                e.setWmState(w, 1, '_NET_WM_STATE_BELOW')
        e.display.flush()
        self.save_note()

    def set_position_normal(self):
        e = ewmh.EWMH()
        for w in e.getClientList():
            if w.get_wm_name() == 'mynotes%s' % self.id:
                e.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                e.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
        e.display.flush()
        self.save_note()

    ### bindings
    def enter_roll(self, event):
        """ mouse is over the roll icon """
        self.roll.configure(image="img_rollactive")

    def leave_roll(self, event):
        """ mouse leaves the roll icon """
        self.roll.configure(image="img_roll")

    def enter_close(self, event):
        """ mouse is over the close icon """
        self.close.configure(image="img_closeactive")

    def leave_close(self, event):
        """ mouse leaves the close icon """
        self.close.configure(image="img_close")

    def change_focus(self, event):
        if not self.is_locked:
            event.widget.focus_force()

    def show_menu(self, event):
        self.menu.tk_popup(event.x_root,event.y_root)

    def show_menu_txt(self, event):
        self.menu_txt.tk_popup(event.x_root,event.y_root)

    def resize(self, event):
        self.save_geometry = self.geometry()

    def bouge(self, event):
        geo = self.geometry().split("+")[1:]
        self.save_geometry = self.save_geometry.split("+")[0] \
                             + "+%s+%s" % tuple(geo)

    def edit_title(self, event):
        self.title_entry.place(x=self.title_label.winfo_x() + 5,
                               y=self.title_label.winfo_y(),
                               anchor="nw",
                               width=self.title_label.winfo_width()-10)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def move(self, event):
        if self.x is not None and self.y is not None:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry("+%s+%s" % (x, y))

    def save_note(self, event=None):
        data = self.save_info()
        data["visible"] = True
        self.master.note_data[self.id] = data
        self.master.save()

    def rollnote(self, event=None):
        if self.txt.winfo_ismapped():
            self.txt.grid_forget()
            self.corner.place_forget()
            self.geometry("%sx22" % self.winfo_width())
        else:
            self.txt.grid(row=1, columnspan=4,
                          column=0, sticky="ewsn", pady=(1,4), padx=4)
            self.corner.place(relx=1.0, rely=1.0, anchor="se")
            self.geometry(self.save_geometry)
        self.save_note()

    def hide(self, event=None):
        """ Hide note (can be displayed again via app menu) """
        title = self.master.menu_notes_title(self.title_var.get().strip())
        self.master.hidden_notes[self.id] = title
        self.master.menu_notes.add_command(label=title,
                                           command=lambda: self.master.show_note(self.id))
        self.master.icon.menu.entryconfigure(4, state="normal")
        data = self.save_info()
        data["visible"] = False
        self.master.note_data[self.id] = data
        del(self.master.notes[self.id])
        self.master.save()
        self.destroy()

    ### Settings update
    def update_title_font(self):
        font = "%s %s" %(CONFIG.get("Font", "title_family").replace(" ", "\ "),
                         CONFIG.get("Font", "title_size"))
        style = CONFIG.get("Font", "title_style").split(",")
        if style:
            font += " "
            font += " ".join(style)
        self.title_label.configure(font=font)

    def update_text_font(self):
        font = "%s %s" %(CONFIG.get("Font", "text_family").replace(" ", "\ "),
                         CONFIG.get("Font", "text_size"))
        self.txt.configure(font=font)

    def update_menu_cat(self, categories):
        """ Update the category submenu """
        self.menu_categories.delete(0, "end")
        for cat in categories:
            self.menu_categories.add_radiobutton(label=cat.capitalize(), value=cat,
                                                 variable=self.category,
                                                 command=self.change_category)
    def update_titlebar(self):
        if CONFIG.get("General", "buttons_position") == "right":
            # right = lock icon - title - roll - close
            self.columnconfigure(1, weight=1)
            self.columnconfigure(2, weight=0)
            self.roll.grid_configure(row=0, column=2, sticky="e")
            self.close.grid_configure(row=0, column=3, sticky="e", padx=(0,2))
            self.cadenas.grid_configure(row=0,column=0, sticky="w")
            self.title_label.grid_configure(row=0, column=1, sticky="ew", pady=(1,0))
        else:
            # left = close - roll - title - lock icon
            self.columnconfigure(2, weight=1)
            self.columnconfigure(1, weight=0)
            self.roll.grid_configure(row=0, column=1, sticky="w")
            self.close.grid_configure(row=0, column=0, sticky="w", padx=(2,0))
            self.cadenas.grid_configure(row=0,column=3, sticky="e")
            self.title_label.grid_configure(row=0, column=2, sticky="ew", pady=(1,0))

    ### Text edition
    def add_checkbox(self):
        ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
        self.txt.window_create("current", window=ch)

    def add_date(self):
        self.txt.insert("current", strftime("%x"))

    def add_image(self):
        fichier = askopenfilename(defaultextension=".png",
                                  filetypes=[("PNG", "*.png")],
                                  initialdir="",
                                  initialfile="",
                                  title=_('Select PNG image'))
        if os.path.exists(fichier):
            self.images.append(PhotoImage(master=self.txt, file=fichier))
            self.txt.image_create("current",
                                  image=self.images[-1],
                                  name=fichier)
        else:
            showerror("Erreur", "L'image %s n'existe pas" % fichier)

    def add_symbols(self):
        symbols = pick_symbol(self,
                              CONFIG.get("Font", "text_family").replace(" ", "\ "),
                              SYMBOLS)
        self.txt.insert("current", symbols)

    def toggle_text_style(self, style):
        '''Toggle the style of the selected text'''
        if self.txt.tag_ranges("sel"):
            current_tags = self.txt.tag_names("sel.first")
            if style in current_tags:
                # first char is in style so 'unstyle' the range
                self.txt.tag_remove(style, "sel.first", "sel.last")
            elif style == "bold" and "bold-italic" in current_tags:
                self.txt.tag_remove("bold-italic", "sel.first", "sel.last")
                self.txt.tag_add("italic", "sel.first", "sel.last")
            elif style == "italic" and "bold-italic" in current_tags:
                self.txt.tag_remove("bold-italic", "sel.first", "sel.last")
                self.txt.tag_add("bold", "sel.first", "sel.last")
            elif style == "bold" and "italic" in current_tags:
                self.txt.tag_add("bold-italic", "sel.first", "sel.last")
            elif style == "italic" and "bold" in current_tags:
                self.txt.tag_add("bold-italic", "sel.first", "sel.last")
            else:
                # first char is normal, so apply style to the whole selection
                self.txt.tag_add(style, "sel.first", "sel.last")

    def change_sel_color(self, color):
        """ change the color of the selection """
        if self.txt.tag_ranges("sel"):
            for coul in TEXT_COLORS.values():
                self.txt.tag_remove(coul, "sel.first", "sel.last")
            if not color == "black":
                self.txt.tag_add(color, "sel.first", "sel.last")

    def set_align(self, alignment):
        """ Align the text according to alignment (left, right, center) """
        if self.txt.tag_ranges("sel"):
            line = self.txt.index("sel.first").split(".")[0]
            line2 = self.txt.index("sel.last").split(".")[0]
            # remove old alignment tag
            self.txt.tag_remove("left", line + ".0", line2 + ".end")
            self.txt.tag_remove("right", line + ".0", line2 + ".end")
            self.txt.tag_remove("center", line + ".0", line2 + ".end")
            # set new alignment tag
            self.txt.tag_add(alignment, line + ".0", line2 + ".end")

    def toggle_bullets(self):
        if self.txt.tag_ranges("sel"):
            line = self.txt.index("sel.first").split(".")[0]
            line2 = self.txt.index("sel.last").split(".")[0]
            i1 = line + ".0"
            i2 = "%i.0" % (int(line2) + 1)
            current_tags = self.txt.tag_names("sel.first")
            if "list" in current_tags:
                self.txt.tag_remove("list", i1, i2)
                for i in range(int(line), int(line2)+1):
                    if self.txt.get("%i.0"  % i, "%i.3"  % i) == "\t•\t":
                        self.txt.delete("%i.0"  % i, "%i.3"  % i)
            else:
                lines  = self.txt.get(i1, line2 + ".end").splitlines()
                for i, l in zip(range(int(line), int(line2)+1), lines):
                    # remove checkboxes
                    try:
                        ch = self.txt.window_cget("%i.0"  % i, "window")
                        self.txt.children[ch.split('.')[-1]].destroy()
                        self.txt.delete("%i.0"  % i)
                    except TclError:
                        # there is no checkbox
                        # remove enumeration
                        res = re.match('^\t[0-9]+\.\t', l)
                        if res:
                            self.txt.delete("%i.0"  % i, "%i.%i"  % (i, res.end()))
                    if self.txt.get("%i.0"  % i, "%i.3"  % i) != "\t•\t":
                        self.txt.insert("%i.0" % i, "\t•\t")
                self.txt.tag_add("list", i1, i2)
                self.txt.tag_remove("todolist", i1, i2)
                self.txt.tag_remove("enum", i1, i2)
            self.update_enum()

    def toggle_enum(self, remove_others=True):
        if self.txt.tag_ranges("sel"):
            line = self.txt.index("sel.first").split(".")[0]
            line2 = self.txt.index("sel.last").split(".")[0]
            i1 = line + ".0"
            i2 = "%i.0" % (int(line2) + 1)
            current_tags = self.txt.tag_names("sel.first")
            self.txt.configure(autoseparators=False)
            self.txt.edit_separator()
            if "enum" in current_tags:
                self.txt.tag_remove("enum", i1, i2)
                lines  = self.txt.get(i1, line2 + ".end").splitlines()
                for i,l in zip(range(int(line), int(line2) + 1), lines):
                    res = re.match('^\t[0-9]+\.\t', l)
                    if res:
                        self.txt.delete("%i.0"  % i, "%i.%i"  % (i, res.end()))
            else:
                for i in range(int(line), int(line2) + 1):
                    # remove checkboxes
                    try:
                        ch = self.txt.window_cget("%i.0"  % i, "window")
                        self.txt.children[ch.split('.')[-1]].destroy()
                        self.txt.delete("%i.0"  % i)
                    except TclError:
                        # there is no checkbox
                        # remove bullets
                        if self.txt.get("%i.0"  % i, "%i.3"  % i) == "\t•\t":
                            self.txt.delete("%i.0"  % i, "%i.3"  % i)
                    self.txt.insert("%i.0" % i, "\t0.\t")
                self.txt.tag_add("enum", i1, i2)
                self.txt.tag_remove("todolist", i1, i2)
                self.txt.tag_remove("list", i1, i2)
            self.update_enum()
            self.txt.configure(autoseparators=True)
            self.txt.edit_separator()

    def toggle_checkboxes(self, remove_others=True):
        if self.txt.tag_ranges("sel"):
            line = self.txt.index("sel.first").split(".")[0]
            line2 = self.txt.index("sel.last").split(".")[0]
            i1 = line + ".0"
            i2 = "%i.0" % (int(line2) + 1)
            current_tags = self.txt.tag_names("sel.first")
            if "todolist" in current_tags:
                self.txt.tag_remove("todolist", i1, i2)
                for i in range(int(line), int(line2)+1):
                    try:
                        ch = self.txt.window_cget("%i.0"  % i, "window")
                        self.txt.children[ch.split('.')[-1]].destroy()
                        self.txt.delete("%i.0"  % i)
                    except TclError:
                        # there is no checkbox
                        pass
            else:
                lines  = self.txt.get(i1, line2 + ".end").splitlines()
                for i,l in zip(range(int(line), int(line2) + 1), lines):
                    res = re.match('^\t[0-9]+\.\t', l)
                    if res:
                        self.txt.delete("%i.0"  % i, "%i.%i"  % (i, res.end()))
                    elif self.txt.get("%i.0"  % i, "%i.3"  % i) == "\t•\t":
                        self.txt.delete("%i.0"  % i, "%i.3"  % i)
                    try:
                        ch = self.txt.window_cget("%i.0"  % i, "window")
                    except TclError:
                        ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
                        self.txt.window_create("%i.0"  % i, window=ch)
                self.txt.tag_add("todolist", i1, i2)
                self.txt.tag_remove("list", i1, i2)
                self.txt.tag_remove("enum", i1, i2)
            self.update_enum()

    def update_enum(self):
        """ update enumeration numbers """
        tag_ranges = self.txt.tag_ranges("enum")
        for deb, fin in zip(tag_ranges[::2], tag_ranges[1::2]):
            lines  = self.txt.get(deb, fin).splitlines()
            indexes = []
            for i,l in enumerate(lines):
                res = re.match('^\t[0-9]+\.\t', l)
                if res:
                    indexes.append((i - 1 + int(deb.string.split(".")[0]), res.end()))
            for j, (i, end) in enumerate(indexes):
                self.txt.delete("%i.0" % (i + 1), "%i.%i" % (i + 1, end))
                self.txt.insert("%i.0" % (i + 1), "\t%i.\t" % (j + 1))
            self.txt.tag_add("enum", deb, fin)


