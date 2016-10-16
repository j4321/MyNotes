#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Copyright 2010 Michael Lange <klappnase@web.de>
Copyright 2016 Juliette Monsel <j_4321@sfr.fr> (adaptation du code pour Python 3.5)

Python wrapper for Tktray.

Tktray is an extension that is able to create system tray icons.
It follows http://www.freedesktop.org specifications when looking up the
system tray manager. This protocol is supported by modern versions of
KDE and Gnome panels, and by some other panel-like application.
"""

import tkinter

class Icon(tkinter.BaseWidget, tkinter.Wm):
    def __init__(self, master=None, cnf={}, **kw):
        '''
            Create a new icon for the system tray. The application managing the
            system tray is notified about the new icon. It normally results in the
            icon being added to the tray. If there is no system tray at the icon
            creation time, the icon will be invisible. When a new system tray appears,
            the icon will be added to it. Since tktray 1.3, if the tray crashes and
            destroys your icon, it will be recreated on a new system tray when it's
            available.
            OPTIONS:
                class   WM_CLASS attribute for icon window. Tray manager may use class
                        name to remember icon position or other attributes. This name
                        may be used for event binding as well. For now, real icon
                        window is distinct from the user-specified widget: it may be
                        recreated and destroyed several times during icon lifetime,
                        when a system tray crashes, terminates, disappears or appears.
                        However, tktray tries to forward click and motion events from
                        this inner window to user widget, so event bindings on widget
                        name should work as they used to. This option applies to a real
                        icon window, not to a user-visible widget, so don't rely on it
                        to set widget defaults from an option database: the standard
                        "TrayIcon" class name is used for it.

                docked  boolean indicating whether the real icon window should be
                        embedded into a tray when it exists. Think of it as a heavier
                        version of -visible option: there is a guarantee that no place
                        for icon will be reserved on any tray.

                image   image to show in the system tray. Since tktray 1.3, image type
                        "photo" is not mandatory anymore. Icon will be automatically
                        redrawn on any image modifications. For Tk, deleting an image
                        and creating an image with the same name later is a kind of
                        image modification, and tktray follows this convention. Photo
                        image operations that modify existing image content are another
                        example of events triggering redisplay. Requested size for icon
                        is set according to the image's width and height, but obeying
                        (or disobeying) this request is left for the tray.

                shape   used to put a nonrectangular shape on an icon window. Ignored
                        for compatibility.

                visible boolean value indicating whether the icon must be visible.
                        The system tray manager continues to manage the icon whether
                        it is visible or not. Thus when invisible icon becomes visible,
                        its position on the system tray is likely to remain the same.
                        Tktray currently tries to find a tray and embed into it as
                        soon as possible, whether visible is true or not. _XEMBED_INFO
                        property is set for embedded window: a tray should show or
                        hide an icon depending on this property. There may be, and
                        indeed are, incomplete tray implementations ignoring
                        _XEMBED_INFO (ex. docker). Gnome-panel "unmaps" an icon by
                        making it one pixel wide, that might to be what you expect.
                        For those implementations, the place for an icon will be
                        reserved but no image will be displayed: tktray takes care of
                        it. Tktray also blocks mouse event forwarding for invisible
                        icons, so you may be confident that no<Button> bindings will
                        be invoked at this time.

            WINDOW MANAGEMENT
                Current implementation of tktray is designed to present an interface
                of a usual toplevel window, but there are some important differences
                (some of them may come up later). System Tray specification is based
                on XEMBED protocol, and the later has a problem: when the embedder
                crashes, nothing can prevent embedded windows from destruction. Since
                tktray 1.3, no explicit icon recreation code is required on Tcl level.
                The widget was split in two: one represented by a caller-specified name,
                and another (currently $path.inner) that exists only when a tray is
                available (and dies and comes back and so on). This solution has some
                disadvantages as well. User-created widget is not mapped at all, thus
                it can't be used any more as a parent for other widgets, showing them
                instead of an image. A temporal inner window, however, may contain
                widgets.

                This version (1.3.9) introduces three virtual events: <<IconCreate>>
                <<IconConfigure>> and <<IconDestroy>>. <<IconCreate>> is generated
                when docking is requesting for an icon. <<IconConfigure>> is generated
                when an icon window is resized or changed in some other way.
                <<IconDestroy>> is generated when an icon is destroyed due to panel
                crash or undocked with unsetting -docked option.
        '''

        if not master:
            if tkinter._support_default_root:
                if not tkinter._default_root:
                    tkinter._default_root = tkinter.Tk()
                master = tkinter._default_root
        self.TktrayVersion = master.tk.call('package', 'require', 'tktray')

        # stolen from tkinter.Toplevel
        if kw:
            cnf = tkinter._cnfmerge((cnf, kw))
        extra = ()
        for wmkey in ['screen', 'class_', 'class', 'visible', 'colormap']:
            if wmkey in cnf:
                val = cnf[wmkey]
                # TBD: a hack needed because some keys
                # are not valid as keyword arguments
                if wmkey[-1] == '_':
                    opt = '-'+wmkey[:-1]
                else:
                    opt = '-'+wmkey
                extra = extra + (opt, val)
                del cnf[wmkey]
        tkinter.BaseWidget.__init__(self, master, 'tktray::icon', cnf, {}, extra)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.menu = tkinter.Menu(self, tearoff=0)
        self.bind('<Button-3>', self._popupmenu)

    def bbox(self):
        return self._getints(self.tk.call(self._w, 'bbox')) or None

    def _popupmenu(self, event):
        w, h = self.menu.winfo_reqwidth(), self.menu.winfo_reqheight()
        x0, y0, x1, y1 = self.bbox()
        # get the coords for the popup menu; we want it to the mouse pointer's
        # left and above the pointer in case the taskbar is on the bottom of the
        # screen, else below the pointer; add 1 pixel towards the pointer in each
        # dimension, so the pointer is '*inside* the menu when the button is being
        # released, so the menu will not unpost on the initial button-release event
        if y0 > self.winfo_screenheight() / 2:
            # assume the panel is at the bottom of the screen
            x, y = event.x_root - w + 1, event.y_root - h + 1
        else:
            x, y = event.x_root - w + 1, event.y_root - 1
        # make sure that x is not outside the screen
        if x < 5:
            x = 5
        self.menu.tk_popup(x, y)
