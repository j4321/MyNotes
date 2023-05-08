#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2019 Juliette Monsel <j_4321@protonmail.com>

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


Main class
"""
import signal
import os
import filecmp
import re
import traceback
import pickle
import tarfile
from shutil import copy, copyfile
from tempfile import TemporaryDirectory
from time import strftime
from tkinter import Tk, TclError
from tkinter import PhotoImage as tkPhotoImage
from tkinter.ttk import Style
from tkinter.font import families

from PIL import Image
from PIL.ImageTk import PhotoImage

import mynoteslib.constants as cst
from mynoteslib.trayicon import TrayIcon, SubMenu
from mynoteslib.constants import CONFIG, COLORS, TEXT_COLORS,\
    PATH_DATA, PATH_DATA_BACKUP, LOCAL_PATH, PATH_LATEX, PATH_LOCAL_DATA,\
    asksaveasfilename, askopenfilename
from mynoteslib.config import Config
from mynoteslib.export import Export, EXT_DICT, MERGE_FCT, EXPORT_FCT, \
    make_archive, export_filename
from mynoteslib.sticky import Sticky
from mynoteslib.about import About
from mynoteslib.notemanager import Manager
from mynoteslib.version_check import UpdateChecker
from mynoteslib.messagebox import showerror, askokcancel
from mynoteslib.mytext import MyText


class App(Tk):
    """
    Main app.

    Put an icon in the system tray with a right click menu to create notes.
    """
    def __init__(self, args):
        Tk.__init__(self, className='MyNotes')
        self.withdraw()
        self.notes = {}
        self.im_icon = PhotoImage(master=self, file=cst.IM_ICON_48)
        self.iconphoto(True, self.im_icon)
        self.im_visible = PhotoImage(file=cst.IM_VISIBLE, master=self)
        self.im_hidden = PhotoImage(file=cst.IM_HIDDEN, master=self)
        self.im_select = PhotoImage(file=cst.IM_SELECT, master=self)
        self.im_sort_rev = PhotoImage(file=cst.IM_SORT_REV, master=self)
        self.im_sort = PhotoImage(file=cst.IM_ROLL, master=self)

        # color boxes for menus
        self.im_text_color = {}
        for name, value in TEXT_COLORS.items():
            self.im_text_color[name] = PhotoImage(cst.color_box(value), master=self)
        self.im_color = {}
        for name, value in COLORS.items():
            self.im_color[name] = PhotoImage(cst.color_box(value), master=self)

        # --- style
        style = Style(self)
        style.theme_use("clam")
        style.map('TEntry', selectbackground=[('!focus', '#c3c3c3')])
        style.element_create('visibility', 'image', self.im_hidden,
                             ('selected', self.im_visible))
        style.layout('Toggle',
                     [('Toggle.border',
                       {'children': [('Toggle.padding',
                                      {'children': [('Toggle.visibility',
                                                     {'sticky': 'nswe'})],
                                       'sticky': 'nswe'})],
                        'sticky': 'nswe'})])
        style.layout('heading.TLabel',
                     [('Label.border',
                       {'sticky': 'nswe',
                        'border': '1',
                        'children': [('Label.padding',
                                      {'sticky': 'nswe',
                                       'border': '1',
                                       'children': [('Label.text', {'sticky': 'nswe'}),
                                                    ('Label.image', {'sticky': 'e'})]})]})])
        style.map('TCheckbutton',
                  indicatorbackground=[('pressed', '#dcdad5'),
                                       ('!disabled', 'alternate', '#ffffff'),
                                       ('disabled', 'alternate', '#dcdad5'),
                                       ('disabled', '#dcdad5')])
        bg = self.cget('background')
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg)
        style.configure('Toggle', background=bg)
        style.configure('TButton', background=bg)
        style.configure('TMenubutton', background=bg)
        style.configure('TNotebook', background=bg)
        style.configure('Vertical.TScrollbar', background=bg)
        style.configure('Horizontal.TScrollbar', background=bg)
        style.configure('TCheckbutton', background=bg)
        style.map('TCheckbutton', indicatorbackground=[])
        style.layout('manager.TCheckbutton', [('Checkbutton.indicator', {'side': 'left', 'sticky': ''})])
        style.configure('manager.TCheckbutton', background='white')
        active_bg = style.lookup('TCheckbutton', 'background', ('active',))
        style.map('manager.TLabel', background=[('active', active_bg)])
        style.map('manager.TFrame', background=[('active', active_bg)])
        style.configure('heading.TLabel', relief='raised', borderwidth=1)
        style.map('heading.TLabel', **style.map('TButton'))
        style.map('heading.TLabel', bordercolor=[])
        style.map('select.heading.TLabel', image=[('active', self.im_select)])
        style.map('heading.TLabel', image=[('active', 'alternate', self.im_sort_rev),
                                           ('active', '!alternate', self.im_sort)])
        style.configure('manager.TFrame', background='white')
        style.configure('bg.TFrame', background='white', relief='sunken', borderwidth=1)
        style.configure('manager.TLabel', background='white')
        style.configure('manager.Toggle', background='white')
        style.map('Toggle', background=[('active', active_bg), ('hover', active_bg)])
        style.configure('TSeparator', background=bg)

        vmax = self.winfo_rgb('white')[0]
        self._im_trough = {}
        self._im_slider = {}
        self._im_slider_prelight = {}
        self._im_slider_active = {}
        for html in COLORS.values():
            color = tuple(int(val / vmax * 255) for val in self.winfo_rgb(html))
            active_bg = cst.active_color(color)
            active_bg2 = cst.active_color(cst.active_color(color, 'RGB'))
            active_bg3 = cst.active_color(cst.active_color(cst.active_color(color, 'RGB'), 'RGB'))
            slider_alpha = Image.open(cst.IM_SCROLL_ALPHA)
            slider_vert = Image.new('RGBA', (13, 28), active_bg)
            slider_vert.putalpha(slider_alpha)
            slider_vert_active = Image.new('RGBA', (13, 28), active_bg3)
            slider_vert_active.putalpha(slider_alpha)
            slider_vert_prelight = Image.new('RGBA', (13, 28), active_bg2)
            slider_vert_prelight.putalpha(slider_alpha)
            self._im_trough[html] = tkPhotoImage(width=15, height=15,
                                                 master=self)
            self._im_trough[html].put(" ".join(["{" + " ".join([html] * 15) + "}"] * 15))
            self._im_slider_active[html] = PhotoImage(slider_vert_active,
                                                      master=self)
            self._im_slider[html] = PhotoImage(slider_vert,
                                               master=self)
            self._im_slider_prelight[html] = PhotoImage(slider_vert_prelight,
                                                        master=self)
            self._im_slider_active[html] = PhotoImage(slider_vert_active,
                                                      master=self)
            style.element_create('%s.Vertical.Scrollbar.trough' % html, 'image',
                                 self._im_trough[html])
            style.element_create('%s.Vertical.Scrollbar.thumb' % html, 'image',
                                 self._im_slider[html],
                                 ('pressed', '!disabled', self._im_slider_active[html]),
                                 ('active', '!disabled', self._im_slider_prelight[html]),
                                 border=6, sticky='ns')
            style.layout('%s.Vertical.TScrollbar' % html,
                         [('%s.Vertical.Scrollbar.trough' % html,
                           {'children': [('%s.Vertical.Scrollbar.thumb' % html,
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
        self.icon = TrayIcon(cst.ICON, fallback_icon_path=cst.IM_ICON_48)

        # --- Clipboards
        self.clipboard = ''
        self.clipboard_content = []  # (type, props)
        self.link_clipboard = {}

        # --- Mono font
        # tkinter.font.families needs a GUI so cannot be run in constants.py
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
        self.icon.menu.add_command(label=_("Toggle All"), command=self.toggle_all)
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
                cst.backup()
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
        self.bind_class('Text', '<Double-1>', self.select_word)
        self.bind_class('Text', '<Button-1>', lambda e: e.widget.focus_set(), True)
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

        if args.show_all:
            self.show_all()
        elif args.hide_all:
            self.hide_all()
        elif args.toggle_all:
            self.toggle_all()

        # react to mynotes --show-all in command line
        signal.signal(signal.SIGUSR1, lambda *args: self.show_all())
        # react to mynotes --hide-all in command line
        signal.signal(signal.SIGUSR2, lambda *args: self.hide_all())
        # react to mynotes --toggle-all in command line
        signal.signal(signal.SIGVTALRM, lambda *args: self.toggle_all())

        # check for updates
        if CONFIG.getboolean("General", "check_update"):
            UpdateChecker(self)

    def report_callback_exception(self, *args):
        if args[0] is not KeyboardInterrupt:
            err = "".join(traceback.format_exception(*args))
            print(err)
            showerror(_("Error"), str(args[1]), err, True)
        else:
            print('KeyboardInterrupt')
            self.quit()

    # --- class bindings methods
    @staticmethod
    def select_word(event):
        """Select word on double click."""
        txt = event.widget
        index = txt.index('@%i,%i' % (event.x, event.y))
        txt.tag_remove('sel', '1.0', 'end')
        try:
            txt.image_cget(index, 'image')
        except TclError:
            # not an image
            start = txt.index('%s wordstart' % index)
            end = txt.index('%s wordend' % index)
            txt.tag_add('sel', start, end)
        else:
            # this is an image
            txt.tag_add('sel', index)

    def copy_text(self, event):
        txt = event.widget
        sel = txt.tag_ranges('sel')
        if sel:
            txt.clipboard_clear()
            txt_copy = txt.get(sel[0], sel[1])
            self.clipboard = txt_copy
            self.clipboard_content.clear()
            self.link_clipboard.clear()

            if isinstance(txt, MyText):
                cst.copy_to_clipboard(txt, txt_copy, *sel)
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
                            latex = txt.latex.get(key, '')
                            tags = list(txt.tag_names(index))
                            if latex:
                                tags.remove(key)
                            self.clipboard_content.append(('image', (im, name, tags, latex)))
                        except TclError:
                            try:
                                name = txt.window_cget(index, 'window')
                                ch = txt.children[name.split(".")[-1]]
                                tags = txt.tag_names(index)
                                self.clipboard_content.append(('checkbox', (ch.state(), tags)))
                            except TclError:
                                tags = txt.tag_names(index)
                                link = [t for t in tags if 'link#' in t]
                                if link:
                                    lnb = int(link[0].split('#')[1])
                                    self.link_clipboard[link[0]] = txt.links[lnb]
                                self.clipboard_content.append(('char', (txt.get(index), tags)))
                    if l < fin[0]:
                        self.clipboard_content.append(('char', ('\n', [])))
                else:
                    txt.clipboard_append(txt_copy)

    def cut_text(self, event):
        self.copy_text(event)
        txt = event.widget
        if isinstance(txt, MyText):
            txt.add_undo_sep()
            txt.delete_undoable('sel.first', 'sel.last')
            txt.add_undo_sep()
        else:
            txt.delete('sel.first', 'sel.last')
        return 'break'

    def paste_text(self, event):
        txt = event.widget
        if isinstance(txt, MyText):
            if txt.tag_ranges("sel"):
                txt.add_undo_sep()
                txt.delete_undoable("sel.first", "sel.last")
            txt.add_undo_sep()
            if self.clipboard == txt.clipboard_get():
                links = {}

                for oldtag, link in self.link_clipboard.items():
                    newtag = txt.master.create_link(link)
                    links[oldtag] = newtag
                if self.clipboard_content:
                    c = self.clipboard_content[0]
                    if c[0] == 'image':
                        tags1 = c[1][2]
                    else:
                        tags1 = c[1][1]
                for c in self.clipboard_content:
                    index = txt.index('insert')
                    if c[0] == 'image':
                        img, name, tags, latex = c[1]
                        if latex and cst.LATEX:
                            txt.master.create_latex(latex, index)
                        else:
                            txt.image_create_undoable(index, align='bottom', image=img, name=name)
                    elif c[0] == 'checkbox':
                        state, tags = c[1]
                        txt.checkbox_create_undoable(index, state)
                        txt.update_idletasks()
                    else:
                        char, tags = c[1]
                        tags = list(tags)
                        if char == '\n':
                            if txt.mode == "list":
                                txt.insert_undoable("insert", "\n")
                                if 'list' not in tags1:
                                    txt.insert_undoable("insert", "\t•\t")
                            elif txt.mode == "todolist":
                                txt.insert_undoable("insert", "\n")
                                if 'todolist' not in tags1:
                                    txt.checkbox_create_undoable("insert", ('!alternate',))
                            elif txt.mode == "enum":
                                txt.insert_undoable("insert", "\n")
                                if 'enum' not in tags1:
                                    txt.insert_undoable("insert", "\t0.\t")
                            else:
                                txt.insert_undoable("insert", "\n")
                        else:
                            link = [t for t in tags if 'link#' in t]
                            if link:
                                tags = list(tags)
                                tags.remove(link[0])
                                tags.append(links[link[0]])
                            txt.insert_undoable('insert', char)
                        for mode in ['list', 'todolist', 'enum']:
                            if mode in tags:
                                tags.remove(mode)
                    for tag in tags:
                        txt.tag_add_undoable(tag, index)
                txt.tag_remove('sel', '1.0', 'end')
                self.highlight_checkboxes(event)
            else:
                self.clipboard = ""
                text = txt.clipboard_get()
                if txt.mode == 'list':
                    text = text.replace('\n', "\n\t•\t")
                    txt.insert_undoable('insert', text)
                elif txt.mode == 'enum':
                    text = text.replace('\n', "\n\t0.\t")
                    txt.insert_undoable('insert', text)
                elif txt.mode == 'todolist':
                    lines = text.split('\n')
                    if lines:
                        txt.insert_undoable('insert', lines[0])
                        for line in lines[1:]:
                            txt.insert_undoable("insert", "\n")
                            txt.checkbox_create_undoable("insert", ('!alternate',))
                            txt.insert_undoable('insert', line)
                else:
                    txt.insert_undoable('insert', text)

            if txt.mode != 'note':
                txt.tag_add(txt.mode, '1.0', 'end')
                if txt.mode == 'enum':
                    txt.update_enum()
            txt.add_undo_sep()
        else:
            if txt.tag_ranges("sel"):
                txt.delete("sel.first", "sel.last")
            txt.insert('insert', txt.clipboard_get())

    def highlight_checkboxes(self, event):
        txt = event.widget
        if isinstance(txt, MyText):
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
    @staticmethod
    def make_notes_sticky():
        for w in cst.EWMH.getClientList():
            try:
                if re.match(r'mynotes[0-9]+', w.get_wm_name()):
                    cst.EWMH.setWmState(w, 1, '_NET_WM_STATE_STICKY')
                    cst.EWMH.setWmState(w, 1, '_NET_WM_STATE_SKIP_TASKBAR')
                    cst.EWMH.setWmState(w, 1, '_NET_WM_STATE_SKIP_PAGER')
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
        initialdir = os.path.dirname(PATH_DATA_BACKUP)
        fichier = asksaveasfilename(defaultextension=".notes",
                                    filetypes=[(_("Notes (.notes)"), '*.notes'),
                                               (_("Notes with data (.tar.*)"), "*.tar.*"),
                                               (_("All files"), "*")],
                                    initialdir=initialdir,
                                    initialfile="backup.notes",
                                    title=_('Backup Notes'))
        if fichier:
            name, ext = os.path.splitext(fichier)
            exts = []
            while ext:
                exts.append(ext)
                name, ext = os.path.splitext(name)
            export_data = '.tar' in exts
            try:
                self._export_pickle(fichier, '.notes', list(self.note_data.keys()),
                                    export_data)
            except Exception as e:
                try:
                    report_msg = e.strerror != 'Permission denied'
                except AttributeError:
                    report_msg = True
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
                                          filetypes=[(_('Backup'), 'notes.backup*'),
                                                     (_("Notes (.notes)"), '*.notes'),
                                                     (_("Notes with data (.tar.*)"), "*.tar.*"),
                                                     (_("All files"), "*")],
                                          initialdir=os.path.dirname(PATH_DATA_BACKUP),
                                          initialfile="",
                                          title=_('Restore Backup'))
            if not fichier:
                return
            try:
                with open(fichier, "rb") as myfich:
                    dp = pickle.Unpickler(myfich)
                    note_data = dp.load()
                keys = list(self.note_data.keys())
                visible_notes = list(self.notes.keys())
                self.hide_all()
                self._load_notes(note_data)
                if not os.path.samefile(fichier, PATH_DATA):
                    copy(fichier, PATH_DATA)
                for key in keys:
                    self.delete_note(key)
            except pickle.UnpicklingError:
                try:
                    keys = list(self.note_data.keys())
                    visible_notes = list(self.notes.keys())
                    self.hide_all()
                    self._load_notes_with_data(fichier, cleanup_cat=True)
                    for key in keys:
                        self.delete_note(key)
                except Exception:
                    for key in visible_notes:
                        self.show_note(key)
                    message = _("The file {file} is not a valid note archive.").format(file=fichier)
                    showerror(_("Error"), message, traceback.format_exc())
            except FileNotFoundError:
                showerror(_("Error"), _("The file {filename} does not exists.").format(filename=fichier))
            except Exception:
                for key in visible_notes:
                    self.show_note(key)
                message = _("The file {file} is not a valid .notes file.").format(file=fichier)
                showerror(_("Error"), message, traceback.format_exc())

    def show_all(self):
        """Show all notes."""
        for key in self.hidden_keys():
            self.show_note(key)

    def show_cat(self, category):
        """Show all notes belonging to category."""
        keys = list(self.hidden_notes[category].keys())
        for key in keys:
            self.show_note(key)

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

    def toggle_all(self):
        """Toggle all notes."""
        shown = list(self.notes.keys())
        hidden = self.hidden_keys()
        for key in hidden:
            self.show_note(key)
        for key in shown:
            self.notes[key].hide()

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

    def hidden_keys(self):
        """Return the keys of all hidden notes."""
        keys = []
        for cat in self.hidden_notes.keys():
            keys = keys + list(self.hidden_notes[cat].keys())
        return keys

    def manage(self):
        """Launch note manager."""
        manager = Manager(self)
        self.wait_window(manager)

    def config(self):
        """Launch the setting manager."""
        conf = Config(self)
        self.wait_window(conf)
        col_changes, name_changes, new_cat, splash_change = conf.get_changes()
        if new_cat or col_changes or name_changes:
            self.update_notes(col_changes, name_changes)
            self.update_menu()
        alpha = CONFIG.getint("General", "opacity") / 100
        for note in self.notes.values():
            note.attributes("-alpha", alpha)
            note.update_title_font()
            note.update_text_font()
            note.update_titlebar()
            if splash_change:
                note.update_position()

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

    def change_note_category(self, nb, cat):
        """Change category of note with id nb."""
        if nb in self.notes:
            self.notes[nb].change_category(cat)
        else:
            self.show_note(nb)
            self.notes[nb].change_category(cat)
            self.notes[nb].hide()

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
        self.notes[key] = Sticky(self, key, date=strftime("%x"))
        data = self.notes[key].save_info()
        data["visible"] = True
        self.note_data[key] = data
        self.nb += 1
        self.make_notes_sticky()

    def _generate(self, filename, extension, notes_to_export, export_data):
        datafiles = {}
        cats = {}
        for key in notes_to_export:
            cat = self.note_data[key]["category"]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append((self.note_data[key]["title"],
                              EXPORT_FCT[extension](self.note_data[key], self, export_data, datafiles)))
        text = MERGE_FCT[extension](cats)
        if export_data:
            make_archive(filename, datafiles, extension, text)
        else:
            with open(filename, 'w') as file:
                file.write(text)

    def _export_pickle(self, filename, extension, notes_to_export, export_data):
        """pickle export (same format as backups)"""
        note_data = {}
        datafiles = {}
        latexfiles = {}
        for key in notes_to_export:
            note_data[key] = self.note_data[key].copy()
            if export_data:
                note_data[key]["inserted_objects"] = self.note_data[key]["inserted_objects"].copy()
                note_data[key]["links"] = self.note_data[key]["links"].copy()
                for link_id, link in tuple(note_data[key]["links"].items()):
                    if os.path.exists(link):
                        link = export_filename(link, datafiles)
                        note_data[key]["links"][link_id] = link
                for ind, (obj_type, val) in tuple(note_data[key]["inserted_objects"].items()):
                    if obj_type == 'image':
                        if os.path.split(val)[0] == PATH_LATEX:
                            val = export_filename(val, latexfiles, 'latex')
                        else:
                            val = export_filename(val, datafiles)
                        note_data[key]["inserted_objects"][ind] = (obj_type, val)
        if export_data:
            make_archive(filename, datafiles, extension, note_data, latexfiles, pickle=True)
        else:
            with open(filename, "wb") as fich:
                dp = pickle.Pickler(fich)
                dp.dump(note_data)

    def export_notes(self):
        """Note export."""
        export = Export(self, self.note_data)
        self.wait_window(export)
        export_type, notes_to_export, export_data = export.get_export()
        if not notes_to_export:
            return
        extension = EXT_DICT[export_type]

        initialdir, initialfile = os.path.split(PATH_DATA_BACKUP % 0)
        if export_data:
            fichier = asksaveasfilename(defaultextension='.tar.gz',
                                        filetypes=[(_('tar.gzip archive (.tar.gz)'), '*.tar.gz'),
                                                   (_('tar.bzip2 archive (.tar.bz2)'), '*.tar.bz2'),
                                                   (_('tar.xz archive (.tar.xz)'), '*.tar.xz'),
                                                   (_("All files"), "*")],
                                        initialdir=initialdir,
                                        initialfile="",
                                        title=_('Export Notes As'))
        else:
            fichier = asksaveasfilename(defaultextension=extension,
                                        filetypes=[(export_type, '*' + extension),
                                                   (_("All files"), "*")],
                                        initialdir=initialdir,
                                        initialfile="",
                                        title=_('Export Notes As'))
        if not fichier:
            return
        try:
            if extension in EXPORT_FCT:
                self._generate(fichier, extension, notes_to_export, export_data)
            else:
                self._export_pickle(fichier, extension, notes_to_export, export_data)

        except Exception as e:
            try:
                report_msg = e.strerror != 'Permission denied'
            except AttributeError:
                report_msg = True
            showerror(_("Error"), str(e), traceback.format_exc(),
                      report_msg)

    def _cleanup_cat(self, cats):
        """Remove categories not in cats"""
        for cat in CONFIG.options("Categories"):
            if cat not in cats:
                CONFIG.remove_option("Categories", cat)
        default = CONFIG.get("General", "default_category")
        if not CONFIG.has_option("Categories", default):
            CONFIG.set("General", "default_category", CONFIG.options("Categories")[0])
            cst.save_config()

    def _load_notes(self, note_data, cleanup_cat=False):
        """Load notes from note_data."""
        categories = set()
        for i, key in enumerate(note_data):
            data = note_data[key]
            note_id = "%i" % (i + self.nb)
            self.note_data[note_id] = data
            cat = data["category"]
            categories.add(cat)
            if not CONFIG.has_option("Categories", cat):
                CONFIG.set("Categories", cat, data["color"])
            if data["visible"]:
                self.notes[note_id] = Sticky(self, note_id, **data)
        self.nb = int(max(self.note_data.keys(), key=lambda x: int(x))) + 1
        if cleanup_cat:
            # remove categories with no notes (for restore)
            self._cleanup_cat(self, categories)
        self.update_menu()
        self.update_notes()
        cst.save_config()

    def _load_notes_with_data(self, filename, cleanup_cat=False):
        """Load notes and data from archive."""

        def get_name_latex(path, local_files):
            name, ext = os.path.splitext(os.path.split(path)[1])
            if name + ext in local_files:
                name = '%i'
                i = 0
                while name % i + ext in local_files:
                    i += 1
                name = name % i
            local_files.append(name + ext)
            return name + ext

        def get_name_data(path, local_files):
            name, ext = os.path.splitext(os.path.split(path)[1])
            if name + ext in local_files:
                if filecmp.cmp(os.path.join(PATH_LOCAL_DATA, name + ext), path, False):
                    return name + ext, False  # non need to copy file
                name = name + '-%i'
                i = 0
                while name % i + ext in local_files:
                    if filecmp.cmp(os.path.join(PATH_LOCAL_DATA, name % i + ext), path, False):
                        return name % i + ext, False  # non need to copy file
                    i += 1
                name = name % i
            local_files.append(name + ext)
            return name + ext, True

        with TemporaryDirectory() as tmpdir:
            # extract archive
            with tarfile.open(filename, 'r') as tar:
                tar.extractall(tmpdir)
            # get path of main folder
            tmppath = os.path.join(tmpdir, os.listdir(tmpdir)[0])
            # load note data
            tmpfile = os.path.join(tmppath, [f for f in os.listdir(tmppath) if '.notes' in f][0])
            with open(tmpfile, "rb") as fich:
                dp = pickle.Unpickler(fich)
                note_data = dp.load()
            # get local data to avoid replacements
            local_latexfiles = os.listdir(PATH_LATEX)
            if not os.path.exists(PATH_LOCAL_DATA):
                os.mkdir(PATH_LOCAL_DATA)
            local_datafiles = os.listdir(PATH_LOCAL_DATA)
            copied_tmp_datafiles = {}
            # create notes
            categories = set()
            for i, key in enumerate(note_data):
                data = note_data[key]
                note_id = "%i" % (i + self.nb)
                self.note_data[note_id] = data
                cat = data["category"]
                categories.add(cat)
                if not CONFIG.has_option("Categories", cat):
                    CONFIG.set("Categories", cat, data["color"])
                # copy link data if it is a local file
                for link_id, link in tuple(data["links"].items()):
                    link_path = os.path.join(tmppath, link)
                    if os.path.exists(link_path):
                        if link in copied_tmp_datafiles:
                            new_link = copied_tmp_datafiles[link]
                        else:
                            new_name, copy_file = get_name_data(link_path, local_datafiles)
                            new_link = os.path.join(PATH_LOCAL_DATA, new_name)
                            copied_tmp_datafiles[link] = new_link
                            if copy_file:
                                copyfile(link_path, new_link)
                        self.note_data[note_id]["links"][link_id] = new_link
                # copy images
                for ind, (obj_type, val) in tuple(data["inserted_objects"].items()):
                    if obj_type == 'image':
                        path, name = os.path.split(val)
                        if path == 'latex':
                            new_val = os.path.join(PATH_LATEX, get_name_latex(val, local_latexfiles))
                            latex_val = self.note_data[note_id]['latex'][os.path.split(val)[1]]
                            del self.note_data[note_id]['latex'][os.path.split(val)[1]]
                            del self.note_data[note_id]['tags'][os.path.split(val)[1]]
                            self.note_data[note_id]['latex'][os.path.split(new_val)[1]] = latex_val
                        else:
                            if val in copied_tmp_datafiles:
                                new_val = copied_tmp_datafiles[val]
                            else:
                                new_name, copy_file = get_name_data(os.path.join(tmppath, val), local_datafiles)
                                new_val = os.path.join(PATH_LOCAL_DATA, new_name)
                                copied_tmp_datafiles[val] = new_val
                                if copy_file:
                                    copyfile(os.path.join(tmppath, val), new_val)
                        self.note_data[note_id]["inserted_objects"][ind] = (obj_type, new_val)

                if data["visible"]:
                    self.notes[note_id] = Sticky(self, note_id, **self.note_data[note_id])

        self.nb = int(max(self.note_data.keys(), key=lambda x: int(x))) + 1
        if cleanup_cat:
            # remove categories with no notes (for restore)
            self._cleanup_cat(categories)
        self.update_menu()
        self.update_notes()

    def import_notes(self):
        """Import notes."""

        fichier = askopenfilename(defaultextension=".notes",
                                  filetypes=[(_("Notes (.notes)"), "*.notes"),
                                             (_("Notes with data (.tar.*)"), "*.tar.*"),
                                             (_("All files"), "*")],
                                  initialdir=LOCAL_PATH,
                                  initialfile="",
                                  title=_('Import'))
        if not fichier:
            return
        try:
            with open(fichier, "rb") as fich:
                dp = pickle.Unpickler(fich)
                note_data = dp.load()
            self._load_notes(note_data)
        except pickle.UnpicklingError:
            try:
                self._load_notes_with_data(fichier)
            except Exception:
                message = _("The file {file} is not a valid note archive.").format(file=fichier)
                showerror(_("Error"), message, traceback.format_exc())

        except Exception:
            message = _("The file {file} is not a valid .notes file.").format(file=fichier)
            showerror(_("Error"), message, traceback.format_exc())

    def cleanup(self):
        """Remove unused local data."""
        if cst.LATEX:
            latex_stored = os.listdir(PATH_LATEX)
        else:
            latex_stored = []
        latex_used = []
        data_stored = os.listdir(PATH_LOCAL_DATA)
        data_used = []
        for data in self.note_data.values():
            latex_used.extend(list(data.get("latex", {}).keys()))
            img = [os.path.split(val[1]) for val in data.get("inserted_objects", {}).values()
                   if val[0] == 'image']
            data_used.extend([im for path, im in img if path == PATH_LOCAL_DATA])
            links = [os.path.split(link) for link in data.get('links', {}).values()]
            data_used.extend([file for path, file in links if path == PATH_LOCAL_DATA])
        for img in latex_stored:
            if img not in latex_used:
                os.remove(os.path.join(PATH_LATEX, img))
        for img in data_stored:
            if img not in data_used:
                os.remove(os.path.join(PATH_LOCAL_DATA, img))

    def quit(self):
        self.destroy()
