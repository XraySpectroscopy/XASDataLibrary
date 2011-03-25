import os
import wx

import wx.lib.agw.pycollapsiblepane as CP

from xasdb import XDIFile

from utils import pack, add_btn, add_menu, popup, FileOpen, FileSave, FloatCtrl

from choices import ElementChoice, EdgeChoice, ColumnChoice, TypeChoice, \
     PersonChoice, BeamlineChoice, MonochromatorChoice, DateTimeCtrl

titlestyle  = wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.GROW
labstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
rlabstyle   = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
choicestyle = wx.ALIGN_LEFT|wx.ALL
namestyle   = wx.ALIGN_LEFT|wx.ALL                
btnstyle    = wx.ALIGN_CENTER|wx.ALL                

def Title(parent, text, colour=(50, 50, 180)):
    title = wx.StaticText(parent, label=text)
    title.SetFont(title.GetFont().Larger().Bold())
    title.SetForegroundColour(colour)
    return title

class HyperText(wx.StaticText):
    def  __init__(self, parent, label, action=None, colour=(50, 50, 180)):
        self.action = action
        wx.StaticText.__init__(self, parent, -1, label=label)
        font  = self.GetFont().Larger().Bold()
        font.SetUnderlined(True)
        self.SetFont(font)
        self.SetForegroundColour(colour)
        self.Bind(wx.EVT_LEFT_UP, self.onSelect)

    def onSelect(self, evt=None):
        if self.action is not None:
            self.action(evt=evt)
        evt.Skip()
        
