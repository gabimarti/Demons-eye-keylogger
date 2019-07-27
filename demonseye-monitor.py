#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------------------------------------------
# Name:         demonseye-monitor.py
# Purpose:      Receive keylogger data (keystrokes and screenshots).
#
# Author:       Gabriel Marti
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      27/07/2019
# Copyright:    (c) Gabriel Marti Fuentes 2019
# License:      GPL
#-----------------------------------------------------------------------------------------------------------
#

import wx

class MainWindow(wx.Frame):
    def __init__(self, parent, title, size=(600,400) ):
        wx.Frame.__init__(self, parent, title=title, size=size)
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.CreateStatusBar()          # A Statusbar in the bottom of the window

        # Setting up the menu.
        filemenu= wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File")        # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)                # Adding the MenuBar to the Frame content.
        self.Show(True)                         # Show the frame (the window)



def main():
    app = wx.App(False)                                         # Create a new app, don't redirect stdout/stderr to a window.
    frame = MainWindow(None, "Demon's Eye Monitor", (800,500))  # Top-level window.
    app.MainLoop()

if __name__ == '__main__':
    main()





