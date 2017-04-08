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


import easywebdav, ftplib
import traceback
import os, shutil
from tkinter import Menu, StringVar
from tkinter.ttk import Frame, Label, Entry, Checkbutton, Menubutton
from mynoteslib.messagebox import showerror, SyncConflict
from mynoteslib.constantes import CONFIG, PATH_DATA, PATH_DATA_INFO, save_modif_info


class SyncSettings(Frame):
    def __init__(self, master, password=""):
        Frame.__init__(self, master)
        self.columnconfigure(1, weight=1)

        self.sync_state = Checkbutton(self,
                                      text=_("Synchronize notes with server"),
                                      command=self.toggle_sync)
        if CONFIG.getboolean("Sync", "on"):
            self.sync_state.state(("selected",))
        else:
            self.sync_state.state(("!selected",))
        self.server_type = StringVar(self, CONFIG.get("Sync", "server_type"))
        menu_type = Menu(self, tearoff=False)
        self.button_type = Menubutton(self, textvariable=self.server_type,
                                      menu=menu_type)
        menu_type.add_radiobutton(label="FTP", value="FTP",
                                  command=self.set_type_ftp,
                                  variable=self.server_type)
        menu_type.add_radiobutton(label="WebDav", value="WebDav",
                                  command=self.set_type_webdav,
                                  variable=self.server_type)
        self.server = Entry(self)
        self.server.insert(0, CONFIG.get("Sync", "server"))
        self.user = Entry(self)
        self.user.insert(0, CONFIG.get("Sync", "username"))
        self.password = Entry(self, show="*")
        self.password.insert(0, password)
        self.protocol = StringVar(self, CONFIG.get("Sync", "protocol"))
        self.menu_protocol = Menu(self, tearoff=False)
        self.button_protocol = Menubutton(self, textvariable=self.protocol,
                                          menu=self.menu_protocol)
        if self.server_type.get() == "FTP":
            self.menu_protocol.add_radiobutton(label="Simple FTP", value="FTP",
                                               variable=self.protocol)
            self.menu_protocol.add_radiobutton(label="FTP over TLS", value="FTPS",
                                               variable=self.protocol)
        else:
            self.menu_protocol.add_radiobutton(label="HTTP", value="http",
                                               command=self.set_protocol_http,
                                               variable=self.protocol)
            self.menu_protocol.add_radiobutton(label="HTTPS", value="https",
                                               command=self.set_protocol_https,
                                               variable=self.protocol)
        self.port = Entry(self)
        self.port.insert(0, CONFIG.get("Sync", "port"))
        self.file = Entry(self)
        self.file.insert(0, CONFIG.get("Sync", "file"))

        self.sync_state.grid(row=0, columnspan=2, sticky="w", padx=4, pady=4)
        Label(self, text=_("Server type")).grid(row=1, column=0,
                                                sticky="e", padx=4, pady=4)
        Label(self, text=_("Server address")).grid(row=2, column=0,
                                                   sticky="e", padx=4, pady=4)
        Label(self, text=_("Username")).grid(row=3, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Password")).grid(row=4, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Protocol")).grid(row=5, column=0,
                                             sticky="e", padx=4, pady=4)
        Label(self, text=_("Port")).grid(row=6, column=0,
                                         sticky="e", padx=4, pady=4)
        Label(self, text=_("Server file")).grid(row=7, column=0,
                                                sticky="e", padx=4, pady=4)
        self.button_type.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.server.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.user.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        self.password.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        self.button_protocol.grid(row=5, column=1, sticky="ew", padx=4, pady=4)
        self.port.grid(row=6, column=1, sticky="ew", padx=4, pady=4)
        self.file.grid(row=7, column=1, sticky="ew", padx=4, pady=4)

        self.toggle_sync()

    def toggle_sync(self):
        if "selected" in self.sync_state.state():
            state = "!disabled"
            if not self.port.get():
                server_type = self.server_type.get()
                if server_type == "FTP":
                    self.port.insert(0, str(ftplib.FTP_PORT))
                elif server_type == "WebDav":
                    if self.protocol.get() == "http":
                        self.port.insert(0, "80")
                    else:
                        self.port.insert(0, "443")
        else:
            state = "disabled"
        self.button_type.state((state,))
        self.server.state((state,))
        self.user.state((state,))
        self.password.state((state,))
        self.port.state((state,))
        self.button_protocol.state((state,))
        self.file.state((state,))

    def set_protocol_http(self):
        self.port.delete(0, "end")
        self.port.insert(0, "80")

    def set_protocol_https(self):
        self.port.delete(0, "end")
        self.port.insert(0, "443")

    def set_type_ftp(self):
        self.port.delete(0, "end")
        self.port.insert(0, str(ftplib.FTP_PORT))
        self.menu_protocol.delete(0, "end")
        self.menu_protocol.add_radiobutton(label="Simple FTP", value="FTP",
                                           variable=self.protocol)
        self.menu_protocol.add_radiobutton(label="FTP over TLS", value="FTPS",
                                           variable=self.protocol)
        self.protocol.set("FTPS")

    def set_type_webdav(self):
        self.port.delete(0, "end")
        self.port.insert(0, "443")
        self.menu_protocol.delete(0, "end")
        self.menu_protocol.add_radiobutton(label="HTTP", value="http",
                                           command=self.set_protocol_http,
                                           variable=self.protocol)
        self.menu_protocol.add_radiobutton(label="HTTPS", value="https",
                                           command=self.set_protocol_https,
                                           variable=self.protocol)
        self.protocol.set("https")

    def save_sync_settings(self):
        CONFIG.set("Sync", "on", str("selected" in self.sync_state.state()))
        CONFIG.set("Sync", "server_type", self.server_type.get())
        CONFIG.set("Sync", "server", self.server.get())
        CONFIG.set("Sync", "username", self.user.get())
        CONFIG.set("Sync", "protocol", self.protocol.get())
        CONFIG.set("Sync", "port", self.port.get())
        CONFIG.set("Sync", "file", self.file.get())
        return self.password.get()