class FileImporter(wx.Frame):
    title = 'ASCII File Importer'
    energy_choices = ('energy (eV)', 'energy (keV)',
                      'angle (degrees)', 'angle steps')

    def __init__(self, fname=None, db=None):
        wx.Frame.__init__(self, parent=None,
                          title=self.title, size=(675, 650))
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
        splitter.SetMinimumPaneSize(175)
        
        self.top_panel = wx.Panel(splitter) # top
        self.bot_panel = wx.Panel(splitter) # bottom
        self.filename  = wx.StaticText(self.bot_panel, -1, label='')
        self.fileview  = wx.TextCtrl(self.bot_panel, size=(150, 175),
                                     style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)

        self.fileview.SetBackgroundColour(wx.Colour(250, 250, 250))

        bot_sizer = wx.BoxSizer(wx.VERTICAL)
        bot_sizer.Add(self.filename, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        bot_sizer.Add(self.fileview, 1, wx.ALIGN_TOP|wx.GROW|wx.ALL, 5)
        pack(self.bot_panel, bot_sizer)
        
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        title_row   = wx.Panel(self.top_panel)
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.top_label = Title(title_row, 'Data from File:', colour=(200,20,20))
        self.save_btn = add_btn(title_row, "Import Data",  action=self.onImport)

        title_sizer.Add(self.top_label, 1, wx.ALIGN_LEFT|wx.ALL, 3)
        title_sizer.Add(self.save_btn,  0, wx.ALIGN_RIGHT|wx.GROW|wx.ALL, 3)

        pack(title_row, title_sizer)
        
        self.nb = wx.Notebook(self.top_panel, size=(600, 300))

        self.buildDataPanel()
        self.buildBeamlinePanel()
        self.buildSamplePanel()
        self.buildReferenceSamplePanel()
        self.buildCitationPanel()

        top_sizer.Add(title_row, 0, wx.ALIGN_LEFT|wx.GROW|wx.ALL, 1)
        top_sizer.Add(self.nb,   1, wx.ALIGN_CENTER|wx.GROW|wx.ALL, 1)

        
        pack(self.top_panel, top_sizer)
        splitter.SplitHorizontally(self.top_panel, self.bot_panel, -1)
        
        framesizer = wx.BoxSizer(wx.VERTICAL)
        framesizer.Add(splitter, 1, wx.GROW|wx.ALL, 5)
        pack(self, framesizer)
        if fname is not None:
            self.ShowFile(fname)
        self.Show()
        self.Raise()

    def buildBeamlinePanel(self):
        "build Beamline info panel"
        # beamline
        # facility
        # monochromator
        # energy units
        panel = self.beamline_panel  = wx.Panel(self.nb)
        self.nb.AddPage(panel, 'Beamline')

        sizer = wx.GridBagSizer(10, 6)

        def stext(label):
            return wx.StaticText(panel, label=label)

        self.person = PersonChoice(panel, db=self.db, show_all=True)
        self.beamline = BeamlineChoice(panel, db=self.db, show_all=True)
        self.monochromator = MonochromatorChoice(panel, db=self.db, show_all=True)

        self.add_person   = HyperText(panel, 'Person:',   action=self.onAddPerson)
        self.add_beamline = HyperText(panel, 'Beamline:', action=self.onAddBeamline)
        self.add_mono     = HyperText(panel, 'Monochromator:', action=self.onAddMono)

        self.collection_datetime = DateTimeCtrl(panel, name="collection_time")
        self.submission_datetime = DateTimeCtrl(panel, name="collection_time", use_now=True)

        sizer.Add(Title(panel, 'Beamline Information:'),  (0, 0), (1, 3), titlestyle, 1)

        irow = 1

        sizer.Add(self.add_person,  (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.person,       (irow, 1), (1, 1), namestyle, 1)


        irow += 1
        sizer.Add(stext('Collection Date:'), (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.collection_datetime,  (irow, 1), (1, 1), namestyle, 1)

        irow += 1
        sizer.Add(stext('Submission Date:'), (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.submission_datetime,  (irow, 1), (1, 1), namestyle, 1)


        irow += 1
        sizer.Add(self.add_beamline,          (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.beamline,              (irow, 1), (1, 1), namestyle, 1)

        irow += 1
        sizer.Add(self.add_mono,               (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.monochromator,          (irow, 1), (1, 1), namestyle, 1)


        ## RHS of Beamline Panel
        sizer.Add(wx.StaticLine(panel, size=(1, 160), style=wx.LI_VERTICAL),
                  (1, 2), (6, 1), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        irow = 1
        self.ring_current = FloatCtrl(panel, precision=2, value=0, min=0, max=1e6)
        self.ring_energy  = FloatCtrl(panel, precision=3, value=0, min=0, max=1e3)        
        self.collimation  = wx.TextCtrl(panel, value='', size=(180, -1))
        self.focussing    = wx.TextCtrl(panel, value='', size=(180, -1))
        self.xray_source  = wx.TextCtrl(panel, value='', size=(180, -1))
        self.harmonic_rej = wx.TextCtrl(panel, value='', size=(180, -1))

        sizer.Add(stext('Ring Current:'), (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.ring_current,      (irow, 5), (1, 1), namestyle, 1)
        sizer.Add(stext('mA'),            (irow, 6), (1, 1), labstyle, 1)

        irow += 1
        sizer.Add(stext('Ring Energy:'),  (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.ring_energy,       (irow, 5), (1, 1), namestyle, 1)
        sizer.Add(stext('GeV'),           (irow, 6), (1, 1), labstyle, 1)

        irow += 1
        sizer.Add(stext('X-ray Source:'),  (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.xray_source,        (irow, 5), (1, 2), namestyle, 1)
        irow += 1
        sizer.Add(stext('focussing:'),    (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.focussing,         (irow, 5), (1, 2), namestyle, 1)

        irow += 1
        sizer.Add(stext('collimation:'),   (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.collimation,        (irow, 5), (1, 2), namestyle, 1)

        irow += 1
        sizer.Add(stext('harmonic rejection:'), (irow, 4), (1, 1), labstyle, 1)
        sizer.Add(self.harmonic_rej,            (irow, 5), (1, 2), namestyle, 1)

        

        
        pack(panel, sizer)
        
    def buildCitationPanel(self):
        "build Reference Sample panel"
        panel = self.refer_panel = wx.Panel(self.nb)
        self.nb.AddPage(panel, 'Citation')

        sizer = wx.GridBagSizer(10, 6)

        def stext(label):
            return wx.StaticText(panel, label=label)

        sizer.Add(Title(panel, 'Literature Citation:'),
                  (0, 0), (1, 3), titlestyle, 1)


        irow = 1

        pack(panel, sizer)
        
    def buildReferenceSamplePanel(self):
        "build Reference Sample panel"
        panel = self.refer_panel = wx.Panel(self.nb)
        self.nb.AddPage(panel, 'Reference Sample')

        sizer = wx.GridBagSizer(10, 6)

        def stext(label):
            return wx.StaticText(panel, label=label)

        self.refer_formula  = wx.TextCtrl(panel, value='', size=(180, -1))
        self.refer_xtal    = add_btn(panel, "Add Reference Crystal Structure Data",
                                      action=self.onReferXTAL)
        self.refer_source  = wx.TextCtrl(panel, value='', size=(210, 75),
                                         style=wx.TE_MULTILINE)

        sizer.Add(Title(panel, 'Information for Reference Sample:'),
                  (0, 0), (1, 3), titlestyle, 1)


        irow = 1

        sizer.Add(stext('Chemical Formula:'),  (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.refer_formula,        (irow, 1), (1, 1), namestyle, 1)
        sizer.Add(self.refer_xtal,         (irow+1, 1), (1, 2), namestyle, 1)        
        sizer.Add(stext('Source:'),          (irow, 2), (1, 1), labstyle, 1)
        sizer.Add(self.refer_source,         (irow, 3), (2, 1), namestyle, 1)

        pack(panel, sizer)
        

    def buildSamplePanel(self):
        "build Sample  panel"
        # temperature
        # citation

        # sample crystal structure data, format
        # ref sample formula
        # ref sample material source
        # ref sample crystal structure data, format
        panel = self.sample_panel = wx.Panel(self.nb)
        self.nb.AddPage(panel, 'Sample')

        sizer = wx.GridBagSizer(10, 6)

        def stext(label):
            return wx.StaticText(panel, label=label)
        
        tpanel = wx.Panel(panel)
        tsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample_temperature  = FloatCtrl(tpanel, precision=3, size=(100, -1),
                                             value=300, min=-500)
        
        self.temperature_units = TypeChoice(tpanel, choices=('K','C','F'), size=(50, -1))
        self.temperature_units.SetSelection(0)

        tsizer.Add(self.sample_temperature, 0, wx.ALIGN_CENTER|wx.ALL, 1)
        tsizer.Add(self.temperature_units,  0, wx.ALIGN_CENTER|wx.ALL, 1)
        pack(tpanel, tsizer)
                
        self.sample_formula = wx.TextCtrl(panel, value='', size=(180, -1))

        self.sample_xtal    = add_btn(panel, "Add Crystal Structure Data",
                                      action=self.onSampleXTAL)
        self.sample_source = wx.TextCtrl(panel, value='', size=(210, 75),
                                         style=wx.TE_MULTILINE)

        sizer.Add(Title(panel, 'Sample Information:'),  (0, 0), (1, 3), titlestyle, 1)

        irow = 1 
        sizer.Add(stext('Chemical Formula:'),  (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(self.sample_formula,       (irow, 1), (1, 1), namestyle, 1)
        sizer.Add(self.sample_xtal,        (irow+1, 1), (1, 2), namestyle, 1)        
        sizer.Add(stext('Source:'),          (irow, 2), (1, 1), labstyle, 1)
        sizer.Add(self.sample_source,        (irow, 3), (2, 1), namestyle, 1)
        
        irow += 2
        sizer.Add(stext('Temperature:'),  (irow, 0), (1, 1), labstyle, 1)
        sizer.Add(tpanel,                 (irow, 1), (1, 2), namestyle, 1)

        irow += 1
        sizer.Add(wx.StaticLine(panel, size=(150, 1), style=wx.LI_HORIZONTAL),
                  (irow, 0), (1, 5), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)
        

        pack(panel, sizer)


    def onAddPerson(self, evt=None):
        print 'Add person ', dir(evt)

    def onAddBeamline(self, evt=None):
        print 'Add beamline ', dir(evt)

    def onAddMono(self, evt=None):
        print 'Add monochromator ', dir(evt)

    def onSampleXTAL(self, evt=None):
        print 'Add Sample XTAL ', evt

    def onReferXTAL(self, evt=None):
        print 'Add Refer XTAL ', evt
        
    def buildDataPanel(self):
        "build Data / Column selection panel"
        
        panel = self.columns_panel = wx.Panel(self.nb)
        self.nb.AddPage(panel, 'Data')
        
        sizer = wx.GridBagSizer(10, 6)

        def stext(label):
            return wx.StaticText(panel, label=label)

        self.elem    = ElementChoice(panel, db=self.db, show_all=True)
        self.edge    = EdgeChoice(panel, db=self.db, show_all=True)
        self.name    = wx.TextCtrl(panel, value='', size=(200,-1))
        self.name_ok = stext('')
        

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


        sizer.Add(Title(panel, 'Data Columns:'), (0, 0), (1, 3), titlestyle, 1)
        
        sizer.Add(stext('Spectra Name:'), (1, 0), (1, 1), labstyle, 1)
        sizer.Add(self.name,              (1, 1), (1, 2), namestyle, 1)
        sizer.Add(self.name_ok,           (1, 3), (1, 1), labstyle, 1)
        #sizer.Add(self.save_btn,          (1, 4), (1, 2), btnstyle, 1)

        
        sizer.Add(stext('Element:'), (2, 0), (1, 1), labstyle, 1)
        sizer.Add(self.elem,         (2, 1), (1, 1), choicestyle, 1)        
        sizer.Add(stext('Edge:'),    (2, 2), (1, 1), rlabstyle, 1)
        sizer.Add(self.edge,         (2, 3), (1, 1), choicestyle, 1)

        sizer.Add(wx.StaticLine(panel, size=(350, 2), style=wx.LI_HORIZONTAL),
                  (3, 0), (1, 6), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        sizer.Add(stext('Data:'),        (4, 0), (1, 1), labstyle, 1)
        sizer.Add(stext(' Type:'),       (4, 1), (1, 1), labstyle, 1)
        sizer.Add(stext('Column #:'),    (4, 2), (1, 1), labstyle, 1)
        
        sizer.Add(stext('Energy:'),      (5, 0), (1, 1), labstyle, 1)
        sizer.Add(stext('I0:'),          (6, 0), (1, 1), labstyle, 1)
        sizer.Add(stext('Transmission:'),(7, 0), (1, 1), labstyle, 1)
        sizer.Add(stext('Fluorescence:'),(8, 0), (1, 1), labstyle, 1)
        sizer.Add(stext('Reference:'),   (9, 0), (1, 1), labstyle, 1)

        sizer.Add(self.type_en,          (5, 1), (1, 1), choicestyle, 1)
        sizer.Add(self.type_i0,          (6, 1), (1, 1), choicestyle, 1)
        sizer.Add(self.type_it,          (7, 1), (1, 1), choicestyle, 1)
        sizer.Add(self.type_if,          (8, 1), (1, 1), choicestyle, 1)
        sizer.Add(self.type_ir,          (9, 1), (1, 1), choicestyle, 1)

        sizer.Add(self.column_en,        (5, 2), (1, 1), choicestyle, 1)
        sizer.Add(self.column_i0,        (6, 2), (1, 1), choicestyle, 1)
        sizer.Add(self.column_it,        (7, 2), (1, 1), choicestyle, 1)
        sizer.Add(self.column_if,        (8, 2), (1, 1), choicestyle, 1)
        sizer.Add(self.column_ir,        (9, 2), (1, 1), choicestyle, 1)

        sizer.Add(stext('Mono d spacing (Ang):'), (5, 3), (1, 1), labstyle, 1)
        sizer.Add(self.mono_dspacing ,            (5, 4), (1, 2), labstyle, 1)        

        sizer.Add(stext('Mono Steps / Degree:'),  (6, 3), (1, 1), labstyle, 1)
        sizer.Add(self.mono_steps ,               (6, 4), (1, 2), labstyle, 1)        
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
                        
        if True:
            self.xdifile = XDIFile(fname)
            self.fill_from_xdifile(self.xdifile)
        else:
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
