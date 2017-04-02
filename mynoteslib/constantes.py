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

IM_ERROR_DATA was taken from "icons.tcl":

	A set of stock icons for use in Tk dialogs. The icons used here
	were provided by the Tango Desktop project which provides a
	unified set of high quality icons licensed under the
	Creative Commons Attribution Share-Alike license
	(http://creativecommons.org/licenses/by-sa/3.0/)

	See http://tango.freedesktop.org/Tango_Desktop_Project

    Copyright (c) 2009 Pat Thoyts <patthoyts@users.sourceforge.net>


Constants
"""


import os
import gettext
from configparser import ConfigParser
from locale import getdefaultlocale, setlocale, LC_ALL
from subprocess import check_output, CalledProcessError

VERSION = "2.0.0"
SYMBOLS = 'ΓΔΘΛΞΠΣΦΨΩαβγδεζηθικλμνξοπρςστυφχψωϐϑϒϕϖæœ«»¡¿£¥$€§ø∞∀∃∄∈∉∫∧∨∩∪÷±√∝∼≃≅≡≤≥≪≫≲≳▪•✭✦➔➢✔▴▸✗✚✳☎✉✎♫⚠⇒⇔'

#----paths----
PATH = os.path.dirname(__file__)

if os.access(PATH, os.W_OK):
    # the path is writable, the app is not installed
    # local directory containing config files and sticky notes data
    LOCAL_PATH = PATH
    PATH_LOCALE = os.path.join(PATH, "locale")
    PATH_DATA_BACKUP = os.path.join(LOCAL_PATH, "backup", "notes.backup%i")
    if not os.path.exists(os.path.join(LOCAL_PATH, "backup")):
        os.mkdir(os.path.join(LOCAL_PATH, "backup"))

else:
    # local directory containing config files and sticky notes data
    LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".mynotes")
    if not os.path.isdir(LOCAL_PATH):
        os.mkdir(LOCAL_PATH)
    PATH_LOCALE = "/usr/share/locale"
    PATH_DATA_BACKUP = os.path.join(LOCAL_PATH, "notes.backup%i")

PATH_CONFIG = os.path.join(LOCAL_PATH, "mynotes.ini")
PATH_DATA = os.path.join(LOCAL_PATH, "notes")
PATH_IMAGES = os.path.join(PATH, "images")

#----images files----
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

IM_ERROR_DATA = """
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
"""


#----config file----
CONFIG = ConfigParser()
if os.path.exists(PATH_CONFIG):
    CONFIG.read(PATH_CONFIG)
    LANGUE = CONFIG.get("General","language")
    if not CONFIG.has_option("General", "position"):
        CONFIG.set("General", "position", "normal")
    if not CONFIG.has_option("General", "buttons_position"):
        CONFIG.set("General", "buttons_position", "right")
    if not CONFIG.has_section("Sync"):
        CONFIG.add_section("Sync")
        CONFIG.set("Sync", "on", "False")
        CONFIG.set("Sync", "server_type", "FTP")
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
    CONFIG.set("Sync", "server_type", "FTP")
    CONFIG.set("Sync", "username", "")
    CONFIG.set("Sync", "protocol", "https")
    CONFIG.set("Sync", "port", "443")
    CONFIG.set("Sync", "file", "")

#----language----
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

#----default categories----
if not CONFIG.has_option("General", "default_category"):
    CONFIG.set("General", "default_category", _("Home"))
    CONFIG.set("Categories", _("home"), '#F9F3A9')
    CONFIG.set("Categories", _("office"), '#A7B6D6')

#----colors----
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


#----filebrowser----
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

#----miscellaneous functions----
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
