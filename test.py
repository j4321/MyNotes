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


Tests
"""

import unittest
from mynoteslib.constantes import LANG
from mynoteslib.app import App
from mynoteslib.messagebox import OneButtonBox, IM_INFO_DATA


_ = LANG.gettext


class TestMyNotes(unittest.TestCase):
    def test_mynotes_app(self):
        app = App()

    def test_mynotes_messagebox(self):
        box = OneButtonBox(title="Test", message="This is a test", button="Ok",
                           image=IM_INFO_DATA)
        self.assertEqual(box.title(), "Test")
