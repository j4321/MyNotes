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


Export dialog
"""
import re
import tarfile
import filecmp
from os.path import split, exists, join, splitext
from os import mkdir
from pickle import Pickler
from tempfile import TemporaryDirectory
from shutil import copyfile
from tkinter import Toplevel, Text, StringVar, Menu
from tkinter.ttk import Checkbutton, Frame, Button, Separator, Menubutton, Label

from mynoteslib.constants import CONFIG, TEXT_COLORS, sorting, text_ranges
from mynoteslib.checkboxtreeview import CheckboxTreeview
from mynoteslib.autoscrollbar import AutoScrollbar as Scrollbar


EXT_DICT = {_("Notes (.notes)"): '.notes',
            _("HTML file (.html)"): '.html',
            _("Markdown file (.md)"): '.md',
            _("reStructuredText file (.rst)"): '.rst'}

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
               'code': "    ",
               'code_start': "\n\n    ",
               'mono': ' ``'}

TAG_CLOSE_MD = {'bold': '** ',
                'italic': '* ',
                'bold-italic': '_** ',
                "link": "",
                "code_end": "\n",
                'mono': '`` '}

TAG_OPEN_RST = {'bold': ' **',
                'italic': ' *',
                "link": "",
                'code_start': "\n\n::\n\n    ",
                'code': "    ",
                'mono': ' ``'}

TAG_CLOSE_RST = {'bold': '** ',
                 'italic': '* ',
                 "link": "",
                 "code_end": "\n",
                 'mono': '`` '}


def make_archive(archive, data, extension, text, latex={}, pickle=False):
    """
    Create archive containing notes and data (images, ...).

    * archive: archive path
    * data: {name: path}
    * extension: extension for the notes
    * text: exported notes
    """

    with TemporaryDirectory() as tmpdir:
        # create archive root directory
        local_dir_name, ext = splitext(split(archive)[1])
        while ext:
            local_dir_name, ext = splitext(local_dir_name)
        local_dir = join(tmpdir, local_dir_name)
        mkdir(local_dir)
        # create data directory
        data_dir = join(local_dir, 'data')
        mkdir(data_dir)
        if latex:
            latex_dir = join(local_dir, 'latex')
            mkdir(latex_dir)
        # create note file
        filename = splitext(local_dir_name)[0] + extension
        tmpfile = join(local_dir, filename)
        if pickle:
            with open(tmpfile, "wb") as fich:
                dp = Pickler(fich)
                dp.dump(text)
        else:
            with open(tmpfile, 'w') as f:
                f.write(text)
        with tarfile.open(name=archive, mode='w') as tar:
            tar.add(tmpfile, arcname=join(local_dir_name, filename))
            for name, path in data.items():
                copyfile(path, join(data_dir, name))
                tar.add(join(data_dir, name), arcname=join(local_dir_name, 'data', name))
            for name, path in latex.items():
                copyfile(path, join(data_dir, name))
                tar.add(join(data_dir, name), arcname=join(local_dir_name, 'latex', name))


def md_rst_generate_formatting_dict(txt, b_open, b_close):

    def add_to_formatting(deb, fin, tag):
        if deb not in formatting:
            formatting[deb] = []
        if fin not in formatting:
            formatting[fin] = []
        try:
            formatting[deb].append(b_open[tag])
            formatting[fin].insert(0, b_close[tag])
        except KeyError:
            # error due to notes created before links restoration was fixed
            pass

    def add_to_formatting_single(index, b, tag):
        if index not in formatting:
            formatting[index] = []
        formatting[index].append(b[tag])

    formatting = {}
    tags = [tag for tag in txt.tag_names() if tag != 'mono']
    for tag in tags:
        tr = [str(i) for i in txt.tag_ranges(tag)]
        for i, (deb, fin) in enumerate(zip(tr[::2], tr[1::2])):
            deb_line = sorting(deb)[0]
            fin_line, fin_col = sorting(fin)
            while fin_col == 0:
                fin = str(txt.index("%s-1c" % fin))
                fin_line, fin_col = sorting(fin)
            if deb_line < fin_line:
                ind = str(txt.index('%i.end' % deb_line))
                if ind != deb:
                    add_to_formatting(deb, ind, tag)
                for line in range(deb_line + 1, fin_line):
                    ind1 = '%i.0' % line
                    ind2 = str(txt.index('%i.end' % line))
                    if ind1 != ind2:
                        add_to_formatting(ind1, ind2, tag)
                ind = '%i.0' % fin_line
                if ind != fin:
                    add_to_formatting(ind, fin, tag)
            elif deb_line == fin_line:
                add_to_formatting(deb, fin, tag)
    # mono
    tr = [str(i) for i in txt.tag_ranges('mono')]
    for i, (deb, fin) in enumerate(zip(tr[::2], tr[1::2])):
        deb_line = sorting(deb)[0]
        fin_line, fin_col = sorting(fin)
        while fin_col == 0:
            fin = str(txt.index("%s-1c" % fin))
            fin_line, fin_col = sorting(fin)
        if deb_line < fin_line:
            add_to_formatting_single(deb, b_open, 'code_start')
            for line in range(deb_line + 1, fin_line):
                ind = '%i.0' % line
                add_to_formatting_single(ind, b_open, 'code')
            ind = '%i.0' % fin_line
            add_to_formatting_single(ind, b_open, 'code')
            add_to_formatting_single(fin, b_close, 'code_end')
        elif deb_line == fin_line:
            add_to_formatting(deb, fin, 'mono')
    return formatting


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


def md_rst_line_cleanup(line):
    """Strip line and remove space just after/before bold or italic start/end."""
    l = line
    if l[:2] == ' *' or l[:3] == ' ``':
        l = l[1:]
    for res in re.finditer(r'\*[^\*]+\*', l):
        ch = res.group()
        if not re.match(r'^\*[ ]+\*$', ch):
            l = l.replace(ch, '*%s*' % ch[1:-1].strip(' '))
    for res in re.finditer(r'``(.)+``', l):
        ch = res.group()
    for res in re.finditer(r'``[^``]+``', l):
        ch = res.group()
        l = l.replace(ch, '``%s``' % ch[2:-2].strip(' '))
    return l


def md_rst_list_enum_format(mode, text_lines):
    if mode == "list":
        for i, line in enumerate(text_lines):
            text_lines[i] = md_rst_line_cleanup(line)
            if "\t•\t" in line:
                text_lines[i] = text_lines[i].replace("\t•\t", "* ")
    elif mode == "enum":
        for i, line in enumerate(text_lines):
            res = re.match('^\t[0-9]+\.\t', line)
            if res:
                line = line.replace(res.group(),
                                    "%s. " % re.search("[0-9]+",
                                                       res.group()).group())
            text_lines[i] = md_rst_line_cleanup(line)
    else:
        for i, line in enumerate(text_lines):
            text_lines[i] = md_rst_line_cleanup(line)


def export_filename(filepath, datafiles, local_dir='data'):
    """For rst, md and html"""
    path, name = split(filepath)
    name, ext = splitext(name)
    if filepath in datafiles.values():
        # file is already in archive
        i = list(datafiles.values()).index(filepath)
        return join(local_dir, list(datafiles.keys())[i])
    if name + ext in datafiles:
        if filecmp.cmp(filepath, datafiles[name + ext], shallow=False):
            # the file are identical
            return join(local_dir, name + ext)
        name = name + '-%i'
        i = 1
        while name % i + ext in datafiles:
            if filecmp.cmp(filepath, datafiles[name % i + ext], shallow=False):
                # the file are identical
                return join(local_dir, name % i + ext)
            i += 1
        name = name % i
    datafiles[name + ext] = filepath
    return join(local_dir, name + ext)  # new path


def note_to_html(data, master, export_data, datafiles):
    """Convert note content to html."""
    txt = Text(master)
    tags = data["tags"]
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    txt.insert('1.0', data["txt"])

    b_open = TAG_OPEN_HTML.copy()
    b_close = TAG_CLOSE_HTML.copy()
    for key, link in data["links"].items():
        if not exists(link):
            if not re.match(r'http(s)?://', link):
                link = 'http://' + link
        elif export_data:
            link = export_filename(link, datafiles)
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
                elif align is None:
                    align = tag
                else:
                    txt.tag_remove(align, index)
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
                        if export_data and exists(val):
                            val = export_filename(val, datafiles)
                        balises[i].append('<img src="%s" style="vertical-align:middle" alt="%s" />' % (val, split(val)[-1]))
            apply_formatting(balises, t, indexes)
    txt.destroy()

    while '' in t:
        t.remove('')

    if data["mode"] == "list":
        for i, line in enumerate(t):
            if "\t•\t" in line:
                line = ('<li>' + line.replace("\t•\t", "") + "</li>").replace('</p></li>', '</li></p>')
                res = re.match(r'<li>\n<p(.)*>\n', line)
                if res:
                    ch = res.group()
                    line = line.replace(ch, ch[4:] + '<li>')
                line = line.replace('</p>\n</li>', '</li>\n</p>')
                t[i] = line
        t = "\n".join(t)
        t = "<ul>\n%s\n</ul>" % t
    elif data["mode"] == "enum":
        for i, line in enumerate(t):
            res = re.search('\t[0-9]+\.\t', line)
            if res:
                line = ("<li>" + line.replace(res.group(), "") + "</li>").replace('</p></li>', '</li></p>')
                res = re.match(r'<li>\n<p(.)*>\n', line)
                if res:
                    ch = res.group()
                    line = line.replace(ch, ch[4:] + '<li>')
                line = line.replace('</p>\n</li>', '</li>\n</p>')
                t[i] = line
        t = "\n".join(t)
        t = "<ol>\n%s\n</ol>" % t
    else:
        t = "<br>\n".join(t)
        t = t.replace('</p>\n<br>', '</p>\n')
    return t


def note_to_md(data, master, export_data, datafiles):
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
        if export_data and exists(link):
            link = export_filename(link, datafiles)
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

    formatting = md_rst_generate_formatting_dict(txt, b_open, b_close)

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
            if export_data and exists(val):
                val = export_filename(val, datafiles)
            formatting[i].append("![%s](%s)" % (split(val)[-1], val))

    t = txt.get("1.0", "end").splitlines()
    txt.destroy()

    apply_formatting(formatting, t, indexes)
    md_rst_list_enum_format(data['mode'], t)

    return "\n\n".join(t)


def note_to_rst(data, master, export_data, datafiles):
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
        if export_data and exists(link):
            link = export_filename(link, datafiles)
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

    formatting = md_rst_generate_formatting_dict(txt, b_open, b_close)

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
            if export_data and exists(val):
                val = export_filename(val, datafiles)
            name = val.replace(' ', '\ ')
#            name = split(val)[-1]
            formatting[i].append("|%s|" % name)
            images.append(".. |%s| image:: %s" % (name, val))

    t = txt.get("1.0", "end").splitlines()
    txt.destroy()

    apply_formatting(formatting, t, indexes)
    md_rst_list_enum_format(data['mode'], t)
    t = "\n\n".join(t).replace('\\', '\\\\')  # escape backslashes
    return t, images


EXPORT_FCT = {'.rst': note_to_rst, '.md': note_to_md, '.html': note_to_html}


def merge_notes_html(cats):
    text = ""
    for cat in cats:
        if cats[cat]:
            # skip empty categories
            cat_txt = "<h1 style='text-align:center'>" + _("Category: {category}").format(category=cat) + "<h1/>\n\n"
            text += cat_txt
            for title, txt in cats[cat]:
                text += "<h2 style='text-align:center'>%s</h2>\n\n" % title
                text += txt
                text += "\n<br>\n<hr /><br>\n\n"
            text += '<hr style="height: 8px;background-color:grey" /><br>\n'
    text = text.encode('ascii', 'xmlcharrefreplace').decode("utf-8")
    text = '<body style="max-width:30em">\n%s\n</body>' % text
    return text


def merge_notes_md(cats):
    text = ""
    for cat in cats:
        if cats[cat]:  # skip empty categories
            cat_txt = _("Category: {category}").format(category=cat) + "\n"
            text += cat_txt
            text += "=" * len(cat_txt)
            text += "\n\n"
            for title, txt in cats[cat]:
                text += title
                text += "\n" + "-" * len(title) + "\n\n"
                text += txt
                text += "\n\n" + "-" * 30 + "\n\n"
            text += "-" * 30 + "\n\n"
    return text


def merge_notes_rst(cats):
    text = ""
    images = set()
    for cat in cats:
        if cats[cat]:   # skip empty categories
            cat_txt = _("Category: {category}").format(category=cat) + "\n"
            text += cat_txt
            text += "=" * len(cat_txt)
            text += "\n\n"
            for title, (txt, img) in cats[cat]:
                images = images.union(set(img))
                text += title
                text += "\n" + "-" * len(title) + "\n\n"
                text += "\n\n"
                text += txt if txt else '...'
                text += "\n\n" + "-" * 30 + "\n\n"
            text = text[:-32]
            text += "#" * 30
            text += "\n\n"
    if text:
        text = text[:-34]
        if text[-30:] == "-" * 30:
            text = text[:-30]
    text = text + '\n\n' + '\n\n'.join(images)
    return text


MERGE_FCT = {'.rst': merge_notes_rst, '.md': merge_notes_md, '.html': merge_notes_html}


class Export(Toplevel):
    """Category export dialog."""
    def __init__(self, master, note_data):
        """Create export dialog."""
        Toplevel.__init__(self, master, class_='MyNotes')
        self.title(_("Export"))
        self.minsize(350, 250)
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.note_data = note_data
        self.categories = CONFIG.options("Categories")
        self.categories.sort()
        self.notes_to_export = []
        self.export_type = None
        self.export_data = False

        # export type
        self.type = StringVar(self, _("Notes (.notes)"))

        type_frame = Frame(self)
        menu_type = Menu(self, tearoff=False)
        for etype in EXT_DICT:
            menu_type.add_radiobutton(label=etype, value=etype, variable=self.type)
        mb = Menubutton(type_frame, menu=menu_type, textvariable=self.type, width=max([int(len(key) * 0.8) for key in EXT_DICT]))
        Label(type_frame, text=_('Export to')).pack(side='left', padx=4)
        mb.pack(side='left', padx=4)
        type_frame.grid(row=0, columnspan=2, sticky='w', pady=4)

        Separator(self).grid(columnspan=2, sticky="ew", padx=4, pady=4)

        # export only visible notes checkbutton
        self.ch_only_visible = Checkbutton(self, text=_("Only visible notes"),
                                           command=self.select_only_visible)
        self.ch_only_visible.grid(columnspan=2, sticky="w", padx=4, pady=4)

        # note selection
        self.tree = CheckboxTreeview(self, show='tree')
        self.tree.grid(row=3, sticky="nsew", padx=4, pady=4)
        scroll = Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=3, column=1, sticky='ns')

        self.tree.insert('', 'end', 'root', text=_('Categories'))
        for cat in self.categories:
            self.tree.insert('root', 'end', cat, text=cat.capitalize())
        for key, data in self.note_data.items():
            self.tree.insert(data['category'], 'end', key,
                             text='{} - {}'.format(data['title'], data.get('date', '??')),
                             tags=['visible'] if data['visible'] else [])
        for cat in self.categories:
            if not self.tree.get_children(cat):
                self.tree.detach(cat)
        self.tree.bind('<<Checked>>', self.toggle_select_visible)
        self.tree.bind('<<Unchecked>>', self.toggle_select_visible)

        Separator(self).grid(sticky="ew", columnspan=2, padx=4, pady=4)
        self.ch_export_data = Checkbutton(self, text=_('Export data (pictures and linked files)'))
        self.ch_export_data.grid(sticky="w", columnspan=2, padx=4, pady=4)

        frame = Frame(self)
        frame.grid(columnspan=2)

        Button(frame, text="Ok",
               command=self.ok).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        Button(frame, text=_("Cancel"),
               command=self.destroy).grid(row=0, column=1, sticky="e", padx=4, pady=4)
        self.tree.check_item('root')
        self.tree.expand_all()
        self.toggle_select_visible()

    def ok(self):
        """Validate choice."""
        self.notes_to_export = self.tree.get_checked()
        self.export_type = self.type.get()
        self.export_data = "selected" in self.ch_export_data.state()
        self.destroy()

    def select_only_visible(self):
        """Select only visible notes."""
        for cat in self.categories:
            for item in self.tree.get_children(cat):
                if self.tree.tag_has('visible', item):
                    self.tree.check_item(item)
                else:
                    self.tree.uncheck_item(item)

    def toggle_select_visible(self, event=None):
        """Change select all checkbutton state when another checkbutton is clicked."""
        checked = list(self.tree.get_checked())
        checked.sort()
        visible = list(self.tree.tag_has('visible'))
        visible.sort()
        self.ch_only_visible.state(['!' * (visible != checked) + 'selected'])

    def get_export(self):
        return self.export_type, self.notes_to_export, self.export_data
