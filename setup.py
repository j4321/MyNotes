#! /usr/bin/python3
# -*- coding:Utf-8 -*-

from setuptools import setup

import os
images = [os.path.join("mynoteslib/images/", img) for img in os.listdir("mynoteslib/images/")]
data_files = [("/usr/share/pixmaps", ["mynotes.svg", "mynotes-tray.svg"]),
              ("/usr/share/doc/mynotes", ["README.rst", "changelog"]),
              ("/usr/share/man/man1", ["mynotes.1.gz"]),
              ("/usr/share/mynotes/images", images),
              ("/usr/share/applications", ["mynotes.desktop"])]
for lang in os.listdir("mynoteslib/locale/"):
    data_files.append(("/usr/share/locale/%s/LC_MESSAGES/" % lang, ["mynoteslib/locale/%s/LC_MESSAGES/MyNotes.mo" % lang]))


with open("mynoteslib/version.py") as file:
    exec(file.read())

setup(name="mynotes",
      version=__version__,
      description="Post-it system tray app",
      keywords=["post-it", "sticky", "notes", "tkinter"],
      author="Juliette Monsel",
      author_email="j_4321@protonmail.com",
      license='GPLv3',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
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
      packages=['mynoteslib', 'mynoteslib.trayicon', 'mynoteslib.config'],
      package_data={'mynoteslib': ['packages.tcl']},
      scripts=["mynotes"],
      data_files=data_files,
      long_description="""
MyNotes is a sticky notes/post-it application. Notes are created using
the system tray icon. They can be organized in categories and each
category has a color. Images, checkboxes and a few predefined symbols
can be inserted in the notes. The style of the text can be changed
(alignment, style).
""",
      install_requires=['Pillow', 'ewmh'])