### FTP
def sync_conflict_ftp(remote_path, local_path, ftp, exists_remote_info, text=None):
    """ handle sync conflict. Return the chosen action. """
    if text:
        ask = SyncConflict(text=text)
    else:
        ask = SyncConflict()
    ask.wait_window(ask)
    action = ask.get_action()
    if action == "download":
        ftp.retrbinary('RETR ' + remote_path, open(local_path, 'wb').write)
        if exists_remote_info:
            ftp.retrlines('RETR %s.info' % remote_path, open(local_path + ".info", 'w').write)
    elif action == "upload":
        ftp.storbinary("STOR " + remote_path, open(local_path, "rb"))
        ftp.storlines("STOR %s.info" % remote_path, open(local_path + ".info", "r"))
    return action

def download_from_server_ftp(password):
    """ Try to download notes from server, return True if it worked. """
    remote_path = CONFIG.get("Sync", "file")
    try:
        if CONFIG.get("Sync", "protocol") == "FTP":
            ftp = ftplib.FTP()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
        else:
            ftp = ftplib.FTP_TLS()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
            ftp.prot_p()
        directory, filename = os.path.split(remote_path)
        if directory:
            ftp.cwd(directory)
        files = ftp.nlst()
        if filename in files:
            exists_remote_info = (filename + ".info") in files
            if os.path.exists(PATH_DATA):
                exists_local_info = os.path.exists(PATH_DATA_INFO)
                if exists_local_info:
                    with open(PATH_DATA_INFO) as fich:
                        tps_local = float(fich.readlines()[1])
                else:
                    tps_local = os.path.getmtime(PATH_DATA)
                    save_modif_info(tps_local)
                if exists_remote_info:
                    ftp.retrlines('RETR %s.info' % filename, open("/tmp/notes.info", 'w').write)
                    with open("/tmp/notes.info") as fich:
                        tps_remote = float(fich.readlines()[1])
                    if int(tps_remote)//60 >= int(tps_local)//60:
                        # file is more recent on server
                        ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
                        shutil.move("/tmp/notes.info", PATH_DATA_INFO)
                        return True
                    else:
                        res = sync_conflict_ftp(filename, PATH_DATA, ftp, True,
                                                text=_("Local notes are more recent than on server. What do you want to do?"))
                        return res != ""
                else:
                    res = sync_conflict_ftp(filename, PATH_DATA, ftp, False)
                    return res != ""

            else:
                # no local notes: download remote notes
                ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
                if exists_remote_info:
                    ftp.retrlines('RETR %s.info' % filename, open(PATH_DATA_INFO, 'w').write)
                return True
        else:
            # first sync
            return True
