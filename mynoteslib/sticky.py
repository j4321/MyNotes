#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
My Notes - Sticky notes/post-it
Copyright 2016-2018 Juliette Monsel <j_4321@protonmail.com>

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


from tkinter import Toplevel, StringVar, Menu, TclError
from tkinter.ttk import  Style, Sizegrip, Entry, Label, Button, Frame
from tkinter.font import Font
from PIL.ImageTk import PhotoImage
from PIL import Image
import os
import re
from time import strftime
from mynoteslib.constants import TEXT_COLORS, askopenfilename,\
    PATH_LATEX, LATEX, CONFIG, COLORS, IM_LOCK, IM_CLIP, sorting,\
    math_to_image, EWMH, INV_COLORS
from mynoteslib.autoscrollbar import AutoScrollbar
from mynoteslib.symbols import pick_symbol
from mynoteslib.mytext import MyText
from mynoteslib.messagebox import showerror, askokcancel
from webbrowser import open as open_url


class Sticky(Toplevel):
    """Sticky note class."""

    def __init__(self, master, key, **kwargs):
        """
        Create a new sticky note.

        Arguments:
            master: main app
            key: key identifying this note in master.note_data
            kwargs: dictionnary of the other arguments
            (title, txt, category, color, tags, geometry, locked, checkboxes, images, rolled)
        """
        Toplevel.__init__(self, master, class_='MyNotes')
        self.withdraw()

        self.x = None
        self.y = None

        # --- window properties
        self.id = key
        self.is_locked = not (kwargs.get("locked", False))
        self.images = []
        self.links_click_id = {}  # delay click effect to avoid triggering <1> with <Double-1>
        self.files = {}
        self.files_click_id = {}  # delay click effect to avoid triggering <1> with <Double-1>
        self.nb_links = 0
        self.nb_files = 0
        self.title('mynotes%s' % key)
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.attributes("-type", "splash")
        self.attributes("-alpha", CONFIG.getint("General", "opacity") / 100)
        self.rowconfigure(1, weight=1)
        self.minsize(10,10)

        # --- style
        self.style = Style(self)
        self.style.configure(self.id + ".TCheckbutton", selectbackground="red")
        selectbg = self.style.lookup('TEntry', 'selectbackground', ('focus',))

        # --- note elements
        # -------- titlebar
        self.titlebar = Frame(self, style=self.id + '.TFrame')
        # title
        font_title = "%s %s" %(CONFIG.get("Font", "title_family").replace(" ", "\ "),
                               CONFIG.get("Font", "title_size"))
        style = CONFIG.get("Font", "title_style").split(",")
        if style:
            font_title += " "
            font_title += " ".join(style)

        self.title_var = StringVar(master=self,
                                   value=kwargs.get("title", _("Title")))
        self.title_label = Label(self.titlebar,
                                 textvariable=self.title_var,
                                 anchor="center",
                                 style=self.id + ".TLabel",
                                 font=font_title)
        self.title_entry = Entry(self.titlebar, textvariable=self.title_var,
                                 exportselection=False,
                                 justify="center", font=font_title)
        # buttons/icons
        self.roll = Label(self.titlebar, image="img_roll", style=self.id + ".TLabel")
        self.close = Label(self.titlebar, image="img_close", style=self.id + ".TLabel")
        self.im_lock = PhotoImage(master=self, file=IM_LOCK)
        self.im_clip = PhotoImage(master=self, file=IM_CLIP)
        self.cadenas = Label(self.titlebar, style=self.id + ".TLabel")

        if CONFIG.get("General", "buttons_position") == "right":
            # right = lock icon - title - roll - close
            self.titlebar.columnconfigure(1, weight=1)
            self.roll.grid(row=0, column=2, sticky="e")
            self.close.grid(row=0, column=3, sticky="e", padx=(0,2))
            self.cadenas.grid(row=0, column=0, sticky="w")
            self.title_label.grid(row=0, column=1, sticky="ew", pady=(1,0))
        else:
            # left = close - roll - title - lock icon
            self.titlebar.columnconfigure(2, weight=1)
            self.roll.grid(row=0, column=1, sticky="w")
            self.close.grid(row=0, column=0, sticky="w", padx=(2,0))
            self.cadenas.grid(row=0,column=3, sticky="e")
            self.title_label.grid(row=0, column=2, sticky="ew", pady=(1,0))

        # -------- body
        # corner grip
        self.corner = Sizegrip(self, style=self.id + ".TSizegrip")
        # texte
        self.scroll = AutoScrollbar(self, orient='vertical')
        self.txt = MyText(self, cb_style=self.id + ".TCheckbutton",
                          selectforeground='white',
                          inactiveselectbackground=selectbg,
                          selectbackground=selectbg,
                          yscrollcommand=self.scroll.set)
        self.scroll.configure(command=self.txt.yview)

        # --- menus
        # --- * menu on title
        self.menu = Menu(self, tearoff=False)
        # note color
        menu_note_color = Menu(self.menu, tearoff=False)
        colors = list(COLORS.keys())
        colors.sort()
        for coul in colors:
            menu_note_color.add_command(label=coul, image=self.master.im_color[coul],
                                        compound='left',
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
        menu_mode = Menu(self.menu, tearoff=False)
        self.mode = StringVar(self, kwargs.get("mode", "note"))
        menu_mode.add_radiobutton(label=_("Note"), value="note",
                                  variable=self.mode,
                                  command=self.set_mode_note)
        menu_mode.add_radiobutton(label=_("List"), value="list",
                                  variable=self.mode,
                                  command=self.set_mode_list)
        menu_mode.add_radiobutton(label=_("ToDo List"), value="todolist",
                                  variable=self.mode,
                                  command=self.set_mode_todolist)
        menu_mode.add_radiobutton(label=_("Enumeration"), value="enum",
                                  variable=self.mode,
                                  command=self.set_mode_enum)

        self.menu.add_command(label=_("Delete"), command=self.delete)
        self.menu.add_cascade(label=_("Category"), menu=self.menu_categories)
        self.menu.add_cascade(label=_("Color"), menu=menu_note_color)
        self.menu.add_command(label=_("Lock"), command=self.lock)
        self.menu.add_cascade(label=_("Position"), menu=menu_position)
        self.menu.add_cascade(label=_("Mode"), menu=menu_mode)

        # --- * menu on main text
        self.menu_txt = Menu(self.txt, tearoff=False)
        # style
        menu_style = Menu(self.menu_txt, tearoff=False)
        menu_style.add_command(label=_("Bold"),
                               command=lambda: self.txt.toggle_text_style("bold"),
                               accelerator='Ctrl+B')
        menu_style.add_command(label=_("Italic"),
                               command=lambda: self.txt.toggle_text_style("italic"),
                               accelerator='Ctrl+I')
        menu_style.add_command(label=_("Underline"),
                               command=self.txt.toggle_underline,
                               accelerator='Ctrl+U')
        menu_style.add_command(label=_("Overstrike"),
                               command=self.txt.toggle_overstrike)
        menu_style.add_command(label=_("Mono"),
                               command=lambda: self.txt.toggle_text_style("mono"),
                               accelerator='Ctrl+M')
        # text alignment
        menu_align = Menu(self.menu_txt, tearoff=False)
        menu_align.add_command(label=_("Left"),
                               command=lambda: self.txt.set_align("left"),
                               accelerator='Ctrl+L')
        menu_align.add_command(label=_("Right"),
                               command=lambda: self.txt.set_align("right"),
                               accelerator='Ctrl+R')
        menu_align.add_command(label=_("Center"),
                               command=lambda: self.txt.set_align("center"))
        # text color
        menu_colors = Menu(self.menu_txt, tearoff=False)
        colors = list(TEXT_COLORS.keys())
        colors.sort()
        for coul in colors:
            menu_colors.add_command(label=coul, image=self.master.im_text_color[coul],
                                    compound='left',
                                    command=lambda key=coul: self.txt.change_sel_color(TEXT_COLORS[key]))

        # insert
        menu_insert = Menu(self.menu_txt, tearoff=False)
        menu_insert.add_command(label=_("Symbols"), command=self.add_symbols,
                                accelerator='Ctrl+S')
        menu_insert.add_command(label=_("Checkbox"), command=self.add_checkbox,
                                accelerator='Ctrl+O')
        menu_insert.add_command(label=_("Image"), command=self.add_image)
        menu_insert.add_command(label=_("Date"), command=self.add_date,
                                accelerator='Ctrl+D')
        menu_insert.add_command(label=_("Link"), command=self.add_link,
                                accelerator='Ctrl+H')
        if LATEX:
            menu_insert.add_command(label="LaTeX", command=self.add_latex,
                                    accelerator='Ctrl+T')

        self.menu_txt.add_cascade(label=_("Style"), menu=menu_style)
        self.menu_txt.add_cascade(label=_("Alignment"), menu=menu_align)
        self.menu_txt.add_cascade(label=_("Color"), menu=menu_colors)
        self.menu_txt.add_cascade(label=_("Insert"), menu=menu_insert)

        # --- restore note content/appearence
        self.color = kwargs.get("color",
                                CONFIG.get("Categories", self.category.get()))
        self.txt.insert('1.0', kwargs.get("txt",""))
        self.txt.edit_reset()  # clear undo stack
        # restore inserted objects (images and checkboxes)
        # we need to restore objects with increasing index to avoid placment errors
        indexes = list(kwargs.get("inserted_objects", {}).keys())
        indexes.sort(key=sorting)

        latex_data = kwargs.get("latex", {})

        for index in indexes:
            kind, val = kwargs["inserted_objects"][index]
            if kind == "checkbox":
                if val:
                    state = ('selected', '!alternate')
                else:
                    state = ('!selected', '!alternate')
                self.txt.checkbox_create(index, state)
            elif kind == "image":
                if os.path.exists(val):
                    self.images.append(PhotoImage(master=self.txt, file=val))
                    self.txt.image_create(index,
                                          image=self.images[-1],
                                          align='bottom',
                                          name=val)
                else:
                    path, img = os.path.split(val)
                    if LATEX and path == PATH_LATEX and img in latex_data:
                        math_to_image(latex_data[img], val,
                                      fontsize=CONFIG.getint("Font", "text_size") - 2)
                        self.images.append(PhotoImage(file=val, master=self))
                        self.txt.image_create(index, image=self.images[-1],
                                              align='bottom', name=val)
                        self.txt.tag_add(img, index)

        # restore tags
        for tag, indices in kwargs.get("tags", {}).items():
            if indices:
                self.txt.tag_add(tag, *indices)

        for link in kwargs.get("links", {}).values():
            self.nb_links += 1
            self.txt.links[self.nb_links] = link
            self.links_click_id[self.nb_links] = ""
            lid = "link#%i" % self.nb_links
            self.txt.tag_bind(lid,
                              "<Button-1>",
                              lambda e, lnb=self.nb_links: self.open_link(lnb))
            self.txt.tag_bind(lid,
                              "<Double-Button-1>",
                              lambda e, lnb=self.nb_links: self.edit_link(lnb))

        for img, latex in latex_data.items():
            self.txt.latex[img] = latex
            if LATEX:
                self.txt.tag_bind(img, '<Double-Button-1>',
                                  lambda e, im=img: self.add_latex(im))

        mode = self.mode.get()
        if mode != "note":
            self.txt.tag_add(mode, "1.0", "end")
        self.txt.mode = mode

        # --- placement
        self.columnconfigure(0, weight=1)
        # titlebar
        self.titlebar.grid(row=0, column=0, columnspan=2, sticky='ew')

        # body
        self.txt.grid(row=1, column=0, sticky="ewsn",
                      pady=(1,4), padx=4)
        self.scroll.grid(row=1, column=1, sticky='ns', pady=(2, 14))
        self.corner.lift(self.txt)
        self.corner.place(relx=1.0, rely=1.0, anchor="se")

        # --- bindings
        self.bind("<FocusOut>", self.save_note)
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
        self.title_label.bind('<Button-4>', self.mouse_roll)
        self.title_label.bind('<Button-5>', self.mouse_roll)

        self.title_entry.bind("<Return>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<FocusOut>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<Escape>", lambda e: self.title_entry.place_forget())

        self.txt.bind("<FocusOut>", self.save_note)
        self.txt.bind('<Button-3>', self.show_menu_txt)

        self.corner.bind('<ButtonRelease-1>', self.resize)

        # --- keyboard shortcuts
        self.txt.bind('<Control-b>', lambda e: self.txt.toggle_text_style('bold'))
        self.txt.bind('<Control-i>', lambda e: self.txt.toggle_text_style('italic'))
        self.txt.bind('<Control-m>', lambda e: self.txt.toggle_text_style('mono'))
        self.txt.bind('<Control-u>', lambda e: self.txt.toggle_underline())
        self.txt.bind('<Control-r>', lambda e: self.txt.set_align('right'))
        self.txt.bind('<Control-l>', lambda e: self.txt.set_align('left'))
        self.txt.bind('<Control-s>', lambda e: self.add_symbols())
        self.txt.bind('<Control-d>', self.add_date)
        self.txt.bind('<Control-o>', self.add_checkbox)
        self.txt.bind('<Control-h>', lambda e: self.add_link())
        if LATEX:
            self.txt.bind('<Control-t>', lambda e: self.add_latex())

        # --- window geometry
        self.update_idletasks()
        self.geometry(kwargs.get("geometry", '220x235'))
        self.save_geometry = kwargs.get("geometry", '220x235')
        self.deiconify()
        self.update_idletasks()
        self.focus_force()
        self.txt.focus_set()
        self.lock()
        if kwargs.get("rolled", False):
            self.rollnote()
        if self.position.get() == "above":
            self.set_position_above()
        elif self.position.get() == "below":
            self.set_position_below()

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name is "color":
            self.style.configure(self.id + ".TSizegrip",
                                 background=self.color)
            self.style.configure(self.id +  ".TLabel",
                                 background=self.color)
            self.style.configure(self.id +  ".TFrame",
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
            self.scroll.configure(style='%s.Vertical.TScrollbar' % INV_COLORS[value])
            self.configure(bg=self.color)
            self.txt.configure(bg=self.color)

    def delete(self, confirmation=True):
        """Delete this note."""
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
        """Put note in read-only mode to avoid unwanted text insertion."""
        if self.is_locked:
            selectbg = self.style.lookup('TEntry', 'selectbackground', ('focus',))
            self.txt.configure(state="normal",
                               selectforeground='white',
                               selectbackground=selectbg,
                               inactiveselectbackground=selectbg)
            self.style.configure("sel.%s.TCheckbutton" % self.id, background=selectbg)
            self.style.map("sel.%s.TCheckbutton" % self.id, background=[("active", selectbg)])
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
            self.style.configure("sel.%s.TCheckbutton" % self.id, background='#c3c3c3')
            self.style.map("sel.%s.TCheckbutton" % self.id, background=[("active", '#c3c3c3')])
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
        """Return the dictionnary containing all the note data."""
        data = {}
        data["txt"] = self.txt.get("1.0","end")[:-1]
        data["tags"] = {}
        for tag in self.txt.tag_names():
            if tag not in ["sel", "todolist", "list", "enum"]:
                data["tags"][tag] = [index.string for index in self.txt.tag_ranges(tag)]
        data["title"] = self.title_var.get()
        data["geometry"] = self.save_geometry
        data["category"] = self.category.get()
        data["color"] = self.color
        data["locked"] = self.is_locked
        data["mode"] = self.mode.get()
        data["inserted_objects"] = {}
        data["rolled"] = not self.txt.winfo_ismapped()
        data["position"] = self.position.get()
        data["links"] = {}
        for i, link in self.txt.links.items():
            if self.txt.tag_ranges("link#%i" % i):
                data["links"][i] = link
        data["latex"] = {}
        for img, latex in self.txt.latex.items():
            if self.txt.tag_ranges(img):
                data["latex"][img] = latex
        for image in self.txt.image_names():
            data["inserted_objects"][self.txt.index(image)] = ("image",
                                                               image.split('#')[0])
        for checkbox in self.txt.window_names():
            ch = self.txt.children[checkbox.split(".")[-1]]
            data["inserted_objects"][self.txt.index(checkbox)] = ("checkbox", "selected" in ch.state())
        return data

    def change_color(self, key):
        """Change the color of the note."""
        self.color = COLORS[key]
        self.save_note()

    def change_category(self, category=None):
        """Change the category of the note if provided and update its color."""
        if category:
            self.category.set(category)
        self.color = CONFIG.get("Categories", self.category.get())
        self.save_note()

    def set_position_above(self):
        """Make note always above the other windows."""
        self.focus_force()
        self.update_idletasks()
        w = EWMH.getActiveWindow()
        if w is None or w.get_wm_name() != 'mynotes%s' % self.id:
            cl = EWMH.getClientList()
            i = 0
            n = len(cl)
            while i < n and cl[i].get_wm_name() != 'mynotes%s' % self.id:
                i += 1
            if i < n:
                w = cl[i]
            else:
                w = None
        if w:
            EWMH.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
            EWMH.setWmState(w, 0, '_NET_WM_STATE_BELOW')
            EWMH.display.flush()
        self.save_note()

    def set_position_below(self):
        """Make note always below the other windows."""
        self.focus_force()
        self.update_idletasks()
        w = EWMH.getActiveWindow()
        if w is None or w.get_wm_name() != 'mynotes%s' % self.id:
            cl = EWMH.getClientList()
            i = 0
            n = len(cl)
            while i < n and cl[i].get_wm_name() != 'mynotes%s' % self.id:
                i += 1
            if i < n:
                w = cl[i]
            else:
                w = None
        if w:
            EWMH.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
            EWMH.setWmState(w, 1, '_NET_WM_STATE_BELOW')
            EWMH.display.flush()
        self.save_note()

    def set_position_normal(self):
        """Make note be on top if active or behind the active window."""
        self.focus_force()
        self.update_idletasks()
        w = EWMH.getActiveWindow()
        if w is None or w.get_wm_name() != 'mynotes%s' % self.id:
            cl = EWMH.getClientList()
            i = 0
            n = len(cl)
            while i < n and cl[i].get_wm_name() != 'mynotes%s' % self.id:
                i += 1
            if i < n:
                w = cl[i]
            else:
                w = None
        if w:
            EWMH.setWmState(w, 0, '_NET_WM_STATE_BELOW')
            EWMH.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
            EWMH.display.flush()
        self.save_note()

    def set_mode_note(self):
        """Set mode to note (classic text input)."""
        self.txt.add_undo_sep()
        self.txt.mode_change('note')
        tags = self.txt.tag_names('1.0')
        if "list" in tags:
            self.txt.tag_remove_undoable("list", "1.0", "end")
        if "todolist" in tags:
            self.txt.tag_remove_undoable("todolist", "1.0", "end")
        if "enum" in tags:
            self.txt.tag_remove_undoable("enum", "1.0", "end")
        self.txt.add_undo_sep()
        self.save_note()
        print(self.mode.get(), [(t, self.txt.tag_ranges(t)) for t in self.txt.tag_names() if self.txt.tag_ranges(t)])

    def set_mode_list(self):
        """Set mode to list (bullet point list)."""
        end = int(self.txt.index("end").split(".")[0])
        lines  = self.txt.get("1.0", "end").splitlines()
        self.txt.add_undo_sep()
        self.txt.mode_change('list')
        tags = self.txt.tag_names('1.0')
        if "todolist" in tags:
            self.txt.tag_remove_undoable("todolist", "1.0", "end")
        if "enum" in tags:
            self.txt.tag_remove_undoable("enum", "1.0", "end")
        for i, l in zip(range(1, end), lines):
            # remove checkboxes
            try:
                ch = self.txt.window_cget("%i.0"  % i, "window")
                self.txt.delete_undoable("%i.0"  % i)
                self.txt.children[ch.split('.')[-1]].destroy()
            except TclError:
                # there is no checkbox
                # remove enumeration
                res = re.match('^\t[0-9]+\.\t', l)
                if res:
                    self.txt.delete_undoable("%i.0"  % i, "%i.%i"  % (i, res.end()))
            if self.txt.get("%i.0"  % i, "%i.3"  % i) != "\t•\t":
                self.txt.insert_undoable("%i.0" % i, "\t•\t")
        self.txt.tag_add_undoable("list", "1.0", "end")
        self.txt.add_undo_sep()
        self.save_note()
        print(self.mode.get(), [(t, self.txt.tag_ranges(t)) for t in self.txt.tag_names() if self.txt.tag_ranges(t)])

    def set_mode_enum(self):
        """Set mode to enum (enumeration)."""
        self.txt.add_undo_sep()
        self.txt.mode_change('enum')
        end = int(self.txt.index("end").split(".")[0])
        lines  = self.txt.get("1.0", "end").splitlines()
        tags = self.txt.tag_names('1.0')
        if "list" in tags:
            self.txt.tag_remove_undoable("list", "1.0", "end")
        if "todolist" in tags:
            self.txt.tag_remove_undoable("todolist", "1.0", "end")
        for i, l in zip(range(1, end), lines):
            # remove checkboxes
            try:
                ch = self.txt.window_cget("%i.0"  % i, "window")
                self.txt.delete_undoable("%i.0"  % i)
                self.txt.children[ch.split('.')[-1]].destroy()
            except TclError:
                # there is no checkbox
                # remove bullets
                if self.txt.get("%i.0"  % i, "%i.3"  % i) == "\t•\t":
                    self.txt.delete_undoable("%i.0"  % i, "%i.3"  % i)
            if not re.match('^\t[0-9]+\.', l):
                self.txt.insert_undoable("%i.0" % i, "\t0.\t")
        self.txt.tag_add_undoable("enum", "1.0", "end")
        self.txt.update_enum()
        self.txt.add_undo_sep()
        self.save_note()
        print(self.mode.get(), [(t, self.txt.tag_ranges(t)) for t in self.txt.tag_names() if self.txt.tag_ranges(t)])

    def set_mode_todolist(self):
        """Set mode to todolist (checkbox list)."""
        end = int(self.txt.index("end").split(".")[0])
        lines  = self.txt.get("1.0", "end").splitlines()
        self.txt.add_undo_sep()
        self.txt.mode_change('todolist')
        tags = self.txt.tag_names('1.0')
        if "list" in tags:
            self.txt.tag_remove_undoable("list", "1.0", "end")
        if "enum" in tags:
            self.txt.tag_remove_undoable("enum", "1.0", "end")

        for i,l in zip(range(1, end), lines):
            res = re.match('^\t[0-9]+\.\t', l)
            if res:
                self.txt.delete_undoable("%i.0"  % i, "%i.%i"  % (i, res.end()))
            elif self.txt.get("%i.0"  % i, "%i.3"  % i) == "\t•\t":
                self.txt.delete_undoable("%i.0"  % i, "%i.3"  % i)
            try:
                self.txt.window_cget("%i.0"  % i, "window")
            except TclError:
                self.txt.checkbox_create_undoable("%i.0"  % i)
        self.txt.tag_add_undoable("todolist", "1.0", "end")
        self.txt.add_undo_sep()
        self.save_note()
        print(self.mode.get(), [(t, self.txt.tag_ranges(t)) for t in self.txt.tag_names() if self.txt.tag_ranges(t)])

    # --- bindings
    def enter_roll(self, event):
        """Mouse is over the roll icon."""
        self.roll.configure(image="img_rollactive")

    def leave_roll(self, event):
        """Mouse leaves the roll icon."""
        self.roll.configure(image="img_roll")

    def enter_close(self, event):
        """Mouse is over the close icon."""
        self.close.configure(image="img_closeactive")

    def leave_close(self, event):
        """Mouse leaves the close icon."""
        self.close.configure(image="img_close")

    def change_focus(self, event):
        """
        Set focus on note.

        Because of the use of window type "splash" (necessary to remove window
        decoration), it is necessary to force the focus in order to write inside
        the Text widget.
        """
        if not self.is_locked:
            event.widget.focus_force()

    def show_menu(self, event):
        """Show main menu."""
        self.menu.tk_popup(event.x_root, event.y_root)

    def show_menu_txt(self, event):
        """Show text menu."""
        self.txt.mark_set("insert", "current")  # put insert cursor beneath mouse
        self.menu_txt.tk_popup(event.x_root, event.y_root)

    def resize(self, event):
        """Save new note geometry after resizing."""
        self.save_geometry = self.geometry()

    def edit_title(self, event):
        """Show entry to edit title."""
        self.title_entry.place(x=self.title_label.winfo_x() + 5,
                               y=self.title_label.winfo_y(),
                               anchor="nw",
                               width=self.title_label.winfo_width()-10)

    def start_move(self, event):
        """Start moving the note."""
        self.x = event.x
        self.y = event.y
        self.configure(cursor='fleur')

    def stop_move(self, event):
        """Stop moving the note."""
        self.x = None
        self.y = None
        self.configure(cursor='')

    def move(self, event):
        """Make note follow cursor motion."""
        if self.x is not None and self.y is not None:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            geo = "+%s+%s" % (x, y)
            self.geometry(geo)
            self.save_geometry = self.save_geometry.split("+")[0] + geo

    def save_note(self, event=None):
        """Save note."""
        data = self.save_info()
        data["visible"] = True
        self.master.note_data[self.id] = data
        self.master.save()

    def mouse_roll(self, event):
        if event.num == 5 and not self.txt.winfo_ismapped():
            self.txt.grid(row=1, columnspan=4,
                          column=0, sticky="ewsn", pady=(1,4), padx=4)
            self.corner.place(relx=1.0, rely=1.0, anchor="se")
            self.geometry(self.save_geometry)
        elif event.num == 4 and self.txt.winfo_ismapped():
            self.txt.grid_forget()
            self.corner.place_forget()
            self.geometry("%sx22" % self.winfo_width())
        self.save_note()

    def rollnote(self, event=None):
        """Roll/unroll note."""
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
        """Hide note (can be displayed again via app menu)."""
        cat = self.category.get()
        self.master.add_note_to_menu(self.id, self.title_var.get().strip(), cat)
        data = self.save_info()
        data["visible"] = False
        self.master.note_data[self.id] = data
        del(self.master.notes[self.id])
        self.master.save()
        self.destroy()

    # --- Settings update
    def update_title_font(self):
        """Update title font after configuration change."""
        font = "%s %s" %(CONFIG.get("Font", "title_family").replace(" ", "\ "),
                         CONFIG.get("Font", "title_size"))
        style = CONFIG.get("Font", "title_style").split(",")
        if style:
            font += " "
            font += " ".join(style)
        self.title_label.configure(font=font)

    def update_text_font(self):
        """Update text font after configuration change."""
        self.txt.update_font()

    def update_menu_cat(self, categories):
        """Update the category submenu."""
        self.menu_categories.delete(0, "end")
        for cat in categories:
            self.menu_categories.add_radiobutton(label=cat.capitalize(), value=cat,
                                                 variable=self.category,
                                                 command=self.change_category)
    def update_titlebar(self):
        """Update title bar button order."""
        if CONFIG.get("General", "buttons_position") == "right":
            # right = lock icon - title - roll - close
            self.titlebar.columnconfigure(1, weight=1)
            self.titlebar.columnconfigure(2, weight=0)
            self.roll.grid(row=0, column=2, sticky="e")
            self.close.grid(row=0, column=3, sticky="e", padx=(0,2))
            self.cadenas.grid(row=0, column=0, sticky="w")
            self.title_label.grid(row=0, column=1, sticky="ew", pady=(1,0))
        else:
            # left = close - roll - title - lock icon
            self.titlebar.columnconfigure(1, weight=0)
            self.titlebar.columnconfigure(2, weight=1)
            self.roll.grid(row=0, column=1, sticky="w")
            self.close.grid(row=0, column=0, sticky="w", padx=(2,0))
            self.cadenas.grid(row=0,column=3, sticky="e")
            self.title_label.grid(row=0, column=2, sticky="ew", pady=(1,0))

    # --- Text edition
    # ---* --Link
    def add_link(self, link_nb=None):
        """Insert link (URL or local file) in note."""

        def local_file():
            d, f = os.path.split(link.get())
            file = askopenfilename("", [], d, initialfile=f)
            if file:
                link.delete(0, 'end')
                link.insert(0, file)

        def ok(event=None):
            lien = link.get()
            txt = text.get()
            if lien:
                self.txt.add_undo_sep()
                if not txt:
                    txt = lien
                if link_nb is None:
                    self.nb_links += 1
                    lnb = self.nb_links
                    lid = "link#%i" % lnb
                else:
                    lnb = link_nb
                    lid = "link#%i" % lnb
                if sel:
                    index = sel[0]
                    self.txt.delete_undoable(*sel)
                else:
                    index = "insert"

                tags = self.txt.tag_names(index) + ("link", lid)
                self.txt.insert_undoable(index, txt, tags)
                self.txt.link_create_undoable(lnb, lien)
                self.txt.add_undo_sep()
                self.txt.tag_bind(lid, "<Button-1>", lambda e: self.open_link(lnb))
                self.txt.tag_bind(lid, "<Double-Button-1>", lambda e: self.edit_link(lnb))
            top.destroy()
            self.txt.focus_force()

        if link_nb is None:
            if self.txt.tag_ranges('sel'):
                txt = self.txt.get('sel.first', 'sel.last')
                sel = self.txt.index("sel.first"), self.txt.index("sel.last")
            else:
                txt = ''
                sel = ()
            link_txt = txt
        else:
            lid = "link#%i" % link_nb
            txt = self.txt.get('%s.first' % lid, '%s.last' % lid)
            link_txt = self.txt.links[link_nb]
            sel = self.txt.index('%s.first' % lid), self.txt.index('%s.last' % lid)
            self.txt.tag_add('sel', *sel)

        top = Toplevel(self, class_='MyNotes')
        top.withdraw()
        top.transient(self)
        top.update_idletasks()
        top.geometry("+%i+%i" % top.winfo_pointerxy())
        top.resizable(True, False)
        top.title(_("Link"))
        top.columnconfigure(1, weight=1)
        link = Entry(top)
        b_file = Button(top, image=self.im_clip, padding=0, command=local_file)
        text = Entry(top)
        text.insert(0, txt)
        text.icursor("end")
        link.insert(0, link_txt)
        link.icursor("end")
        Label(top, text=_("URL or file")).grid(row=0, column=0, sticky="e", padx=4, pady=4)
        Label(top, text=_("Text")).grid(row=1, column=0, sticky="e", padx=4, pady=4)
        link.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        b_file.grid(row=0, column=2, padx=4, pady=4)
        text.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        Button(top, text="Ok", command=ok).grid(row=2, columnspan=3, padx=4, pady=4)
        link.focus_set()
        text.bind("<Return>", ok)
        link.bind("<Return>", ok)
        top.bind('<Escape>', lambda e: top.destroy())
        top.deiconify()
        top.update_idletasks()
        top.grab_set()

    def create_link(self, link):
        self.nb_links += 1
        lnb = self.nb_links
        lid = "link#%i" % lnb
        self.txt.link_create_undoable(lnb, link)
        self.txt.tag_bind(lid, "<Button-1>", lambda e: self.open_link(lnb))
        self.txt.tag_bind(lid, "<Double-Button-1>", lambda e: self.edit_link(lnb))
        return lid

    def open_link(self, link_nb):
        """Open link after small delay to avoid opening link on double click."""
        lien = self.txt.links[link_nb]
        self.links_click_id[link_nb] = self.after(500, lambda: open_url(lien))

    def edit_link(self, link_nb):
        """Edit link number link_nb."""
        # cancel link opening
        self.after_cancel(self.links_click_id[link_nb])
        self.add_link(link_nb)

    # ---* --Add other objects
    def add_checkbox(self, event=None):
        """Insert checkbox in note."""
        index = self.txt.index("insert")
        self.txt.add_undo_sep()
        self.txt.checkbox_create_undoable(index)
        self.txt.add_undo_sep()

    def add_date(self, event=None):
        """Insert today's date in note."""
        self.txt.add_undo_sep()
        self.txt.insert_undoable("insert", strftime("%x"))
        self.txt.add_undo_sep()

    def add_latex(self, img_name=None):
        """Insert image generated from latex expression given in the entry."""

        def ok(event):
            latex = r'%s' % text.get()
            if latex:
                if img_name is None:
                    l = [int(os.path.splitext(f)[0]) for f in os.listdir(PATH_LATEX)]
                    l.sort()
                    if l:
                        i = l[-1] + 1
                    else:
                        i = 0
                    img = "%i.png" % i
                    self.txt.tag_bind(img, '<Double-Button-1>',
                                      lambda e: self.add_latex(img))
                else:
                    img = img_name
                im = os.path.join(PATH_LATEX, img)
                try:
                    math_to_image(latex, im, fontsize=CONFIG.getint("Font", "text_size")-2)
                    self.images.append(PhotoImage(file=im, master=self))
                    self.txt.add_undo_sep()
                    if sel:
                        index = sel[0]
                        self.txt.delete_undoable(*sel)
                    else:
                        if img_name:
                            index = self.txt.index("current")
                            self.txt.delete_undoable(index)
                        else:
                            index = self.txt.index("insert")
                    self.txt.latex_create_undoable(index, img, self.images[-1], latex)
                    self.txt.tag_add_undoable(img, index)
                    self.txt.add_undo_sep()
                    top.destroy()
                    self.txt.focus_force()

                except Exception as e:
                    showerror(_("Error"), str(e))

        top = Toplevel(self, class_='MyNotes')
        top.withdraw()
        top.transient(self)
        top.update_idletasks()
        top.geometry("+%i+%i" % top.winfo_pointerxy())
        top.resizable(True, False)
        top.title("LaTeX")
        text = Entry(top, justify='center')
        if img_name is not None:
            text.insert(0, self.txt.latex[img_name])

            sel = ()
        else:
            if self.txt.tag_ranges('sel'):
                sel = self.txt.index("sel.first"), self.txt.index("sel.last")
                text.insert(0, '$')
                text.insert('end', self.txt.get('sel.first', 'sel.last'))
                text.insert('end', '$')

            else:
                sel = ()
                text.insert(0, '$$')
                text.icursor(1)

        text.pack(fill='x', expand=True)
        text.bind('<Return>', ok)
        text.bind('<Escape>', lambda e: top.destroy())
        text.focus_set()
        top.deiconify()
        top.update_idletasks()
        top.grab_set()

    def create_latex(self, latex, index):
        l = [int(os.path.splitext(f)[0]) for f in os.listdir(PATH_LATEX)]
        l.sort()
        if l:
            i = l[-1] + 1
        else:
            i = 0
        img = "%i.png" % i
        self.txt.tag_bind(img, '<Double-Button-1>',
                          lambda e: self.add_latex(img))
        im = os.path.join(PATH_LATEX, img)
        math_to_image(latex, im, fontsize=CONFIG.getint("Font", "text_size") - 2)
        self.images.append(PhotoImage(file=im, master=self))
        self.txt.latex_create_undoable(index, img, self.images[-1], latex)
        self.txt.tag_add_undoable(img, index)

    def add_image(self, event=None):
        """Insert image in note."""
        fichier = askopenfilename(defaultextension="",
                                  filetypes=[("PNG", "*.png"),
                                             ("JPEG", "*.jpg"),
                                             ("GIF", "*.gif"),
                                             (_("All files"), "*")],
                                  initialdir="",
                                  initialfile="",
                                  title=_('Select image'))
        if os.path.exists(fichier):
            try:
                im = PhotoImage(master=self.txt, file=fichier)
            except OSError:
                showerror(_("Error"),
                          _("{file}: Unsupported image format.").format(file=fichier))
            else:
                self.images.append(im)
                index = self.txt.index("insert")
                self.txt.add_undo_sep()
                self.txt.image_create_undoable(index,
                                               align='bottom',
                                               image=im,
                                               name=fichier)
                self.txt.add_undo_sep()
                self.txt.focus_force()
        elif fichier:
            showerror(_("Error"), _("{file} does not exist.").format(file=fichier))

    def add_symbols(self):
        """Insert symbol in note."""
        symbols = pick_symbol(self,
                              CONFIG.get("Font", "text_family").replace(" ", "\ "),
                              CONFIG.get("General", "symbols"),
                              class_='MyNotes')
        self.txt.add_undo_sep()
        self.txt.insert_undoable("insert", symbols)
        self.txt.add_undo_sep()
