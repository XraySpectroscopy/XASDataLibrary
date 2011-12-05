import wx
from utils import pack, add_btn, add_menu, popup, FileOpen, FileSave

class SpectraPanel(wx.Panel):
    "build spectra panel"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        labstyle = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.GROW
        toprow = wx.Panel(self)
        self.label  = wx.StaticText(toprow, label='Spectra:')
        self.element   = wx.StaticText(toprow, label='Element:')
        self.edge      = wx.StaticText(toprow, label='Edge: ')

        tsizer =  wx.BoxSizer(wx.HORIZONTAL)
        tsizer.Add(self.label,   1, labstyle, 4)
        tsizer.Add(self.element, 0, labstyle, 4)
        tsizer.Add(self.edge,    0, labstyle, 4)

        pack(toprow, tsizer)

        nb = self.notebook = wx.Notebook(self)

        self.data_panel  = wx.Panel(nb)
        self.sample_panel  = wx.Panel(nb)
        self.beamline_panel  = wx.Panel(nb)
        self.info_panel  = wx.Panel(nb)


        self.data_panel.SetBackgroundColour(wx.Colour(255, 255, 250))
        self.info_panel.SetBackgroundColour(wx.Colour(215, 215, 250))
        self.sample_panel.SetBackgroundColour(wx.Colour(255, 235, 250))

        nb.AddPage(self.data_panel, 'Data')
        nb.AddPage(self.sample_panel, 'Sample')
        nb.AddPage(self.beamline_panel, 'Beamline/Mono')
        nb.AddPage(self.info_panel, 'Info')

        nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChange)

        sizer =  wx.BoxSizer(wx.VERTICAL)
        sizer.Add(toprow,    0, wx.ALIGN_LEFT|wx.ALIGN_TOP, 5)
        sizer.Add(nb,        1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW, 5)
        pack(self, sizer)

        self.build_datapanel()

    def build_datapanel(self):
        self.data_panel.SetBackgroundColour(wx.Colour(250, 250, 250))

        dpan = self.data_panel
        dlabel  = wx.StaticText(dpan, label='No Data Selected')
        sizer =  wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dlabel,   0, wx.ALIGN_LEFT|wx.ALIGN_TOP, 5)
        pack(dpan, sizer)

    def onPageChange(self, evt=None):
        old = evt.GetOldSelection()
        new = evt.GetSelection()
        sel = self.notebook.GetSelection()
        evt.Skip()