#                setlocale(LC_ALL, 'C')
#                mtime_server = time.mktime(time.strptime(ftp.sendcmd('MDTM '+ filename),
#                                                         "%Y%m%d%H%M%S"))
#                mtime_local = time.gmtime(os.path.getmtime(PATH_DATA))
#                mtime_local = time.strftime("%Y%m%d%H%M%S", mtime_local)
#                mtime_local = time.mktime(time.strptime(mtime_local, "%Y%m%d%H%M%S"))
#                if mtime_server//60 - mtime_local//60 >= -1:
#                    # file is more recent on server
#                    ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
#                    return True
#                else:
#                    # local file is more recent than the remote one
#                    ask = SyncConflict()
#                    ask.wait_window(ask)
#                    action = ask.get_action()
#                    if action == "download":
#                        ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
#                        return True
#                    elif action == "upload":
#                        ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
#                        return True
#                    else:
#                        return False
#            else:
#                # no local notes: download remote notes
#                ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
#        else:
#            # first sync
#            return True
    except ftplib.Error as e:
        showerror(_("Error"), str(e))
        return False
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False
    finally:
        ftp.quit()

def upload_to_server_ftp(password, last_sync_time):
    """ upload notes to server. """
    remote_path = CONFIG.get("Sync", "file")

    try:
        if CONFIG.get("Sync", "protocol") == "FTP":
            ftp = ftplib.FTP()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
        else:
            ftp = ftplib.FTP_TLS()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
            ftp.prot_p()
        directory, filename = os.path.split(remote_path)
        if directory:
            ftp.cwd(directory)
        files = ftp.nlst()
        if filename in files:
            exists_remote_info = (filename + ".info") in files
            save_modif_info()
            with open(PATH_DATA_INFO) as fich:
                info_local = fich.readlines()
            if exists_remote_info:
                ftp.retrlines('RETR %s.info' % filename, open("/tmp/notes.info", 'w').write)
                with open("/tmp/notes.info") as fich:
                    info_remote = fich.readlines()
                if info_local[0] != info_remote[0] and last_sync_time//60 < float(info_remote[1])//60:
                    # there was an update from another computer in the mean time
                    sync_conflict_ftp(filename, PATH_DATA, ftp, True)
                else:
                    ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
                    ftp.storlines("STOR %s.info" % filename, open(PATH_DATA_INFO, "r"))
            else:
                sync_conflict_ftp(filename, PATH_DATA, ftp, False)

        else:
            # first sync
            ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
            ftp.storlines("STOR %s.info" % filename, open(PATH_DATA_INFO, "r"))

#            setlocale(LC_ALL, 'C')
#            mtime_server = time.mktime(time.strptime(ftp.sendcmd('MDTM '+ filename),
#                                                     "%Y%m%d%H%M%S"))
#            mtime_local = time.gmtime(os.path.getmtime(PATH_DATA))
#            mtime_local = time.strftime("%Y%m%d%H%M%S", mtime_local)
#            mtime_local = time.mktime(time.strptime(mtime_local, "%Y%m%d%H%M%S"))
#            if mtime_local//60 - mtime_server//60 >= -1:
#                # local file is more recent than remote one
#                ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
#            else:
#                ask = SyncConflict()
#                ask.wait_window(ask)
#                action = ask.get_action()
#                if action == "download":
#                    ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
#                elif action == "upload":
#                    ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
#        else:
#            # first sync
#            ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
#
    except ftplib.Error as e:
        showerror(_("Error"), str(e))
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local notes not found."))
    except Exception:
        showerror(_("Error"), traceback.format_exc())
    finally:
        ftp.quit()

def check_login_info_ftp(password):
    try:
        if CONFIG.get("Sync", "protocol") == "FTP":
            ftp = ftplib.FTP()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
        else:
            ftp = ftplib.FTP_TLS()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
        return True
    except ftplib.error_perm as e:
        print(e)
        showerror(_("Error"), _("Wrong login information."))
        return False
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False
    finally:
        ftp.quit()

