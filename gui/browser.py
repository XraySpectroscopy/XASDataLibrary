#!/usr/bin/env python
"""GUI App for CARS Phonebook
"""
import os
import wx
import time
import copy
import cStringIO
import warnings
warnings.simplefilter('ignore')

import lib as xasdb
from lib import XASDataLibrary, isXASDataLibrary
from lib.wx import OrderedDict, pack, add_btn, add_menu, popup, \
     FileOpen, FileSave

import xdi

from SpectraPanel import SpectraPanel
from FileImporter import FileImporter

class MainFrame(wx.Frame):
    """This is the main XAS DataBrowser Frame."""
    title = 'XAS Data Library'
    filters = ('Suites of Spectra', 'Element',
               'Beamline', 'Facility', 'People')

    def __init__(self, dbfile=None):
        wx.Frame.__init__(self, parent=None, title=self.title,
                          size=(200, -1))
        self.xasdb = None

        self.current_filter = self.filters[0]
        self.create_frame()
        self.SetTitle("%s: %s" % (self.title, 'No Library Open'))
        self.ReadXDLFile(dbfile)
        
    def ReadXDLFile(self, dbname=None):            
        if dbname is not None and isXASDataLibrary(dbname):
            self.xasdb = XASDataLibrary(dbname)
            self.SetTitle("%s :%s " % (self.title,
                                       os.path.abspath(dbname)))
            for s in self.xasdb.query(xasdb.Spectra):
                print 'Spectra: ', s

    def onReadXDLFile(self, evt=None):
        "open an XDL file"
        wildcard = "XAS Data Libraries (*.xdl)|*.xdl|"  \
           "All files (*.*)|*.*"
        dbname = FileOpen(self, "Open XAS Data Library",
                          wildcard=wildcard)
        self.ReadXDLFile(dbname)

    def OpenNewXDLFile(self, evt=None):
        "create new XDL file"
        wildcard = "XAS Data Libraries (*.xdl)|*.xdl|"  \
           "All files (*.*)|*.*"
        dbname = FileSave(self, "Create New XAS Data Library",
                          wildcard=wildcard)
        if dbname is not None:
            self.xasdb = XASDataLibrary()
            if not dbname.endswith('.xdl'):
                dbname = dbname + '.xdl'
            self.xasdb.create_newdb(dbname, connect=True)
            if len(list(self.xasdb.query(xasdb.Person))) == 0:
                print 'No People yet defined!!'

    def onNewThing(self, evt=None):
        print 'this thing is not yet implemented!'
        
    def ImportSpectra(self, evt=None):
        "import spectra from ASCII Column file"
        wildcard = "XAS Data Interchange (*.xdi)|*.xdi|"  \
           "All files (*.*)|*.*"
        fname = FileOpen(self, "Import Spectra",
                          wildcard=wildcard)
        if fname is not None:
            FileImporter(fname)

    def ExportSpectra(self, evt=None):
        "export spectra to  XDI ASCII file"
        wildcard = "XAS Data Interchange (*.xdi)|*.xdi|"  \
           "All files (*.*)|*.*"
        fname = FileSave(self, "Export Current Spectra",
                         wildcard=wildcard)
        if fname is not None:
            print 'Export to ', fname

    def query (self, *args, **kws):
        "wrapper for query"
        return self.xasdb.session.query(*args, **kws)

    def get_people(self):
        "make self.people  name: id "
        self.people = OrderedDict()
        self.people["<Add New Person>"] = None
        for row in self.xasdb.query(xasdb.Person):
            name = "%s %s" % (row.firstname, row.lastname)
            self.people[name] = row.id

    def get_suites(self):
        "make self.suites  name: id "
        self.suites = OrderedDict()
        self.suites["<Add New Suite>"] = None
        for row in self.xasdb.query(xasdb.Suite):
            self.suites[row.name] = row.id

    def get_spectra(self):
        "make self.spectra  name: id "
        self.spectra = OrderedDict()
        self.spectra["<Add New Spectra>"] = None
        for row in self.xasdb.query(xasdb.Spectra):
            self.spectra[row.name] = row.id
        

    def create_frame(self):
        "create top level frame"
        # Create the menubar
        menuBar = wx.MenuBar()
        fmenu = wx.Menu()
        add_menu(self, fmenu, "Open Library",
                      "Open Existing XAS Data Library",
                      action = self.onReadXDLFile)

        add_menu(self, fmenu, "New Library",
                      "Create New XAS Data Library",
                      action=self.OpenNewXDLFile)

        fmenu.AppendSeparator()
        add_menu(self, fmenu, "Import Spectra",
                      "Read Spectra from ASCII File",
                      action=self.ImportSpectra)
        add_menu(self, fmenu, "Export Spectra",
                      "Write Spectra to ASCII (XDI) File",
                      action=self.ExportSpectra)        
        fmenu.AppendSeparator()
        add_menu(self, fmenu, "E&xit\tAlt-X", "Exit this Program",
                      action=self.onClose)

        omenu = wx.Menu()
        add_menu(self, omenu, "View/Add Suites of Spectra",
                 "Manage Suites of Spectra",
                 action=self.onNewThing)
        add_menu(self, omenu, "View/Add Samples",
                 "Manage Samples",
                 action=self.onNewThing)        
        add_menu(self, omenu, "View/Add People",
                 "Manage People Adding to Library",
                 action=self.onNewThing)
        add_menu(self, omenu, "View/Add Beamlines",
                 "Manage Beamline, Facilities, Monochromators",
                 action=self.onNewThing)        

        # and put the menu on the menubar
        menuBar.Append(fmenu, "&File")
        menuBar.Append(omenu, "&Tables")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar(1, wx.CAPTION|wx.THICK_FRAME)
        
        # Now create the Main Panel to put the other controls on.
        #  SelectFilter | CurrentFilter | SpectraList
        #  ------------------------------------------
        #    Spectra details
        #  ------------------------------------------
        topsection = wx.Panel(self)
        self.filterchoice = wx.Choice(topsection, size=(-1,-1),
                                     choices = self.filters)
        self.filterchoice.SetStringSelection(self.current_filter)
        self.filterchoice.Bind(wx.EVT_CHOICE, self.onFilterChoice)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(topsection,
                                label='Filter Spectra by:'),
                  0, wx.ALIGN_LEFT|wx.ALIGN_CENTER|wx.ALL, 1)
        sizer.Add(self.filterchoice, 0, wx.ALIGN_LEFT|wx.ALL, 1)

        pack(topsection, sizer)
        
        splitter1  = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter1.SetMinimumPaneSize(200)

        self.top_panel = wx.Panel(splitter1)  # top
        self.bot_panel = SpectraPanel(splitter1)  # bottom

        splitter2 = wx.SplitterWindow(self.top_panel, style=wx.SP_LIVE_UPDATE)
        splitter2.SetMinimumPaneSize(200)
        
        # left hand side -- filter
        self.left_panel   = wx.Panel(splitter2)
        self.selection_list  = wx.ListBox(self.left_panel)
        self.selection_label = wx.StaticText(self.left_panel,
                                             label=self.current_filter)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.selection_label, 0, wx.ALIGN_LEFT|wx.ALL, 1)
        sizer.Add(self.selection_list, 1, wx.ALIGN_LEFT|wx.GROW|wx.ALL, 1)

        pack(self.left_panel, sizer)

        # right hand side -- filtered spectra
        self.right_panel   = wx.Panel(splitter2)
        self.spectra_list  = wx.ListBox(self.right_panel)
        self.spectra_label = wx.StaticText(self.right_panel,
                                             label='Spectra')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.spectra_label, 0, wx.ALIGN_LEFT|wx.ALL, 1)
        sizer.Add(self.spectra_list, 1, wx.ALIGN_LEFT|wx.GROW|wx.ALL, 1)

        pack(self.right_panel, sizer)

        self.selection_list.SetBackgroundColour(wx.Colour(255, 240, 250))
        self.spectra_list.SetBackgroundColour(wx.Colour(250, 250, 240))

        self.selection_list.Clear()
        for name in ('Suite1', 'Suite2'):
            self.selection_list.Append(name)

        self.spectra_list.Clear()
        for name in ('S1', 'S2'):
            self.spectra_list.Append(name)

        self.selection_list.Bind(wx.EVT_LISTBOX, self.onSelectionSelect)
        self.spectra_list.Bind(wx.EVT_LISTBOX, self.onSpectraSelect)
        
        splitter2.SplitVertically(self.left_panel, self.right_panel, 0)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(splitter2, 1, wx.GROW|wx.ALL, 5)
        pack(self.top_panel, sizer2)
        

        splitter1.SplitHorizontally(self.top_panel, self.bot_panel, 1)
       
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topsection, 0, wx.ALL, 5)
        sizer.Add(splitter1, 1, wx.GROW|wx.ALL, 5)
        pack(self, sizer)


    def onFilterChoice(self, evt=None, choice=None):
        if evt is not None:
            choice = evt.GetString()
        if choice is None:
            return

        self.selection_label.SetLabel(choice)
        if choice == 'People':
            sel_list = ["%s %s" % (e.firstname, e.lastname) for e in self.xasdb.query(xasdb.Person)]
        else:
            if choice == 'Element':
                thisclass = xasdb.Element
            elif choice == 'Beamline':
                thisclass = xasdb.Beamline
            elif choice == 'Facility':
                thisclass = xasdb.Facility
            elif choice == 'Suites of Spectra':
                thisclass = xasdb.Suite
            sel_list = [e.name for e in self.xasdb.query(thisclass)]
        self.current_filter = choice
        self.selection_list.Clear()
        for name in sel_list:
            self.selection_list.Append(name)
        
    def onSelectionSelect(self, evt=None):
        print 'onSelection Select %s=%s'  % (self.current_filter, evt.GetString())
        

    def onSpectraSelect(self, evt=None):
        print 'onSpectra Select ' , evt.GetString()
        
    def build_spectra_panel(self):
        "build lower panel"

        labstyle = wx.ALIGN_LEFT#|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.GROW
        panel = self.bot_panel
        self.xabel  = wx.StaticText(panel, label='Spectra:')
        #self.element   = wx.StaticText(toprow, label='Element:')
        #self.edge      = wx.StaticText(toprow, label='Edge: ')

        tsizer =  wx.BoxSizer(wx.HORIZONTAL) 
        tsizer.Add(self.xabel, 1, labstyle, 3)
        # tsizer.Add(self.element,  0, labstyle, 3)
        #tsizer.Add(self.edge,     0, labstyle, 3)
        
        pack(panel, tsizer)

