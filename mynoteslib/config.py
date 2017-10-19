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


Configuration Window
"""


from tkinter import Toplevel, StringVar, Menu, TclError, Text
from mynoteslib.messagebox import showinfo
from tkinter.ttk import Label, Radiobutton, Button, Scale, Style, Separator
from tkinter.ttk import Notebook, Combobox, Frame, Menubutton, Checkbutton
from mynoteslib.constantes import CONFIG, save_config, COLORS, SYMBOLS, LATEX, LANGUAGES, REV_LANGUAGES
from mynoteslib.categories import CategoryManager
from tkinter import font


class Config(Toplevel):
    """Config dialog."""
    def __init__(self, master):
        """Create Config dialog."""
        Toplevel.__init__(self, master)
        self.title(_("Preferences"))
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.changes = {}, {}, False, False, False

        # --- style
        style = Style(self)
        style.theme_use("clam")
        style.configure("TScale", sliderlength=20)
        style.map("TCombobox",
                  fieldbackground=[('readonly', 'white')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', 'black')])
        style.configure("prev.TLabel", background="white")
        style.map("prev.TLabel", background=[("active", "white")])
        color = CONFIG.get("Categories",
                           CONFIG.get("General", "default_category"))
        style.configure("titlebar.TFrame", background=color)
        style.configure("titlebar.TLabel", background=color)
        style.configure("text.TFrame", background="white")

        # --- body
        self.notebook = Notebook(self)
        okcancel_frame = Frame(self)
        okcancel_frame.columnconfigure(0, weight=1)
        okcancel_frame.columnconfigure(1, weight=1)
        self.notebook.pack(expand=True, fill="both")
        okcancel_frame.pack(fill="x", expand=True)

        # --- * General settings
        general_settings = Frame(self.notebook)
        general_settings.columnconfigure(0, weight=1)
        self.notebook.add(general_settings, text=_("General"),
                          sticky="ewsn", padding=4)

        # --- *-- language

        self.lang = StringVar(self, LANGUAGES[CONFIG.get("General", "language")])
        lang_frame = Frame(general_settings)
        Label(lang_frame, text=_("Language")).grid(row=0, sticky="w", padx=4,
                                                   pady=4)
        menu_lang = Menu(lang_frame, tearoff=False)
        Menubutton(lang_frame, menu=menu_lang, width=9,
                   textvariable=self.lang).grid(row=0, column=1, padx=8, pady=4)
        for lang in LANGUAGES.values():
            menu_lang.add_radiobutton(variable=self.lang, label=lang,
                                      value=lang, command=self.translate)
#        menu_lang.add_radiobutton(label="English", value="English",
#                                  variable=self.lang, command=self.translate)
#        menu_lang.add_radiobutton(label="Français", value="Français",
#                                  variable=self.lang, command=self.translate)
#        menu_lang.add_radiobutton(label="Nederlands", value="Nederlands",
#                                  variable=self.lang, command=self.translate)
        # --- *-- opacity
        self.opacity_scale = Scale(general_settings, orient="horizontal", length=200,
                                   from_=0, to=100,
                                   value=CONFIG.get("General", "opacity"),
                                   command=self.display_label)
        self.opacity_label = Label(general_settings,
                                   text="{val}%".format(val=self.opacity_scale.get()))
        # --- *-- position
        frame_position = Frame(general_settings)
        self.position = StringVar(self, CONFIG.get("General", "position"))
        Label(frame_position,
              text=_("Default position of the notes")).grid(row=0,
                                                            columnspan=3,
                                                            sticky="w",
                                                            padx=4, pady=4)
        Radiobutton(frame_position, text=_("Always above"), value="above",
                    variable=self.position).grid(row=1, column=0)
        Radiobutton(frame_position, text=_("Always below"), value="below",
                    variable=self.position).grid(row=1, column=1)
        Radiobutton(frame_position, text=_("Normal"), value="normal",
                    variable=self.position).grid(row=1, column=2)
        # --- *-- titlebar
        self.titlebar_disposition = StringVar(self, CONFIG.get("General",
                                                               "buttons_position"))
        font_title = "%s %s" % (CONFIG.get("Font", "title_family").replace(" ", "\ "),
                                CONFIG.get("Font", "title_size"))
        style = CONFIG.get("Font", "title_style").split(",")
        if style:
            font_title += " "
            font_title += " ".join(style)

        frame_titlebar = Frame(general_settings)
        frame_titlebar.columnconfigure(1, weight=1)
        frame_titlebar.columnconfigure(3, weight=1)
        Label(frame_titlebar,
              text=_("Title bar disposition")).grid(row=0, columnspan=4,
                                                    sticky="w", padx=4, pady=4)
        Radiobutton(frame_titlebar, value="right",
                    variable=self.titlebar_disposition).grid(row=1, column=0)
        right = Frame(frame_titlebar, style="titlebar.TFrame")
        right.grid(row=1, column=1, sticky="ew")

        def select_right(event):
            self.titlebar_disposition.set("right")

        Label(right, text=_("Title"), style="titlebar.TLabel", anchor="center",
              font=font_title).pack(side="left", fill="x", expand=True)
        Label(right, image="img_close", style="titlebar.TLabel").pack(side="right")
        Label(right, image="img_roll", style="titlebar.TLabel").pack(side="right")
        for ch in right.children.values():
            ch.bind("<Button-1>", select_right)
        Radiobutton(frame_titlebar, value="left",
                    variable=self.titlebar_disposition).grid(row=1, column=2)
        left = Frame(frame_titlebar, style="titlebar.TFrame")
        left.grid(row=1, column=3, sticky="ew")

        def select_left(event):
            self.titlebar_disposition.set("left")

        Label(left, image="img_close", style="titlebar.TLabel").pack(side="left")
        Label(left, image="img_roll", style="titlebar.TLabel").pack(side="left")
        Label(left, text=_("Title"), style="titlebar.TLabel", anchor="center",
              font=font_title).pack(side="right", fill="x", expand=True)
        for ch in left.children.values():
            ch.bind("<Button-1>", select_left)
        # --- *-- placement
        lang_frame.grid(sticky="w")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        Label(general_settings,
              text=_("Opacity")).grid(sticky="w", padx=4, pady=4)
        self.opacity_scale.grid(padx=4, pady=(4, 10))
        self.opacity_label.place(in_=self.opacity_scale, relx=1, rely=0.5,
                                 anchor="w", bordermode="outside")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        frame_position.grid(sticky="ew")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        frame_titlebar.grid(sticky="ew", pady=4)
        if LATEX:
            Separator(general_settings,
                      orient="horizontal").grid(sticky="ew", pady=10)
            Button(general_settings,
                   text=_('Delete unused LaTex data'),
                   command=self.cleanup).grid(padx=4, pady=4, sticky='w')

        # --- * Font settings
        font_settings = Frame(self.notebook)
        font_settings.columnconfigure(0, weight=1)
        self.notebook.add(font_settings, text=_("Font"),
                          sticky="ewsn", padding=4)

        # --- *-- title
        fonttitle_frame = Frame(font_settings)

        title_size = CONFIG.get("Font", "title_size")
        title_family = CONFIG.get("Font", "title_family")

        self.sampletitle = Label(fonttitle_frame, text=_("Sample text"),
                                 anchor="center",
                                 style="prev.TLabel", relief="groove")

        self.sampletitle.grid(row=2, columnspan=2, padx=4, pady=6,
                              ipadx=4, ipady=4, sticky="eswn")
        self.fonts = list(set(font.families()))
        self.fonts.append("TkDefaultFont")
        self.fonts.sort()
        w = max([len(f) for f in self.fonts])
        self.sizes = ["%i" % i for i in (list(range(6, 17)) + list(range(18, 32, 2)))]

        self.fonttitle_family = Combobox(fonttitle_frame, values=self.fonts,
                                         width=(w * 2) // 3,
                                         exportselection=False,
                                         validate="key")
        self._validate_title_size = self.register(lambda *args: self.validate_font_size(self.fonttitle_size, *args))
        self._validate_title_family = self.register(lambda *args: self._validate_font_family(self.fonttitle_family, *args))
        self.fonttitle_family.configure(validatecommand=(self._validate_title_family,
                                                         "%d", "%S", "%i", "%s", "%V"))
        self.fonttitle_family.current(self.fonts.index(title_family))
        self.fonttitle_family.grid(row=0, column=0, padx=4, pady=4)
        self.fonttitle_size = Combobox(fonttitle_frame, values=self.sizes, width=5,
                                       exportselection=False,
                                       validate="key",
                                       validatecommand=(self._validate_title_size, "%d", "%P", "%V"))
        self.fonttitle_size.current(self.sizes.index(title_size))
        self.fonttitle_size.grid(row=0, column=1, padx=4, pady=4)

        frame_title_style = Frame(fonttitle_frame)
        frame_title_style.grid(row=1, columnspan=2, padx=4, pady=6)
        self.is_bold = Checkbutton(frame_title_style, text=_("Bold"),
                                   command=self.update_preview_title)
        self.is_italic = Checkbutton(frame_title_style, text=_("Italic"),
                                     command=self.update_preview_title)
        self.is_underlined = Checkbutton(frame_title_style, text=_("Underline"),
                                         command=self.update_preview_title)
        style = CONFIG.get("Font", "title_style")
        if "bold" in style:
            self.is_bold.state(("selected",))
        if "italic" in style:
            self.is_italic.state(("selected",))
        if "underline" in style:
            self.is_underlined.state(("selected",))
        self.is_bold.pack(side="left")
        self.is_italic.pack(side="left")
        self.is_underlined.pack(side="left")

        self.update_preview_title()
        # --- *-- text
        size = CONFIG.get("Font", "text_size")
        family = CONFIG.get("Font", "text_family")

        font_frame = Frame(font_settings)
        self.sample = Label(font_frame, text=_("Sample text"), anchor="center",
                            style="prev.TLabel", relief="groove")
        self.sample.grid(row=1, columnspan=2, padx=4, pady=6,
                         ipadx=4, ipady=4, sticky="eswn")

        self.font_family = Combobox(font_frame, values=self.fonts, width=(w * 2) // 3,
                                    exportselection=False, validate="key")
        self._validate_family = self.register(lambda *args: self._validate_font_family(self.font_family, *args))
        self._validate_size = self.register(lambda *args: self.validate_font_size(self.font_size, *args))
        self.font_family.configure(validatecommand=(self._validate_family,
                                                    "%d", "%S", "%i", "%s", "%V"))
        self.font_family.current(self.fonts.index(family))
        self.font_family.grid(row=0, column=0, padx=4, pady=4)
        self.font_size = Combobox(font_frame, values=self.sizes, width=5,
                                  exportselection=False,
                                  validate="key",
                                  validatecommand=(self._validate_size, "%d", "%P", "%V"))
        self.font_size.current(self.sizes.index(size))
        self.font_size.grid(row=0, column=1, padx=4, pady=4)

        self.update_preview()

        # --- *-- placement
        Label(font_settings,
              text=_("Title")).grid(row=0, padx=4, pady=4, sticky="w")
        fonttitle_frame.grid(row=1)
        Separator(font_settings, orient="horizontal").grid(row=2, sticky="ew", pady=10)
        Label(font_settings,
              text=_("Text")).grid(row=3, padx=4, pady=4, sticky="w")
        font_frame.grid(row=4)

        # --- * Categories
        self.category_settings = CategoryManager(self.notebook, master)
        self.notebook.add(self.category_settings, text=_("Categories"),
                          sticky="ewsn", padding=4)
        # --- * Symbols
        symbols_settings = Frame(self.notebook)
        self.notebook.add(symbols_settings, text=_("Symbols"),
                          sticky="ewsn", padding=4)
        txt_frame = Frame(symbols_settings, relief="sunken", borderwidth=1,
                          style="text.TFrame")
        self.symbols = Text(txt_frame, width=1, height=1, highlightthickness=0,
                            spacing2=5, spacing1=5, relief="flat", padx=4, pady=4,
                            font="%s %s" % (family.replace(" ", "\ "), size))
        self.symbols.insert("1.0", CONFIG.get("General", "symbols"))
        Label(symbols_settings, text=_("Available symbols")).pack(padx=4, pady=4)
        txt_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.symbols.pack(fill="both", expand=True)
        Button(symbols_settings, text=_('Reset'),
               command=self.reset_symbols).pack(padx=4, pady=4)

        # --- Ok/Cancel buttons
        Button(okcancel_frame, text="Ok",
               command=self.ok).grid(row=1, column=0, padx=4, pady=10, sticky="e")
        Button(okcancel_frame, text=_("Cancel"),
               command=self.destroy).grid(row=1, column=1, padx=4, pady=10, sticky="w")
        # --- bindings
        self.font_family.bind('<<ComboboxSelected>>', self.update_preview)
        self.font_family.bind('<Return>', self.update_preview)
        self.font_size.bind('<<ComboboxSelected>>', self.update_preview, add=True)
        self.font_size.bind('<Return>', self.update_preview, add=True)
        self.fonttitle_family.bind('<<ComboboxSelected>>', self.update_preview_title)
        self.fonttitle_size.bind('<<ComboboxSelected>>', self.update_preview_title, add=True)
        self.fonttitle_family.bind('<Return>', self.update_preview_title)
        self.fonttitle_size.bind('<Return>', self.update_preview_title, add=True)

    def reset_symbols(self):
        self.symbols.delete('1.0', 'end')
        self.symbols.insert('1.0', SYMBOLS)

    def cleanup(self):
        """Remove unused latex images."""
        self.master.cleanup()

    def validate_font_size(self, combo, d, ch, V):
        """Validation of the size entry content."""
        if d == '1':
            l = [i for i in self.sizes if i[:len(ch)] == ch]
            if l:
                i = self.sizes.index(l[0])
                combo.current(i)
                index = combo.index("insert")
                combo.selection_range(index + 1, "end")
                combo.icursor(index + 1)
            return ch.isdigit()
        else:
            return True

    def _validate_font_family(self, combo, action, modif, pos, prev_txt, V):
        """Complete the text in the entry with existing font names."""
        try:
            sel = combo.selection_get()
            txt = prev_txt.replace(sel, '')
        except TclError:
            txt = prev_txt
        if action == "0":
            txt = txt[:int(pos)] + txt[int(pos) + 1:]
            return True
        else:
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            l = [i for i in self.fonts if i[:len(txt)] == txt]
            if l:
                i = self.fonts.index(l[0])
                combo.current(i)
                index = combo.index("insert")
                combo.delete(0, "end")
                combo.insert(0, l[0].replace("\ ", " "))
                combo.selection_range(index + 1, "end")
                combo.icursor(index + 1)
                return True
            else:
                return False

    def ok(self):
        """Validate configuration."""
        family = self.font_family.get()
        if family not in self.fonts:
            l = [i for i in self.fonts if i[:len(family)] == family]
            if l:
                family = l[0]
            else:
                family = 'TkDefaultFont'
        size = self.font_size.get()
        familytitle = self.fonttitle_family.get()
        if familytitle not in self.fonts:
            l = [i for i in self.fonts if i[:len(familytitle)] == familytitle]
            if l:
                familytitle = l[0]
            else:
                familytitle = 'TkDefaultFont'
        sizetitle = self.fonttitle_size.get()
        opacity = "%i" % float(self.opacity_scale.get())
        opacity_change = opacity != CONFIG.getint("General", "opacity")
        language = REV_LANGUAGES[self.lang.get()]
        style = ""
        if self.is_bold.instate(("selected",)):
            style += "bold,"
        if self.is_italic.instate(("selected",)):
            style += "italic,"
        if self.is_underlined.instate(("selected",)):
            style += "underline,"
        if style:
            style = style[:-1]

        symbols = [l.strip() for l in self.symbols.get("1.0", "end").splitlines()]

        CONFIG.set("General", "default_category",
                   self.category_settings.default_category.get().lower())
        CONFIG.set("General", "language", language)
        CONFIG.set("General", "opacity", opacity)
        CONFIG.set("General", "position", self.position.get())
        disposition = self.titlebar_disposition.get()
        disposition_change = CONFIG.get("General", "buttons_position") != disposition
        CONFIG.set("General", "buttons_position", disposition)
        CONFIG.set("General", "symbols", "".join(symbols))
        CONFIG.set("Font", "text_size", size)
        CONFIG.set("Font", "text_family", family)
        CONFIG.set("Font", "title_family", familytitle)
        CONFIG.set("Font", "title_size", sizetitle)
        CONFIG.set("Font", "title_style", style)

        col_changes = {}
        name_changes = {}
        new_cat = False
        for cat in self.category_settings.categories:
            new_name = self.category_settings.get_name(cat)
            if cat in CONFIG.options("Categories"):
                old_color = CONFIG.get("Categories", cat)
                new_color = COLORS[self.category_settings.get_color(cat)]
                if new_name != cat:
                    name_changes[cat] = new_name
                    CONFIG.remove_option("Categories", cat)
                    CONFIG.set("Categories", new_name, new_color)
                if old_color != new_color:
                    col_changes[new_name] = (old_color, new_color)
                    CONFIG.set("Categories", new_name, new_color)

            else:
                new_cat = True
                CONFIG.set("Categories", new_name,
                           COLORS[self.category_settings.get_color(cat)])
        save_config()
        self.changes = col_changes, name_changes, new_cat, opacity_change, disposition_change
        self.destroy()

    def get_changes(self):
        return self.changes

    def translate(self):
        """Show information dialog about language change."""
        showinfo("Information",
                 _("The language setting will take effect after restarting the application"),
                 parent=self)

    def update_preview(self, event=None):
        """Update font preview."""
        family = self.font_family.get()
        size = self.font_size.get()
        self.sample.configure(font="%s %s" % (family.replace(" ", "\ "), size))

    def update_preview_title(self, event=None):
        """Update title font preview."""
        family = self.fonttitle_family.get()
        size = self.fonttitle_size.get()
        config = "%s %s" % (family.replace(" ", "\ "), size)
        if self.is_bold.instate(("selected",)):
            config += " bold"
        if self.is_italic.instate(("selected",)):
            config += " italic"
        if self.is_underlined.instate(("selected",)):
            config += " underline"
        self.sampletitle.configure(font=config)

    def display_label(self, value):
        self.opacity_label.configure(text=" {val} %".format(val=int(float(value))))

    def quit(self):
        self.destroy()
