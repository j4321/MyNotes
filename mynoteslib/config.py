#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
My Notes - Sticky notes/post-it
Copyright 2016 Juliette Monsel <j_4321@hotmail.fr>

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

from tkinter import Toplevel, PhotoImage, StringVar, Menu
from tkinter.messagebox import showinfo
from tkinter.ttk import Label, Button, Scale, Style, Separator, Combobox, Frame, Menubutton
from mynoteslib.constantes import CONFIG, LANG, save_config
from tkinter import font
_ = LANG.gettext

class Config(Toplevel):

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title(_("Configure"))
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.rowconfigure(0,weight=1)

        self._validate_size = self.register(self.validate_font_size)

        style = Style(self)
        style.theme_use("clam")
        style.configure("TScale", sliderlength=20)
        style.map("TCombobox",
                  fieldbackground=[('readonly','white')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', 'black')])
        style.configure("prev.TLabel", background="white")

        # Font
        Label(self, text=_("Font")).grid(row=0, sticky="w", padx=4, pady=4)
        font_frame = Frame(self)
        font_frame.grid(row=1, columnspan=2)
        self.sample = Label(font_frame, text = _("Sample text"), anchor="center",
                            style="prev.TLabel", relief="groove")
        self.sample.grid(row=1, columnspan=2, padx=4, pady=6,
                         ipadx=4, ipady=4, sticky="eswn")
        self.fonts = list(set(font.families())) + ["TkDefaultFont"]
        self.fonts.sort()
        w = max([len(f) for f in self.fonts])
        self.sizes = ["%i" % i for i in (list(range(6,17)) + list(range(18,32,2)))]

        self.font_family = Combobox(font_frame, values=self.fonts, width=(w*2)//3,
                                    exportselection=False,
                                    state="readonly")
        self.font_family.current(self.fonts.index(CONFIG.get("Font", "family")))
        self.font_family.grid(row=0, column=0, padx=4, pady=4)
        self.font_size = Combobox(font_frame, values=self.sizes, width=5,
                                  exportselection=False,
                                  validate="key",
                                  validatecommand=(self._validate_size, "%d", "%P", "%V"))
        self.font_size.current(self.sizes.index(CONFIG.get("Font", "size")))
        self.font_size.grid(row=0, column=1, padx=4, pady=4)

        Separator(self, orient="horizontal").grid(row=2, columnspan=2, sticky="ew", pady=10)

        # Opacity
        Label(self, text=_("Opacity")).grid(row=3, sticky="w", padx=4, pady=4)
        self.opacity_scale = Scale(self, orient="horizontal", length=200,
                                   from_=0, to=100, value=CONFIG.get("General", "opacity"),
                                   command=self.display_label)
        self.opacity_label = Label(self, text=" {val} %".format(val=self.opacity_scale.get()))
        self.opacity_scale.grid(row=4, columnspan=2, padx=4, pady=(4,10))
        self.opacity_label.place(in_=self.opacity_scale, relx=1, rely=0.5,anchor="w", bordermode="outside")

        Separator(self, orient="horizontal").grid(row=5, columnspan=2, sticky="ew", pady=10)


        lang = {"fr":"Français", "en":"English"}
        self.lang = StringVar(self, lang[CONFIG.get("General","language")])
        lang_frame = Frame(self)
        lang_frame.grid(row=6, columnspan=2, sticky="w")
        Label(lang_frame, text=_("Language")).grid(row=0, sticky="w", padx=4, pady=4)
        menu_lang = Menu(lang_frame, tearoff=False)
        Menubutton(lang_frame, menu=menu_lang, width=9,
                   textvariable=self.lang).grid(row=0, column=1, padx=8, pady=4)
        menu_lang.add_radiobutton(label="English", value="English",
                                  variable=self.lang, command=self.translate)
        menu_lang.add_radiobutton(label="Français", value="Français",
                                  variable=self.lang, command=self.translate)

        Separator(self, orient="horizontal").grid(row=7, columnspan=2, sticky="ew", pady=10)

        frame = Frame(self)
        frame.grid(row=8, columnspan=2)
        Button(frame, text="Ok", command=self.ok).grid(row=1, column=0,
                                                       padx=8, pady=4)
        Button(frame, text=_("Cancel"),  command=self.destroy).grid(row=1, column=1,
                                                                    padx=4, pady=4)

        self.font_family.bind('<<ComboboxSelected>>', self.update_preview)
        self.font_size.bind('<<ComboboxSelected>>', self.update_preview, add=True)

    def validate_font_size(self, d, ch, V):
        ''' Validation of the size entry content '''
        l = [i for i in self.sizes if i[:len(ch)] == ch]
        if l:
            i = self.sizes.index(l[0])
            self.font_size.current(i)
        if d == '1':
            return ch.isdigit()
        else:
            return True

    def ok(self):
        family = self.font_family.get()
        size = self.font_size.get()
        opacity = "%i" % float(self.opacity_scale.get())
        language = self.lang.get().lower()[2:]
        CONFIG.set("General", "language", language)
        CONFIG.set("General", "opacity", opacity)
        CONFIG.set("Font", "family", family)
        CONFIG.set("Font", "size", size)
        save_config()
        self.destroy()

    def translate(self):
        showinfo("Information",
                 _("The language setting will take effect after restarting the application"),
                parent=self)

    def update_preview(self, event):
        family = self.font_family.get()
        size = self.font_size.get()
        self.sample.configure(font= "%s %s" % (family.replace(" ", "\ "), size))

    def display_label(self, value):
        self.opacity_label.configure(text= " {val} %".format(val=int(float(value))))

    def quit(self):
        self.destroy()

#if __name__ == "__main__":
  #  from tkinter import Tk
  #  fen = Tk()
  #  c = Config(fen)
  #  fen.mainloop()
