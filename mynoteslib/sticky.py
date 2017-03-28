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


from tkinter import Text,  Toplevel, PhotoImage, StringVar, Menu
from tkinter.ttk import  Style, Sizegrip, Entry, Checkbutton, Label
from tkinter.messagebox import askokcancel, showerror
import os
from time import strftime

from mynoteslib.constantes import CONFIG, COLORS, IM_LOCK, askopenfilename
from mynoteslib.constantes import TEXT_COLORS, NB_SYMB, IM_SYMB

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
        self.title('mynotes')

        self.attributes("-type", "splash")
        self.attributes("-alpha", CONFIG.getint("General", "opacity")/100)
        self.focus_force()
        self.update_idletasks()
        self.geometry(kwargs.get("geometry", '220x235'))
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.id = key
        self.is_locked = not (kwargs.get("locked", False))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.minsize(10,10)
        self.save_geometry = kwargs.get("geometry", '220x235')
        self.images = []

        # right-click menu on the title
        self.menu = Menu(self, tearoff=False)
        self.menu_colors = Menu(self.menu, tearoff=False)
        colors = list(COLORS.keys())
        colors.sort()
        for coul in colors:
            self.menu_colors.add_command(label=coul,
                                           command=lambda key=coul: self.change_color(key))
        self.category = StringVar(self)
        self.menu_categories = Menu(self.menu, tearoff=False)
        categories = CONFIG.options("Categories")
        categories.sort()
        for cat in categories:
            self.menu_categories.add_radiobutton(label=cat.capitalize(), value=cat,
                                                 variable=self.category,
                                                 command=lambda category=cat: self.change_category(category))
        self.category.set(kwargs.get("category",
                                     CONFIG.get("General", "default_category")))
        self.menu.add_command(label=_("Delete"), command=self.delete)
        self.menu.add_cascade(label=_("Category"), menu=self.menu_categories)
        self.menu.add_cascade(label=_("Color"), menu=self.menu_colors)
        self.menu.add_command(label=_("Lock"), command=self.lock)

        # style
        self.style = Style(self)
        self.style.configure(self.id + ".TCheckbutton", selectbackground="red")
        self.style.map('TEntry', selectbackground=[('!focus', '#c3c3c3')])

        font_text = "%s %s" %(CONFIG.get("Font", "text_family").replace(" ", "\ "),
                              CONFIG.get("Font", "text_size"))
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
        self.title_label.grid(row=0, column=1, sticky="ew", pady=(1,0))

        self.title_entry = Entry(self, textvariable=self.title_var,
                                 exportselection=False,
                                 justify="center", font=font_text)

        self.txt = Text(self, wrap='word', undo=True,
                        selectforeground='white',
                        inactiveselectbackground='#c3c3c3',
                        selectbackground=self.style.lookup('TEntry', 'selectbackground', ('focus',)),
                        relief="flat", borderwidth=0,
                        highlightthickness=0, font=font_text)
        self.txt.grid(row=1, columnspan=4, column=0, sticky="ewsn",
                      pady=(1,4), padx=4)
        self.txt.insert('1.0', kwargs.get("txt",""))
        self.txt.edit_reset()

        # right-click menu on the main text of the note
        self.menu_txt = Menu(self.txt, tearoff=False)
        menu_style = Menu(self.menu_txt, tearoff=False)
        menu_align = Menu(self.menu_txt, tearoff=False)
        menu_symbols = Menu(self.menu_txt, tearoff=False)
        menu_colors = Menu(self.menu_txt, tearoff=False)

        menu_style.add_command(label=_("Bold"), command=lambda: self.toggle_text_style("bold"))
        menu_style.add_command(label=_("Italic"), command=lambda: self.toggle_text_style("italic"))
        menu_style.add_command(label=_("Underline"), command=lambda: self.toggle_text_style("underline"))
        menu_style.add_command(label=_("Overstrike"), command=lambda: self.toggle_text_style("overstrike"))

        menu_align.add_command(label=_("Left"), command=lambda: self.set_align("left"))
        menu_align.add_command(label=_("Right"), command=lambda: self.set_align("right"))
        menu_align.add_command(label=_("Center"), command=lambda: self.set_align("center"))


        colors = list(TEXT_COLORS.keys())
        colors.sort()
        for coul in colors:
            menu_colors.add_command(label=coul,
                                    command=lambda key=coul: self.change_sel_color(TEXT_COLORS[key]))
        self.symbols = []
        for i in range(NB_SYMB):
            self.symbols.append(PhotoImage(master=self, file=IM_SYMB[i]))
            menu_symbols.add_command(image=self.symbols[-1],
                                          command=lambda nb=i: self.add_symbol(nb))

        self.menu_txt.add_cascade(label=_("Style"), menu=menu_style)
        self.menu_txt.add_cascade(label=_("Paragraph"), menu=menu_align)
        self.menu_txt.add_cascade(label=_("Color"), menu=menu_colors)
        self.menu_txt.add_cascade(label=_("Symbols"), menu=menu_symbols)
        self.menu_txt.add_command(label=_("Checkbox"), command=self.add_checkbox)
        self.menu_txt.add_command(label=_("Image"), command=self.add_image)
        self.menu_txt.add_command(label=_("Date"), command=self.add_date)

        self.txt.tag_configure("bold", font="Liberation\ Sans 10 bold")
        self.txt.tag_configure("italic", font="Liberation\ Sans 10 italic")
        self.txt.tag_configure("bold-italic", font="Liberation\ Sans 10 bold italic")
        self.txt.tag_configure("underline", underline=True)
        self.txt.tag_configure("overstrike", overstrike=True)
        self.txt.tag_configure("center", justify="center")
        self.txt.tag_configure("left", justify="left")
        self.txt.tag_configure("right", justify="right")
        for coul in TEXT_COLORS.values():
            self.txt.tag_configure(coul, foreground=coul)

        # restore checkboxes
        for index in kwargs.get("checkboxes", []):
            ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
            if kwargs["checkboxes"][index]:
                ch.state(("selected",))
            self.txt.window_create(index, window=ch)

        # restore symbols
        for index in kwargs.get("symbols", []):
            nb = kwargs['symbols'][index]
            self.txt.image_create(index, image=self.symbols[nb],
                                  name="symb%i" % nb)

        # restore images
        for i,index in enumerate(kwargs.get("images", [])):
            fich = kwargs["images"][index]
            if os.path.exists(fich):
                self.images.append(PhotoImage(master=self.txt, file=fich))
                self.txt.image_create(index, image=self.images[-1], name=fich)

        # restore tags
        for tag in kwargs.get("tags", []):
            indices = kwargs["tags"][tag]
            if indices:
                self.txt.tag_add(tag, *indices)

        self.txt.focus_set()

        self.roll = Label(self, image="img_roll", style=self.id + ".TLabel")
        self.roll.grid(row=0, column=2, sticky="e")
        self.close = Label(self, image="img_close", style=self.id + ".TLabel")
        self.close.grid(row=0, column=3, sticky="e")

        self.corner = Sizegrip(self, style=self.id + ".TSizegrip")
        self.corner.place(relx=1.0, rely=1.0, anchor="se")
        self.im_lock = PhotoImage(master=self, file=IM_LOCK)
        self.cadenas = Label(self, style=self.id + ".TLabel")

        self.color = kwargs.get("color",
                                CONFIG.get("Categories", self.category.get()))

        self.cadenas.grid(row=0,column=0, sticky="w")


        self.close.bind("<Button-1>", self.hide)
        self.roll.bind("<Button-1>", self.rollnote)
        self.close.bind("<Enter>", self.enter_close)
        self.roll.bind("<Enter>", self.enter_roll)
        self.close.bind("<Leave>", self.leave_close)
        self.roll.bind("<Leave >", self.leave_roll)

        self.title_label.bind("<Double-Button-1>", self.edit_title)
        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<ButtonRelease-1>", self.stop_move)
        self.title_label.bind("<B1-Motion>", self.move)
        self.title_entry.bind("<Return>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<FocusOut>", lambda e: self.title_entry.place_forget())
        self.title_entry.bind("<Escape>", lambda e: self.title_entry.place_forget())
        self.bind("<FocusOut>", self.focus_out)
        self.title_label.bind('<Button-3>', self.show_menu)
        self.txt.bind('<Button-3>', self.show_menu_txt)
        self.bind_class('Text', '<Control-a>', self.select_all_text)
        self.bind_class('TEntry', '<Control-a>', self.select_all_entry)
        # remove Ctrl+Y from shortcuts since it's pasting things like Ctrl+V
        self.txt.unbind_class('Text', '<Control-y>')
        self.corner.bind('<ButtonRelease-1>', self.resize)
        self.bind('<Configure>', self.bouge)

        self.lock()
        if kwargs.get("rolled", False):
            self.rollnote()
        self.bind('<Button-1>', self.change_focus, True)

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

    def select_all_text(self, event):
        event.widget.tag_add("sel","1.0","end")

    def select_all_entry(self, event):
        event.widget.selection_range(0, "end")

    def change_focus(self, event):
        if not self.is_locked:
            event.widget.focus_force()

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
                                                 command=lambda category=cat: self.change_category(category))

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

    def add_checkbox(self):
        ch = Checkbutton(self.txt, style=self.id + ".TCheckbutton")
        self.txt.window_create("insert", window=ch)

    def add_date(self):
        self.txt.insert("insert", strftime("%x"))

    def add_image(self):
        fichier = askopenfilename(defaultextension=".png",
                                  filetypes=[("PNG", "*.png")],
                                  initialdir="",
                                  initialfile="",
                                  title=_('Select PNG image'))
        if os.path.exists(fichier):
            self.images.append(PhotoImage(master=self.txt, file=fichier))
            self.txt.image_create("insert",
                                  image=self.images[-1],
                                  name=fichier)
        else:
            showerror("Erreur", "L'image %s n'existe pas" % fichier)


    def add_symbol(self, nb):
        self.txt.image_create("insert", image=self.symbols[nb], name="symb%i" % nb)

    def change_color(self, key):
        self.color = COLORS[key]

    def change_category(self, category):
        self.color = CONFIG.get("Categories", category)

    def focus_out(self, event):
        data = self.save_info()
        data["visible"] = True
        self.master.note_data[self.id] = data
        self.master.save()

    def delete(self, confirmation=True):
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
        if self.is_locked:
            self.txt.configure(state="normal",
                               selectforeground='white',
                               selectbackground=self.style.lookup('TEntry',
                                                                  'selectbackground',
                                                                  ('focus',)))
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
                               selectbackground='#c3c3c3')
            self.cadenas.configure(image=self.im_lock)
            for checkbox in self.txt.window_names():
                ch = self.txt.children[checkbox.split(".")[-1]]
                ch.configure(state="disabled")
            self.is_locked = True
            self.menu.entryconfigure(3, label=_("Unlock"))
            self.title_label.unbind("<Double-Button-1>")
            self.txt.unbind('<Button-3>')

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
        data["checkboxes"] = {}
        data["images"] = {}
        data["symbols"] = {}
        data["rolled"] = not self.txt.winfo_ismapped()
        for image in self.txt.image_names():
            if image[:4] == "symb":
                data["symbols"][self.txt.index(image)] = int(image[4:].split('#')[0])
            else:
                data["images"][self.txt.index(image)] = image.split('#')[0]
        for checkbox in self.txt.window_names():
            ch = self.txt.children[checkbox.split(".")[-1]]
            data["checkboxes"][self.txt.index(checkbox)] = ("selected" in ch.state())
        return data

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



    def edit_title(self, event):
        self.title_entry.place(x=self.title_label.winfo_x() + 5,
                               y=self.title_label.winfo_y(),
                               anchor="nw",
                               width=self.title_label.winfo_width()-10)

    def hide(self, event=None):
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
            current_tags = self.txt.tag_names("sel.first")
            for coul in TEXT_COLORS.values():
                if coul in current_tags:
                    self.txt.tag_remove(coul, "sel.first", "sel.last")
            self.txt.tag_add(color, "sel.first", "sel.last")

    def set_align(self, alignment):
        """ Align the text according to alignment (left, right, center) """
        if self.txt.tag_ranges("sel"):
            line = self.txt.index("sel.first").split(".")[0]
            # remove old alignment tag
            self.txt.tag_remove("left", line + ".0", line + ".end")
            self.txt.tag_remove("right", line + ".0", line + ".end")
            self.txt.tag_remove("center", line + ".0", line + ".end")
            # set new alignment tag
            self.txt.tag_add(alignment, line + ".0", line + ".end")
