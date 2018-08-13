#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

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


Export dialog
"""


import re
from os.path import split, exists
from tkinter import Toplevel, Text
from tkinter.ttk import Checkbutton, Frame, Button, Separator
from mynoteslib.constants import CONFIG, TEXT_COLORS, sorting, text_ranges

TAG_OPEN_HTML = {"bold": "<b>",
                 "italic": "<i>",
                 "underline": "<u>",
                 "overstrike": "<s>",
                 "mono": "<tt>",
                 "list": "",
                 "enum": "",
                 "link": "",
                 "todolist": "",
                 "left": '\n<p style="text-align:left">\n',
                 'center': '\n<p style="text-align:center">\n',
                 'right': '\n<p style="text-align:right">\n'}

TAG_CLOSE_HTML = {"bold": "</b>",
                  "italic": "</i>",
                  "underline": "</u>",
                  "overstrike": "</s>",
                  "mono": "</tt>",
                  "list": "",
                  "enum": "",
                  "todolist": "",
                  "link": "",
                  "left": '\n</p>\n',
                  'center': '\n</p>\n',
                  'right': '\n</p>\n'}

for color in TEXT_COLORS.values():
    TAG_OPEN_HTML[color] = '<span style="color:%s">' % color
    TAG_CLOSE_HTML[color] = '</span>'

TAG_OPEN_MD = {'bold': ' **',
               'italic': ' *',
               'bold-italic': ' **_',
               "link": "",
               'mono': ' ``'}

TAG_CLOSE_MD = {'bold': '** ',
                'italic': '* ',
                'bold-italic': '_** ',
                "link": "",
                'mono': '`` '}

TAG_OPEN_RST = {'bold': ' **',
                'italic': ' *',
                "link": "",
                'mono': ' ``'}

TAG_CLOSE_RST = {'bold': '** ',
                 'italic': '* ',
                 "link": "",
                 'mono': '`` '}


def apply_formatting(balises, text_lines, obj_indexes):
    indices = list(balises.keys())
    indices.sort(key=sorting, reverse=True)
    for index in indices:
        line, col = index.split(".")
        line = int(line) - 1
        col = int(col)
        while line >= len(text_lines):
            text_lines.append("")
        l = list(text_lines[line])
        if index in obj_indexes:
            del(l[col])
        l.insert(col, "".join(balises[index]))
        text_lines[line] = "".join(l)


def md_rst_list_enum_format(mode, text_lines):
    if mode == "list":
        for i, line in enumerate(text_lines):
            if "\t•\t" in line:
                text_lines[i] = line.replace("\t•\t", "* ").strip()
            else:
                text_lines[i] = line.strip()
    elif mode == "enum":
        for i, line in enumerate(text_lines):
            res = re.match('^\t[0-9]+\.\t', line)
            if res:
                text_lines[i] = line.replace(res.group(),
                                             "%s. " % re.search("[0-9]+",
                                                                res.group()).group()).strip()
            else:
                text_lines[i] = line.strip()
    else:
        text_lines = [line.strip() for line in text_lines]


def note_to_html(data, master):
    """Convert note content to html."""
    txt = Text(master)
    tags = data["tags"]
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    txt.insert('1.0', data["txt"])

    b_open = TAG_OPEN_HTML.copy()
    b_close = TAG_CLOSE_HTML.copy()

    for key, link in data["links"].items():
        if not exists(link) and not re.match(r'http(s)?://', link):
            link = 'http://' + link
        b_open["link#%i" % key] = '<a href="%s" target="_blank">' % link
        b_close["link#%i" % key] = "</a>"

    for key in data['tags']:
        if key not in b_open:
            b_open[key] = ''
            b_close[key] = ''

    for index in indexes:
        txt.insert(index, " ")
    # restore tags
    for tag in tags:
        indices = tags[tag]
        if indices:
            txt.tag_add(tag, *indices)
    end = int(str(txt.index("end")).split(".")[0])
    for line in range(1, end):
        l_end = int(txt.index("%i.end" % line).split(".")[1])
        for col in range(l_end):
            index = "%i.%i" % (line, col)
            tags = set()
            align = None
            for tag in txt.tag_names(index):
                if tag not in ["center", "left", "right"]:
                    txt.tag_remove(tag, index)
                    if "-" in tag:
                        t1, t2 = tag.split("-")
                        tags.add(t1)
                        tags.add(t2)
                    else:
                        tags.add(tag)
                else:
                    align = tag
            tags = list(tags)
            tags.sort()
            if tags:
                txt.tag_add("-".join(tags), index)
            if align is None:
                txt.tag_add('left', index)
    left = [i.string for i in txt.tag_ranges("left")]
    right = [i.string for i in txt.tag_ranges("right")]
    center = [i.string for i in txt.tag_ranges("center")]
    # html balises
    t = txt.get("1.0", "end").splitlines()
    alignments = {"left": left, "right": right, "center": center}
    for align in alignments.values():
        a = align.copy()
        for fin, deb in zip(a[1::2], a[2::2]):
            if fin == deb or txt.index('%s+1c' % fin) == txt.index(deb):
                align.remove(fin)
                align.remove(deb)
            elif fin.split('.')[1] == '0':
                ind = align.index(fin)
                align[ind] = str(txt.index('%s-1c' % fin))

    # alignment
    for a, align in alignments.items():
        for deb, fin in zip(align[::2], align[1::2]):
            balises = {deb: [b_open[a]], fin: [b_close[a]]}
            tags = {t: text_ranges(txt, t, deb, fin) for t in txt.tag_names() if t not in ['right', 'center', 'left']}
            for tag in tags:
                for o, c in zip(tags[tag][::2], tags[tag][1::2]):
                    if o not in balises:
                        balises[o] = []
                    if c not in balises:
                        balises[c] = []
                    l = tag.split("-")
                    while "" in l:
                        l.remove("")
                    ob = "".join([b_open[t] for t in l])
                    cb = "".join([b_close[t] for t in l[::-1]])
                    balises[o].append(ob)
                    balises[c].insert(0, cb)
            # --- checkboxes and images
            for i in indexes:
                if sorting(i) >= sorting(deb) and sorting(i) <= sorting(fin):
                    if i not in balises:
                        balises[i] = []
                    tp, val = obj[i]
                    if tp == "checkbox":
                        if val:
                            balises[i].append('<input type="checkbox" checked />')
                        else:
                            balises[i].append('<input type="checkbox" />')
                    elif tp == "image":
                        balises[i].append('<img src="%s" style="vertical-align:middle" alt="%s" />' % (val, split(val)[-1]))
            apply_formatting(balises, t, indexes)
    txt.destroy()

    if data["mode"] == "list":
        for i, line in enumerate(t):
            if "\t•\t" in line:
                t[i] = ('<li>' + line.replace("\t•\t", "") + "</li>").replace('</p></li>', '</li></p>')
        t = "<br>\n".join(t)
        t = "<ul>\n%s\n</ul>" % t
    elif data["mode"] == "enum":
        for i, line in enumerate(t):
            res = re.search('\t[0-9]+\.\t', line)
            if res:
                t[i] = ("<li>" + line.replace(res.group(), "") + "</li>").replace('</p></li>', '</li></p>')
        t = "\n".join(t)
        t = "<ol>\n%s\n</ol>" % t
    else:
        t = "<br>\n".join(t)
    return t


def note_to_md(data, master):
    """Convert note content to .md"""
    txt = Text(master)
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    indexes.sort(reverse=True, key=sorting)
    tags = {tag: data['tags'][tag] for tag in data['tags'] if (tag in TAG_OPEN_MD or 'link' in tag)}

    b_open = TAG_OPEN_MD.copy()
    b_close = TAG_CLOSE_MD.copy()
    for key, link in data["links"].items():
        b_open["link#%i" % key] = '['
        b_close["link#%i" % key] = "](%s)" % link

    txt.insert('1.0', data["txt"])
    for index in indexes:
        txt.insert(index, " ")
    # restore tags
    for tag in tags:
        indices = tags[tag]
        if indices:
            txt.tag_add(tag, *indices)

    end = int(str(txt.index("end")).split(".")[0])
    for line in range(1, end):
        l_end = int(txt.index("%i.end" % line).split(".")[1])
        for col in range(l_end):
            index = "%i.%i" % (line, col)
            tags = txt.tag_names(index)
            if 'mono' in tags:  # mono clashes with other formatting
                for tag in tags:
                    if tag != 'mono':
                        txt.tag_remove(tag, index)
            elif 'link' in tags:  # remove link formatting
                for tag in tags:
                    if 'link#' not in tag:
                        txt.tag_remove(tag, index)

    formatting = {}
    for tag in txt.tag_names():
        tr = txt.tag_ranges(tag)
        for deb, fin in zip(tr[::2], tr[1::2]):
            deb = str(deb)
            fin = str(fin)
            if deb not in formatting:
                formatting[deb] = []
            if fin not in formatting:
                formatting[fin] = []
            formatting[deb].append(b_open[tag])
            formatting[fin].insert(0, b_close[tag])

    for i in indexes:
        tp, val = obj[i]
        if i not in formatting:
            formatting[i] = []
        if tp == "checkbox":
            if val:
                formatting[i].append("☒ ")
            else:
                formatting[i].append("☐ ")
        elif tp == "image":
            formatting[i].append("![%s](%s)" % (split(val)[-1], val))

    t = txt.get("1.0", "end").splitlines()
    txt.destroy()

    apply_formatting(formatting, t, indexes)
    md_rst_list_enum_format(data['mode'], t)

    return "<br>\n".join(t)


def note_to_rst(data, master):
    """Convert note content to .rst"""
    txt = Text(master)
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    indexes.sort(reverse=True, key=sorting)
    tags = {tag: data['tags'][tag] for tag in data['tags'] if (tag in TAG_OPEN_MD or 'link' in tag)}

    b_open = TAG_OPEN_RST.copy()
    b_close = TAG_CLOSE_RST.copy()
    for key, link in data["links"].items():
        b_open["link#%i" % key] = '`'
        b_close["link#%i" % key] = " <%s>`__" % link.replace(' ', '\ ')

    txt.insert('1.0', data["txt"])
    for index in indexes:
        txt.insert(index, " ")
    # restore tags
    for tag in tags:
        indices = tags[tag]
        if indices:
            txt.tag_add(tag, *indices)

    end = int(str(txt.index("end")).split(".")[0])
    for line in range(1, end):
        l_end = int(txt.index("%i.end" % line).split(".")[1])
        for col in range(l_end):
            index = "%i.%i" % (line, col)
            tags = txt.tag_names(index)
            if 'mono' in tags:  # mono clashes with other formatting
                for tag in tags:
                    if tag != 'mono':
                        txt.tag_remove(tag, index)
            elif 'link' in tags:  # remove link formatting
                for tag in tags:
                    if 'link#' not in tag:
                        txt.tag_remove(tag, index)
            elif 'bold-italic' in tags:  # bold-italic not supported by rst
                for tag in tags:
                    txt.tag_remove(tag, index)
                txt.tag_add('bold', index)

    formatting = {}
    for tag in txt.tag_names():
        tr = [str(i) for i in txt.tag_ranges(tag)]
        for i, (deb, fin) in enumerate(zip(tr[::2], tr[1::2])):
            deb_line = sorting(deb)[0]
            fin_line = sorting(fin)[0]
            if deb_line < fin_line:
                ind = 2 * i + 1
                tr.insert(ind, '%i.0' % fin_line)
                for line in range(fin_line - 1, deb_line, -1):
                    tr.insert(ind, str(txt.index('%i.end' % line)))
                    tr.insert(ind, '%i.0' % line)
                tr.insert(ind, str(txt.index('%i.end' % deb_line)))
                for i in reversed(range(len(tr) // 2)):
                    if tr[2 * i] == tr[2 * i + 1]:
                        del tr[2 * i + 1]
                        del tr[2 * i]
        for deb, fin in zip(tr[::2], tr[1::2]):
            if deb not in formatting:
                formatting[deb] = []
            if fin not in formatting:
                formatting[fin] = []
            formatting[deb].append(b_open[tag])
            formatting[fin].insert(0, b_close[tag])

    images = []
    for i in indexes:
        tp, val = obj[i]
        if i not in formatting:
            formatting[i] = []
        if tp == "checkbox":
            if val:
                formatting[i].append("☒ ")
            else:
                formatting[i].append("☐ ")
        elif tp == "image":
            name = split(val)[-1]
            formatting[i].append("|%s|" % name)
            images.append(".. |%s| image:: %s" % (name, val))

    t = txt.get("1.0", "end").splitlines()
    txt.destroy()

    apply_formatting(formatting, t, indexes)
    md_rst_list_enum_format(data['mode'], t)
    t.extend(images)
    return "\n\n".join(t)


class Export(Toplevel):
    """Category export dialog."""
    def __init__(self, master):
        """Create export dialog."""
        Toplevel.__init__(self, master, class_='MyNotes')
        self.title(_("Export"))
        self.resizable(False, False)
        self.grab_set()
        self.categories = CONFIG.options("Categories")
        self.categories.sort()
        self.categories_to_export = []
        self.only_visible = False

        # select all checkbutton
        self.ch_all = Checkbutton(self, text=_("Select all"),
                                  command=self.select_all)
        # export only visible notes checkbutton
        self.ch_only_visible = Checkbutton(self, text=_("Only visible notes"))
        self.ch_all.grid(sticky="w", padx=4, pady=4)
        self.ch_only_visible.grid(sticky="w", padx=4, pady=4)
        Separator(self).grid(sticky="ew", padx=4, pady=4)
        self.checkbuttons = []
        # one checkbutton by category
        for cat in self.categories:
            self.checkbuttons.append(Checkbutton(self, text=cat.capitalize(),
                                                 command=self.toggle_select_all))
            self.checkbuttons[-1].grid(sticky="w", padx=4, pady=4)

        frame = Frame(self)
        frame.grid()

        Button(frame, text="Ok",
               command=self.ok).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        Button(frame, text=_("Cancel"),
               command=self.destroy).grid(row=0, column=1, sticky="e", padx=4, pady=4)
        self.ch_all.state(("selected",))
        self.select_all()

    def ok(self):
        """Validate choice."""
        for ch, cat in zip(self.checkbuttons, self.categories):
            if "selected" in ch.state():
                self.categories_to_export.append(cat)
        self.only_visible = "selected" in self.ch_only_visible.state()
        self.destroy()

    def select_all(self):
        """Select all categories."""
        if ("selected" in self.ch_all.state()):
            state = "selected"
        else:
            state = "!selected"
        for ch in self.checkbuttons:
            ch.state((state,))

    def toggle_select_all(self):
        """Change select all checkbutton state when another checkbutton is clicked."""
        b = 0
        for ch in self.checkbuttons:
            if "selected" in ch.state():
                b += 1
        if b == len(self.checkbuttons):
            self.ch_all.state(("selected",))
        else:
            self.ch_all.state(("!selected",))

    def get_export(self):
        return self.categories_to_export, self.only_visible
