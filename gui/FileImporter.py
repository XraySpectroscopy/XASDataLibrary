import os
import wx
from xasdb import XDIFile

from utils import pack, add_btn, add_menu, popup, FileOpen, FileSave
from utils import ElementChoice, EdgeChoice, ColumnChoice, TypeChoice, FloatCtrl

class FileImporter(wx.Frame):

    title = 'ASCII File Importer'
    energy_choices = ('energy (eV)', 'energy (keV)',
                      'angle (degrees)', 'angle steps')

    def __init__(self, fname=None, db=None):
        wx.Frame.__init__(self, parent=None,
                          title=self.title, size=(500, 500))
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
        splitter.SetMinimumPaneSize(150)
        
        self.top_panel = wx.Panel(splitter) # top
        self.bot_panel = wx.Panel(splitter) # bottom
        self.filename  = wx.StaticText(self.bot_panel, -1, label='')
        self.fileview  = wx.TextCtrl(self.bot_panel, size=(150, 175),
                                     style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)

        self.fileview.SetBackgroundColour(wx.Colour(250, 250, 250))

        bsizer = wx.BoxSizer(wx.VERTICAL)
        bsizer.Add(self.filename, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        bsizer.Add(self.fileview, 1, wx.ALIGN_TOP|wx.GROW|wx.ALL, 5)
        pack(self.bot_panel, bsizer)
        
        tsizer = wx.BoxSizer(wx.VERTICAL)
        self.top_label = wx.StaticText(self.top_panel, -1,
                                       label='Data from File:')
        self.nb = wx.Notebook(self.top_panel, size=(600, 300))
        tsizer.Add(self.top_label,                  
                   0, wx.ALIGN_LEFT|wx.ALIGN_CENTER|wx.ALL, 1)
        tsizer.Add(self.nb, 1, wx.ALIGN_CENTER|wx.GROW|wx.ALL, 1)

        self.buildNotebooks()
        pack(self.top_panel, tsizer)
        splitter.SplitHorizontally(self.top_panel, self.bot_panel, -1)
       
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
        # self.col_panel.SetBackgroundColour(wx.Colour(255, 255, 250))

        self.sample_panel  = wx.Panel(nb)
        nb.AddPage(self.sample_panel, 'Sample')

        self.beamline_panel  = wx.Panel(nb)
        nb.AddPage(self.beamline_panel, 'Beamline')
        self.buildDataPanel()

        
    def buildDataPanel(self):
        "build Data / Column selection panel"
        
        panel = self.col_panel
        sizer = wx.GridBagSizer(10, 5)

        labstyle = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        choicestyle = wx.ALIGN_LEFT|wx.ALL
        namestyle = wx.ALIGN_LEFT|wx.ALL                
        btnstyle   = wx.ALIGN_CENTER|wx.ALL                
        
        def stext(label):
            return wx.StaticText(panel, label=label)

        self.elem  = ElementChoice(panel, db=self.db, show_all=True)
        self.edge  = EdgeChoice(panel, db=self.db, show_all=True)
        self.name  = wx.TextCtrl(panel, value='', size=(200,-1))

        self.save_btn = add_btn(panel, "Import Data",  action=self.onImport)

        self.column_en = ColumnChoice(panel)
        
        self.column_i0 = ColumnChoice(panel)
        self.column_it = ColumnChoice(panel)
        self.column_if = ColumnChoice(panel)
        self.column_ir = ColumnChoice(panel)
        
        self.type_en = TypeChoice(panel, self.energy_choices)
        self.type_i0 = TypeChoice(panel, ('intensity',))
        self.type_it = TypeChoice(panel, ('not collected', 'intensity','mu'))
        self.type_if = TypeChoice(panel, ('not collected', 'intensity','mu'))
        self.type_ir = TypeChoice(panel, ('not collected', 'intensity','mu'))

        self.column_en.SetSelection(0)
        self.type_en.SetSelection(0)
        self.type_i0.SetSelection(0)
        self.type_it.SetSelection(0)
        self.type_ir.SetSelection(0)
        self.type_if.SetSelection(0)
        
        self.mono_dspacing = FloatCtrl(panel, precision=6, value=0, min=0, max=100.0)
        self.mono_steps    = FloatCtrl(panel, precision=2, value=0, min=0, max=1e10)

        self.type_en.Bind(wx.EVT_CHOICE, self.onEnergyChoice)

        
        sizer.Add(stext('Spectra Name:'), (1, 0), (1, 1), labstyle, 2)
        sizer.Add(self.name,              (1, 1), (1, 2), namestyle, 2)
        sizer.Add(self.save_btn,          (1, 4), (1, 2), btnstyle, 2)

        
        sizer.Add(stext('Element:'), (2, 0), (1, 1), labstyle, 2)
        sizer.Add(self.elem,         (2, 1), (1, 1), choicestyle, 2)        
        sizer.Add(stext('Edge:'),    (2, 2), (1, 1), rlabstyle, 2)
        sizer.Add(self.edge,         (2, 3), (1, 1), choicestyle, 2)

        
        sizer.Add(stext('Data:'),        (3, 0), (1, 1), labstyle, 2)
        sizer.Add(stext(' Type:'),       (3, 1), (1, 1), labstyle, 2)
        sizer.Add(stext('Column #:'),    (3, 2), (1, 1), labstyle, 2)
        
        sizer.Add(stext('Energy:'),      (4, 0), (1, 1), labstyle, 2)
        sizer.Add(stext('I0:'),          (5, 0), (1, 1), labstyle, 2)
        sizer.Add(stext('Transmission:'),(6, 0), (1, 1), labstyle, 2)
        sizer.Add(stext('Fluorescence:'),(7, 0), (1, 1), labstyle, 2)
        sizer.Add(stext('Reference:'),   (8, 0), (1, 1), labstyle, 2)

        sizer.Add(self.type_en,          (4, 1), (1, 1), choicestyle, 2)
        sizer.Add(self.type_i0,          (5, 1), (1, 1), choicestyle, 2)
        sizer.Add(self.type_it,          (6, 1), (1, 1), choicestyle, 2)
        sizer.Add(self.type_if,          (7, 1), (1, 1), choicestyle, 2)
        sizer.Add(self.type_ir,          (8, 1), (1, 1), choicestyle, 2)

        sizer.Add(self.column_en,        (4, 2), (1, 1), choicestyle, 2)
        sizer.Add(self.column_i0,        (5, 2), (1, 1), choicestyle, 2)
        sizer.Add(self.column_it,        (6, 2), (1, 1), choicestyle, 2)
        sizer.Add(self.column_if,        (7, 2), (1, 1), choicestyle, 2)
        sizer.Add(self.column_ir,        (8, 2), (1, 1), choicestyle, 2)

        sizer.Add(stext('Mono d spacing (Ang):'), (4, 3), (1, 1), labstyle, 2)
        sizer.Add(self.mono_dspacing ,            (4, 4), (1, 2), labstyle, 2)        

        sizer.Add(stext('Mono Steps / Degree:'),  (5, 3), (1, 1), labstyle, 2)
        sizer.Add(self.mono_steps ,               (5, 4), (1, 2), labstyle, 2)        
        self.mono_dspacing.DisableEntry()
        self.mono_steps.DisableEntry()

        
        pack(panel, sizer)
        
    def onImport(self, evt=None):
        print "Import Data to db!"
        
    def onEnergyChoice(self, evt=None):
        """ on selection of energy type """
        if 'angle' in evt.GetString().lower():
            self.mono_dspacing.EnableEntry()
        else:
            self.mono_dspacing.DisableEntry()

        if 'step' in evt.GetString().lower():
            self.mono_steps.EnableEntry()
        else:
            self.mono_steps.DisableEntry()
            
            
    def ShowFile(self, fname=None):
        if fname is not None:
            text = open(fname,'r').read()
            
            short_fname =os.path.basename(fname)
            self.name.SetValue(short_fname.replace('/', '_'))
            self.filename.SetLabel(fname)
            self.top_label.SetLabel('Data from File: %s' % (short_fname))
            self.fileview.Clear()
            self.fileview.SetValue(text)
            self.fileview.ShowPosition(0)
                        
        try:
            self.xdifile = XDIFile(fname)
            self.fill_from_xdifile(self.xdifile)
        except:
            print 'Not an XDI File'

    def fill_from_xdifile(self, xfile):
        "fill in form from XDIFile"
        edge = xfile.attrs['edge']
        elem = xfile.attrs['element']

        self.edge.Select(edge)
        self.elem.Select(elem)
        nrow, ncol =  xfile.rawdata.shape
        col_choices = ['%i' % (i+1) for i in range(ncol)]
        
        self.column_i0.SetChoices(col_choices)
        self.column_it.SetChoices(col_choices)
        self.column_if.SetChoices(col_choices)
        self.column_ir.SetChoices(col_choices)

        for key, val in xfile.columns.items():
            if val is not None:
                if key == 'energy':
                    self.column_en.Select(val)
                elif key == 'i0':
                    self.column_i0.Select(val)
                elif key.endswith('trans'):
                    self.column_it.Select(val)
                    self.type_it.Select('intensity')                    
                    if key.startswith('mu'):
                        self.type_it.Select('mu')
                elif key.endswith('refer'):
                    self.column_ir.Select(val)
                    self.type_ir.Select('intensity')                    
                    if key.startswith('mu'):
                        self.type_ir.Select('mu')
                elif key.endswith('fluor') or key.endswith('emit'):
                    self.column_if.Select(val)
                    self.type_if.Select('intensity')                    
                    if key.startswith('mu'):
                        self.type_if.Select('mu')                    

        # guess energy data 
        en = xfile.column_data['energy'][:2]
        enguess = self.energy_choices[0]
        if en[1] < en[0]:
            enguess =self.energy_choices[3]
            if en[1] > 90:
                enguess =self.energy_choices[4]
        elif en[1] < 200:
            enguess = self.energy_choices[1]
        self.type_en.Select(enguess)
    
        
    def onClose(self, evt=None):
        "quit frame"
        self.Destroy()
