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
import wx
import wx.xrc

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

class MainFrame ( wx.Frame ):
    def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Demon's Eye Monitor", pos = wx.DefaultPosition, size = wx.Size( 651,490 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		bSizer2 = wx.BoxSizer( wx.VERTICAL )
		self.m_toolBar1 = wx.ToolBar( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL )
		self.m_toolBar1.Realize()
		bSizer2.Add( self.m_toolBar1, 0, wx.EXPAND, 5 )
		self.m_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.m_notebook1, 1, wx.EXPAND |wx.ALL, 5 )
		self.SetSizer( bSizer2 )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.m_menu_program = wx.Menu()
		self.m_menuItem_exitprogram = wx.MenuItem( self.m_menu_program, wx.ID_ANY, u"Exit Program", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_program.Append( self.m_menuItem_exitprogram )

		self.m_menubar1.Append( self.m_menu_program, u"Program" )

		self.m_menu_monitor = wx.Menu()
		self.m_menuItem_serverStart = wx.MenuItem( self.m_menu_monitor, wx.ID_ANY, u"Server Start", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_monitor.Append( self.m_menuItem_serverStart )

		self.m_menuItem_serverStop = wx.MenuItem( self.m_menu_monitor, wx.ID_ANY, u"Server Stop", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_monitor.Append( self.m_menuItem_serverStop )

		self.m_menubar1.Append( self.m_menu_monitor, u"Monitor" )

		self.m_menu_help = wx.Menu()
		self.m_menuItem_about = wx.MenuItem( self.m_menu_help, wx.ID_ANY, u"About", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_help.Append( self.m_menuItem_about )

		self.m_menubar1.Append( self.m_menu_help, u"Help" )

		self.SetMenuBar( self.m_menubar1 )

		self.m_statusBar1 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

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





