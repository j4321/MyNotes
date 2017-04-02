#! /usr/bin/python3
# -*- coding:Utf-8 -*-

try:
    from setuptools import setup
except:
    from distutils.core import setup

files = ["images/*"]
data_files = [("share/pixmaps", ["mynotes.svg"]),
              ("share/locale/en_US/LC_MESSAGES/", ["mynoteslib/locale/en_US/LC_MESSAGES/MyNotes.mo"]),
              ("share/locale/fr_FR/LC_MESSAGES/", ["mynoteslib/locale/fr_FR/LC_MESSAGES/MyNotes.mo"]),
              ("share/applications", ["mynotes.desktop"])]

setup(name = "mynotes",
      version = "2.1.0-beta",
      description = "Post-it system tray app",
      author = "Juliette Monsel",
      author_email = "j_4321@protonmail.fr",
      license = "GNU General Public License v3",
      packages = ['mynoteslib'],
      package_data = {'mynoteslib' : files },
      scripts = ["mynotes"],
      data_files = data_files,
      long_description =
"""
MyNotes is a sticky notes/post-it application. Notes are created using
the system tray icon. They can be organized in categories and each
category has a color. Images, checkboxes and a few predefined symbols
can be inserted in the notes. The style of the text can be changed
(alignment, style).
""",
      requires = ["tkinter", "sys", "os", "locale", "gettext",
                  'configparser', 'subprocess', 'time', 'shutil',
                  'pickle', 'ewmh', 'ftplib', 'easywebdav']
)


