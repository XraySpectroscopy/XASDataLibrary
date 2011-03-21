import wx
import  wx.lib.scrolledpanel as scrolled
import xdi
from lib.wx import OrderedDict, pack, add_btn, add_menu, popup, \
     FileOpen, FileSave

class FileViewerPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, fname):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        labstyle = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.GROW
        ftext = open(fname, 'r').read()
        wx.StaticText(self, -1, ftext)
        

class FileImporter(wx.Frame):
    title = 'ASCII File Importer'
    def __init__(self, fname=None):
        wx.Frame.__init__(self, parent=None,
                          title=self.title, size=(400, -1))
        
        menuBar = wx.MenuBar()
        fmenu = wx.Menu()
        add_menu(self, fmenu, "E&xit\tAlt-X", "Exit this Program",
                      action=self.onClose)
        
        menuBar.Append(fmenu, "&File")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar(1, wx.CAPTION|wx.THICK_FRAME)

        splitter  = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(100)
        
        self.top_panel = wx.Panel(splitter)  # top
        self.bot_panel = FileViewerPanel(splitter, fname)  # bottom

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self.top_panel,
                                label='File Column Selections'),
                  0, wx.ALIGN_LEFT|wx.ALIGN_CENTER|wx.ALL, 1)
        pack(self.top_panel, sizer)

        splitter.SplitHorizontally(self.top_panel, self.bot_panel, 1)
       
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 5)
        pack(self, sizer)
        self.Show()
        self.Raise()

    def onClose(self, evt=None):
        "quit frame"
        self.Destroy()
