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


Configuration Window
"""


from tkinter import Toplevel, StringVar, Menu, Text, BooleanVar
from mynoteslib.messagebox import showinfo
from mynoteslib.autocomplete import AutoCompleteCombobox
from tkinter.ttk import Label, Radiobutton, Button, Style, Separator
from tkinter.ttk import Notebook, Combobox, Frame, Menubutton, Checkbutton
from mynoteslib.constants import CONFIG, save_config, COLORS, SYMBOLS,\
    LANGUAGES, REV_LANGUAGES, TOOLKITS, AUTOCORRECT
from mynoteslib.autoscrollbar import AutoScrollbar
from .categories import CategoryManager
from .autocorrect import AutoCorrectConfig
from .opacity import OpacityFrame
from tkinter import font
from time import strftime


class Config(Toplevel):
    """Config dialog."""
    def __init__(self, master):
        """Create Config dialog."""
        Toplevel.__init__(self, master, class_='MyNotes')
        self.title(_("Preferences"))
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.changes = {}, {}, False
        self.minsize(width=430, height=450)

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
        okcancel_frame.pack(fill="x", side='bottom')
        self.notebook.pack(expand=True, fill="both")

        # --- * General settings
        self._init_general()

        # --- * Font settings
        self._init_font()

        # --- * Categories
        self.category_settings = CategoryManager(self.notebook, master)
        self.notebook.add(self.category_settings, text=_("Categories"),
                          sticky="ewsn", padding=4)
        # --- * Symbols
        size = CONFIG.get("Font", "text_size")
        family = CONFIG.get("Font", "text_family")
        symbols_settings = Frame(self.notebook, padding=4)
        self.notebook.add(symbols_settings, text=_("Symbols"),
                          sticky="ewsn", padding=4)
        txt_frame = Frame(symbols_settings, relief="sunken", borderwidth=1,
                          style="text.TFrame")
        txt_frame.rowconfigure(0, weight=1)
        txt_frame.columnconfigure(0, weight=1)
        self.symbols = Text(txt_frame, width=1, height=1, highlightthickness=0,
                            spacing2=5, spacing1=5, relief="flat", padx=4, pady=4,
                            font="%s %s" % (family.replace(" ", "\ "), size))
        scroll_y = AutoScrollbar(txt_frame, orient='vertical',
                                 command=self.symbols.yview)
        self.symbols.configure(yscrollcommand=scroll_y.set)

        self.symbols.insert("1.0", CONFIG.get("General", "symbols"))
        Label(symbols_settings, text=_("Available symbols")).pack(padx=4, pady=4)
        txt_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.symbols.grid(sticky='ewns')
        scroll_y.grid(row=0, column=1, sticky='ns')
        Button(symbols_settings, text=_('Reset'),
               command=self.reset_symbols).pack(padx=4, pady=4)

        # --- * AutoCorrect
        self.autocorrect_settings = AutoCorrectConfig(self.notebook, master)
        self.notebook.add(self.autocorrect_settings, text=_("AutoCorrect"),
                          sticky="ewsn", padding=4)

        # --- Ok/Cancel buttons
        Button(okcancel_frame, text="Ok",
               command=self.ok).grid(row=1, column=0, padx=4, pady=10, sticky="e")
        Button(okcancel_frame, text=_("Cancel"),
               command=self.destroy).grid(row=1, column=1, padx=4, pady=10, sticky="w")
        # --- bindings
        self.font_family.bind('<<ComboboxSelected>>', self.update_preview)
        self.font_family.bind('<Return>', self.update_mono_preview)
        self.mono_family.bind('<<ComboboxSelected>>', self.update_preview)
        self.mono_family.bind('<Return>', self.update_mono_preview)
        self.font_size.bind('<<ComboboxSelected>>', self.update_preview, add=True)
        self.font_size.bind('<Return>', self.update_preview, add=True)
        self.fonttitle_family.bind('<<ComboboxSelected>>', self.update_preview_title)
        self.fonttitle_size.bind('<<ComboboxSelected>>', self.update_preview_title, add=True)
        self.fonttitle_family.bind('<Return>', self.update_preview_title)
        self.fonttitle_size.bind('<Return>', self.update_preview_title, add=True)

    def _init_general(self):
        general_settings = Frame(self.notebook, padding=4)
        general_settings.columnconfigure(0, weight=1)
        self.notebook.add(general_settings, text=_("General"),
                          sticky="ewsn", padding=4)

        # ---- language

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
        # ---- gui toolkit
        self.gui = StringVar(self, CONFIG.get("General", "trayicon").capitalize())
        gui_frame = Frame(general_settings)
        Label(gui_frame,
              text=_("GUI Toolkit for the system tray icon")).grid(row=0, column=0,
                                                                   padx=4, pady=4,
                                                                   sticky="w")
        menu_gui = Menu(gui_frame, tearoff=False)
        Menubutton(gui_frame, menu=menu_gui, width=9,
                   textvariable=self.gui).grid(row=0, column=1,
                                               padx=4, pady=4, sticky="w")
        for toolkit, b in TOOLKITS.items():
            if b:
                menu_gui.add_radiobutton(label=toolkit.capitalize(),
                                         value=toolkit.capitalize(),
                                         variable=self.gui,
                                         command=self.change_gui)
        # ---- opacity
        self.opacity = OpacityFrame(general_settings,
                                    CONFIG.getint("General", "opacity"))
        # ---- position
        frame_position = Frame(general_settings)
        self.position = StringVar(self, CONFIG.get("General", "position"))
        Label(frame_position,
              text=_("Default position of the notes")).grid(row=0,
                                                            columnspan=3,
                                                            sticky="w",
                                                            padx=4, pady=4)
        Radiobutton(frame_position, text=_("Always above"), value="above",
                    variable=self.position).grid(row=1, column=0, padx=4)
        Radiobutton(frame_position, text=_("Always below"), value="below",
                    variable=self.position).grid(row=1, column=1, padx=4)
        Radiobutton(frame_position, text=_("Normal"), value="normal",
                    variable=self.position).grid(row=1, column=2, padx=4)
        # ---- titlebar
        self.titlebar_disposition = StringVar(self, CONFIG.get("General",
                                                               "buttons_position"))
        self.title_var = StringVar(self)  # to add date if date_in_title is true
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
                    variable=self.titlebar_disposition).grid(row=1, column=0, padx=4)
        right = Frame(frame_titlebar, style="titlebar.TFrame")
        right.grid(row=1, column=1, sticky="ew", padx=4)

        def select_right(event):
            self.titlebar_disposition.set("right")

        Label(right, textvariable=self.title_var, style="titlebar.TLabel",
              anchor="center", font=font_title).pack(side="left", fill="x", expand=True)
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
        Label(left, textvariable=self.title_var, style="titlebar.TLabel",
              anchor="center", font=font_title).pack(side="right", fill="x", expand=True)
        for ch in left.children.values():
            ch.bind("<Button-1>", select_left)

        self.date_in_title = BooleanVar(self, CONFIG.getboolean('General', 'date_in_title', fallback=True))
        date_in_title = Checkbutton(frame_titlebar, variable=self.date_in_title,
                                    text=_('Display creation date in title'),
                                    command=self.toggle_date)
        date_in_title.grid(row=2, columnspan=4, sticky='w', pady=4, padx=4)
        self.toggle_date()
        # ---- placement
        lang_frame.grid(sticky="w")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        gui_frame.grid(sticky="w")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        # opacity_frame.grid(sticky='w')
        self.opacity.grid(sticky='w', padx=4)
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        frame_position.grid(sticky="ew")
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        frame_titlebar.grid(sticky="ew", pady=4)

        # ---- clean local data
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        Button(general_settings,
               text=_('Delete unused local data'),
               command=self.cleanup).grid(padx=4, pady=4, sticky='w')

        # ---- splash supported
        Separator(general_settings,
                  orient="horizontal").grid(sticky="ew", pady=10)
        self.splash_support = Checkbutton(general_settings,
                                          text=_("Check this box if the notes disappear when you click"))
        self.splash_support.grid(padx=4, pady=4, sticky='w')
        if not CONFIG.getboolean('General', 'splash_supported', fallback=True):
            self.splash_support.state(('selected', '!alternate'))
        else:
            self.splash_support.state(('!selected', '!alternate'))

    def _init_font(self):
        font_settings = Frame(self.notebook, padding=4)
        font_settings.columnconfigure(1, weight=1)
        self.notebook.add(font_settings, text=_("Font"),
                          sticky="ewsn", padding=4)

        # ---- title
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

        self.fonttitle_family = AutoCompleteCombobox(fonttitle_frame, values=self.fonts,
                                                     width=(w * 2) // 3,
                                                     exportselection=False)
        self._validate_title_size = self.register(lambda *args: self.validate_font_size(self.fonttitle_size, *args))
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

        # ---- text
        size = CONFIG.get("Font", "text_size")
        family = CONFIG.get("Font", "text_family")

        font_frame = Frame(font_settings)
        self.sample = Label(font_frame, text=_("Sample text"), anchor="center",
                            style="prev.TLabel", relief="groove")
        self.sample.grid(row=1, columnspan=2, padx=4, pady=6,
                         ipadx=4, ipady=4, sticky="eswn")

        self.font_family = AutoCompleteCombobox(font_frame, values=self.fonts,
                                                width=(w * 2) // 3,
                                                exportselection=False)
        self._validate_size = self.register(lambda *args: self.validate_font_size(self.font_size, *args))
        self.font_family.current(self.fonts.index(family))
        self.font_family.grid(row=0, column=0, padx=4, pady=4)
        self.font_size = Combobox(font_frame, values=self.sizes, width=5,
                                  exportselection=False,
                                  validate="key",
                                  validatecommand=(self._validate_size, "%d", "%P", "%V"))
        self.font_size.current(self.sizes.index(size))
        self.font_size.grid(row=0, column=1, padx=4, pady=4)

        # ---- mono
        self.mono_fonts = [f for f in self.fonts if 'Mono' in f]
        mono_family = CONFIG.get("Font", "mono")

        mono_frame = Frame(font_settings)
        self.sample_mono = Label(mono_frame, text=_("Mono text"), anchor="center",
                                 style="prev.TLabel", relief="groove")
        self.sample_mono.grid(row=1, columnspan=2, padx=4, pady=6,
                              ipadx=4, ipady=4, sticky="eswn")

        self.mono_family = AutoCompleteCombobox(mono_frame, values=self.mono_fonts,
                                                width=(w * 2) // 3,
                                                exportselection=False)
        self.mono_family.current(self.mono_fonts.index(mono_family))
        self.mono_family.grid(row=0, column=0, padx=4, pady=4)

        # ---- placement
        Label(font_settings,
              text=_("Title")).grid(row=0, column=0, padx=4, pady=4, sticky="nw")
        fonttitle_frame.grid(row=0, column=1, sticky="w", padx=20)
        Separator(font_settings, orient="horizontal").grid(row=1, columnspan=2,
                                                           sticky="ew", pady=10)
        Label(font_settings,
              text=_("Text")).grid(row=2, column=0, padx=4, pady=4, sticky="nw")
        font_frame.grid(row=2, column=1, sticky="w", padx=20)
        Separator(font_settings, orient="horizontal").grid(row=3, columnspan=2,
                                                           sticky="ew", pady=10)
        Label(font_settings,
              text=_("Mono")).grid(row=4, column=0, padx=4, pady=4, sticky="nw")
        mono_frame.grid(row=4, column=1, sticky="w", padx=20)
        self.update_preview()
        self.update_preview_title()

    def reset_symbols(self):
        self.symbols.delete('1.0', 'end')
        self.symbols.insert('1.0', SYMBOLS)

    def toggle_date(self):
        if self.date_in_title.get():
            self.title_var.set('{} - {}'.format(_('Title'), strftime('%x')))
        else:
            self.title_var.set(_('Title'))

    def cleanup(self):
        """Remove unused local data and latex images."""
        self.master.cleanup()
        showinfo(_('Information'), _('Unused local data have been cleaned up.'))

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

    def ok(self):
        """Validate configuration."""
        # --- font
        # mono
        mono = self.mono_family.get()
        if mono not in self.fonts:
            l = [i for i in self.fonts if i[:len(mono)] == mono]
            if l:
                family = l[0]
            else:
                family = 'TkDefaultFont'
        # text family
        family = self.font_family.get()
        if family not in self.fonts:
            l = [i for i in self.fonts if i[:len(family)] == family]
            if l:
                family = l[0]
            else:
                family = 'TkDefaultFont'
        # text size
        size = self.font_size.get()
        try:
            int(size)
        except ValueError:
            size = CONFIG.get("Font", "text_size")
        # title family
        familytitle = self.fonttitle_family.get()
        if familytitle not in self.fonts:
            l = [i for i in self.fonts if i[:len(familytitle)] == familytitle]
            if l:
                familytitle = l[0]
            else:
                familytitle = 'TkDefaultFont'
        # title size
        sizetitle = self.fonttitle_size.get()
        try:
            int(sizetitle)
        except ValueError:
            sizetitle = CONFIG.get("Font", "title_size")
        # title style
        style = ""
        if self.is_bold.instate(("selected",)):
            style += "bold,"
        if self.is_italic.instate(("selected",)):
            style += "italic,"
        if self.is_underlined.instate(("selected",)):
            style += "underline,"
        if style:
            style = style[:-1]

        # --- opacity
        opacity = "%i" % self.opacity.get()

        # --- language
        language = REV_LANGUAGES[self.lang.get()]

        # --- symbols
        symbols = [l.strip() for l in self.symbols.get("1.0", "end").splitlines()]

        # --- autocorrect
        self.autocorrect_settings.ok()
        autocorrect = "\t".join(["%s %s" % (key, val) for key, val in AUTOCORRECT.items()])

        # --- update CONFIG
        CONFIG.set("General", "default_category",
                   self.category_settings.default_category.get().lower())
        CONFIG.set("General", "language", language)
        CONFIG.set("General", "opacity", opacity)
        CONFIG.set("General", "position", self.position.get())
        CONFIG.set("General", "buttons_position", self.titlebar_disposition.get())
        CONFIG.set("General", "date_in_title", str(self.date_in_title.get()))
        CONFIG.set("General", "symbols", "".join(symbols))
        CONFIG.set("General", "trayicon", self.gui.get().lower())
        CONFIG.set("General", "autocorrect", autocorrect)
        CONFIG.set('General', 'splash_supported', str(not self.splash_support.instate(('selected',))))

        CONFIG.set("Font", "text_size", size)
        CONFIG.set("Font", "text_family", family)
        CONFIG.set("Font", "title_family", familytitle)
        CONFIG.set("Font", "title_size", sizetitle)
        CONFIG.set("Font", "title_style", style)
        CONFIG.set("Font", "mono", mono)

        # --- notes config
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
        self.changes = col_changes, name_changes, new_cat
        self.destroy()

    def get_changes(self):
        return self.changes

    def translate(self):
        """Show information dialog about language change."""
        showinfo(_("Information"),
                 _("The language setting will take effect after restarting the application"),
                 parent=self)

    def change_gui(self):
        """Show information dialog about gui toolkit change."""
        showinfo("Information",
                 _("The GUI Toolkit setting will take effect after restarting the application"),
                 parent=self)

    def update_preview(self, event=None):
        """Update font preview."""
        family = self.font_family.get()
        size = self.font_size.get()
        self.sample.configure(font="%s %s" % (family.replace(" ", "\ "), size))
        self.update_mono_preview()

    def update_mono_preview(self, event=None):
        """Update mono font preview."""
        family = self.mono_family.get()
        size = self.font_size.get()
        self.sample_mono.configure(font="%s %s" % (family.replace(" ", "\ "), size))

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
