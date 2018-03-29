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


Text class with improved undo/redo
"""

from tkinter import Text, TclError
from tkinter.font import Font
from tkinter.ttk import Checkbutton
from mynoteslib.constantes import sorting, CONFIG, TEXT_COLORS, PATH_LATEX
import os
import re



class Checkbox(Checkbutton):
    def __init__(self, master, **kw):
        Checkbutton.__init__(self, master, command=self.command, **kw)

    def command(self):
        self.master.cb_state_change(self, 'selected' in self.state())


class MyText(Text):

    auto_replace = {'->': '→', '<-': '←', '<->': '↔', '=>': '⇒', '<=': '⇐',
                    '<=>': '⇔', '=<': '≤', '>=': '≥', ":)": '☺'}

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

    def mode_change(self, new_mode):
        self._undo_stack[-1].append(('mode', self.mode, new_mode))
        self.mode = new_mode

    def cb_state_change(self, cb, new_state):
        self.add_undo_sep()
        self._undo_stack[-1].append(('checkbox_state', self.index(cb), new_state))
        self.add_undo_sep()

    def undo(self, event=None):
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
            replacement = self.auto_replace.get(self._current_word)
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
                    self.master.update_enum()
            elif self.index("insert") != "1.0":
                if re.match('^\t[0-9]+\.\t$', deb_line) and 'enum' in tags:
                    self.delete_undoable("insert linestart", "insert")
                    self.insert_undoable("insert", "\t\t")
                    self.master.update_enum()
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
                self.tag_add_undoable("list", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "todolist":
                self.add_undo_sep()
                self.insert_undoable("insert", "\n")
                self.checkbox_create_undoable("insert", ('!alternate',))
                self.tag_add_undoable("todolist", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "enum":
                self.add_undo_sep()
                self.insert_undoable("insert", "\n\t0.\t")
                self.master.update_enum()
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

    def _restore_text_with_prop(self, index1, content):
        """Restore text, images, checkboxes and formatting at index1."""
        self.mark_set('insert', index1)
        for c in content:
            index = self.index('insert')
            if c[0] is 'image':
                self.image_create(index, **c[1])
            elif c[0] is 'latex':
                self.image_create(index, **c[1])
                self.latex[c[3]] = c[4]
            elif c[0] is 'checkbox':
                self.checkbox_create(index, c[1])
                self.update_idletasks()
            else:
                self.insert('insert', c[1])
            for tag in c[2]:
                self.tag_add(tag, index)
        self.tag_remove('sel', '1.0', 'end')
