#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
MyNotes - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

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

Custom tkinter messageboxes
"""


from webbrowser import open as url_open
from tkinter import Toplevel, PhotoImage, Text
from tkinter.ttk import Label, Button, Frame, Style
from mynoteslib.autoscrollbar import AutoScrollbar as Scrollbar
from mynoteslib.constants import ICONS, IM_ERROR_DATA


class SyncConflict(Toplevel):
    def __init__(self, master=None,
                 text=_("There is a synchronization conflict. What do you want to do?")):
        Toplevel.__init__(self, master, class_='MyNotes')
        self.icon = PhotoImage(data=IM_ERROR_DATA)
        self.title(_("Sync Conflict"))
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.action = ""
        frame = Frame(self)
        frame.grid(row=0, columnspan=2, sticky="eswn")
        Label(frame, image=self.icon).pack(padx=4, pady=4, side="left")
        Label(frame, text=text,
              font="TkDefaultFont 10 bold").pack(side="right", fill="x",
                                                 anchor="center", expand=True,
                                                 padx=4, pady=4)
        Button(self, text=_("Download notes from server"),
               command=self.download).grid(row=1, column=0, padx=4, pady=4, sticky='ew')
        Button(self, text=_("Upload local notes on server"),
               command=self.upload).grid(row=1, column=1, padx=4, pady=4, sticky='ew')

    def download(self):
        self.action = "download"
        self.destroy()

    def upload(self):
        self.action = "upload"
        self.destroy()

    def get_action(self):
        return self.action


class OneButtonBox(Toplevel):
    def __init__(self, parent=None, title="", message="", button="Ok", image=None):
        """
        Create a message box with one button.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text (that can be selected)
            button: message displayed on the button
            image: image displayed at the left of the message, either a PhotoImage or a string
        """
        Toplevel.__init__(self, parent, class_='MyNotes')
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.result = ""
        self.button = button
        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = PhotoImage(master=self, data=data)
            else:
                self.img = PhotoImage(master=self, file=image)
            image = self.img
        frame = Frame(self)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        l = len(message)
        w = max(1, min(l, 50))
        h = 0
        for line in message.splitlines():
            h += 1 + len(line) // w
        if h < 3:
            w = min(l, 35)
            h = 0
            for line in message.splitlines():
                h += 1 + len(line) // w
        display = Text(frame, relief='flat', highlightthickness=0,
                       font="TkDefaultFont 10 bold", bg=self.cget('bg'),
                       height=h, width=w, wrap="word")
        display.configure(inactiveselectbackground=display.cget("selectbackground"))
        display.insert("1.0", message)
        display.configure(state="disabled")
        display.grid(row=0, column=1, pady=(10, 4), padx=4, sticky="ewns")
        display.bind("<Button-1>", lambda event: display.focus_set())
        if image:
            Label(frame, image=image).grid(row=0, column=0, padx=4, pady=(10, 4))
        b = Button(self, text=button, command=self.validate)
        frame.pack()
        b.pack(padx=10, pady=10)
        self.grab_set()
        b.focus_set()

    def validate(self):
        self.result = self.button
        self.destroy()

    def get_result(self):
        return self.result


class ShowError(Toplevel):
    def __init__(self, parent=None, title="", message="", traceback="",
                 report_msg=False, button="Ok", image="error"):
        """
        Create an error messagebox.
        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text (that can be selected)
            button: message displayed on the button
            traceback: error traceback to display below the error message
            report_msg: if True display a suggestion to report error
            image: image displayed at the left of the message, either a PhotoImage or a string
        """
        Toplevel.__init__(self, parent, class_='MyNotes')
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.result = ""
        self.button = button

        style = Style(self)
        style.configure("url.TLabel", foreground="blue")
        style.configure("txt.TFrame", background='white')
        if not parent:
            style.theme_use('clam')

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = PhotoImage(master=self, data=data)
            else:
                self.img = PhotoImage(master=self, file=image)
            image = self.img
        frame = Frame(self)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        l = len(message)
        l2 = len(traceback)
        w = max(1, min(max(l, l2), 50))
        if not l2 and l // w < 3:
            w = 35
        h = 0
        for line in message.splitlines():
            h += 1 + len(line) // w
        h2 = 0
        for line in traceback.splitlines():
            h2 += 1 + len(line) // w

        display = Text(frame, relief='flat', highlightthickness=0,
                       font="TkDefaultFont 10 bold", bg=self.cget('bg'),
                       height=h, width=w, wrap="word")
        display.configure(inactiveselectbackground=display.cget("selectbackground"))
        display.insert("1.0", message)
        display.configure(state="disabled")
        display.grid(row=0, column=1, pady=(10, 4), padx=4, sticky="ewns")
        display.bind("<Button-1>", lambda event: display.focus_set())
        if image:
            Label(frame, image=image).grid(row=0, column=0, padx=4, pady=(10, 4))
        frame.pack(fill='x')

        if traceback:
            frame2 = Frame(self)
            frame2.columnconfigure(0, weight=1)
            frame2.rowconfigure(0, weight=1)
            txt_frame = Frame(frame2, style='txt.TFrame', relief='sunken',
                              borderwidth=1)
            error_msg = Text(txt_frame, width=w, wrap='word', font="TkDefaultFont 10",
                             bg='white', height=8, highlightthickness=0)
            error_msg.bind("<Button-1>", lambda event: error_msg.focus_set())
            error_msg.insert('1.0', traceback)
            error_msg.configure(state="disabled")
            scrolly = Scrollbar(frame2, orient='vertical',
                                command=error_msg.yview)
            scrolly.grid(row=0, column=1, sticky='ns')
            scrollx = Scrollbar(frame2, orient='horizontal',
                                command=error_msg.xview)
            scrollx.grid(row=1, column=0, sticky='ew')
            error_msg.configure(yscrollcommand=scrolly.set,
                                xscrollcommand=scrollx.set)
            error_msg.pack(side='left', fill='both', expand=True)
            txt_frame.grid(row=0, column=0, sticky='ewsn')
            frame2.pack(fill='both', padx=4, pady=(4, 4))
        if report_msg:
            report_frame = Frame(self)
            Label(report_frame, text=_("Please report this bug on ")).pack(side="left")
            url = Label(report_frame, style="url.TLabel", cursor="hand1",
                        font="TkDefaultFont 10 underline",
                        text="https://github.com/j4321/MyNotes/issues")
            url.pack(side="left")
            url.bind("<Button-1>", lambda e: url_open("https://github.com/j4321/MyNotes/issues"))
            report_frame.pack(fill="x", padx=4, pady=(4, 0))
        b = Button(self, text=button, command=self.validate)
        b.pack(padx=10, pady=(4, 10))
        self.update_idletasks()
        bbox = display.bbox('end - 1c')
        if display.winfo_height() - bbox[1] - bbox[3] > 10:
            display.configure(height=h - 1)
        self.grab_set()
        b.focus_set()

    def validate(self):
        self.result = self.button
        self.destroy()

    def get_result(self):
        return self.result


class TwoButtonBox(Toplevel):
    """Messagebox with two buttons."""

    def __init__(self, parent, title="", message="", button1=_("Yes"),
                 button2=_("No"), image=None):
        """
        Create a messagebox with two buttons.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text
            button1/2: message displayed on the first/second button
            image: image displayed at the left of the message
        """

        Toplevel.__init__(self, parent, class_='MyNotes')
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.result = ""
        self.button1 = button1
        self.button2 = button2

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = PhotoImage(master=self, data=data)
            else:
                self.img = PhotoImage(master=self, file=image)
            image = self.img
        frame = Frame(self)
        frame.grid(row=0, columnspan=2, sticky="ewsn")
        if image:
            Label(frame, image=image).pack(side="left", padx=(10, 4), pady=(10, 4))
        Label(frame, text=message, font="TkDefaultFont 10 bold",
              wraplength=335).pack(side="left", padx=(4, 10), pady=(10, 4))

        b1 = Button(self, text=button1, command=self.command1)
        b1.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        Button(self, text=button2,
               command=self.command2).grid(row=1, column=1, padx=10, pady=10,
                                           sticky="w")
        self.grab_set()
        b1.focus_set()

    def command1(self):
        self.result = self.button1
        self.destroy()

    def command2(self):
        self.result = self.button2
        self.destroy()

    def get_result(self):
        return self.result


class AskYesNoCancel(Toplevel):
    """Messagebox with two buttons."""

    def __init__(self, parent, title="", message="", image=None,
                 button1=_("Yes"), button2=_("No"), button3=_("Cancel")):
        """
        Create a messagebox with three buttons.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text
            button1/2: message displayed on the first/second button
            image: image displayed at the left of the message
        """

        Toplevel.__init__(self, parent, class_='MyNotes')
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.result = None

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = PhotoImage(master=self, data=data)
            else:
                self.img = PhotoImage(master=self, file=image)
            image = self.img
        frame = Frame(self)
        frame.grid(row=0, columnspan=3, sticky="ewsn")
        if image:
            Label(frame, image=image).pack(side="left", padx=(10, 4), pady=(10, 4))
        Label(frame, text=message, font="TkDefaultFont 10 bold",
              wraplength=335).pack(side="left", padx=(4, 10), pady=(10, 4))

        b1 = Button(self, text=button1, command=self.command1)
        b1.grid(row=1, column=0, padx=10, pady=10)
        Button(self, text=button2, command=self.command2).grid(row=1, column=1,
                                                               padx=10, pady=10)
        Button(self, text=button3, command=self.destroy).grid(row=1, column=2,
                                                              padx=10, pady=10)
        self.grab_set()
        b1.focus_set()

    def command1(self):
        self.result = True
        self.destroy()

    def command2(self):
        self.result = False
        self.destroy()

    def get_result(self):
        return self.result


def showmessage(title="", message="", parent=None, button="Ok", image=None):
    """
    Display a dialog with a single button.

    Return the text of the button ("Ok" by default)

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        button: text displayed on the button
        image: image to display on the left of the message, either a PhotoImage
               or a string ('information', 'error', 'question', 'warning' or
               image path)
    """
    box = OneButtonBox(parent, title, message, button, image)
    box.wait_window(box)
    return box.get_result()


def showerror(title="", message="", traceback="", report_msg=False, parent=None):
    """
    Display an error dialog.

    Return "Ok"

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        traceback: error traceback to display below the error message
        report_msg: if True display a suggestion to report error
        parent: parent window
    """
    box = ShowError(parent, title, message, traceback, report_msg)
    box.wait_window(box)
    return box.get_result()


def showinfo(title="", message="", parent=None):
    """
    Display an information dialog with a single button.

    Return "Ok".

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
    """
    return showmessage(title, message, parent, image="information")


def askokcancel(title="", message="", parent=None, icon=None):
    """
    Display a dialog with buttons "Ok" and "Cancel".

    Return True if "Ok" is selected, False otherwise.

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        icon: icon to display on the left of the message, either a PhotoImage
              or a string ('information', 'error', 'question', 'warning' or
               mage path)
    """
    if icon is None:
        icon = "question"
    box = TwoButtonBox(parent, title, message, "Ok", _("Cancel"), icon)
    box.wait_window(box)
    return box.get_result() == "Ok"


def askyesnocancel(title="", message="", parent=None, icon=None):
    """
    Display a dialog with buttons "Yes","No" and "Cancel".

    Return True if "Ok" is selected, False if "No" is selected, None otherwise.

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        icon: icon to display on the left of the message, either a PhotoImage
              or a string ('information', 'error', 'question', 'warning' or
               mage path)
    """
    if icon is None:
        icon = "question"
    box = AskYesNoCancel(parent, title, message, image=icon)
    box.wait_window(box)
    return box.get_result()
