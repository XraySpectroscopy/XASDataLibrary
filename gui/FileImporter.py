import os
import wx
import xdi

from utils import pack, add_btn, add_menu, popup, FileOpen, FileSave
from utils import ElementChoice, EdgeChoice

class FileImporter(wx.Frame):
    title = 'ASCII File Importer'
    def __init__(self, fname=None, db=None):
        wx.Frame.__init__(self, parent=None,
                          title=self.title, size=(400, -1))
        self.fname = fname
        self.db    = db
        menuBar = wx.MenuBar()
        fmenu = wx.Menu()
        add_menu(self, fmenu, "E&xit\tAlt-X", "Exit this Program",
                      action=self.onClose)
        
        menuBar.Append(fmenu, "&File")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar(1, wx.CAPTION|wx.THICK_FRAME)

        splitter  = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(125)
        
        self.top_panel = wx.Panel(splitter) # top
        self.bot_panel = wx.Panel(splitter) # bottom
        self.filename  = wx.StaticText(self.bot_panel, -1, label='')
        self.fileview  = wx.TextCtrl(self.bot_panel, size=(450,200),
                                     style=wx.TE_READONLY|wx.TE_MULTILINE)

        self.fileview.SetBackgroundColour(wx.Colour(250, 250, 250))

        bsizer = wx.BoxSizer(wx.VERTICAL)

        bsizer.Add(self.filename, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        bsizer.Add(self.fileview, 1, wx.ALIGN_TOP|wx.GROW|wx.ALL, 5)
        pack(self.bot_panel, bsizer)
        
        tsizer = wx.BoxSizer(wx.VERTICAL)
        self.top_label = wx.StaticText(self.top_panel, -1,
                                       label='Data from File:')
        self.nb = wx.Notebook(self.top_panel)
        tsizer.Add(self.top_label,                  
                   0, wx.ALIGN_LEFT|wx.ALIGN_CENTER|wx.ALL, 1)
        tsizer.Add(self.nb, 1, wx.ALIGN_CENTER|wx.GROW|wx.ALL, 1)

        self.buildNotebooks()
        pack(self.top_panel, tsizer)
        splitter.SplitHorizontally(self.top_panel, self.bot_panel, 0)
       
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 5)
        pack(self, sizer)
        if fname is not None:
            self.ShowFile(fname)
        self.Show()
        self.Raise()

    def buildNotebooks(self):
        top = self.top_panel
        nb  = self.nb
        self.col_panel  = wx.Panel(nb)
        nb.AddPage(self.col_panel, 'Data Column')
        self.col_panel.SetBackgroundColour(wx.Colour(255, 255, 250))

        self.sample_panel  = wx.Panel(nb)
        nb.AddPage(self.sample_panel, 'Sample')
        self.sample_panel.SetBackgroundColour(wx.Colour(205, 255, 250))
        
        self.beamline_panel  = wx.Panel(nb)
        nb.AddPage(self.beamline_panel, 'Beamline')
        self.buildColumnPanel()

        
    def buildColumnPanel(self):
        panel = self.col_panel
        sizer = wx.GridBagSizer(10,6)
        sizer.Add(wx.StaticText(panel, label='Element:'), (1, 0), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)
        self.elem = ElementChoice(panel, db=self.db, show_all=True)
        sizer.Add(self.elem,  (1, 1), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)        
        sizer.Add(wx.StaticText(panel, label='Edge:'), (1, 2), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)
        self.edge = EdgeChoice(panel, db=self.db, show_all=True)
        sizer.Add(self.edge,  (1, 3), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)        
        pack(panel, sizer)
        
        
    def ShowFile(self, fname=None):
        if fname is not None:
            text = open(fname,'r').read()
            self.filename.SetLabel(fname)
            self.top_label.SetLabel('Data from File: %s' % (os.path.basename(fname)))
            self.fileview.Clear()
            self.fileview.SetValue(text)
            self.fileview.ShowPosition(0)
            

        try:
            self.xdifile = xdi.XDIFile(fname)
        except XDIFileException:
            self.xdifile = None
            print 'Not an XDI File'

        if self.xdifile is not None:
            print dir(self.xdifile)
            
                
    def onClose(self, evt=None):
        "quit frame"
        self.Destroy()
