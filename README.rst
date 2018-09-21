MyNotes - Sticky notes/post-it
==============================
|Release|_ |Linux| |License|_

MyNotes is a sticky note application. An icon appears in the system tray
and from it you can create and manage your sticky notes. Notes can be
organized in categories and you can set a default color for each category.
Checkboxes and images can be incorporated in the notes. If your desktop
environment supports compositing, the opacity of the notes can be modified.

MyNotes is designed for Linux. It is written in Python 3 and relies
mostly on the Tk GUI toolkit.


Install
-------

- Archlinux

    MyNotes is available in `AUR <https://aur.archlinux.org/packages/mynotes>`__.

- Ubuntu

    MyNotes is available in the PPA `ppa:j-4321-i/ppa`.

    ::

        $ sudo add-apt-repository ppa:j-4321-i/ppa
        $ sudo apt-get update
        $ sudo apt-get install mynotes

- Source code

    First, install the missing dependencies among:
        - Tkinter (Python wrapper for Tk)
        - Tktray https://code.google.com/archive/p/tktray/downloads
        - ewmh https://pypi.python.org/pypi/ewmh
        - optional dependency: matplotlib + texlive for basic LaTeX formula support
        
    For instance, in Ubuntu/Debian you will need to install the following packages:
    python3-tk, tk-tktray, python3-ewmh (available in >= 17.04 only),
    python3-pil, python3-pil.imagetk

    ewmh can be installed with pip:
    
    ::
    
        $ sudo pip3 install ewmh

    Then install the application:
    
    ::
    
        $ sudo python3 setup.py install

You can now launch it from `Menu > Utility > MyNotes`. You can launch
it from the command line with `mynotes`.


Troubleshooting
---------------

Several gui toolkits are available to display the system tray icon, so if the
icon does not behave properly, try to change toolkit, they are not all fully
compatible with every desktop environment.

If you encounter bugs or if you have suggestions, please open an issue
on `GitHub <https://github.com/j4321/MyNotes/issues>`__ or write me
an email at <j_4321@protonmail.com>.


.. |Release| image:: https://badge.fury.io/gh/j4321%2FMyNotes.svg
    :alt: Latest Release
.. _Release: https://badge.fury.io/gh/j4321%2FMyNotes
.. |Linux| image:: https://img.shields.io/badge/platform-Linux-blue.svg
    :alt: Linux
.. |License| image:: https://img.shields.io/github/license/j4321/MyNotes.svg
.. _License: https://www.gnu.org/licenses/gpl-3.0.en.html
