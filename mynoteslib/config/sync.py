from tkinter import Menu, StringVar
from tkinter.ttk import Frame, Label, Entry, Checkbutton, Menubutton
from mynoteslib.constants import CONFIG, EASYWEBDAV
import ftplib


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
        if EASYWEBDAV:
            menu_type.add_radiobutton(label="WebDav", value="WebDav",
                                      command=self.set_type_webdav,
                                      variable=self.server_type)
        elif self.server_type.get() == "WebDav":
            self.server_type.set("FTP")
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
