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


Sync note with server
"""


import easywebdav
import time
import os
from tkinter import Toplevel, PhotoImage
from tkinter.ttk import Frame, Label, Button, Entry, Checkbutton, Frame
from tkinter.messagebox import showerror
from mynoteslib.constantes import CONFIG, PATH_DATA, setlocale, LC_ALL, IM_ERROR_DATA


class SyncSettings(Frame):
    def __init__(self, master, password=""):
        Frame.__init__(self, master)
        self.columnconfigure(1, weight=1)

        self.sync_state = Checkbutton(self,
                                      text=_("Synchronize note with server"),
                                      command=self.toggle_sync)
        if CONFIG.getboolean("Sync", "on"):
            self.sync_state.state(("selected",))
        else:
            self.sync_state.state(("!selected",))
        self.server = Entry(self)
        self.server.insert(0, CONFIG.get("Sync", "server"))
        self.user = Entry(self)
        self.user.insert(0, CONFIG.get("Sync", "username"))
        self.password = Entry(self, show="*")
        self.password.insert(0, password)
        self.protocol = Entry(self)
        self.protocol.insert(0, CONFIG.get("Sync", "protocol"))
        self.port = Entry(self)
        self.port.insert(0, CONFIG.get("Sync", "port"))
        self.file = Entry(self)
        self.file.insert(0, CONFIG.get("Sync", "file"))

        self.sync_state.grid(row=0, columnspan=2, sticky="w", padx=4, pady=4)
        Label(self, text=_("Server address")).grid(row=1, column=0,
                                                   sticky="e", padx=4, pady=4)
        Label(self, text=_("Username")).grid(row=2, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Password")).grid(row=3, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Protocol")).grid(row=4, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Port")).grid(row=5, column=0,
                                         sticky="e", padx=4, pady=4)
        Label(self, text=_("Server file")).grid(row=6, column=0,
                                                sticky="e", padx=4, pady=4)

        self.server.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.user.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.password.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        self.protocol.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        self.port.grid(row=5, column=1, sticky="ew", padx=4, pady=4)
        self.file.grid(row=6, column=1, sticky="ew", padx=4, pady=4)

        self.toggle_sync()

    def toggle_sync(self):
        if "selected" in self.sync_state.state():
            state = "!disabled"
        else:
            state = "disabled"
        self.server.state((state,))
        self.user.state((state,))
        self.password.state((state,))
        self.protocol.state((state,))
        self.port.state((state,))
        self.file.state((state,))

    def save_sync_settings(self):
        CONFIG.set("Sync", "on", str("selected" in self.sync_state.state()))
        CONFIG.set("Sync", "server", self.server.get())
        CONFIG.set("Sync", "username", self.user.get())
        CONFIG.set("Sync", "protocol", self.protocol.get())
        CONFIG.set("Sync", "port", self.port.get())
        CONFIG.set("Sync", "file", self.file.get())
        return self.password.get()


class SyncConflict(Toplevel):
    def __init__(self, master=None):
        Toplevel.__init__(self, master)
        self.icon = PhotoImage(data=IM_ERROR_DATA)
        self.title(_("Sync Conflict"))
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.action = ""
        frame = Frame(self)
        frame.grid(row=0, columnspan=2, sticky="eswn")
        Label(frame, image=self.icon).pack(padx=4, pady=4, side="left")
        Label(frame,
              text=_("There is a synchronization conflict. What do you want to do?"),
              font="TkDefaultFont 10 bold").pack(side="right", fill="x",
                                                 anchor="center", expand=True,
                                                 padx=4, pady=4)
        Button(self, text=_("Download notes from server"),
               command=self.download).grid(row=1, column=0, padx=4, pady=4)
        Button(self, text=_("Upload local notes on server"),
               command=self.upload).grid(row=1, column=1, padx=4, pady=4)

    def download(self):
        self.action = "download"
        self.destroy()

    def upload(self):
        self.action = "upload"
        self.destroy()

    def get_action(self):
        return self.action


def download_from_server(password):
    """ Try to download notes from server, return True if it worked. """
    remote_path = CONFIG.get("Sync", "file")
    local_path = PATH_DATA
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            if os.path.exists(PATH_DATA):
                setlocale(LC_ALL, 'C')
                mtime_server = time.mktime(time.strptime(webdav.ls(remote_path)[0].mtime + time.strftime("%z"),
                                                         "%a, %d %b %Y %X GMT%z"))
                mtime_local = time.gmtime(os.path.getmtime(local_path))
                mtime_local = time.strftime('%a, %d %b %Y %X GMT', mtime_local)
                mtime_local = time.mktime(time.strptime(mtime_local, '%a, %d %b %Y %X GMT'))
                print(mtime_server//60 - mtime_local//60)
                if mtime_server//60 - mtime_local//60 >= -1:
                    # file is more recent on server
                    webdav.download(remote_path, local_path)
                    return True
                else:
                    # local file is more recent than the remote one
                    ask = SyncConflict()
                    ask.wait_window(ask)
                    action = ask.get_action()
                    if action == "download":
                        webdav.download(remote_path, local_path)
                        return True
                    elif action == "upload":
                        webdav.upload(local_path, remote_path)
                        return True
                    else:
                        return False
            else:
                # no local notes: download remote notes
                webdav.download(remote_path, local_path)
        else:
            # first sync
            return True
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return False
    finally:
        setlocale(LC_ALL, '')

def upload_to_server(password):
    """ upload notes to server. """
    remote_path = CONFIG.get("Sync", "file")
    local_path = PATH_DATA
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            setlocale(LC_ALL, 'C')
            mtime_server = time.mktime(time.strptime(webdav.ls(remote_path)[0].mtime + time.strftime("%z"),
                                                     "%a, %d %b %Y %X GMT%z"))
            mtime_local = time.gmtime(os.path.getmtime(local_path))
            mtime_local = time.strftime('%a, %d %b %Y %X GMT', mtime_local)
            mtime_local = time.mktime(time.strptime(mtime_local, '%a, %d %b %Y %X GMT'))
            if mtime_local//60 - mtime_server//60 >= -1:
                # local file is more recent than remote one
                webdav.upload(local_path, remote_path)
            else:
                ask = SyncConflict()
                ask.wait_window(ask)
                action = ask.get_action()
                if action == "download":
                    webdav.download(remote_path, local_path)
                elif action == "upload":
                    webdav.upload(local_path, remote_path)
        else:
            # first sync
            webdav.upload(local_path, remote_path)
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return False
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local notes not found."))
    finally:
        setlocale(LC_ALL, '')

def check_login_info(password):
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        webdav.exists(CONFIG.get("Sync", "file"))
        return True
    except easywebdav.OperationFailed as e:
        if e.actual_code == 401:
            showerror(_("Error"), _("Wrong login information."))
            return False
        else:
            err = str(e).splitlines()
            message = err[0] + "\n" + err[-1].split(":")[-1].strip()
            showerror(_("Error"), message)
            return False