#         nb = self.notebook = wx.Notebook(panel)
#  
#         self.data_panel  = wx.Panel(nb)
#         nb.AddPage(self.data_panel, 'Data')
# 
#         self.sample_panel  = wx.Panel(nb)
#         nb.AddPage(self.sample_panel, 'Sample')
# 
#         self.beamline_panel  = wx.Panel(nb)
#         nb.AddPage(self.beamline_panel, 'Beamline/Mono')
# 
#         self.info_panel  = wx.Panel(nb)
#         nb.AddPage(self.info_panel, 'Info')
#        
        sizer =  wx.BoxSizer(wx.VERTICAL) 
        sizer.Add(tsizer, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP, 5)
        #sizer.Add(nb, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW, 5)
        pack(panel, sizer)
    
#         
#         self.spectra_label  = wx.StaticText(panel, label='Spectra:')
#         nb = self.notebook = wx.Notebook(panel)
# 
#         self.sample_panel  = wx.Panel(nb)
#         nb.AddPage(self.sample_panel, 'Sample')
# 
#         self.info_panel  = wx.Panel(nb)
#         nb.AddPage(self.info_panel, 'Info')
# 
#         
#         sizer =  wx.BoxSizer(wx.VERTICAL) 
#         sizer.Add(self.spectra_label, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP, 5)
#         sizer.Add(self.notebook, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW, 5)
#         pack(panel, sizer)
# 
#         self.sample_panel  = wx.Panel(panel)
#         # nb.AddPage(self.sample_panel, 'Sample')
    def onClose(self, evt=None):
        "quit application"
        ret = popup(self, "Really Quit?", "Exit XAS Data Library?",
                    style=wx.YES_NO|wx.ICON_QUESTION)
        if ret == wx.ID_YES:
            self.xasdb.close()
            self.Destroy()

    def onSave(self, evt):
        "save data on form to database"
        fname, lname, email = (get(self.first_name),
                               get(self.last_name),
                               get(self.email))

        if self.current_id is None:
            if fname == '' or lname == '' or email == '':
                popup(self, """New entry must have
    email, first name, and last name""",
                           'Incomplete Address entry')
                return
            # check if email is alresdy in use
            q_email = "select * from person where email='%s'" % get(self.email)
            row = self.query(q_email)
            try:
                if row[0]['id'] is not None:
                    popup(self, "Email '%s' is already in use!" % email,
                          'Invalid Address entry')
                    return
            except:
                pass
            
            q = """insert into person(first_name,middle_name,last_name,email)
            values('%s','%s','%s','%s')"""
            self.query(q % (fname, get(self.middle_name), lname, email))
            time.sleep(0.25)
            self.set_person_list(make_list=True)

            row = self.query(q_email)
            self.current_id = row[0]['id']
            self.current_name = "%s %s" % (row[0]['first_name'],
                                          row[0]['last_name'])

            
        base_q = "update person set %%s where last_name='%s' and first_name='%s'" % (lname, fname)
        for attr in (self.simple_attr + self.multiline_attr):
            # print base_q % ("%s='%s'" %(attr, get(getattr(self, attr))))
            self.query(base_q % ("%s='%s'" %(attr, get(getattr(self, attr)))))

        affil_name = self.affil.GetStringSelection()
        affil_index = 0
        for a_idx, a_name in self.affil_dict.items():
            if a_name == affil_name:
                affil_index = a_idx
            
        self.query(base_q % ("status='%s'" %
                             (self.status.GetStringSelection())))
        self.query(base_q % ("affiliation=%i" % affil_index))
        img_encoded = base64.b64encode(self.raw_image)
        if len(img_encoded) > MAX_IMAGE_SIZE:
            popup(self, "Image is too large.\n Use one smaller than 2 Mb",
                  "Image too big to save")
            return
        self.query(base_q % ("picture='%s'" % img_encoded))
        self.query(base_q % ("new_picture=1"))

        if self.current_id is None:
            row = self.query(q_email)
            self.current_id = row[0]['id']
            
        self.query("delete from person_sector where user_id='%i'" %
                   (self.current_id))
        q = "insert into person_sector(user_id, sector_id) values(%i, %i)"
        for k, cb in self.sector_cb.items():
            if cb.GetValue():
                self.query(q % (self.current_id, k))
        self.SetStatusText("Saved data for %s" % self.current_name)
            

        
if __name__ == '__main__':
    import sys
    dbfile = None
    if len(sys.argv) > 1:
        dbfile = sys.argv[1]
    app = wx.PySimpleApp()        
    MainFrame(dbfile=dbfile).Show()
    app.MainLoop()
