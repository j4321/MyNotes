#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - System tray unread mail checker
Copyright 2016-2018 Juliette Monsel <j_4321@protonmail.com>

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


System tray icon using Gtk 3.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APPIND_SUPPORT = 1
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except ValueError:
    APPIND_SUPPORT = 0


class SubMenu(Gtk.Menu):
    def __init__(self, *args, **kwargs):
        Gtk.Menu.__init__(self)

    def add_command(self, label="", command=None):
        item = Gtk.MenuItem(label=label)
        self.append(item)
        if command is not None:
            item.connect("activate", lambda *args: command())
        item.show()

    def add_cascade(self, label="", menu=None):
        item = Gtk.MenuItem(label=label)
        self.append(item)
        if menu is not None:
            item.set_submenu(menu)
        item.show()

    def add_separator(self):
        sep = Gtk.SeparatorMenuItem()
        self.append(sep)
        sep.show()

    def delete(self, item1, item2=None):
        index1 = self.index(item1)
        if item2 is None:
            self.remove(self.get_children()[index1])
        else:
            index2 = self.index(item2)
            c = self.get_children()
            for i in range(index1, index2):
                self.remove(c[i])

    def index(self, index):
        if isinstance(index, int):
            return index
        elif index == "end":
            return len(self.get_children())
        else:
            try:
                i = [i.get_label() for i in self.get_children()].index(index)
            except ValueError:
                raise ValueError("%r not in menu" % index)
            return i

    def get_item_label(self, item):
        return self.get_children()[self.index(item)].get_label()

    def set_item_label(self, item, label):
        self.get_children()[self.index(item)].set_label(label)

    def get_item_menu(self, item):
        return self.get_children()[self.index(item)].get_submenu()

    def set_item_menu(self, item, menu):
        self.get_children()[self.index(item)].set_submenu(menu)

    def disable_item(self, item):
        self.get_children()[self.index(item)].set_sensitive(False)

    def enable_item(self, item):
        self.get_children()[self.index(item)].set_sensitive(True)


class TrayIcon:
    """Gtk system tray icon."""
    def __init__(self, icon, fallback_icon_path, appid="TrayIcon", **kwargs):
        self.menu = SubMenu()

        icon_exists = Gtk.IconTheme.get_default().has_icon(icon)

        if APPIND_SUPPORT == 1:
            if icon_exists:
                self.tray_icon = AppIndicator3.Indicator.new(appid, icon,
                                                             AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            else:
                self.tray_icon = AppIndicator3.Indicator.new(appid,
                                                             fallback_icon_path,
                                                             AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.tray_icon.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.tray_icon.set_menu(self.menu)
            self.change_icon = self._change_icon_appind
        else:
            if icon_exists:
                self.tray_icon = Gtk.StatusIcon.new_from_icon_name(icon)
            else:
                self.tray_icon = Gtk.StatusIcon.new_from_file(fallback_icon_path)
            self.tray_icon.connect('popup-menu', self._on_popup_menu)
            self.change_icon = self._change_icon_fallback

    def _on_popup_menu(self, icon, button, time):
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)

    def _change_icon_appind(self, icon, desc):
        self.tray_icon.set_icon_full(icon, desc)

    def _change_icon_fallback(self, icon, desc):
        self.tray_icon.set_from_file(icon)

    def loop(self, tk_window):
        """Update Gtk GUI inside tkinter mainloop."""
        while Gtk.events_pending():
            Gtk.main_iteration()
        tk_window.loop_id = tk_window.after(10, self.loop, tk_window)

    def bind_left_click(self, command):
        if not APPIND_SUPPORT:
            self.tray_icon.connect('activate', lambda *args: command())
