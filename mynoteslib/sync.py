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


import traceback
import os
from mynoteslib.messagebox import showerror, SyncConflict
from mynoteslib.constants import CONFIG, PATH_DATA, EASYWEBDAV
import ftplib
if EASYWEBDAV:
    import easywebdav


# ---  FTP
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
    """Download notes from server."""
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
#        files = ftp.nlst()
#        if filename in files:
        ftp.retrbinary('RETR ' + filename, open(PATH_DATA, 'wb').write)
#        else:
#            raise FileNotFoundError("{remote_data_path} does not exists".format(remote_data_path=remote_path))
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc(), False)
    finally:
        ftp.quit()


def upload_to_server_ftp(password, last_sync_time):
    """Upload notes to server."""
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
        ftp.storbinary("STOR " + filename, open(PATH_DATA, "rb"))
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local notes not found."))
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc)
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
        showerror(_("Error"), _("Wrong login information."))
        return False
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())
        return False
    finally:
        ftp.quit()


def warn_exist_remote_ftp(password):
    """
    When sync is activated, if a remote note file exists, it will
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
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())
        return "error"
    finally:
        ftp.quit()


# ---  WebDav
def sync_conflict_webdav(remote_path, local_path, webdav, exists_remote_info,
                         text=None):
    """Handle sync conflict. Return the chosen action."""
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
    """Download notes from server."""
    remote_path = CONFIG.get("Sync", "file")
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        webdav.download(remote_path, PATH_DATA)
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())


def upload_to_server_webdav(password, last_sync_time):
    """ upload notes to server. """
    remote_path = CONFIG.get("Sync", "file")
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        webdav.upload(PATH_DATA, remote_path)
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local notes not found."))
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())


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
            showerror(_("Error"), str(type(e)), traceback.format_exc())
            return False
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())
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
        showerror(_("Error"), str(type(e)), traceback.format_exc())
        return "error"
    except Exception as e:
        showerror(_("Error"), str(type(e)), traceback.format_exc())
        return "error"


# ---  General functions
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
