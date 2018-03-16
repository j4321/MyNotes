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


Main class
"""

from tkinter import Tk, TclError
from tkinter import PhotoImage as tkPhotoImage
from tkinter.ttk import Style
from tkinter.font import families
from PIL import Image
from PIL.ImageTk import PhotoImage
import os
import re
import traceback
from shutil import copy
import pickle
from mynoteslib.trayicon import TrayIcon, SubMenu
from mynoteslib.constantes import CONFIG, PATH_DATA, PATH_DATA_BACKUP,\
    LOCAL_PATH, backup, asksaveasfilename, askopenfilename, COLORS, IM_SCROLL_ALPHA
import mynoteslib.constantes as cst
from mynoteslib.config import Config
from mynoteslib.export import Export
from mynoteslib.sticky import Sticky
from mynoteslib.about import About
from mynoteslib.notemanager import Manager
from mynoteslib.version_check import UpdateChecker
from mynoteslib.messagebox import showerror, askokcancel


class App(Tk):
    """
    Main app.

    Put an icon in the system tray with a right click menu to create notes.
    """
    def __init__(self):
        Tk.__init__(self, className='MyNotes')
        self.withdraw()
        self.notes = {}
        self.im_icon = PhotoImage(master=self, file=cst.IM_ICON_48)
        self.iconphoto(True, self.im_icon)

        style = Style(self)
        style.theme_use("clam")
        style.map('TEntry', selectbackground=[('!focus', '#c3c3c3')])
        style.map('TCheckbutton',
                  indicatorbackground=[('pressed', '#dcdad5'),
                                       ('!disabled', 'alternate', '#ffffff'),
                                       ('disabled', 'alternate', '#dcdad5'),
                                       ('disabled', '#dcdad5')])
        bg = self.cget('background')
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg)
        style.configure('TButton', background=bg)
        style.configure('TMenubutton', background=bg)
        style.configure('TNotebook', background=bg)
        style.configure('Vertical.TScrollbar', background=bg)
        style.configure('Horizontal.TScrollbar', background=bg)
        style.configure('TCheckbutton', background=bg)
        style.configure('TSeparator', background=bg)

        vmax = self.winfo_rgb('white')[0]
        self._im_trough = {}
        self._im_slider = {}
        self._im_slider_prelight = {}
        self._im_slider_active = {}
        for name, html in COLORS.items():
            color = tuple(int(val / vmax * 255) for val in self.winfo_rgb(html))
            active_bg = cst.active_color(color)
            active_bg2 = cst.active_color(cst.active_color(color, 'RGB'))
            active_bg3 = cst.active_color(cst.active_color(cst.active_color(color, 'RGB'), 'RGB'))
            slider_alpha = Image.open(IM_SCROLL_ALPHA)
            slider_vert = Image.new('RGBA', (13, 28), active_bg)
            slider_vert.putalpha(slider_alpha)
            slider_vert_active = Image.new('RGBA', (13, 28), active_bg3)
            slider_vert_active.putalpha(slider_alpha)
            slider_vert_prelight = Image.new('RGBA', (13, 28), active_bg2)
            slider_vert_prelight.putalpha(slider_alpha)
            self._im_trough[name] = tkPhotoImage(width=15, height=15,
                                                 master=self)
            self._im_trough[name].put(" ".join(["{" + " ".join([html] * 15) + "}"] * 15))
            self._im_slider_active[name] = PhotoImage(slider_vert_active,
                                                      master=self)
            self._im_slider[name] = PhotoImage(slider_vert,
                                               master=self)
            self._im_slider_prelight[name] = PhotoImage(slider_vert_prelight,
                                                        master=self)
            self._im_slider_active[name] = PhotoImage(slider_vert_active,
                                                      master=self)
            style.element_create('%s.Vertical.Scrollbar.trough' % name, 'image',
                                 self._im_trough[name])
            style.element_create('%s.Vertical.Scrollbar.thumb' % name, 'image',
                                 self._im_slider[name],
                                 ('pressed', '!disabled', self._im_slider_active[name]),
                                 ('active', '!disabled', self._im_slider_prelight[name]),
                                 border=6, sticky='ns')
            style.layout('%s.Vertical.TScrollbar' % name,
                         [('%s.Vertical.Scrollbar.trough' % name,
                           {'children': [('%s.Vertical.Scrollbar.thumb' % name,
                                          {'expand': '1'})],
                            'sticky': 'ns'})])

        self.close1 = PhotoImage(name="img_close", file=cst.IM_CLOSE, master=self)
        self.close2 = PhotoImage(name="img_closeactive", file=cst.IM_CLOSE_ACTIVE,
                                 master=self)
        self.roll1 = PhotoImage(name="img_roll", file=cst.IM_ROLL,
                                master=self)
        self.roll2 = PhotoImage(name="img_rollactive", file=cst.IM_ROLL_ACTIVE,
                                master=self)

        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.icon = TrayIcon(cst.ICON)

        # --- Clipboards
        self.clipboard = ''
        self.clibboard_content = []  # (type, props)
        self.link_clipboard = {}

        # --- Mono font
        # tkinter.font.families needs a GUI so cannot be run in constantes.py
        if not CONFIG.get('Font', 'mono'):
            fonts = [f for f in families() if 'Mono' in f]
            if 'FreeMono' in fonts:
                CONFIG.set("Font", "mono", "FreeMono")
            elif fonts:
                CONFIG.set("Font", "mono", fonts[0])
            else:
                CONFIG.set("Font", "mono", "TkDefaultFont")

        # --- Menu
        self.menu_notes = SubMenu(parent=self.icon.menu)
        self.hidden_notes = {cat: {} for cat in CONFIG.options("Categories")}
        self.menu_show_cat = SubMenu(parent=self.icon.menu)
        self.menu_hide_cat = SubMenu(parent=self.icon.menu)
        self.icon.menu.add_command(label=_("New Note"), command=self.new)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('Show All'),
                                   command=self.show_all)
        self.icon.menu.add_cascade(label=_('Show Category'),
                                   menu=self.menu_show_cat)
        self.icon.menu.add_cascade(label=_('Show Note'), menu=self.menu_notes)
        self.icon.menu.disable_item(_('Show Note'))
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('Hide All'),
                                   command=self.hide_all)
        self.icon.menu.add_cascade(label=_('Hide Category'),
                                   menu=self.menu_hide_cat)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Preferences"),
                                   command=self.config)
        self.icon.menu.add_command(label=_("Note Manager"), command=self.manage)
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
        self.icon.loop(self)

        # --- Restore notes
        self.note_data = {}
        if os.path.exists(PATH_DATA):
            try:
                with open(PATH_DATA, "rb") as fich:
                    dp = pickle.Unpickler(fich)
                    note_data = dp.load()
            except EOFError:
                # the data is corrupted
                # try to restore last backup
                path = os.path.dirname(PATH_DATA)
                l = [f for f in os.scandir(path) if f.name[:12] == "notes.backup"]
                l.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                i = 0
                error = True
                while error and i < len(l):
                    os.rename(l[i].path, PATH_DATA)
                    try:
                        with open(PATH_DATA, "rb") as fich:
                            dp = pickle.Unpickler(fich)
                            note_data = dp.load()
                    except EOFError:
                        pass
                    else:
                        error = False
                if error:
                    showerror(_('Error'),
                              _("The data is corrupted, all notes were lost. If you made a backup, you can restore it from the main menu."))
                else:
                    showerror(_('Error'),
                              _("The data is corrupted, an older backup has been restored and there might be some data losses."))

            else:
                backup()
            for i, key in enumerate(note_data):
                self.note_data["%i" % i] = note_data[key]

            for key in self.note_data:
                data = self.note_data[key]
                cat = data["category"]
                if not CONFIG.has_option("Categories", cat):
                    CONFIG.set("Categories", cat, data["color"])
                if data["visible"]:
                    self.notes[key] = Sticky(self, key, **data)
                else:
                    self.add_note_to_menu(key, data["title"], cat)
        self.nb = len(self.note_data)
        self.update_menu()
        self.update_notes()
        self.make_notes_sticky()

        # --- class bindings
#        # newline depending on mode
#        self.bind_class("Text", "<Return>", self.insert_newline)
#        # char deletion taking into account list type
#        self.bind_class("Text", "<BackSpace>", self.delete_char)
        # change Ctrl+A to select all instead of go to the beginning of the line
        self.bind_class('Text', '<Control-a>', self.select_all_text)
        self.bind_class('TEntry', '<Control-a>', self.select_all_entry)
        # bind Ctrl+Y to redo
        self.bind_class('Text', '<Control-y>', lambda e: None)
        self.bind_class('Text', '<Control-z>', lambda e: None)
        # unbind Ctrl+I and Ctrl+B
        self.bind_class('Text', '<Control-i>', lambda e: None)
        self.bind_class('Text', '<Control-b>', lambda e: None)
        self.bind_class('Text', '<Control-d>', lambda e: None)
        self.bind_class('Text', '<Control-o>', lambda e: None)
        self.bind_class('Text', '<Control-h>', lambda e: None)
        self.bind_class('Text', '<Control-t>', lambda e: None)
        self.bind_class('Text', '<<Paste>>', lambda e: None)
        self.bind_class('Text', '<Control-x>', self.cut_text)
        self.bind_class('Text', '<Control-c>', self.copy_text)
        self.bind_class('Text', '<Control-v>', self.paste_text)
        # highlight checkboxes when inside text selection
        self.bind_class("Text", "<ButtonPress-1>", self.highlight_checkboxes, True)
        self.bind_class("Text", "<ButtonRelease-1>", self.highlight_checkboxes, True)
        self.bind_class("Text", "<B1-Motion>", self.highlight_checkboxes, True)
        evs = ['<<SelectAll>>', '<<SelectLineEnd>>', '<<SelectLineStart>>',
               '<<SelectNextChar>>', '<<SelectNextLine>>', '<<SelectNextPara>>',
               '<<SelectNextWord>>', '<<SelectNone>>', '<<SelectPrevChar>>',
               '<<SelectPrevLine>>', '<<SelectPrevPara>>', '<<SelectPrevWord>>']
        for ev in evs:
            self.bind_class("Text", ev, self.highlight_checkboxes, True)

        # check for updates
        if CONFIG.getboolean("General", "check_update"):
            UpdateChecker(self)

    def report_callback_exception(self, *args):
        err = "".join(traceback.format_exception(*args))
        showerror(_("Error"), str(args[1]), err, True)

    # --- class bindings methods
    def copy_text(self, event):
        txt = event.widget
        sel = txt.tag_ranges('sel')
        if sel:
            txt.clipboard_clear()
            txt_copy = txt.get(sel[0], sel[1])
            self.clipboard = txt_copy
            txt.clipboard_append(txt_copy)
            self.clibboard_content.clear()
            self.link_clipboard.clear()
            deb = cst.sorting(str(sel[0]))
            fin = cst.sorting(str(sel[1]))
            for l in range(deb[0], fin[0] + 1):
                if l == deb[0]:
                    dc = deb[1]
                else:
                    dc = 0
                if l == fin[0]:
                    nc = fin[1]
                else:
                    nc = cst.sorting(str(txt.index('%i.end' % l)))[1]

                for c in range(dc, nc):
                    index = '%i.%i' % (l, c)
                    try:
                        im = txt.image_cget(index, 'image')
                        name = txt.image_cget(index, 'name').split('#')[0]
                        key = os.path.split(name)[1]
                        latex = txt.master.latex.get(key, '')
                        tags = list(txt.tag_names(index))
                        if latex:
                            tags.remove(key)
                        self.clibboard_content.append(('image', (im, name, tags, latex)))
                    except TclError:
                        try:
                            name = txt.window_cget(index, 'window')
                            ch = txt.children[name.split(".")[-1]]
                            tags = txt.tag_names(index)
                            self.clibboard_content.append(('checkbox', (ch.state(), tags)))
                        except TclError:
                            tags = txt.tag_names(index)
                            link = [t for t in tags if 'link#' in t]
                            if link:
                                lnb = int(link[0].split('#')[1])
                                self.link_clipboard[link[0]] = txt.master.links[lnb]
                            self.clibboard_content.append(('char', (txt.get(index), tags)))
                if l < fin[0]:
                    self.clibboard_content.append(('char', ('\n', [])))

    def cut_text(self, event):
        self.copy_text(event)
        event.widget.add_undo_sep()
        event.widget.delete_undoable('sel.first', 'sel.last')
        event.widget.add_undo_sep()
        return 'break'

    def paste_text(self, event):
        txt = event.widget
#        txt.event_generate('<<BeforePaste>>')
        txt.add_undo_sep()
        if self.clipboard == txt.clipboard_get():
            links = {}

            for oldtag, link in self.link_clipboard.items():
                newtag = txt.master.create_link(link)
                links[oldtag] = newtag

            for c in self.clibboard_content:
                index = txt.index('insert')
                if c[0] is 'image':
                    img, name, tags, latex = c[1]
                    if latex and cst.LATEX:
                        txt.master.create_latex(latex, index)
                    else:
                        txt.image_create_undoable(index, align='bottom', image=img, name=name)
                elif c[0] is 'checkbox':
                    state, tags = c[1]

#                    def create_ch():
#                        ch = Checkbox(txt, takefocus=False, style='sel.TCheckbutton')
#                        ch.state(state)
#                        return ch
#
#                    txt.window_create_undoable(index, create=create_ch)
                    txt.checkbox_create_undoable(index, state)
                    txt.update_idletasks()
#                    ch = txt.nametowidget(txt.window_cget(index, 'window'))
#                    ch.state(state)
                else:
                    char, tags = c[1]
                    link = [t for t in tags if 'link#' in t]
                    if link:
                        tags = list(tags)
                        tags.remove(link[0])
                        tags.append(links[link[0]])
                    txt.insert_undoable('insert', char)
                for tag in tags:
                    txt.tag_add_undoable(tag, index)
            txt.tag_remove('sel', '1.0', 'end')
            self.highlight_checkboxes(event)
        else:
            self.clipboard = ""
            txt.insert_undoable('insert', txt.clipboard_get())
        txt.add_undo_sep()
#        txt.event_generate('<<Paste>>')

    def highlight_checkboxes(self, event):
        txt = event.widget
        try:
            deb = cst.sorting(txt.index("sel.first"))
            fin = cst.sorting(txt.index("sel.last"))
            for ch in txt.children.values():
                try:
                    i = cst.sorting(txt.index(ch))
                    if i >= deb and i <= fin:
                        ch.configure(style="sel.%s.TCheckbutton" % txt.master.id)
                    else:
                        ch.configure(style=txt.master.id + ".TCheckbutton")
                except TclError:
                    pass
        except TclError:
            for ch in txt.children.values():
                try:
                    i = cst.sorting(txt.index(ch))
                    ch.configure(style=txt.master.id + ".TCheckbutton")
                except TclError:
                    pass

    def select_all_entry(self, event):
        event.widget.selection_range(0, "end")

    def select_all_text(self, event):
        event.widget.tag_add("sel", "1.0", "end-1c")
        self.highlight_checkboxes(event)

    # --- Other methods
    def make_notes_sticky(self):
        for w in cst.EWMH.getClientList():
            try:
                if re.match(r'mynotes[0-9]+', w.get_wm_name()):
                    cst.EWMH.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            except TypeError:
                pass   # some windows have name b''
        cst.EWMH.display.flush()

    def add_note_to_menu(self, nb, note_title, category):
        """Add note to 'show notes' menu."""
        try:
            menu = self.menu_notes.get_item_menu(category.capitalize())
            end = menu.index("end")
            if end:
                # le menu n'est pas vide
                titles = self.hidden_notes[category].values()
                titles = [t for t in titles if t.split(" ~#")[0] == note_title]
                if titles:
                    title = "%s ~#%i" % (note_title, len(titles) + 1)
                else:
                    title = note_title
            else:
                title = note_title
        except ValueError:
            # cat is not in the menu
            menu = SubMenu(parent=self.menu_notes)
            self.menu_notes.add_cascade(label=category.capitalize(), menu=menu)
            title = note_title
        self.icon.menu.enable_item(4)
        menu.add_command(label=title, command=lambda: self.show_note(nb))
        self.hidden_notes[category][nb] = title

    def backup(self):
        """Create a backup at the location indicated by user."""
        initialdir, initialfile = os.path.split(PATH_DATA_BACKUP % 0)
        fichier = asksaveasfilename(defaultextension=".backup",
                                    filetypes=[],
                                    initialdir=initialdir,
                                    initialfile="notes.backup0",
                                    title=_('Backup Notes'))
        if fichier:
            try:
                with open(fichier, "wb") as fich:
                    dp = pickle.Pickler(fich)
                    dp.dump(self.note_data)
            except Exception as e:
                report_msg = e.strerror != 'Permission denied'
                showerror(_("Error"), _("Backup failed."),
                          traceback.format_exc(), report_msg)

    def restore(self, fichier=None, confirmation=True):
        """Restore notes from backup."""
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
                    keys = list(self.note_data.keys())
                    for key in keys:
                        self.delete_note(key)
                    if not os.path.samefile(fichier, PATH_DATA):
                        copy(fichier, PATH_DATA)
                    with open(PATH_DATA, "rb") as myfich:
                        dp = pickle.Unpickler(myfich)
                        note_data = dp.load()
                    for i, key in enumerate(note_data):
                        data = note_data[key]
                        note_id = "%i" % i
                        self.note_data[note_id] = data
                        cat = data["category"]
                        if not CONFIG.has_option("Categories", cat):
                            CONFIG.set("Categories", cat, data["color"])
                        if data["visible"]:
                            self.notes[note_id] = Sticky(self, note_id, **data)
                    self.nb = len(self.note_data)
                    self.update_menu()
                    self.update_notes()
                except FileNotFoundError:
                    showerror(_("Error"), _("The file {filename} does not exists.").format(filename=fichier))
                except Exception as e:
                    showerror(_("Error"), str(e), traceback.format_exc(), True)

    def show_all(self):
        """Show all notes."""
        for cat in self.hidden_notes.keys():
            keys = list(self.hidden_notes[cat].keys())
            for key in keys:
                self.show_note(key)

    def show_cat(self, category):
        """Show all notes belonging to category."""
        keys = list(self.hidden_notes[category].keys())
        for key in keys:
            self.show_note(key)

    def hide_all(self):
        """Hide all notes."""
        keys = list(self.notes.keys())
        for key in keys:
            self.notes[key].hide()

    def hide_cat(self, category):
        """Hide all notes belonging to category."""
        keys = list(self.notes.keys())
        for key in keys:
            if self.note_data[key]["category"] == category:
                self.notes[key].hide()

    def manage(self):
        """Launch note manager."""
        Manager(self)

    def config(self):
        """Launch the setting manager."""
        conf = Config(self)
        self.wait_window(conf)
        col_changes, name_changes, new_cat = conf.get_changes()
        if new_cat or col_changes or name_changes:
            self.update_notes(col_changes, name_changes)
            self.update_menu()
        alpha = CONFIG.getint("General", "opacity") / 100
        for note in self.notes.values():
            note.attributes("-alpha", alpha)
            note.update_title_font()
            note.update_text_font()
            note.update_titlebar()

    def delete_cat(self, category):
        """Delete all notes belonging to category."""
        keys = list(self.notes.keys())
        for key in keys:
            if self.note_data[key]["category"] == category:
                self.notes[key].delete(confirmation=False)

    def delete_note(self, nb):
        """Delete note with id nb."""
        if self.note_data[nb]["visible"]:
            self.notes[nb].delete(confirmation=False)
        else:
            cat = self.note_data[nb]["category"]
            menu = self.menu_notes.get_item_menu(cat.capitalize())
            index = menu.index(self.hidden_notes[cat][nb])
            menu.delete(index)
            if not menu.index("end"):
                # the menu is empty
                self.menu_notes.delete(cat.capitalize())
                if not self.menu_notes.index('end'):
                    self.icon.menu.disable_item(4)
            del(self.hidden_notes[cat][nb])
            del(self.note_data[nb])
            self.save()

    def show_note(self, nb):
        """Display the note corresponding to the 'nb' key in self.note_data."""
        self.note_data[nb]["visible"] = True
        cat = self.note_data[nb]["category"]
        menu = self.menu_notes.get_item_menu(cat.capitalize())
        index = menu.index(self.hidden_notes[cat][nb])
        del(self.hidden_notes[cat][nb])
        self.notes[nb] = Sticky(self, nb, **self.note_data[nb])
        menu.delete(index)
        if not menu.index("end"):
            # the menu is empty
            self.menu_notes.delete(cat.capitalize())
            if not self.menu_notes.index('end'):
                self.icon.menu.disable_item(4)
        self.make_notes_sticky()

    def update_notes(self, col_changes={}, name_changes={}):
        """Update the notes after changes in the categories."""
        categories = CONFIG.options("Categories")
        categories.sort()
        self.menu_notes.delete(0, "end")
        self.hidden_notes = {cat: {} for cat in categories}
        for key in self.note_data:
            cat = self.note_data[key]["category"]
            if cat in name_changes:
                cat = name_changes[cat]
                self.note_data[key]["category"] = cat
                if self.note_data[key]["visible"]:
                    self.notes[key].change_category(cat)
            elif cat not in categories:
                default = CONFIG.get("General", "default_category")
                default_color = CONFIG.get("Categories", default)
                if self.note_data[key]["visible"]:
                    self.notes[key].change_category(default)
                self.note_data[key]["category"] = default
                self.note_data[key]["color"] = default_color
                cat = default
            if cat in col_changes:
                old_color, new_color = col_changes[cat]
                if self.note_data[key]["color"] == old_color:
                    self.note_data[key]["color"] = new_color
                    if self.note_data[key]["visible"]:
                        self.notes[key].change_color(cst.INV_COLORS[new_color])
            if not self.note_data[key]['visible']:
                self.add_note_to_menu(key, self.note_data[key]["title"],
                                      self.note_data[key]['category'])
            else:
                self.notes[key].update_menu_cat(categories)
        self.save()
        if self.menu_notes.index("end"):
            self.icon.menu.enable_item(4)
        else:
            self.icon.menu.disable_item(4)

    def update_menu(self):
        """Populate self.menu_show_cat and self.menu_hide_cat with the categories."""
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
        """Save the data."""
        with open(PATH_DATA, "wb") as fich:
            dp = pickle.Pickler(fich)
            dp.dump(self.note_data)

    def new(self):
        """Create a new note."""
        key = "%i" % self.nb
        self.notes[key] = Sticky(self, key)
        data = self.notes[key].save_info()
        data["visible"] = True
        self.note_data[key] = data
        self.nb += 1
        self.make_notes_sticky()

    def export_notes(self):
        """Note export."""
        export = Export(self)
        self.wait_window(export)
        categories_to_export, only_visible = export.get_export()
        if categories_to_export:
            initialdir, initialfile = os.path.split(PATH_DATA_BACKUP % 0)
            fichier = asksaveasfilename(defaultextension=".html",
                                        filetypes=[(_("HTML file (.html)"), "*.html"),
                                                   (_("Text file (.txt)"), "*.txt"),
                                                   (_("All files"), "*")],
                                        initialdir=initialdir,
                                        initialfile="",
                                        title=_('Export Notes As'))
            if fichier:
                try:
                    if os.path.splitext(fichier)[-1] == ".html":
        # --- html export
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
                            fich.write(text.encode('ascii', 'xmlcharrefreplace').decode("utf-8"))
                            fich.write("\n</body>")
#                if os.path.splitext(fichier)[-1] == ".txt":
                    else:
        # --- txt export
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
                            text += "=" * len(cat_txt)
                            text += "\n\n"
                            for title, txt in cats[cat]:
                                text += title
                                text += "\n"
                                text += "-" * len(title)
                                text += "\n\n"
                                text += txt
                                text += "\n\n"
                                text += "-" * 30
                                text += "\n\n"
                            text += "#" * 30
                            text += "\n\n"
                        with open(fichier, "w") as fich:
                            fich.write(text)

                except Exception as e:
                    report_msg = e.strerror != 'Permission denied'
                    showerror(_("Error"), str(e), traceback.format_exc(),
                              report_msg)

    def import_notes(self):
        """Import notes."""
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
                        self.hidden_notes[cat] = {}
                    if data["visible"]:
                        self.notes[note_id] = Sticky(self, note_id, **data)
                self.nb = int(max(self.note_data.keys(), key=lambda x: int(x))) + 1
                self.update_menu()
                self.update_notes()
            except Exception:
                message = _("The file {file} is not a valid .notes file.").format(file=fichier)
                showerror(_("Error"), message, traceback.format_exc())

    def cleanup(self):
        """Remove unused latex images."""
        img_stored = os.listdir(cst.PATH_LATEX)
        img_used = []
        for data in self.note_data.values():
            img_used.extend(list(data.get("latex", {}).keys()))
        for img in img_stored:
            if img not in img_used:
                os.remove(os.path.join(cst.PATH_LATEX, img))

    def quit(self):
        self.destroy()
