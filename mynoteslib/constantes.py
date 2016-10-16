#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
My Notes - Sticky notes/post-it
Copyright 2016 Juliette Monsel <j_4321@hotmail.fr>

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


Constants
"""

import os
import gettext
from configparser import ConfigParser
from locale import getdefaultlocale, setlocale, LC_ALL

setlocale(LC_ALL, '')

PATH = os.path.dirname(__file__)

# local directory containing config files and sticky notes data
LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".mynotes")
if not os.path.isdir(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

PATH_CONFIG = os.path.join(LOCAL_PATH, "mynotes.ini")
PATH_DATA = os.path.join(LOCAL_PATH, "notes")
PATH_DATA_BACKUP = os.path.join(LOCAL_PATH, "notes.backup%i")
PATH_LOCALE = os.path.join(PATH, "locale")
PATH_IMAGES = os.path.join(PATH, "images")

# images files
IM_ICON = os.path.join(PATH_IMAGES, "mynotes.png")
IM_ICON_24 = os.path.join(PATH_IMAGES, "mynotes24.png")
IM_ICON_48 = os.path.join(PATH_IMAGES, "mynotes48.png")
IM_CLOSE = os.path.join(PATH_IMAGES, "close.png")
IM_CLOSE_ACTIVE = os.path.join(PATH_IMAGES, "close_active.png")
IM_ROLL = os.path.join(PATH_IMAGES, "roll.png")
IM_ROLL_ACTIVE = os.path.join(PATH_IMAGES, "roll_active.png")
IM_LOCK = os.path.join(PATH_IMAGES, "verr.png")
NB_SYMB = 15
IM_SYMB = [os.path.join(PATH_IMAGES, "puce%i.png" % i) for i in range(NB_SYMB)]

# read config file
CONFIG = ConfigParser()
if os.path.exists(PATH_CONFIG):
    CONFIG.read(PATH_CONFIG)
    LANGUE = CONFIG.get("General","language")
else:
    LANGUE = ""
    CONFIG.add_section("General")
    CONFIG.set("General", "language", "en")
    CONFIG.set("General", "opacity", "82")
    CONFIG.add_section("Font")
    CONFIG.set("Font", "family", "TkDefaultFont")
    CONFIG.set("Font", "size", "12")
    CONFIG.add_section("Categories")

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
_ = LANG.gettext

# colors
COLORS = {_("Blue"): '#A7B6D6', _("Turquoise"): "#9FC9E2",
          _("Orange"): "#E1C59A",  _("Red"): "#CD9293",
          _("Grey"): "#CECECE",  _("White"): "#FFFFFF",
          _("Green"): '#C6FFB4',  _("Black"): "#7D7A7A",
          _("Purple"): "#B592CD",  _("Yellow"): '#F9F3A9',
          _("Dark Blue"): "#4D527D"}

INV_COLORS = {col:name for name, col in COLORS.items()}

if not CONFIG.has_option("General", "default_category"):
    CONFIG.set("General", "default_category", _("Home"))
    CONFIG.set("Categories", _("home"), '#F9F3A9')
    CONFIG.set("Categories", _("office"), '#A7B6D6')

def fill(image, color):
     """Fill image with a color=#hex."""
     width = image.width()
     height = image.height()
     horizontal_line = "{" + " ".join([color]*width) + "}"
     image.put(" ".join([horizontal_line]*height))

def save_config():
    """ sauvegarde du dictionnaire contenant la configuration du logiciel (langue ...) """
    with open(PATH_CONFIG, 'w') as fichier:
        CONFIG.write(fichier)

def backup(nb_backup=12):
    backups = [int(f.split(".")[-1][6:]) for f in os.listdir(LOCAL_PATH) if f[:12] == "notes.backup"]
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