def warn_exist_remote_ftp(password):
    """ When sync is activated, if a remote note file exists, it will
        be erased when the local file will be sync when app is closed. So
        warn user and ask him what to do.
    """
    remote_path = CONFIG.get("Sync", "file")

    try:
        if CONFIG.get("Sync", "protocol") == "FTP":
            ftp = ftplib.FTP()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
        else:
            ftp = ftplib.FTP_TLS()
            ftp.connect(CONFIG.get("Sync", "server"),
                        CONFIG.getint("Sync", "port"))
            ftp.login(user=CONFIG.get("Sync", "username"), passwd=password)
            ftp.prot_p()
        if ftp.nlst(remote_path):
            # it's a directory
            CONFIG.set("Sync", "file", os.path.join(remote_path, "notes"))
            directory, filename = remote_path, "notes"
        else:
            directory, filename = os.path.split(remote_path)
        if directory:
            ftp.cwd(directory)
        if filename in ftp.nlst():
            ask = SyncConflict(text=_("The file {filename} already exists on the server.\nWhat do you want to do?").format(filename=remote_path))
            ask.wait_window(ask)
            action = ask.get_action()
            if action == "download":
                ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
            elif action == "upload":
                ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
            return action
        else:
            return "upload"
    except ftplib.Error as e:
        showerror(_("Error"), str(e))
        return "error"
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return "error"
    finally:
        ftp.quit()

### WebDav
def sync_conflict_webdav(remote_path, local_path, webdav, exists_remote_info,
                         text=None):
    """ handle sync conflict. Return the chosen action. """
    if text:
        ask = SyncConflict(text=text)
    else:
        ask = SyncConflict()
    ask.wait_window(ask)
    action = ask.get_action()
    if action == "download":
        webdav.download(remote_path, local_path)
        if exists_remote_info:
            webdav.download(remote_path + ".info", local_path + ".info")
    elif action == "upload":
        webdav.upload(local_path, remote_path)
        webdav.upload(local_path + ".info", remote_path + ".info")
    return action

def download_from_server_webdav(password):
    """ Try to download notes from server, return True if it worked. """
    remote_path = CONFIG.get("Sync", "file")
    remote_info_path = remote_path + ".info"
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            exists_remote_info = webdav.exists(remote_info_path)
            if os.path.exists(PATH_DATA):
                exists_local_info = os.path.exists(PATH_DATA_INFO)
                if exists_local_info:
                    with open(PATH_DATA_INFO) as fich:
                        tps_local = float(fich.readlines()[1])
                else:
                    tps_local = os.path.getmtime(PATH_DATA)
                    save_modif_info(tps_local)
                if exists_remote_info:
                    webdav.download(remote_info_path, "/tmp/notes.info")
                    with open("/tmp/notes.info") as fich:
                        tps_remote = float(fich.readlines()[1])
                    if int(tps_remote)//60 >= int(tps_local)//60:
                        # file is more recent on server
                        webdav.download(remote_path, PATH_DATA)
                        shutil.move("/tmp/notes.info", PATH_DATA_INFO)
                        return True
                    else:
                        res = sync_conflict_webdav(remote_path, PATH_DATA,
                                                   webdav, exists_remote_info,
                                                   text=_("Local notes are more recent than on server. What do you want to do?"))
                        return res != ""
                else:
                    res = sync_conflict_webdav(remote_path, PATH_DATA, webdav, False)
                    return res != ""

            else:
                # no local notes: download remote notes
                webdav.download(remote_path, PATH_DATA)
                if exists_remote_info:
                    webdav.download(remote_info_path, PATH_DATA_INFO)
                return True
        else:
            # first sync
            return True
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return False
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False

