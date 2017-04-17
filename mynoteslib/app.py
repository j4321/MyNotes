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


Main class
"""

from tkinter import Tk, PhotoImage, Menu, Toplevel, TclError
from tkinter.ttk import Style, Label, Checkbutton, Button, Entry
import os, re
from shutil import copy
import pickle
from mynoteslib import tktray
from mynoteslib.constantes import CONFIG, PATH_DATA, PATH_DATA_BACKUP, LOCAL_PATH
from mynoteslib.constantes import backup, asksaveasfilename, askopenfilename
import mynoteslib.constantes as cst
from mynoteslib.config import Config
from mynoteslib.export import Export
from mynoteslib.sticky import Sticky
from mynoteslib.about import About
from mynoteslib.version_check import UpdateChecker
from mynoteslib.messagebox import showerror, showinfo, askokcancel
import ewmh


class App(Tk):
    """ Main app: put an icon in the system tray with a right click menu to
        create notes ... """
    def __init__(self):
        Tk.__init__(self)
        self.withdraw()
        self.notes = {}
        self.img = PhotoImage(file=cst.IM_ICON)
        self.icon = PhotoImage(master=self, file=cst.IM_ICON_48)
        self.iconphoto(True, self.icon)

        self.ewmh = ewmh.EWMH()

        style = Style(self)
        style.theme_use("clam")

        self.close1 = PhotoImage("img_close", file=cst.IM_CLOSE)
        self.close2 = PhotoImage("img_closeactive", file=cst.IM_CLOSE_ACTIVE)
        self.roll1 = PhotoImage("img_roll", file=cst.IM_ROLL)
        self.roll2 = PhotoImage("img_rollactive", file=cst.IM_ROLL_ACTIVE)

        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.icon = tktray.Icon(self, docked=True)

        ### Menu
        self.menu_notes = Menu(self.icon.menu, tearoff=False)
        self.hidden_notes = {}
        self.menu_show_cat = Menu(self.icon.menu, tearoff=False)
        self.menu_hide_cat = Menu(self.icon.menu, tearoff=False)
        self.icon.configure(image=self.img)
        self.icon.menu.add_command(label=_("New Note"), command=self.new)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('Show All'),
                                   command=self.show_all)
        self.icon.menu.add_cascade(label=_('Show Category'),
                                   menu=self.menu_show_cat)
        self.icon.menu.add_cascade(label=_('Show Note'), menu=self.menu_notes,
                                   state="disabled")
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('Hide All'),
                                   command=self.hide_all)
        self.icon.menu.add_cascade(label=_('Hide Category'),
                                   menu=self.menu_hide_cat)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Preferences"),
                                   command=self.config)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Backup Notes"), command=self.backup)
        self.icon.menu.add_command(label=_("Restore Backup"), command=self.restore)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Export"), command=self.export_notes)
        self.icon.menu.add_command(label=_("Import"), command=self.import_notes)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('Check for Updates'),
                                   command=lambda: UpdateChecker(self))
        self.icon.menu.add_command(label=_('About'), command=lambda: About(self))
        self.icon.menu.add_command(label=_('Quit'), command=self.quit)

        ### Restore notes
        self.note_data = {}
        if os.path.exists(PATH_DATA):
            with open(PATH_DATA, "rb") as fich:
                dp = pickle.Unpickler(fich)
                note_data = dp.load()
                for i, key in enumerate(note_data):
                    self.note_data["%i" % i] = note_data[key]
            backup()
            for key in self.note_data:
                data = self.note_data[key]
                cat = data["category"]
                if not CONFIG.has_option("Categories", cat):
                    CONFIG.set("Categories", cat, data["color"])
                if data["visible"]:
                    self.notes[key] = Sticky(self, key, **data)
                else:
                    title = self.menu_notes_title(data["title"])
                    self.hidden_notes[key] = title
                    self.menu_notes.add_command(label=title,
                                                command=lambda nb=key: self.show_note(nb))
                    self.icon.menu.entryconfigure(4, state="normal")
        self.nb = len(self.note_data)
        self.update_menu()
        self.update_notes()
        self.make_notes_sticky()

        # newline depending on mode
        self.bind_class("Text", "<Return>",  self.insert_newline)
        # char deletion taking into account list type
        self.bind_class("Text", "<BackSpace>",  self.delete_char)
        # change Ctrl+A to select all instead of go to the beginning of the line
        self.bind_class('Text', '<Control-a>', self.select_all_text)
        self.bind_class('TEntry', '<Control-a>', self.select_all_entry)
        # bind Ctrl+Y to redo
        self.bind_class('Text', '<Control-y>', self.redo_event)

        # check for updates
        if CONFIG.getboolean("General", "check_update"):
            UpdateChecker(self)

    ### class bindings
    def redo_event(self, event):
        try:
            event.widget.edit_redo()
        except TclError:
            # nothing to redo
            pass

    def select_all_entry(self, event):
        event.widget.selection_range(0, "end")

    def select_all_text(self, event):
        event.widget.tag_add("sel","1.0","end")

    def delete_char(self, event):
        txt = event.widget
        deb_line = txt.get("insert linestart", "insert")
        tags = txt.tag_names("insert")
        if txt.tag_ranges("sel"):
            if txt.tag_nextrange("enum", "sel.first", "sel.last"):
                update = True
            else:
                update = False
            txt.delete("sel.first", "sel.last")
            if update:
                txt.master.update_enum()
        elif txt.index("insert") != "1.0":
            if re.match('^\t[0-9]+\.\t$', deb_line) and 'enum' in tags:
                txt.delete("insert linestart", "insert")
                txt.master.update_enum()
            elif deb_line == "\t•\t" and 'list' in tags:
                txt.delete("insert linestart", "insert")
                txt.insert("insert", "\t\t")
            elif deb_line == "\t\t":
                txt.delete("insert linestart", "insert")
            else:
                txt.delete("insert-1c")

    def insert_newline(self, event):
        mode = event.widget.master.mode.get()
        if mode == "list":
            event.widget.insert("insert", "\n\t•\t")
            event.widget.tag_add("list", "1.0", "end")
        elif mode == "todolist":
            event.widget.insert("insert", "\n")
            ch = Checkbutton(event.widget, style=event.widget.master.id + ".TCheckbutton")
            event.widget.window_create("insert", window=ch)
            event.widget.tag_add("todolist", "1.0", "end")
        elif mode == "enum":
            event.widget.configure(autoseparators=False)
            event.widget.edit_separator()
            event.widget.insert("insert", "\n\t0.\t")
#            event.widget.tag_add("enum", "1.0", "end")
            event.widget.master.update_enum()
            event.widget.edit_separator()
            event.widget.configure(autoseparators=True)
        else:
            event.widget.insert("insert", "\n")

    def make_notes_sticky(self):
        for w in self.ewmh.getClientList():
            if w.get_wm_name()[:7] == 'mynotes':
                self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
        self.ewmh.display.flush()

    def menu_notes_title(self, note_title):
        """
            Return the title to display in the Show note submenu for the note
            whose title is note_title. The title returned will be 'note_title'
            if only this note has this title in the menu. Otherwise, it will
            be 'note_title ~#n', if it is the n-th note with this title.
        """
        end = self.menu_notes.index("end")
        if end is not None:
            # le menu n'est pas vide
            titles = self.hidden_notes.values()
            titles = [t for t in titles if t.split(" ~#")[0] == note_title]
            if titles:
                return "%s ~#%i" % (note_title, len(titles) + 1)
            else:
                return note_title
        else:
            return note_title

    def backup(self):
        """ create a backup at the location indicated by user """
        initialdir, initialfile = os.path.split(PATH_DATA_BACKUP % 0)
        fichier = asksaveasfilename(defaultextension=".backup",
                                    filetypes=[],
                                    initialdir=initialdir,
                                    initialfile="notes.backup0",
                                    title=_('Backup Notes'))
        if fichier:
            with open(fichier, "wb") as fich:
                dp = pickle.Pickler(fich)
                dp.dump(self.note_data)

    def restore(self, fichier=None, confirmation=True):
        """ restore notes from backup """
        if confirmation:
            rep = askokcancel(_("Warning"),
                              _("Restoring a backup will erase the current notes."),
                              icon="warning")
        else:
            rep = True
        if rep:
            if fichier is None:
                fichier = askopenfilename(defaultextension=".backup",
                                          filetypes=[],
                                          initialdir=LOCAL_PATH,
                                          initialfile="",
                                          title=_('Restore Backup'))
            if fichier:
                try:
                    if not os.path.samefile(fichier, PATH_DATA):
                        copy(fichier, PATH_DATA)
                    self.show_all()
                    keys = list(self.notes.keys())
                    for key in keys:
                        self.notes[key].delete(confirmation=False)
                    with open(PATH_DATA, "rb") as fich:
                        dp = pickle.Unpickler(fich)
                        note_data = dp.load()
                    for i, key in enumerate(note_data):
                        data = note_data[key]
                        note_id = "%i" % i
                        self.note_data[note_id] = data
                        cat = data["category"]
                        if not CONFIG.has_option("Categories", cat):
                            CONFIG.set("Categories", cat, data["color"])
                        if data["visible"]:
                            self.notes[note_id] = Sticky(self, key, **data)
                        else:
                            title = self.menu_notes_title(data["title"])
                            self.hidden_notes[note_id] = title
                            self.menu_notes.add_command(label=title,
                                                        command=lambda nb=note_id: self.show_note(nb))
                            self.icon.menu.entryconfigure(4, state="normal")
                    self.nb = len(self.note_data)
                    self.update_menu()
                    self.update_notes()
                except FileNotFoundError:
                    showerror(_("Error"), _("The file {filename} does not exists.").format(filename=fichier))

    def show_all(self):
        """ Show all notes """
        keys = list(self.hidden_notes.keys())
        for key in keys:
            self.show_note(key)

    def show_cat(self, category):
        """ Show all notes belonging to category """
        keys = list(self.hidden_notes.keys())
        for key in keys:
            if self.note_data[key]["category"] == category:
                self.show_note(key)

    def hide_all(self):
        """ Hide all notes """
        keys = list(self.notes.keys())
        for key in keys:
            self.notes[key].hide()

    def hide_cat(self, category):
        """ Hide all notes belonging to category """
        keys = list(self.notes.keys())
        for key in keys:
            if self.note_data[key]["category"] == category:
                self.notes[key].hide()

    def config(self):
        """ Launch the setting manager """
        conf = Config(self)
        self.wait_window(conf)
        changes = conf.get_changes()
        if changes is not None:
            self.update_notes()
            self.update_menu()
            self.update_cat_colors(changes)
            alpha = CONFIG.getint("General", "opacity")/100
            for note in self.notes.values():
                note.attributes("-alpha", alpha)
                note.update_title_font()
                note.update_text_font()
                note.update_titlebar()

    def delete_cat(self, category):
        """ Delete all notes belonging to category """
        keys = list(self.notes.keys())
        for key in keys:
            if self.note_data[key]["category"] == category:
                self.notes[key].delete(confirmation=False)

    def show_note(self, nb):
        """ Display the note corresponding to the 'nb' key in self.note_data """
        self.note_data[nb]["visible"] = True
        index = self.menu_notes.index(self.hidden_notes[nb])
        del(self.hidden_notes[nb])
        self.notes[nb] = Sticky(self, nb, **self.note_data[nb])
        self.menu_notes.delete(index)
        if self.menu_notes.index("end") is None:
            # the menu is empty
            self.icon.menu.entryconfigure(4, state="disabled")
        self.make_notes_sticky()

    def update_notes(self):
        """ Update the notes after changes in the categories """
        categories = CONFIG.options("Categories")
        categories.sort()
        for key in self.note_data:
            if not self.note_data[key]["category"] in categories:
                default = CONFIG.get("General", "default_category")
                default_color = CONFIG.get("Categories", default)
                if self.note_data[key]["visible"]:
                    self.notes[key].change_category(default)
                self.note_data[key]["category"] = default
                self.note_data[key]["color"] = default_color
        for note in self.notes.values():
            note.update_menu_cat(categories)
        self.save()

    def update_cat_colors(self, changes):
        """ Default color of the categories was changed, so change the color of the
            notes belonging to this category if they were of the default color
            changes = {category: (old_color, new_color)}
        """
        for key in self.note_data:
            if self.note_data[key]["category"] in changes:
                old_color, new_color = changes[self.note_data[key]["category"]]
                if self.note_data[key]["color"] == old_color:
                    self.note_data[key]["color"] = new_color
                    if self.note_data[key]["visible"]:
                        self.notes[key].change_color(cst.INV_COLORS[new_color])

    def update_menu(self):
        """ Populate self.menu_show_cat and self.menu_hide_cat with the categories """
        self.menu_hide_cat.delete(0, "end")
        self.menu_show_cat.delete(0, "end")
        categories = CONFIG.options("Categories")
        categories.sort()
        for cat in categories:
            self.menu_show_cat.add_command(label=cat.capitalize(),
                                           command=lambda c=cat: self.show_cat(c))
            self.menu_hide_cat.add_command(label=cat.capitalize(),
                                           command=lambda c=cat: self.hide_cat(c))

    def save(self):
        """ Save the data """
        with open(PATH_DATA, "wb") as fich:
            dp = pickle.Pickler(fich)
            dp.dump(self.note_data)

    def new(self):
        """ Create a new note """
        key = "%i" % self.nb
        self.notes[key] = Sticky(self, key)
        data = self.notes[key].save_info()
        data["visible"] = True
        self.note_data[key] = data
        self.nb += 1
        self.make_notes_sticky()

    def export_notes(self):
        export = Export(self)
        self.wait_window(export)
        categories_to_export, only_visible = export.get_export()
        if categories_to_export:
            initialdir, initialfile = os.path.split(PATH_DATA_BACKUP % 0)
            fichier = asksaveasfilename(defaultextension=".notes",
                                        filetypes=[(_("Notes (.notes)"), "*.notes"),
                                                   (_("HTML file (.html)"), "*.html"),
                                                   (_("Text file (.txt)"), "*.txt"),
                                                   (_("All files"), "*")],
                                        initialdir=initialdir,
                                        initialfile="",
                                        title=_('Export Notes As'))
            if fichier:
                if os.path.splitext(fichier)[-1] == ".txt":
    ### txt export
                    # export notes to .txt: all formatting is lost
                    cats = {cat: [] for cat in categories_to_export}
                    for key in self.note_data:
                        cat = self.note_data[key]["category"]
                        if cat in cats and ((not only_visible) or self.note_data[key]["visible"]):
                            cats[cat].append((self.note_data[key]["title"],
                                              cst.note_to_txt(self.note_data[key])))
                    text = ""
                    for cat in cats:
                        cat_txt = _("Category: {category}").format(category=cat) + "\n"
                        text += cat_txt
                        text += "="*len(cat_txt)
                        text += "\n\n"
                        for title, txt in cats[cat]:
                            text += title
                            text += "\n"
                            text += "-"*len(title)
                            text += "\n\n"
                            text += txt
                            text += "\n\n"
                            text += "-"*30
                            text += "\n\n"
                        text += "#"*30
                        text += "\n\n"
                    with open(fichier, "w") as fich:
                        fich.write(text)

                elif os.path.splitext(fichier)[-1] == ".html":
    ### html export
                    cats = {cat: [] for cat in categories_to_export}
                    for key in self.note_data:
                        cat = self.note_data[key]["category"]
                        if cat in cats and ((not only_visible) or self.note_data[key]["visible"]):
                            cats[cat].append((self.note_data[key]["title"],
                                              cst.note_to_html(self.note_data[key], self)))
                    text = ""
                    for cat in cats:
                        cat_txt = "<h1 style='text-align:center'>" + _("Category: {category}").format(category=cat) + "<h1/>\n"
                        text += cat_txt
                        text += "<br>"
                        for title, txt in cats[cat]:
                            text += "<h2 style='text-align:center'>%s</h2>\n" % title
                            text += txt
                            text += "<br>\n"
                            text += "<hr />"
                            text += "<br>\n"
                        text += '<hr style="height: 8px;background-color:grey" />'
                        text += "<br>\n"
                    with open(fichier, "w") as fich:
                        fich.write('<body style="max-width:30em">\n')
                        fich.write(text)
                        fich.write("\n</body>")

                else:
    ### pickle export
                    note_data = {}
                    for key in self.note_data:
                        if self.note_data[key]["category"] in categories_to_export:
                            if (not only_visible) or self.note_data[key]["visible"]:
                                note_data[key] = self.note_data[key]

                    with open(fichier, "wb") as fich:
                        dp = pickle.Pickler(fich)
                        dp.dump(note_data)

    def import_notes(self):
        fichier = askopenfilename(defaultextension=".backup",
                                  filetypes=[(_("Notes (.notes)"), "*.notes"),
                                             (_("All files"), "*")],
                                  initialdir=LOCAL_PATH,
                                  initialfile="",
                                  title=_('Import'))
        if fichier:
            try:
                with open(fichier, "rb") as fich:
                    dp = pickle.Unpickler(fich)
                    note_data = dp.load()
                for i, key in enumerate(note_data):
                    data = note_data[key]
                    note_id = "%i" % (i + self.nb)
                    self.note_data[note_id] = data
                    cat = data["category"]
                    if not CONFIG.has_option("Categories", cat):
                        CONFIG.set("Categories", cat, data["color"])
                    if data["visible"]:
                        self.notes[note_id] = Sticky(self, note_id, **data)
                    else:
                        title = self.menu_notes_title(data["title"])
                        self.hidden_notes[note_id] = title
                        self.menu_notes.add_command(label=title,
                                                    command=lambda nb=note_id: self.show_note(nb))
                        self.icon.menu.entryconfigure(4, state="normal")
                self.nb = len(self.note_data)
                self.update_menu()
                self.update_notes()
            except Exception as e:
                message = _("The file {file} is not a valid .notes file.").format(file=fichier)
                showerror(_("Error"), message + "\n" + str(e))

    def quit(self):
        self.destroy()
