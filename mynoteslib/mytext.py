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


Text class with improved undo/redo
"""
import os
import re
from tkinter import Text, TclError
from tkinter.font import Font
from tkinter.ttk import Checkbutton

from mynoteslib.constants import CONFIG, TEXT_COLORS, PATH_LATEX, AUTOCORRECT, \
    text_ranges, sorting
from mynoteslib.export import TAG_OPEN_HTML, TAG_CLOSE_HTML



class Checkbox(Checkbutton):
    def __init__(self, master, **kw):
        Checkbutton.__init__(self, master, command=self.command, **kw)

    def command(self):
        self.master.cb_state_change(self, 'selected' in self.state())


class MyText(Text):

    def __init__(self, master=None, mode='note', cb_style="TCheckbutton", **kw):
        Text.__init__(self, master, wrap='word', undo=False,
                      autoseparator=False, tabs=(10, 'right', 21, 'left'),
                      relief="flat", borderwidth=0,
                      highlightthickness=0, **kw)

        self.mode = mode
        self.cb_style = cb_style
        self.links = {}
        self.latex = {}

        self._current_word = ""

        # --- undo/redo
        self._undo_stack = [[]]
        self._redo_stack = []

        size = CONFIG.get("Font", "text_size")
        font_text = "%s %s" % (CONFIG.get("Font", "text_family").replace(" ", "\ "), size)
        mono = "%s %s" % (CONFIG.get("Font", "mono").replace(" ", "\ "), size)
        self.configure(font=font_text)

        # --- tags
        self.tag_configure("mono", font=mono)
        self.tag_configure("bold", font="%s bold" % font_text)
        self.tag_configure("italic", font="%s italic" % font_text)
        self.tag_configure("bold-italic", font="%s bold italic" % font_text)

        try:    # only >= tk8.6.6 support selectforeground
            self.tag_configure("underline", underline=True,
                               selectforeground="white")
            self.tag_configure("overstrike", overstrike=True,
                               selectforeground="white")
            self.tag_configure("link", foreground="blue", underline=True,
                               selectforeground="white")
            self.tag_configure("file", foreground="blue", underline=True,
                               selectforeground="white")
            for coul in TEXT_COLORS.values():
                self.tag_configure(coul, foreground=coul,
                                   selectforeground="white")
                self.tag_configure(coul + "-underline", foreground=coul,
                                   selectforeground="white", underline=True)
                self.tag_configure(coul + "-overstrike", foreground=coul,
                                   overstrike=True, selectforeground="white")
        except TclError:
            self.tag_configure("underline", underline=True)
            self.tag_configure("overstrike", overstrike=True)
            self.tag_configure("link", foreground="blue", underline=True)
            self.tag_configure("file", foreground="blue", underline=True)
            for coul in TEXT_COLORS.values():
                self.tag_configure(coul, foreground=coul)
                self.tag_configure(coul + "-underline", foreground=coul,
                                   underline=True)
                self.tag_configure(coul + "-overstrike", foreground=coul,
                                   overstrike=True)
        self.tag_configure("center", justify="center")
        self.tag_configure("left", justify="left")
        self.tag_configure("right", justify="right")
        self.tag_configure("list", lmargin1=0, lmargin2=21,
                           tabs=(10, 'right', 21, 'left'))
        self.tag_configure("todolist", lmargin1=0, lmargin2=21,
                           tabs=(10, 'right', 21, 'left'))
        margin = 2 * Font(self, font=font_text).measure("m")
        self.tag_configure("enum", lmargin1=0, lmargin2=margin + 5,
                           tabs=(margin, 'right', margin + 5, 'left'))

        # --- bindings
        self.bind('<Key>', self._on_keypress)
        self.bind('<Control-Key>', self._on_ctrl_keypress)
        self.bind('<Control-z>', self.undo)
        self.bind('<Control-y>', self.redo)

        self.bind_class('Text', '<Control-y>', lambda e: None)

        self.tag_bind("link", "<Enter>",
                      lambda event: self.configure(cursor="hand1"))
        self.tag_bind("link", "<Leave>",
                      lambda event: self.configure(cursor=""))

    def update_font(self):
        """Update font after configuration change."""
        size = CONFIG.get("Font", "text_size")
        font = "%s %s" % (CONFIG.get("Font", "text_family").replace(" ", "\ "),
                          size)
        mono = "%s %s" % (CONFIG.get("Font", "mono").replace(" ", "\ "), size)
        self.configure(font=font)
        self.tag_configure("mono", font=mono)
        self.tag_configure("bold", font="%s bold" % font)
        self.tag_configure("italic", font="%s italic" % font)
        self.tag_configure("bold-italic", font="%s bold italic" % font)
        margin = 2 * Font(self, font=font).measure("m")
        self.tag_configure("enum", lmargin1=0, lmargin2=margin + 5,
                           tabs=(margin, 'right', margin + 5, 'left'))

    def mode_change(self, new_mode):
        self._undo_stack[-1].append(('mode', self.mode, new_mode))
        self.mode = new_mode

    def cb_state_change(self, cb, new_state):
        self.add_undo_sep()
        self._undo_stack[-1].append(('checkbox_state', self.index(cb), new_state))
        self.add_undo_sep()

    def undo(self, event=None):
        if self.cget("state") != "disabled":
            try:
                items = []
                # skip empty sets
                while not items:
                    items = self._undo_stack.pop()
            except IndexError:
                # empty stack
                self._undo_stack.append([])
            else:
                self._redo_stack.append(items)
                for item in reversed(items):
                    self._undo_single(item)
                if not self._undo_stack:
                    self._undo_stack.append([])
        return "break"

    def redo(self, event=None):
        if self.cget("state") != "disabled":
            try:
                items = self._redo_stack.pop()
            except IndexError:
                # empty stack
                pass
            else:
                self._undo_stack.append(items)
                for item in items:
                    self._redo_single(item)
        return "break"

    def add_undo_sep(self):
        if self._undo_stack[-1]:
            self._undo_stack.append([])
        self._redo_stack.clear()

    def _undo_single(self, item):
        if 'insert_' in item[0]:
            self.delete(item[1])
        elif item[0] == 'insert':
            self.delete(item[1], item[2])
        elif item[0] == 'link':
            self.links[item[1]] = item[2]
        elif item[0] == 'delete':
            self._restore_text_with_prop(item[1], item[3])
        elif item[0] == 'paste':
            self.delete(item[1], item[2])
        elif item[0] == 'tag_remove':
            self.tag_add(*item[1:])
        elif item[0] == 'tag_add':
            self.tag_remove(item[1], item[2], *item[3])
        elif item[0] == 'mode':
            self.mode = item[1]
            self.master.mode.set(item[1])
        elif item[0] == 'checkbox_state':
            win = self.window_cget(item[1], 'window')
            if item[2]:
                self.nametowidget(win).state(('!selected', '!alternate'))
            else:
                self.nametowidget(win).state(('selected', '!alternate'))

    def _redo_single(self, item):
        if item[0] == 'insert_char':
            self.insert(item[1], item[2])
        elif item[0] == 'insert_image':
            self.image_create(item[1], item[2])
        elif item[0] == 'insert_latex':
            index, kw, img_name, latex = item[1:]
            self.latex[img_name] = latex
            self.image_create(index, **kw)
        elif item[0] == 'insert_checkbox':
            self.checkbox_create(item[1], item[2])
        elif item[0] == 'insert':
            self.insert(item[1], item[3], *item[4])
            if self.mode != "note":
                self.tag_add(self.mode, "1.0", "end")
        elif item[0] == 'link':
            self.links[item[1]] = item[3]
        elif item[0] == 'delete':
            self.delete(item[1], item[2])
        elif item[0] == 'paste':
            self._restore_text_with_prop(item[1], item[3])
        elif item[0] == 'tag_remove':
            self.tag_remove(*item[1:])
        elif item[0] == 'tag_add':
            self.tag_add(item[1], item[2], *item[3])
        elif item[0] == 'mode':
            self.mode = item[2]
            self.master.mode.set(item[2])
        elif item[0] == 'checkbox_state':
            win = self.window_cget(item[1], 'window')
            if item[2]:
                self.nametowidget(win).state(('selected', '!alternate'))
            else:
                self.nametowidget(win).state(('!selected', '!alternate'))

    def checkbox_create(self, index, state=('!alternate',), **kw):
        kw2 = kw.copy()
        kw2['takefocus'] = False
        kw2['style'] = self.cb_style
        ch = Checkbox(self, **kw2)
        ch.state(state)
        self.window_create(index, window=ch)

    def checkbox_create_undoable(self, index, state=('!alternate',)):
        self._undo_stack[-1].append(('insert_checkbox', self.index(index), state))
        self._redo_stack.clear()
        ch = Checkbox(self, takefocus=False, style=self.cb_style)
        ch.state(state)
        self.window_create(index, window=ch)

    def image_create_undoable(self, index, **kw):
        self._undo_stack[-1].append(('insert_image', self.index(index), kw))
        self._redo_stack.clear()
        self.image_create(index, **kw)

    def link_create_undoable(self, link_nb, link):
        self._undo_stack[-1].append(('link', link_nb, self.links.get(link_nb), link))
        self._redo_stack.clear()
        self.links[link_nb] = link

    def latex_create_undoable(self, index, img_name, image, latex):
        """Insert image generated from latex expression given in the entry."""
        im = os.path.join(PATH_LATEX, img_name)
        kw = dict(align='bottom', image=image, name=im)
        self._undo_stack[-1].append(('insert_latex', self.index(index), kw, img_name, latex))
        self._redo_stack.clear()
        self.latex[img_name] = latex
        self.image_create(index, **kw)

    def tag_remove_undoable(self, tagName, index1, index2=None):
        self._undo_stack[-1].append(('tag_remove', tagName, self.index(index1),
                                    self.index(index2)))
        self.tag_remove(tagName, index1, index2)

    def tag_add_undoable(self, tagName, index1, *args):
        self._undo_stack[-1].append(('tag_add', tagName, self.index(index1), [self.index(i) for i in args]))
        self.tag_add(tagName, index1, *args)

    def _on_ctrl_keypress(self, event):
        pass

    def delete_undoable(self, index1, index2=None):
        index1 = self.index(index1)
        if index2 is None:
            index2 = self.index('{}+1c'.format(index1))
        else:
            index2 = self.index(index2)
        self._undo_stack[-1].append(('delete', index1, index2,
                                     self._copy_text(index1, index2)))
        self.delete(index1, index2)

    def insert_undoable(self, index, chars, *args):
        index1 = self.index(index)
        self.insert(index, chars, *args)
        index2 = self.index('{}+{}c'.format(index1, len(chars)))
        self._undo_stack[-1].append(('insert', index1, index2, chars, args))

    def _auto_word_replacement(self):
        if self._current_word == self.get('insert-%ic' % len(self._current_word), 'insert'):
            replacement = AUTOCORRECT.get(self._current_word)
            if replacement is not None:
                self.add_undo_sep()
                self.delete_undoable('insert-%ic' % len(self._current_word), 'insert')
                self.insert_undoable('insert', replacement)
                self.add_undo_sep()
        self._current_word = ""

    def _on_keypress(self, event):
        # --- deletion
        if event.keysym == 'BackSpace':
            self._redo_stack.clear()
            self._current_word = ""
            self.add_undo_sep()
            deb_line = self.get("insert linestart", "insert")
            tags = self.tag_names("insert")
            if self.tag_ranges("sel"):
                if self.tag_nextrange("enum", "sel.first", "sel.last"):
                    update = True
                else:
                    update = False
                self.delete_undoable("sel.first", "sel.last")
                if update:
                    self.update_enum()
            elif self.index("insert") != "1.0":
                if re.match('^\t[0-9]+\.\t$', deb_line) and 'enum' in tags:
                    self.delete_undoable("insert linestart", "insert")
                    self.insert_undoable("insert", "\t\t")
                    self.update_enum()
                elif deb_line == "\t•\t" and 'list' in tags:
                    self.delete_undoable("insert linestart", "insert")
                    self.insert_undoable("insert", "\t\t")
                elif deb_line == "\t\t":
                    self.delete_undoable("insert linestart", "insert")
                elif "todolist" in tags and self.index("insert") == self.index("insert linestart+1c"):
                    try:
                        ch = self.window_cget("insert-1c", "window")
                        self.delete_undoable("insert-1c")
                        self.children[ch.split('.')[-1]].destroy()
                        self.insert_undoable("insert", "\t\t")
                    except TclError:
                        self.delete_undoable("insert-1c")
                else:
                    self.delete_undoable("insert-1c")
            self.add_undo_sep()
            return 'break'
        elif event.keysym == 'Delete':
            self._redo_stack.clear()
            self._current_word = ""
            sel = self.tag_ranges('sel')
            if sel:
                self.add_undo_sep()
                self._undo_stack[-1].append(('delete', sel[0], sel[1],
                                             self._copy_text(*sel)))
                self.add_undo_sep()
        # --- newline
        elif event.keysym == 'Return':
            self._redo_stack.clear()
            self._auto_word_replacement()
            if self.mode == "list":
                self.add_undo_sep()
                self.insert_undoable("insert", "\n\t•\t")
                self.tag_add("list", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "todolist":
                self.add_undo_sep()
                self.insert_undoable("insert", "\n")
                self.checkbox_create_undoable("insert", ('!alternate',))
                self.tag_add("todolist", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "enum":
                self.add_undo_sep()
                self.insert_undoable("insert", "\n\t0.\t")
                self.update_enum()
                self.add_undo_sep()
            else:
                self.insert_undoable("insert", "\n")
                self.add_undo_sep()
            return 'break'
        # --- normal char
        elif event.char != '':
            self._redo_stack.clear()
            char = event.char
            self._current_word += char
            sel = self.tag_ranges('sel')
            if sel:
                self.add_undo_sep()
                self._undo_stack[-1].append(('delete', sel[0], sel[1],
                                             self._copy_text(*sel)))
                self.add_undo_sep()
                self._undo_stack[-1].append(('insert_char', sel[0], char))
            else:
                self._undo_stack[-1].append(('insert_char', self.index('insert'), char))
            if event.keysym in ['space', 'Tab']:
                self._current_word = self._current_word[:-1]
                self._auto_word_replacement()
                self.add_undo_sep()

    def _copy_text(self, index1, index2):
        """Copy text, images, checkboxes with the formatting between index1 and index2."""
        content = []
        deb = sorting(str(index1))
        fin = sorting(str(index2))
        for l in range(deb[0], fin[0] + 1):
            if l == deb[0]:
                dc = deb[1]
            else:
                dc = 0
            if l == fin[0]:
                nc = fin[1]
            else:
                nc = sorting(str(self.index('%i.end' % l)))[1]

            for c in range(dc, nc):
                index = '%i.%i' % (l, c)
                try:
                    keys = ['name', 'image', 'align', 'padx', 'pady']
                    kw = {k: self.image_cget(index, k) for k in keys}
                    tags = self.tag_names(index)
                    i = 0
                    while i < len(tags) and not re.match(r'[0-9]+\.png', tags[i]):
                        i += 1
                    if i < len(tags):
                        latex = self.latex[tags[i]]
                        content.append(('latex', kw, tags, tags[i], latex))
                    else:
                        content.append(('image', kw, tags))
                except TclError:
                    try:
                        win = self.nametowidget(self.window_cget(index, 'window'))
                        state = win.state()
                        tags = self.tag_names(index)
                        content.append(('checkbox', state, tags))
                    except TclError:
                        tags = self.tag_names(index)
                        content.append(('char', self.get(index), tags))
            if l < fin[0]:
                content.append(('char', '\n', []))
        return content

    @staticmethod
    def _apply_tag(tag, tag_dic, split=1):
        """Return HTML tag corresponding to Text tag."""
        if "-" in tag:
            tag1, tag2 = tag.split("-")[::split]
            return tag_dic.get(tag1, "") + tag_dic.get(tag2, "")
        return tag_dic.get(tag, "")

    def _checkbox_to_html(self, ch_name):
        """Return the HTML code for the checkbox."""
        ch = self.children[ch_name.split(".")[-1]]
        if 'selected' in ch.state():
            return '<input type="checkbox" checked />'
        return '<input type="checkbox" />'

    def get_rich_text(self, start='1.0', end='end'):
        """Return HTML formatted text between indices START and END."""
        tag_open_html = TAG_OPEN_HTML.copy()
        tag_close_html = TAG_CLOSE_HTML.copy()

        for nb, link in self.links.items():
            link_id = f"link#{nb}"
            if not os.path.exists(link):
                if not re.match(r'http(s)?://', link):
                    link = f'http://{link}'
            tag_open_html[link_id] = '<a href="%s" target="_blank">' % link
            tag_close_html[link_id] = "</a>"

        #~actions = {
        #~    'tagon': lambda tag: self._apply_tag(tag, tag_open_html),
        #~    'tagoff': lambda tag: self._apply_tag(tag, tag_close_html, -1),
        #~    'text': lambda text: text,
        #~    'image': lambda path: '<img src="file://%s" style="vertical-align:middle" alt="%s" />' % (path, os.path.split(path)[-1]),
        #~    'window': self._checkbox_to_html,
        #~}
        actions = {
            'tagon': lambda tag: '<b>' if tag == 'bold' else '',
            'tagoff': lambda tag: '</b>' if tag == 'bold' else '',
            'text': lambda text: text,
            'image': lambda w: '',
            'window': lambda w: '',
        }

        content = self.dump(start, end, tag=True, text=True,
                            image=True, window=True)
        html = [actions[key](value) for key, value, index in content]
        return ''.join(html)

    def _restore_text_with_prop(self, index1, content):
        """Restore text, images, checkboxes and formatting at index1."""
        self.mark_set('insert', index1)
        for c in content:
            index = self.index('insert')
            if c[0] == 'image':
                self.image_create(index, **c[1])
            elif c[0] == 'latex':
                self.image_create(index, **c[1])
                self.latex[c[3]] = c[4]
            elif c[0] == 'checkbox':
                self.checkbox_create(index, c[1])
                self.update_idletasks()
            else:
                self.insert('insert', c[1])
            for tag in c[2]:
                self.tag_add(tag, index)
        self.tag_remove('sel', '1.0', 'end')

    # --- Text style
    def toggle_text_style(self, style):
        """Toggle the style of the selected text."""
        if self.tag_ranges("sel"):
            current_tags = self.tag_names("sel.first")
            self.add_undo_sep()
            # remove tag
            if style in current_tags:
                # first char is in style so 'unstyle' the range
                tag_ranges = text_ranges(self, style, "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable(style, d, f)
                tag_ranges = text_ranges(self, "bold-italic", "sel.first", "sel.last")
                style2 = "bold" if style == "italic" else "italic"
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("bold-italic", d, f)
                    self.tag_add_undoable(style2, d, f)
            elif style == "bold" and "bold-italic" in current_tags:
                tag_ranges = text_ranges(self, "bold-italic", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("bold-italic", d, f)
                    self.tag_add_undoable("italic", d, f)
                tag_ranges = text_ranges(self, "bold", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("bold", d, f)
            elif style == "italic" and "bold-italic" in current_tags:
                tag_ranges = text_ranges(self, "bold-italic", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("bold-italic", d, f)
                    self.tag_add_undoable("bold", d, f)
                tag_ranges = text_ranges(self, "italic", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("italic", d, f)
            # add tag
            elif style == "bold":
                self.tag_add_undoable("bold", "sel.first", "sel.last")
                tag_ranges = text_ranges(self, "italic", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_add_undoable("bold-italic", d, f)
                    self.tag_remove_undoable("italic", d, f)
                    self.tag_remove_undoable("bold", d, f)
            elif style == "italic":
                self.tag_add_undoable("italic", "sel.first", "sel.last")
                tag_ranges = text_ranges(self, "bold", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_add_undoable("bold-italic", d, f)
                    self.tag_remove_undoable("italic", d, f)
                    self.tag_remove_undoable("bold", d, f)
            else:
                self.tag_add_undoable(style, "sel.first", "sel.last")
            self.add_undo_sep()

    def toggle_underline(self):
        """Toggle underline property of the selected text."""
        if self.tag_ranges("sel"):
            current_tags = self.tag_names("sel.first")
            self.add_undo_sep()
            if "underline" in current_tags:
                # first char is in style so 'unstyle' the range
                tag_ranges = text_ranges(self, "underline", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("underline", d, f)
                for coul in TEXT_COLORS.values():
                    tag_ranges = text_ranges(self, coul + "-underline", "sel.first", "sel.last")
                    for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                        self.tag_remove_undoable(coul + "-underline", d, f)
            else:
                self.tag_add_undoable("underline", "sel.first", "sel.last")
                for coul in TEXT_COLORS.values():
                    r = text_ranges(self, coul, "sel.first", "sel.last")
                    if r:
                        for deb, fin in zip(r[::2], r[1::2]):
                            self.tag_add_undoable(coul + "-underline", deb, fin)
            self.add_undo_sep()

    def toggle_overstrike(self):
        """Toggle overstrike property of the selected text."""
        if self.tag_ranges("sel"):
            current_tags = self.tag_names("sel.first")
            self.add_undo_sep()
            if "overstrike" in current_tags:
                # first char is in style so 'unstyle' the range
                tag_ranges = text_ranges(self, "overstrike", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable("overstrike", d, f)
                for coul in TEXT_COLORS.values():
                    tag_ranges = text_ranges(self, coul + "-overstrike", "sel.first", "sel.last")
                    for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                        self.tag_remove_undoable(coul + "-overstrike", d, f)
            else:
                self.tag_add_undoable("overstrike", "sel.first", "sel.last")
                for coul in TEXT_COLORS.values():
                    r = text_ranges(self, coul, "sel.first", "sel.last")
                    if r:
                        for deb, fin in zip(r[::2], r[1::2]):
                            self.tag_add_undoable(coul + "-overstrike", deb, fin)
            self.add_undo_sep()

    def change_sel_color(self, color):
        """Change the color of the selection."""
        if self.tag_ranges("sel"):
            self.add_undo_sep()
            for coul in TEXT_COLORS.values():
                tag_ranges = text_ranges(self, coul, "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable(coul, d, f)
                tag_ranges = text_ranges(self, coul + "-overstrike", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable(coul + "-overstrike", d, f)
                tag_ranges = text_ranges(self, coul + "-underline", "sel.first", "sel.last")
                for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                    self.tag_remove_undoable(coul + "-underline", d, f)
            if not color == "black":
                self.tag_add_undoable(color, "sel.first", "sel.last")
                underline = text_ranges(self, "underline", "sel.first", "sel.last")
                overstrike = text_ranges(self, "overstrike", "sel.first", "sel.last")

                for deb, fin in zip(underline[::2], underline[1::2]):
                    self.tag_add_undoable(color + "-underline", deb, fin)
                for deb, fin in zip(overstrike[::2], overstrike[1::2]):
                    self.tag_add_undoable(color + "-overstrike", deb, fin)
            self.add_undo_sep()

    def set_align(self, alignment):
        """Align the text according to alignment (left, right, center)."""
        if self.tag_ranges("sel"):
            deb = self.index("sel.first linestart")
            fin = self.index("sel.last lineend")
        else:
            deb = self.index("insert linestart")
            fin = self.index("insert lineend")
        if "\t" not in self.get(deb, fin):
            self.add_undo_sep()
            # tabulations don't support right/center alignment
            # remove old alignment tag
            for align in ['left', 'right', 'center']:
                if align != alignment:
                    tag_ranges = text_ranges(self, align, deb, fin)
                    for d, f in zip(tag_ranges[::2], tag_ranges[1::2]):
                        self.tag_remove_undoable(align, d, f)
            # set new alignment tag
            self.tag_add_undoable(alignment, deb, fin)
            self.add_undo_sep()

    def update_enum(self):
        """Update enumeration numbers."""
        lines = self.get("1.0", "end").splitlines()
        indexes = []
        for i, l in enumerate(lines):
            res = re.match('^\t[0-9]+\.\t', l)
            res2 = re.match('^\t[0-9]+\.', l)
            if res:
                indexes.append((i, res.end()))
            elif res2:
                indexes.append((i, res2.end()))
        for j, (i, end) in enumerate(indexes):
            self.delete_undoable("%i.0" % (i + 1), "%i.%i" % (i + 1, end))
            self.insert_undoable("%i.0" % (i + 1), "\t%i.\t" % (j + 1))
        self.tag_add("enum", "1.0", "end")
        self.add_undo_sep()
