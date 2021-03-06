#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>
based on code by Fredrik Lundh copyright 1998
<http://effbot.org/zone/tkinter-autoscrollbar.htm>

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


Scrollbar that hide automatically when not needed.
"""


from tkinter.ttk import Scrollbar
from tkinter import TclError


class AutoScrollbar(Scrollbar):
    """
    Scrollbar that hides itself if it's not needed.

    Only works with the grid geometry manager.
    """

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")

    def place(self, **kw):
        raise TclError("cannot use place with this widget")
