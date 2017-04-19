#! /usr/bin/python3
# -*- coding:Utf-8 -*-

from setuptools import setup

import os
images = [os.path.join("mynoteslib/images/", img) for img in os.listdir("mynoteslib/images/")]
data_files = [("share/pixmaps", ["mynotes.svg"]),
              ("share/doc/mynotes", ["README.rst", "changelog"]),
              ("share/man/man1", ["mynotes.1.gz"]),
              ("share/mynotes/images", images),
              ("share/locale/en_US/LC_MESSAGES/", ["mynoteslib/locale/en_US/LC_MESSAGES/MyNotes.mo"]),
              ("share/locale/fr_FR/LC_MESSAGES/", ["mynoteslib/locale/fr_FR/LC_MESSAGES/MyNotes.mo"]),
              ("share/applications", ["mynotes.desktop"])]

setup(name="mynotes",
      version="2.1.1b1",
      description="Post-it system tray app",
      keywords=["post-it", "sticky", "notes", "tkinter"],
      author="Juliette Monsel",
      author_email="j_4321@protonmail.com",
      license='GPLv3',
      classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: X11 Applications',
            'Intended Audience :: End Users/Desktop',
            'Topic :: Text Editors',
            'Topic :: Office/Business',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Natural Language :: English',
            'Natural Language :: French',
            'Operating System :: POSIX :: Linux',
      ],
      url="https://sourceforge.net/projects/my-notes",
      packages=['mynoteslib'],
      scripts=["mynotes"],
      data_files=data_files,
      long_description=
"""
MyNotes is a sticky notes/post-it application. Notes are created using
the system tray icon. They can be organized in categories and each
category has a color. Images, checkboxes and a few predefined symbols
can be inserted in the notes. The style of the text can be changed
(alignment, style).
""",
      requires=["tkinter", "sys", "os", "locale", "gettext", 're',
                'configparser', 'subprocess', 'time', 'shutil','html',
                'pickle', 'setuptools', 'ewmh']
)

