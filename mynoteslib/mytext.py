#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 14 13:00:10 2018

@author: juliette
"""

from tkinter import Text, TclError
from tkinter.ttk import Checkbutton
from tkfilebrowser import askopenfilename
from mynoteslib import constantes as cst
import re


class Checkbox(Checkbutton):
    def __init__(self, master, **kw):
        Checkbutton.__init__(self, master, command=self.command, **kw)

    def command(self):
        self.master.cb_state_change(self, 'selected' in self.state())


class MyText(Text):
    def __init__(self, master=None, mode='note', **kw):
        Text.__init__(self, master, **kw)

        self.mode = mode

        self._undo_stack = [[]]
        self._redo_stack = []

        self.bind('<Key>', self._on_keypress)
        self.bind('<Control-Key>', self._on_ctrl_keypress)
        self.bind('<Control-z>', self.undo)
        self.bind('<Control-y>', self.redo)
#        self.bind('<<Cut>>', self._on_cut)
#        self.bind('<<BeforePaste>>', self._on_before_paste)
#        self.bind('<<Paste>>', self._on_paste)
        self.bind_class('Text', '<Control-y>', lambda e: None)

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
        elif item[0] == 'insert_window':
            self.window_create(item[1], **item[2])
        elif item[0] == 'insert':
            self.insert(item[1], item[3], *item[4])
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

    def image_create_undoable(self, index, cnf={}, **kw):
        self._undo_stack[-1].append(('insert_image', self.index(index), kw))
        self._redo_stack.clear()
        self.image_create(index, cnf, **kw)

    def window_create_undoable(self, index, cnf={}, **kw):
        win = cnf.pop('window', None) or kw.pop('window', None)
        if win:
            props = {key: win.cget(key) for key in win.keys()}
            props['master'] = self

            if 'class' in props and not props['class']:
                del props['class']

            def create():
                return win.__class__(**props)

            kw['create'] = create
        self._undo_stack[-1].append(('insert_window', self.index(index), kw))
        self._redo_stack.clear()
        Text.window_create(self, index, cnf, **kw)

    def window_create(self, index, cnf={}, **kw):
        win = cnf.pop('window', None) or kw.pop('window', None)
        if win:
            win = kw.pop('window')
            props = {key: win.cget(key) for key in win.keys()}
            props['master'] = self

            if 'class' in props and not props['class']:
                del props['class']

            def create():
                return win.__class__(**props)

            kw['create'] = create

        Text.window_create(self, index, cnf, **kw)

    def tag_remove_undoable(self, tagName, index1, index2=None):
        self._undo_stack[-1].append(('tag_remove', tagName, self.index(index1),
                                    self.index(index2)))
        self.tag_remove(tagName, index1, index2)

    def tag_add_undoable(self, tagName, index1, *args):
        self._undo_stack[-1].append(('tag_add', tagName, self.index(index1), [self.index(i) for i in args]))
        self.tag_add(tagName, index1, *args)

    def _on_ctrl_keypress(self, event):
        pass

#    def _on_cut(self, event):
#        self._redo_stack.clear()
#        sel = self.tag_ranges('sel')
#        if sel:
#            index1, index2 = self.index(sel[0]), self.index(sel[1])
#            self.add_undo_sep()
#            self._undo_stack[-1].append(('delete', index1, index2,
#                                         self._copy_text(index1, index2)))
#            self.add_undo_sep()
#
#    def _on_paste(self, event):
#        index1 = self._undo_stack[-1][1]
#        index2 = self.index('insert')
#        self._undo_stack[-1][-1].extend([index2, self._copy_text(index1, index2)])
#        self.add_undo_sep()
#
#    def _on_before_paste(self, event):
#        self.add_undo_sep()
#        self._undo_stack[-1].append(['paste', self.index('insert')])

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

    def _on_keypress(self, event):
        if event.keysym == 'BackSpace':
            self._redo_stack.clear()
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

#            sel = self.tag_ranges('sel')
#            if sel:
#                index1, index2 = self.index(sel[0]), self.index(sel[1])
#                self.add_undo_sep()
#                self._undo_stack[-1].append(('delete', index1, index2,
#                                             self._copy_text(index1, index2)))
#                self.add_undo_sep()
#            else:
#                index = self.index('insert-1c')
#                index2 = self.index('insert')
#                if index != index2:
#                    self.add_undo_sep()
#                    self._undo_stack[-1].append(('delete', index, index2,
#                                                 self._copy_text(index, index2)))
#                    self.add_undo_sep()
        elif event.keysym == 'Return':
            self._redo_stack.clear()
            if self.mode == "list":
                self.add_undo_sep()
                event.widget.insert_undoable("insert", "\n\t•\t")
                event.widget.tag_add_undoable("list", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "todolist":
                self.add_undo_sep()
                event.widget.insert_undoable("insert", "\n")

                def create():
                    ch = Checkbox(event.widget, takefocus=False,
                                     style=event.widget.master.id + ".TCheckbutton")
                    return ch

                event.widget.window_create_undoable("insert", create=create)
                event.widget.tag_add_undoable("todolist", "1.0", "end")
                self.add_undo_sep()
            elif self.mode == "enum":
                self.add_undo_sep()
                event.widget.insert_undoable("insert", "\n\t0.\t")
                event.widget.master.update_enum()
                self.add_undo_sep()
            else:
                event.widget.insert_undoable("insert", "\n")
                self.add_undo_sep()
            return 'break'
        elif event.char != '':
            self._redo_stack.clear()
            char = event.char
            sel = self.tag_ranges('sel')
            if sel:
                print(sel)
                self.add_undo_sep()
                self._undo_stack[-1].append(('delete', sel[0], sel[1],
                                             self._copy_text(*sel)))
                self.add_undo_sep()
                self._undo_stack[-1].append(('insert_char', sel[0], char))
            else:
                self._undo_stack[-1].append(('insert_char', self.index('insert'), char))
            if event.keysym in ['space', 'Tab']:
                self.add_undo_sep()

    def _copy_text(self, index1, index2):
        content = []
        deb = cst.sorting(str(index1))
        fin = cst.sorting(str(index2))
        for l in range(deb[0], fin[0] + 1):
            if l == deb[0]:
                dc = deb[1]
            else:
                dc = 0
            if l == fin[0]:
                nc = fin[1]
            else:
                nc = cst.sorting(str(self.index('%i.end' % l)))[1]

            for c in range(dc, nc):
                index = '%i.%i' % (l, c)
                try:
                    keys = ['name', 'image', 'align', 'padx', 'pady']
                    kw = {k: self.image_cget(index, k) for k in keys}
                    tags = self.tag_names(index)
                    content.append(('image', kw, tags))
                except TclError:
                    try:
                        keys = ['align', 'padx', 'pady', 'stretch', 'create']
                        kw = {k: self.window_cget(index, k) for k in keys}
                        try:
                            state = self.nametowidget(self.window_cget(index, 'window')).state()
                        except AttributeError:
                            state = None
                        tags = self.tag_names(index)
                        content.append(('window', kw, tags, state))
                    except TclError:
                        tags = self.tag_names(index)
                        content.append(('char', self.get(index), tags))
            if l < fin[0]:
                content.append(('char', '\n', []))
        return content

    def _restore_text_with_prop(self, index1, content):
        self.mark_set('insert', index1)
        for c in content:
            index = self.index('insert')
            if c[0] is 'image':
                self.image_create(index, **c[1])
            elif c[0] is 'window':
                self.window_create(index, **c[1])
                self.update_idletasks()
                if c[3]:
                    win = self.nametowidget(self.window_cget(index, 'window'))
                    win.state(c[3])
            else:
                self.insert('insert', c[1])
            for tag in c[2]:
                self.tag_add(tag, index)
        self.tag_remove('sel', '1.0', 'end')


if __name__ == '__main__':
    from tkinter import Tk, PhotoImage, Button
    from tkinter.ttk import Checkbutton, Style

    def add_image():
        file = askopenfilename(root)
        if file:
            t.images.append(PhotoImage(file=file, master=root))
            t.image_create_undoable('insert', image=t.images[-1])

    def add_ch():
#        ch = Checkbutton(t)
#        ch.state(('selected', '!alternate' ))
        def create():
            return Checkbox(t)

        t.add_undo_sep()
        index = t.index('insert')
        t.window_create_undoable('insert', create=create)
        t.update_idletasks()
        t.nametowidget(t.window_cget(index, 'window')).state(('selected', '!alternate'))
#        t.window_create_undoable('insert', window=ch)
        t.add_undo_sep()

    root = Tk()
    s = Style(root)
    s.theme_use('clam')
    t = MyText(root, mode='list')
    t.images = []
    t.pack()
    Button(root, text='Image', command=add_image).pack()
    Button(root, text='Ch', command=add_ch).pack()
#    root.mainloop()
