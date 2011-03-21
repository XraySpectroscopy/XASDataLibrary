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
            print 'Import from ', fname

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

        self.top_panel     = wx.Panel(splitter1)  # top
        self.spectra_panel = wx.Panel(splitter1)  # bottom

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

        self.build_spectra_panel()
        splitter1.SplitHorizontally(self.top_panel, self.spectra_panel, 1)
        
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
        print 'onSpectra Select ' , evt
        
    def build_spectra_panel(self):
        "build lower panel"
        panel = self.spectra_panel
        sizer =  wx.BoxSizer(wx.HORIZONTAL) # wx.GridBagSizer(5, 5)
        toplabel    = wx.StaticText(panel, label='Spectra Panel')
        sizer.Add(toplabel, 1, wx.GROW, 5)
        pack(panel, sizer)

    def build_filter_panel(self):
        "build lower panel"
        panel = self.filter
        sizer =  wx.BoxSizer(wx.HORIZONTAL) # wx.GridBagSizer(5, 5)
        toplabel    = wx.StaticText(panel, label='Spectra Panel')
        sizer.Add(toplabel, 1, wx.GROW, 5)
        pack(panel, sizer)

    def x(self):
        self.status = wx.Choice(self.rightpanel, -1, (180, 60),
                                choices=self.status_choices)
        self.affil = wx.Choice(panel, -1, (300, -1),
                               choices=list(self.affil_choices))

        for attr in self.simple_attr:
            setattr(self, attr, wx.TextCtrl(panel, value="", size=(225, 25)))

        mline_style = wx.TE_MULTILINE|wx.TE_PROCESS_ENTER
        for attr in self.multiline_attr:
            setattr(self, attr, wx.TextCtrl(panel, value="", size=(225, 75),
                                            style=mline_style))

        self.img = wx.StaticBitmap(panel, -1, wx.EmptyBitmap(144, 164))

        sizer.Add(self.toplabel, (0, 0), (1, 5), wx.ALIGN_CENTRE|wx.ALL, 2)
        sizer.Add(wx.StaticText(panel, label='Status:'), (1, 0), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)
        
        srow = wx.BoxSizer(wx.HORIZONTAL)
        srow.Add(self.status, 0, wx.ALL, 4)

        srow.Add(wx.StaticText(panel, label='  Affiliation:'), 0, wx.ALL, 4)
        srow.Add(self.affil, 0, wx.ALL, 4)        
        sizer.Add(srow, (1, 1), (1, 5), wx.ALIGN_LEFT|wx.ALL, 2)

        self.sector_cb = {}
        cbrow = wx.BoxSizer(wx.HORIZONTAL)
        for sid, sname  in self.sector_choices:
            self.sector_cb[sid] = wx.CheckBox(panel, -1, sname,
                                              style=wx.RB_GROUP)
            cbrow.Add(self.sector_cb[sid], 0, wx.ALL, 4)
            
        sizer.Add(wx.StaticText(panel, label='Groups:'), (2, 0), (1, 1),
                  wx.ALIGN_LEFT|wx.ALL, 2)
        sizer.Add(cbrow, (2, 1), (1, 5), wx.ALIGN_LEFT|wx.ALL, 2)

        def add_col(label, control, row=1, col=1):
            "add a label/control pair to columns on this page"
            sizer.Add(wx.StaticText(panel, label=label),
                      (row, col), (1, 1), wx.ALIGN_LEFT|wx.ALL, 2)
            sizer.Add(control, (row, col+1), (1, 1), wx.ALIGN_LEFT|wx.ALL, 2)
            
        add_col("First Name:",   self.first_name,  row=3, col=0)
        add_col("Middle Name:",  self.middle_name, row=4, col=0)
        add_col("Last Name:",    self.last_name,   row=5, col=0)
        add_col("Email:",        self.email,       row=6, col=0)
        add_col("Title:",        self.title,       row=7, col=0)
        add_col("ANL Badge:",    self.anl_badge,   row=8, col=0)
        add_col("Work Address:", self.address,     row=9, col=0)
        
        add_col("ANL Phone:",    self.anl_phone,   row=3, col=2)
        add_col("UofC Phone:",   self.uofc_phone,  row=4, col=2)
        add_col("Home Phone:",   self.home_phone,  row=5, col=2)
        add_col("Cell Phone:",   self.cell_phone,  row=6, col=2)
        add_col("Fax:",          self.fax,         row=7, col=2)
        add_col("CNET Id:",      self.cnetid,      row=8, col=2)
        add_col("Home Address:", self.home_address, row=9, col=2)        
        add_col("Employment\nDates:",   self.start_date,  row=10, col=0)

        sizer.Add(wx.StaticText(panel,
                                label='\nEmergency Contact Information:'),
                  (11, 0), (1, 2),  wx.ALIGN_LEFT|wx.ALL, 2)
        add_col("Contact Name:",  self.emergency_contact, row=12, col=0)
        add_col("Contact Phone:", self.emergency_contact_phone, row=13, col=0)

        sizer.Add(self.img, (10, 3),(4, 2), wx.ALIGN_CENTER|wx.TOP|wx.ALL, 2)


        btn_save   = add_btn(panel, "Save Changes",  action=self.onSave)
        btn_remove = add_btn(panel, "Remove Person", action=self.onRemove)
        btn_pict   = add_btn(panel, "Change Picture", action=self.onPicture)
        btn_delpict = add_btn(panel, "Delete Picture", action=self.onDelPicture)

        brow = wx.BoxSizer(wx.HORIZONTAL)
        brow.Add(btn_save,   0, wx.ALIGN_LEFT|wx.ALL, 10)
        brow.Add(btn_remove, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        
        sizer.Add(brow,     (15, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL, 4)
        sizer.Add(btn_delpict, (15, 2), (1, 1), wx.ALIGN_CENTER|wx.ALL, 2)
        sizer.Add(btn_pict, (15, 3), (1, 1), wx.ALIGN_CENTER|wx.ALL, 2)

        pack(panel, sizer)
        self.ShowPerson()
        
    def ShowPerson(self, evt=None, pid=None):
        "fill in form from data for this person"
        if evt is not None:
            sel = str(self.itemlist.GetStringSelection())
            pid = self.people.get(sel, None)
            
        row = dict(id=None, affiliation=0,  status=None, picture='')
        for attr in (self.simple_attr + self.multiline_attr):
            row[attr] = ''
        
        if pid is not None:
            row = self.query("select * from person where id=%i" % int(pid))[0]

        if row.get('status', None) is None:
            row['status'] = self.status_choices[0]

        for attr in (self.simple_attr + self.multiline_attr):
            put(getattr(self, attr), row[attr])

        self.status.SetStringSelection(row['status'])
        try:
            affil_name = self.affil_dict[row['affiliation']]
        except:
            affil_name = self.affil_choices[0]
        self.affil.SetStringSelection(affil_name)
        self.current_name = "%s %s" % (row['first_name'], row['last_name'])
        self.current_id   = row['id']
        self.current_data = row
        
        for cb in self.sector_cb.values():
            cb.SetValue(False)

        label = "Add New Person to Phone Book"
        q_sector = 'select * from person_sector where user_id=%i'
        if self.current_id is not None:
            label = "Edit Information for %s" % self.current_name
            for sect in self.query(q_sector % self.current_id):
                self.sector_cb[sect['sector_id']].SetValue(True)

        self.toplabel.SetLabel(label)
        self.raw_image = DEFAULT_IMAGE

    def set_person_list(self, make_list=False, active=True, inactive=True):
        "set the list of people on the left-side panel"
        if make_list:
            self.get_people(active=active, inactive=inactive)
        self.itemlist.Clear()
        for name in self.people:
            self.itemlist.Append(name)

        # this tweaking of the splitter sash seems to be needed to 
        # keep sash and scrollbar visible when the list is repopulated
        sash = max(165, self.itemlist.GetParent().GetSashPosition())
        idx = len(self.people)
        self.itemlist.GetParent().SetSashPosition(sash + (-1 + 2*(idx%2)))
       
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