def upload_to_server_webdav(password, last_sync_time):
    """ upload notes to server. """
    remote_path = CONFIG.get("Sync", "file")
    remote_info_path = remote_path + ".info"
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            exists_remote_info = webdav.exists(remote_info_path)
            save_modif_info()
            with open(PATH_DATA_INFO) as fich:
                info_local = fich.readlines()
            if exists_remote_info:
                webdav.download(remote_info_path, "/tmp/notes.info")
                with open("/tmp/notes.info") as fich:
                    info_remote = fich.readlines()
                if info_local[0] != info_remote[0] and last_sync_time//60 < float(info_remote[1])//60:
                    # there was an update from another computer in the mean time
                    sync_conflict_webdav(remote_path, PATH_DATA, webdav, exists_remote_info)
                else:
                    webdav.upload(PATH_DATA, remote_path)
                    webdav.upload(PATH_DATA_INFO, remote_info_path)
            else:
                sync_conflict_webdav(remote_path, PATH_DATA, webdav, False)
#            setlocale(LC_ALL, 'C')
#            mtime_server = time.mktime(time.strptime(webdav.ls(remote_path)[0].mtime + time.strftime("%z"),
#                                                     "%a, %d %b %Y %X GMT%z"))
#            mtime_local = time.gmtime(os.path.getmtime(PATH_DATA))
#            mtime_local = time.strftime('%a, %d %b %Y %X GMT', mtime_local)
#            mtime_local = time.mktime(time.strptime(mtime_local, '%a, %d %b %Y %X GMT'))
#            if mtime_local//60 - mtime_server//60 >= -1:
#                # local file is more recent than remote one
#                webdav.upload(PATH_DATA, remote_path)
#            else:
#                ask = SyncConflict()
#                ask.wait_window(ask)
#                action = ask.get_action()
#                if action == "download":
#                    webdav.download(remote_path, PATH_DATA)
#                elif action == "upload":
#                    webdav.upload(PATH_DATA, remote_path)
        else:
            # first sync
            webdav.upload(PATH_DATA, remote_path)
            webdav.upload(PATH_DATA_INFO, remote_info_path)
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local notes not found."))
    except Exception:
        showerror(_("Error"), traceback.format_exc())

def check_login_info_webdav(password):
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
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False

def warn_exist_remote_webdav(password):
    """ When sync is activated, if a remote note file exists, it will
        be erased when the local file will be sync when app is closed. So
        warn user and ask him what to do.
    """
    remote_path = CONFIG.get("Sync", "file")
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            ls = webdav.ls(remote_path)
            if len(ls) == 1:
                # it's a file
                remote_info_path = remote_path + '.info'
                ex = webdav.exists(remote_info_path)
                action = sync_conflict_webdav(remote_path, PATH_DATA, webdav, ex,
                                              _("The file {filename} already exists on the server.\
\nWhat do you want to do?").format(filename=remote_path))
                return action
            else:
                # it's a folder
                remote_path = os.path.join(remote_path, 'notes')
                CONFIG.set("Sync", "file", remote_path)
                if webdav.exists(remote_path):
                    remote_info_path = remote_path + '.info'
                    ex = webdav.exists(remote_info_path)
                    action = sync_conflict_webdav(remote_path, PATH_DATA, webdav, ex,
                                                  _("The file {filename} already exists on the server.\
\nWhat do you want to do?").format(filename=remote_path))
                    return action
                else:
                    return "upload"
        else:
            return "upload"
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return "error"
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return "error"

### General functions
def download_from_server(password):
    server_type = CONFIG.get("Sync", "server_type")
    if server_type == "FTP":
        return download_from_server_ftp(password)
    elif server_type == "WebDav":
        return download_from_server_webdav(password)
    else:
        raise ValueError("Wrong server type %s" % server_type)

def upload_to_server(password, time):
    server_type = CONFIG.get("Sync", "server_type")
    if server_type == "FTP":
        upload_to_server_ftp(password, time)
    elif server_type == "WebDav":
        upload_to_server_webdav(password, time)
    else:
        raise ValueError("Wrong server type %s" % server_type)

def check_login_info(password):
    server_type = CONFIG.get("Sync", "server_type")
    if server_type == "FTP":
        return check_login_info_ftp(password)
    elif server_type == "WebDav":
        return check_login_info_webdav(password)
    else:
        raise ValueError("Wrong server type %s" % server_type)

def warn_exist_remote(password):
    server_type = CONFIG.get("Sync", "server_type")
    if server_type == "FTP":
        return warn_exist_remote_ftp(password)
    elif server_type == "WebDav":
        return warn_exist_remote_webdav(password)
    else:
        raise ValueError("Wrong server type %s" % server_type)


