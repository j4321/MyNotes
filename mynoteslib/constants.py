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

The scroll.png image is a modified version of the slider-vert.png assets from
the arc-theme https://github.com/horst3180/arc-theme
Copyright 2015 horst3180 (https://github.com/horst3180)

The png icons are modified versions of icons from the elementary project
(the xfce fork to be precise https://github.com/shimmerproject/elementary-xfce)
Copyright 2007-2013 elementary LLC.


The images IM_INFO_DATA, IM_ERROR_DATA, IM_QUESTION_DATA and IM_WARNING_DATA
were taken from "icons.tcl":

    A set of stock icons for use in Tk dialogs. The icons used here
    were provided by the Tango Desktop project which provides a
    fied set of high quality icons licensed under the
    Creative Commons Attribution Share-Alike license
    (http://creativecommons.org/licenses/by-sa/3.0/)

    See http://tango.freedesktop.org/Tango_Desktop_Project

    Copyright (c) 2009 Pat Thoyts <patthoyts@users.sourceforge.net>


Constants and functions
"""



import time
import platform
import os
import gettext
from configparser import ConfigParser
from locale import getdefaultlocale, setlocale, LC_ALL
from subprocess import check_output, CalledProcessError
from tkinter import Text
import ewmh
import warnings
from PIL import Image, ImageDraw


EWMH = ewmh.EWMH()

SYMBOLS = 'ΓΔΘΛΞΠΣΦΨΩαβγδεζηθικλμνξοπρςστυφχψωϐϑϒϕϖæœ«»¡¿£¥$€§ø∞∀∃∄∈∉∫∧∨∩∪÷±√∝∼≃≅≡≤≥≪≫≲≳▪•✭✦➔➢✔▴▸✗✚✳☎✉✎♫⚠⇒⇔'

# --- paths
PATH = os.path.dirname(__file__)

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files and sticky notes data
    LOCAL_PATH = PATH
    PATH_LOCALE = os.path.join(PATH, "locale")
    PATH_IMAGES = os.path.join(PATH, "images")
    PATH_DATA_BACKUP = os.path.join(LOCAL_PATH, "backup", "notes.backup%i")
    PATH_DATA = os.path.join(LOCAL_PATH, "backup", "notes")
    PATH_DATA_INFO = os.path.join(LOCAL_PATH, "backup", "notes.info")
    if not os.path.exists(os.path.join(LOCAL_PATH, "backup")):
        os.mkdir(os.path.join(LOCAL_PATH, "backup"))
else:
    # local directory containing config files and sticky notes data
    LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".mynotes")
    if not os.path.isdir(LOCAL_PATH):
        os.mkdir(LOCAL_PATH)
    PATH_LOCALE = "/usr/share/locale"
    PATH_IMAGES = "/usr/share/mynotes/images"
    PATH_DATA_BACKUP = os.path.join(LOCAL_PATH, "notes.backup%i")
    PATH_DATA = os.path.join(LOCAL_PATH, "notes")
    PATH_DATA_INFO = os.path.join(LOCAL_PATH, "notes.info")

PATH_CONFIG = os.path.join(LOCAL_PATH, "mynotes.ini")
PATH_LATEX = os.path.join(LOCAL_PATH, "latex")
PIDFILE = os.path.join(LOCAL_PATH, "mynotes.pid")

if not os.path.exists(PATH_LATEX):
    os.mkdir(PATH_LATEX)


# --- images files
IM_ICON = os.path.join(PATH_IMAGES, "mynotes.png")
IM_ICON_24 = os.path.join(PATH_IMAGES, "mynotes24.png")
IM_ICON_48 = os.path.join(PATH_IMAGES, "mynotes48.png")
IM_CLOSE = os.path.join(PATH_IMAGES, "close.png")
IM_CLOSE_ACTIVE = os.path.join(PATH_IMAGES, "close_active.png")
IM_ROLL = os.path.join(PATH_IMAGES, "roll.png")
IM_ROLL_ACTIVE = os.path.join(PATH_IMAGES, "roll_active.png")
IM_LOCK = os.path.join(PATH_IMAGES, "verr.png")
IM_PLUS = os.path.join(PATH_IMAGES, "plus.png")
IM_MOINS = os.path.join(PATH_IMAGES, "moins.png")
IM_DELETE_16 = os.path.join(PATH_IMAGES, "delete_16.png")
IM_DELETE = os.path.join(PATH_IMAGES, "delete.png")
IM_SELECT_ALL = os.path.join(PATH_IMAGES, "select_all.png")
IM_DESELECT_ALL = os.path.join(PATH_IMAGES, "deselect_all.png")
IM_CHANGE = os.path.join(PATH_IMAGES, "change.png")
IM_VISIBLE = os.path.join(PATH_IMAGES, "visible.png")
IM_HIDDEN = os.path.join(PATH_IMAGES, "hidden.png")
IM_VISIBLE_24 = os.path.join(PATH_IMAGES, "visible_24.png")
IM_HIDDEN_24 = os.path.join(PATH_IMAGES, "hidden_24.png")
IM_CLIP = os.path.join(PATH_IMAGES, "clip.png")
IM_SCROLL_ALPHA = os.path.join(PATH_IMAGES, "scroll.png")

# --- images data
IM_ERROR_DATA = """
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
"""

IM_QUESTION_DATA = """
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
SUVORK5CYII=
"""

IM_INFO_DATA = """
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
9Uqvu3HLjfhvTUo85WzjhogAAAAASUVORK5CYII=
"""

IM_WARNING_DATA = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAABSZJREFU
WIXll1toVEcYgL+Zc87u2Yu7MYmrWRuTJuvdiMuqiJd4yYKXgMQKVkSjFR80kFIVJfWCWlvpg4h9
8sXGWGof8iKNICYSo6JgkCBEJRG8ImYThNrNxmaTeM7pQ5IlJkabi0/9YZhhZv7///4z/8zPgf+7
KCNRLgdlJijXwRyuDTlcxV9hbzv8nQmxMjg+XDtiOEplkG9PSfkztGmTgmFQd+FCVzwa3fYN/PHZ
AcpBaReicW5xcbb64IEQqko8Lc26d/58cxS+/BY6hmJvyEfQBoUpwWCmW1FErKaGWHU13uRk4QkE
UtxQNFR7QwIoB4eiKD9PWbVKbb10CZmaCqmpxCormRYO26QQx85B0mcD+AeK0xYvHqu1tNDx+DH6
gQM4jh0j3tCA3tGBLyfHLuD7zwJwAcYqun44sHy51nr5MsqsWWj5+djCYdS5c4ldvUr24sU2qarf
lUL6qAN0wqH0vDy7+fAhXZEI+v79CNmt7igpofPVK5SmJvyhkJBwYlQBSiHd7vUWZ86bp8WqqtCW
LkVbuBAhBEIItGAQ2+rVxG7cICMY1KTDsekc5IwagIQTmStXis47dzBiMfR9+xCi+wb39s79+zFi
MczGRjLmzTMlnBoVgLMwyzF+/Cb/lClq2/Xr2AoKUKdPxzAMWltbiUajmKaJkpGBY8sW3tbW4g8E
VNXrXVEKK0YMoMKp7Px8K15Tg2VZOHbvBiASiRAMBgkGg0QiEYQQOIuLsRSFrnv3yJo/HxVOW594
7D4KUAa57qysvNSUFOVtbS32rVuRfj9CCFwuV2Kfy+VCCIFMScFVVET7/fukJidLm883rQy+HhaA
BUII8cvUNWt4W1WFcLvRd+5MnHl/AOjOB+eOHchx44jX1ZEdCqkSTpaDbcgA5+GrpNmzc9ymKdvr
67Hv2oVMSko4cjgcKIqCoijoup64EdLpxLV3Lx1PnuCVUrgmTfK9hV1DAjgKqlSUk1PCYdl25QrS
70cvLEw4SWS+04nT6XxvXgiBc8MGtKlTaa+rIysnR1Ok/OF38PxngAzY4VuwYKL99WvR8fQpjj17
kLqeiL6393g8eDyeAWBSVfEcOkRXczOOaBRvVpZuDPJEDwD4DVyKrv+UlZurxSorUWfMQC8oGOBc
CDHgC/Rdc4TD2BctIl5fT+bkyTahaXvOw8RPApiwd2Ju7hjZ2EhXSwvOkhKQcoADgIqKCioqKgYc
QW9LOnIEIxZDbWpiXCCABT9+FKAUxtm83pKMUEiLVVejLVqEtmTJB50LIdi2bRuFPbnRd7232efM
wbVuHR2PHjHR77dJXS8sg5mDAihweFJenmrevYvR1oazpGTQ6IQQaJqG7ClI/dd655IOHsSyLMSL
F6QFAib9nugEQClk2Xy+orTsbK3t1i3sa9ei5eQMGr0QgvLyci5evDiocyEEtsxMPNu30/nsGRO8
XlVzu8NlkNvrV+0T/fHMZcusrtu3MeNx9PXrobUVq8cYQrw3TrRub1h9+v573Bs3Ej1zBvP5c/zp
6dbLhoaTwPy+ANKCfF92thq7dg2A6JYt/fNlxGK8eUNSerryHEJHQT8K8V4A5ztojty8OeaLzZul
1DSwLCzDANPEMozusWFgmWZ33288YK3/nGlixuM0v3xpWfDX0Z4i1VupXEWwIgRnJfhGPfQ+YsLr
+7DzNFwCuvqWyiRg7DSYoIBu9smPkYqEd4AwIN4ITUAL0A4Da7UC6ICdEfy2fUBMoAvo7GnWKNoe
mfwLcAuinuFNL7QAAAAASUVORK5CYII=
"""

ICONS = {"information": IM_INFO_DATA, "error": IM_ERROR_DATA,
         "question": IM_QUESTION_DATA, "warning": IM_WARNING_DATA}


# --- config file
AUTOCORRECT = {'->': '→', '<-': '←', '<->': '↔', '=>': '⇒', '<=': '⇐',
                '<=>': '⇔', '=<': '≤', '>=': '≥', ":)": '☺'}

CONFIG = ConfigParser()
if os.path.exists(PATH_CONFIG):
    CONFIG.read(PATH_CONFIG)
    LANGUE = CONFIG.get("General", "language")
    if not CONFIG.has_option("General", "position"):
        CONFIG.set("General", "position", "normal")
    if not CONFIG.has_option("General", "check_update"):
        CONFIG.set("General", "check_update", "True")
    if not CONFIG.has_option("General", "buttons_position"):
        CONFIG.set("General", "buttons_position", "right")
    if not CONFIG.has_option("General", "symbols"):
        CONFIG.set("General", "symbols", SYMBOLS)
    if not CONFIG.has_option("General", "trayicon"):
        CONFIG.set("General", "trayicon", "")
    if not CONFIG.has_option("Font", "mono"):
        CONFIG.set("Font", "mono", "")
    if not CONFIG.has_option("General", "autocorrect"):
        value = "\t".join(["%s %s" % (key, val) for key, val in AUTOCORRECT.items()])
        CONFIG.set("General", "autocorrect", value)
    else:
        AUTOCORRECT = {}
        for ch in CONFIG.get("General", "autocorrect").split('\t'):
            key, val = ch.split(' ')
            AUTOCORRECT[key] = val
    if not CONFIG.has_section("Sync"):
        CONFIG.add_section("Sync")
        CONFIG.set("Sync", "on", "False")
        CONFIG.set("Sync", "server_type", "WebDav")
        CONFIG.set("Sync", "server", "")
        CONFIG.set("Sync", "username", "")
        CONFIG.set("Sync", "protocol", "https")
        CONFIG.set("Sync", "port", "443")
        CONFIG.set("Sync", "file", "")
else:
    LANGUE = ""
    CONFIG.add_section("General")
    CONFIG.set("General", "language", "en")
    CONFIG.set("General", "opacity", "82")
    CONFIG.set("General", "position", "normal")
    CONFIG.set("General", "buttons_position", "right")
    CONFIG.set("General", "check_update", "True")
    CONFIG.set("General", "symbols", SYMBOLS)
    CONFIG.set("General", "trayicon", "")
    value = "\t".join(["%s %s" % (key, val) for key, val in AUTOCORRECT.items()])
    CONFIG.set("General", "autocorrect", value)
    CONFIG.add_section("Font")
    CONFIG.set("Font", "text_family", "TkDefaultFont")
    CONFIG.set("Font", "text_size", "12")
    CONFIG.set("Font", "title_family", "TkDefaultFont")
    CONFIG.set("Font", "title_size", "14")
    CONFIG.set("Font", "title_style", "bold")
    CONFIG.set("Font", "mono", "")
    CONFIG.add_section("Categories")
    CONFIG.add_section("Sync")
    CONFIG.set("Sync", "on", "False")
    CONFIG.set("Sync", "server", "")
    CONFIG.set("Sync", "server_type", "WebDav")
    CONFIG.set("Sync", "username", "")
    CONFIG.set("Sync", "protocol", "https")
    CONFIG.set("Sync", "port", "443")
    CONFIG.set("Sync", "file", "")

# --- system tray icon
def get_available_gui_toolkits():
    """Check which gui toolkits are available to create a system tray icon."""
    toolkits = {'gtk': True, 'qt': True, 'tk': True}
    b = False
    try:
        import gi
        b = True
    except ImportError:
        toolkits['gtk'] = False

    try:
        import PyQt5
        b = True
    except ImportError:
        try:
            import PyQt4
            b = True
        except ImportError:
            try:
                import PySide
                b = True
            except ImportError:
                toolkits['qt'] = False

    tcl_packages = check_output(["tclsh",
                                 os.path.join(PATH, "packages.tcl")]).decode().strip().split()
    toolkits['tk'] = "tktray" in tcl_packages
    b = b or toolkits['tk']
    if not b:
        raise ImportError("No GUI toolkits available to create the system tray icon.")
    return toolkits


TOOLKITS = get_available_gui_toolkits()
GUI = CONFIG.get("General", "trayicon").lower()

if not TOOLKITS.get(GUI):
    DESKTOP = os.environ.get('XDG_CURRENT_DESKTOP')
    if DESKTOP == 'KDE':
        if TOOLKITS['qt']:
            GUI = 'qt'
        else:
            warnings.warn("No version of PyQt was found, falling back to another GUI toolkits so the system tray icon might not behave properly in KDE.")
            GUI = 'gtk' if TOOLKITS['gtk'] else 'tk'
    else:
        if TOOLKITS['gtk']:
            GUI = 'gtk'
        elif TOOLKITS['qt']:
            GUI = 'qt'
        else:
            GUI = 'tk'
    CONFIG.set("General", "trayicon", GUI)

if GUI == 'tk':
    ICON = IM_ICON
else:
    ICON = IM_ICON_48

# --- language
setlocale(LC_ALL, '')

APP_NAME = "MyNotes"

LANGUAGES = {"fr": "Français", "en": "English", "nl": "Nederlands", "de": "Deutsch"}
REV_LANGUAGES = {val: key for key, val in LANGUAGES.items()}

if LANGUE not in LANGUAGES:
    # Check the default locale
    LANGUE = getdefaultlocale()[0].split('_')[0]
    if LANGUE in LANGUAGES:
        CONFIG.set("General", "language", LANGUE)
    else:
        CONFIG.set("General", "language", "en")

gettext.find(APP_NAME, PATH_LOCALE)
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
gettext.bindtextdomain(APP_NAME, PATH_LOCALE)
gettext.textdomain(APP_NAME)
LANG = gettext.translation(APP_NAME, PATH_LOCALE,
                           languages=[LANGUE], fallback=True)
LANG.install()


# --- default categories
if not CONFIG.has_option("General", "default_category"):
    CONFIG.set("General", "default_category", _("home"))
    CONFIG.set("Categories", _("home"), '#F9F3A9')
    CONFIG.set("Categories", _("office"), '#A7B6D6')


# --- colors
COLORS = {_("Blue"): '#A7B6D6', _("Turquoise"): "#9FC9E2",
          _("Orange"): "#E1C59A", _("Red"): "#CD9293",
          _("Grey"): "#CECECE", _("White"): "#FFFFFF",
          _("Green"): '#C6FFB4', _("Black"): "#7D7A7A",
          _("Purple"): "#B592CD", _("Yellow"): '#F9F3A9',
          _("Dark Blue"): "#4D527D"}

INV_COLORS = {col: name for name, col in COLORS.items()}

TEXT_COLORS = {_("Black"): "black", _("White"): "white",
               _("Blue"): "blue", _("Green"): "green",
               _("Red"): "red", _("Yellow"): "yellow",
               _("Cyan"): "cyan", _("Magenta"): "magenta",
               _("Grey"): "grey", _("Orange"): "orange"}


def active_color(color, output='HTML'):
    """Return a lighter shade of color (RGB triplet with value max 255) in HTML format."""
    r, g, b = color
    r *= 0.7
    g *= 0.7
    b *= 0.7
    if output == 'HTML':
        return ("#%2.2x%2.2x%2.2x" % (round(r), round(g), round(b))).upper()
    else:
        return (round(r), round(g), round(b))


def color_box(color):
    im = Image.new('RGBA', (18, 16), (0,0,0,0))
    draw = ImageDraw.Draw(im)
    draw.rectangle([3, 3, 13, 13], color, 'black')
    return im


# --- latex (optional):  insertion of latex formulas via matplotlib
try:
    from matplotlib import rc
    rc('text', usetex=True)
    from matplotlib.mathtext import MathTextParser
    from matplotlib.image import imsave
    parser = MathTextParser('bitmap')
    LATEX = True
except Exception:
    LATEX = False


def math_to_image(latex, image_path, **options):
    img = parser.to_rgba(latex, **options)[0]
    imsave(image_path, img)


# --- filebrowser
ZENITY = False

paths = os.environ['PATH'].split(":")
for path in paths:
    if os.path.exists(os.path.join(path, "zenity")):
        ZENITY = True

try:
    import tkfilebrowser as tkfb
except ImportError:
    tkfb = False
    from tkinter import filedialog


def askopenfilename(defaultextension, filetypes, initialdir, initialfile="",
                    title=_('Open'), **options):
    """
    Open filebrowser dialog to select file to open.

    Arguments:
        - defaultextension: extension added if none is given
        - initialdir: directory where the filebrowser is opened
        - initialfile: initially selected file
        - filetypes: [('NAME', '*.ext'), ...]
    """
    if tkfb:
        return tkfb.askopenfilename(title=title,
                                    defaultext=defaultextension,
                                    filetypes=filetypes,
                                    initialdir=initialdir,
                                    initialfile=initialfile,
                                    **options)
    elif ZENITY:
        try:
            args = ["zenity", "--file-selection",
                    "--filename", os.path.join(initialdir, initialfile)]
            for ext in filetypes:
                args += ["--file-filter", "%s|%s" % ext]
            args += ["--title", title]
            file = check_output(args).decode("utf-8").strip()
            filename, ext = os.path.splitext(file)
            if not ext:
                ext = defaultextension
            return filename + ext
        except CalledProcessError:
            return ""
        except Exception:
            return filedialog.askopenfilename(title=title,
                                              defaultextension=defaultextension,
                                              filetypes=filetypes,
                                              initialdir=initialdir,
                                              initialfile=initialfile,
                                              **options)
    else:
        return filedialog.askopenfilename(title=title,
                                          defaultextension=defaultextension,
                                          filetypes=filetypes,
                                          initialdir=initialdir,
                                          initialfile=initialfile,
                                          **options)


def asksaveasfilename(defaultextension, filetypes, initialdir=".", initialfile="",
                      title=_('Save As'), **options):
    """
    Open filebrowser dialog to select file to save to.

    Arguments:
        - defaultextension: extension added if none is given
        - initialdir: directory where the filebrowser is opened
        - initialfile: initially selected file
        - filetypes: [('NAME', '*.ext'), ...]
    """
    if tkfb:
        return tkfb.asksaveasfilename(title=title,
                                      defaultext=defaultextension,
                                      filetypes=filetypes,
                                      initialdir=initialdir,
                                      initialfile=initialfile,
                                      **options)
    elif ZENITY:
        try:
            args = ["zenity", "--file-selection",
                    "--filename", os.path.join(initialdir, initialfile),
                    "--save", "--confirm-overwrite"]
            for ext in filetypes:
                args += ["--file-filter", "%s|%s" % ext]
            args += ["--title", title]
            file = check_output(args).decode("utf-8").strip()
            if file:
                filename, ext = os.path.splitext(file)
                if not ext:
                    ext = defaultextension
                return filename + ext
            else:
                return ""
        except CalledProcessError:
            return ""
        except Exception:
            return filedialog.asksaveasfilename(title=title,
                                                defaultextension=defaultextension,
                                                initialdir=initialdir,
                                                filetypes=filetypes,
                                                initialfile=initialfile,
                                                **options)
    else:
        return filedialog.asksaveasfilename(title=title,
                                            defaultextension=defaultextension,
                                            initialdir=initialdir,
                                            filetypes=filetypes,
                                            initialfile=initialfile,
                                            **options)


# --- miscellaneous functions
def sorting(index):
    """Sorting key for text indexes."""
    line, char = index.split(".")
    return (int(line), int(char))


def save_config():
    """Save configuration to file."""
    with open(PATH_CONFIG, 'w') as fichier:
        CONFIG.write(fichier)


def backup(nb_backup=12):
    """Backup current note data."""
    backups = [int(f.split(".")[-1][6:])
               for f in os.listdir(os.path.dirname(PATH_DATA_BACKUP))
               if f[:12] == "notes.backup"]
    if len(backups) < nb_backup:
        os.rename(PATH_DATA, PATH_DATA_BACKUP % len(backups))
    else:
        os.remove(PATH_DATA_BACKUP % 0)
        for i in range(1, len(backups)):
            os.rename(PATH_DATA_BACKUP % i, PATH_DATA_BACKUP % (i - 1))
        os.rename(PATH_DATA, PATH_DATA_BACKUP % (nb_backup - 1))


def optionmenu_patch(om, var):
    """Variable bug patch + bind menu so that it disapear easily."""
    menu = om['menu']
    last = menu.index("end")
    for i in range(0, last + 1):
        menu.entryconfig(i, variable=var)
    menu.bind("<FocusOut>", menu.unpost())


def text_ranges(widget, tag, index1="1.0", index2="end"):
    """
    Equivalent of Text.tag_ranges but with an index restriction.

    Arguments:
        - widget: Text widget
        - tag: tag to find
        - index1: start search at this index
        - index2: end search at this index
    """
    r = [i.string for i in widget.tag_ranges(tag)]
    i1 = widget.index(index1)
    i2 = widget.index(index2)
    deb = r[::2]
    fin = r[1::2]
    i = 0
    while i < len(deb) and sorting(deb[i]) < sorting(i1):
        i += 1
    j = len(fin) - 1
    while j >= 0 and sorting(fin[j]) > sorting(i2):
        j -= 1
    tag_ranges = r[2 * i:2 * j + 2]
    if i > 0 and sorting(fin[i - 1]) > sorting(i1):
        if i - 1 <= j:
            tag_ranges.insert(0, fin[i - 1])
            tag_ranges.insert(0, i1)
        else:
            tag_ranges.insert(0, i2)
            tag_ranges.insert(0, i1)
            return tag_ranges
    if j < len(fin) - 1 and sorting(deb[j + 1]) < sorting(i2):
        tag_ranges.append(deb[j + 1])
        tag_ranges.append(i2)

    return tag_ranges

def save_modif_info(tps=None):
    """ save info about last modifications (machine and time) """
    if tps is None:
        tps = time.time()
    info = platform.uname()
    info = "%s %s %s %s %s\n" % (info.system, info.node, info.release,
                               info.version, info.machine)
    lines = [info, str(tps)]
    with open(PATH_DATA_INFO, 'w') as fich:
        fich.writelines(lines)

# --- export
BALISES_OPEN = {"bold": "<b>",
                "italic": "<i>",
                "underline": "<u>",
                "overstrike": "<s>",
                "mono": "<tt>",
                "list": "",
                "enum": "",
                "link": "",
                "todolist": "",
                'center': '<div style="text-align:center">',
                'left': '',
                'right': '<div style="text-align:right">'}

BALISES_CLOSE = {"bold": "</b>",
                 "italic": "</i>",
                 "underline": "</u>",
                 "overstrike": "</s>",
                 "mono": "</tt>",
                 "list": "",
                 "enum": "",
                 "todolist": "",
                 "link": "",
                 'center': '</div>',
                 'left': '',
                 'right': '</div>'}

for color in TEXT_COLORS.values():
    BALISES_OPEN[color] = '<span style="color:%s">' % color
    BALISES_CLOSE[color] = '</span>'


def note_to_html(data, master):
    """Convert note content to html."""
    txt = Text(master)
    tags = data["tags"]
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    indexes.sort(reverse=True, key=sorting)
    txt.insert('1.0', data["txt"])

    b_open = BALISES_OPEN.copy()
    b_close = BALISES_CLOSE.copy()

    for key, link in data["links"].items():
        b_open["link#%i" % key] = "<a href='%s'>" % link
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
    end = int(txt.index("end").split(".")[0])
    for line in range(1, end):
        l_end = int(txt.index("%i.end" % line).split(".")[1])
        for col in range(l_end):
            index = "%i.%i" % (line, col)
            tags = set()
            for tag in txt.tag_names(index):
                if tag not in ["center", "left", "right"]:
                    txt.tag_remove(tag, index)
                    if "-" in tag:
                        t1, t2 = tag.split("-")
                        tags.add(t1)
                        tags.add(t2)
                    else:
                        tags.add(tag)
            tags = list(tags)
            tags.sort()
            txt.tag_add("-".join(tags), index)
    right = [i.string for i in txt.tag_ranges("right")]
    center = [i.string for i in txt.tag_ranges("center")]
    left = []
    for deb, fin in zip(right[::2], right[1::2]):
        left.append(txt.index("%s-1c" % deb))
        left.append(txt.index("%s+1c" % fin))
    for deb, fin in zip(center[::2], center[1::2]):
        left.append(txt.index("%s-1c" % deb))
        left.append(txt.index("%s+1c" % fin))
    left.sort(key=sorting)
    doubles = []
    for i in left[::2]:
        if i in left[1::2]:
            doubles.append(i)
    for i in doubles:
        left.remove(i)
        left.remove(i)
    if "1.0" in left:
        left.remove("1.0")
    else:
        left.insert(0, "1.0")
    if txt.index("end") in left:
        left.remove(txt.index("end"))
    else:
        left.append(txt.index("end"))
    # html balises
    t = txt.get("1.0", "end").splitlines()
    alignments = {"left": left, "right": right, "center": center}
    # alignment
    for a, align in alignments.items():
        for deb, fin in zip(align[::2], align[1::2]):
            balises = {deb: [b_open[a]], fin: [b_close[a]]}
            tags = {t: text_ranges(txt, t, deb, fin) for t in txt.tag_names()}
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
                        balises[i].append('<img src="%s" style="vertical-align:middle" alt="%s" />' % (val, os.path.split(val)[-1]))
            indices = list(balises.keys())
            indices.sort(key=sorting, reverse=True)
            for index in indices:
                line, col = index.split(".")
                line = int(line) - 1
                col = int(col)
                while line >= len(t):
                    t.append("")
                l = list(t[line])
                if index in indexes:
                    del(l[col])
                l.insert(col, "".join(balises[index]))
                t[line] = "".join(l)
    txt.destroy()

    # --- list
    if data["mode"] == "list":
        for i, line in enumerate(t):
            if "\t•\t" in line:
                t[i] = line.replace("\t•\t", "<li>") + "</li>"
        t = "<br>\n".join(t)
        t = "<ul>%s</ul>" % t
    else:
        t = "<br>\n".join(t)
    return t


def note_to_txt(data):
    """Convert note content to .txt"""
    t = data["txt"].splitlines()
    obj = data["inserted_objects"]
    indexes = list(obj.keys())
    indexes.sort(reverse=True, key=sorting)
    for i in indexes:
        tp, val = obj[i]
        line, col = i.split(".")
        line = int(line) - 1
        while line >= len(t):
            t.append("")
        col = int(col)
        l = list(t[line])
        if tp == "checkbox":
            if val:
                l.insert(col, "☒ ")
            else:
                l.insert(col, "☐ ")
        elif tp == "image":
            l.insert(col, "![%s](%s)" % (os.path.split(val)[-1], val))
        t[line] = "".join(l)
    return "\n".join(t)
