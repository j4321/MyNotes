MyNotes - Sticky notes/post-it
=============================================
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

MyNotes is a sticky note application. An icon appears in the system tray
and from it you can create and manage your sticky notes. Notes can be 
organized in categories and you can set a default color for each category.
Checkboxes and images can be incorporated in the notes. If your desktop
environment supports compositing, the opacity of the notes can be modified.

MyNotes is designed for Linux. It is written in Python 3 and relies on
Tk GUI toolkit. 

Install
-------

First, install the missing dependencies among:
    - Tkinter (Python wrapper for Tk)
    - Tktray https://code.google.com/archive/p/tktray/downloads
    - ewmh https://pypi.python.org/pypi/ewmh
For instance, in Ubuntu/Debian you will need to install the following packages:
python3-tk, tk-tktray, python3-ewmh (available in zesty only)

In Archlinux, you will need to install the following packages:
tk, tktray (AUR), python-ewmh (AUR)

ewmh can be installed with pip:
::
    $ sudo pip3 install ewmh

Then install the application:
:: 
    $ sudo python3 setup.py install

You can now launch it from `Menu > Utility > MyNotes`. You can launch
it from the command line with `mynotes`.

If you encounter bugs or if you have suggestions, please write me an email
at <j_4321@protonmail.com>.

