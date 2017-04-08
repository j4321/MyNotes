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


The icons are modified versions of icons from the elementary project
(the xfce fork to be precise https://github.com/shimmerproject/elementary-xfce)
Copyright 2007-2013 elementary LLC.

Constants and functions
"""



VERSION = "2.1.0"

import time
import platform
import os
import gettext
from configparser import ConfigParser
from locale import getdefaultlocale, setlocale, LC_ALL
from subprocess import check_output, CalledProcessError

SYMBOLS = 'ΓΔΘΛΞΠΣΦΨΩαβγδεζηθικλμνξοπρςστυφχψωϐϑϒϕϖæœ«»¡¿£¥$€§ø∞∀∃∄∈∉∫∧∨∩∪÷±√∝∼≃≅≡≤≥≪≫≲≳▪•✭✦➔➢✔▴▸✗✚✳☎✉✎♫⚠⇒⇔'

### paths
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

### images files
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

### config file
CONFIG = ConfigParser()
if os.path.exists(PATH_CONFIG):
    CONFIG.read(PATH_CONFIG)
    LANGUE = CONFIG.get("General","language")
    if not CONFIG.has_option("General", "position"):
        CONFIG.set("General", "position", "normal")
    if not CONFIG.has_option("General", "check_update"):
        CONFIG.set("General", "check_update", "True")
    if not CONFIG.has_option("General", "buttons_position"):
        CONFIG.set("General", "buttons_position", "right")
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
    CONFIG.add_section("Font")
    CONFIG.set("Font", "text_family", "TkDefaultFont")
    CONFIG.set("Font", "text_size", "12")
    CONFIG.set("Font", "title_family", "TkDefaultFont")
    CONFIG.set("Font", "title_size", "14")
    CONFIG.set("Font", "title_style", "bold")
    CONFIG.add_section("Categories")
    CONFIG.add_section("Sync")
    CONFIG.set("Sync", "on", "False")
    CONFIG.set("Sync", "server", "")
    CONFIG.set("Sync", "server_type", "WebDav")
    CONFIG.set("Sync", "username", "")
    CONFIG.set("Sync", "protocol", "https")
    CONFIG.set("Sync", "port", "443")
    CONFIG.set("Sync", "file", "")

### language
setlocale(LC_ALL, '')

APP_NAME = "MyNotes"

if LANGUE not in ["en", "fr"]:
    # Check the default locale
    lc = getdefaultlocale()[0][:2]
    if lc == "fr":
        # If we have a default, it's the first in the list
        LANGUE = "fr_FR"
    else:
        LANGUE = "en_US"
    CONFIG.set("General", "language", LANGUE[:2])

gettext.find(APP_NAME, PATH_LOCALE)
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
gettext.bindtextdomain(APP_NAME, PATH_LOCALE)
gettext.textdomain(APP_NAME)
LANG = gettext.translation(APP_NAME, PATH_LOCALE,
                           languages=[LANGUE], fallback=True)
LANG.install()

### default categories
if not CONFIG.has_option("General", "default_category"):
    CONFIG.set("General", "default_category", _("home"))
    CONFIG.set("Categories", _("home"), '#F9F3A9')
    CONFIG.set("Categories", _("office"), '#A7B6D6')

### colors
COLORS = {_("Blue"): '#A7B6D6', _("Turquoise"): "#9FC9E2",
          _("Orange"): "#E1C59A",  _("Red"): "#CD9293",
          _("Grey"): "#CECECE",  _("White"): "#FFFFFF",
          _("Green"): '#C6FFB4',  _("Black"): "#7D7A7A",
          _("Purple"): "#B592CD",  _("Yellow"): '#F9F3A9',
          _("Dark Blue"): "#4D527D"}

INV_COLORS = {col:name for name, col in COLORS.items()}

TEXT_COLORS = {_("Black"): "black", _("White"): "white",
               _("Blue"): "blue", _("Green"): "green",
               _("Red"): "red", _("Yellow"): "yellow",
               _("Cyan"): "cyan", _("Magenta"): "magenta",
               _("Grey"): "grey", _("Orange"):"orange",
               }

### filebrowser
ZENITY = False

paths = os.environ['PATH'].split(":")
for path in paths:
    if os.path.exists(os.path.join(path, "zenity")):
        ZENITY = True

try:
    import tkFileBrowser as tkfb
except ImportError:
    tkfb = False
    from tkinter import filedialog

def askopenfilename(defaultextension, filetypes, initialdir, initialfile="",
                    title=_('Open'), **options):
    """ file browser:
            - defaultextension: extension added if none is given
            - initialdir: directory where the filebrowser is opened
            - filetypes: [('NOM', '*.ext'), ...]
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
    """ plateform specific file browser for saving a file:
            - defaultextension: extension added if none is given
            - initialdir: directory where the filebrowser is opened
            - filetypes: [('NOM', '*.ext'), ...]
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

### miscellaneous functions
def fill(image, color):
     """Fill image with a color=#hex."""
     width = image.width()
     height = image.height()
     horizontal_line = "{" + " ".join([color]*width) + "}"
     image.put(" ".join([horizontal_line]*height))

def sorting(index):
    """ sorting key for text indexes """
    line, char = index.split(".")
    return (int(line), int(char))

def save_config():
    """ sauvegarde du dictionnaire contenant la configuration du logiciel (langue ...) """
    with open(PATH_CONFIG, 'w') as fichier:
        CONFIG.write(fichier)

def backup(nb_backup=12):
    backups = [int(f.split(".")[-1][6:])
               for f in os.listdir(os.path.dirname(PATH_DATA_BACKUP))
               if f[:12] == "notes.backup"]
    if len(backups) < nb_backup:
        os.rename(PATH_DATA, PATH_DATA_BACKUP % len(backups))
    else:
        os.remove(PATH_DATA_BACKUP % 0)
        for i in range(1, len(backups)):
            os.rename(PATH_DATA_BACKUP % i, PATH_DATA_BACKUP % (i - 1))
        os.rename(PATH_DATA, PATH_DATA_BACKUP % (nb_backup-1))

def optionmenu_patch(om, var):
    """ variable bug patch + bind menu so that it disapear easily """
    menu = om['menu']
    last = menu.index("end")
    for i in range(0, last+1):
        menu.entryconfig(i, variable=var)
    menu.bind("<FocusOut>", menu.unpost())

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