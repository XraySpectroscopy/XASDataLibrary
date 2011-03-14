#!/usr/bin/env python
"""GUI App for CARS Phonebook
"""
import wx
import time
import copy
import cStringIO
import warnings
warnings.simplefilter('ignore')

import xasdb
from xasdb import XASDataLibrary, isXASDataLibrary
from xasdb.wx import OrderedDict, pack, add_btn, add_menu, popup, \
     FileOpen, FileSave

class MainFrame(wx.Frame):
    """This is the main XAS DataBrowser Frame."""
    def __init__(self, title='XAS Data Library', dbfile=None):
        
        wx.Frame.__init__(self, None, -1, title, size=(500, 700))
        self.xasdb = None
        self.create_frame()
        #if dbfile is None:
        #    self.ReadXDLFile()
            
    def ReadXDLFile(self, evt=None):
        "open an XDL file"
        wildcard = "XAS Data Libraries (*.xdl)|*.xdl|"  \
           "All files (*.*)|*.*"
        dbname = FileOpen(self, "Open XAS Data Library",
                          wildcard=wildcard)
        if dbname is not None and isXASDataLibrary(dbname):
            self.xasdb = XASDataLibrary(dbname)
            
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
                      action = self.ReadXDLFile)
        
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
        #omenu.Append(4910, "Show All", "Show All People", 
#                      wx.ITEM_RADIO)
#         omenu.Append(4911, "Show Active Only",
#                      "Show Active People Only", wx.ITEM_RADIO)
#         omenu.Append(4912, "Show Inactive Only",
#                      "Show Inactive People Only",  wx.ITEM_RADIO)
#         self.Bind(wx.EVT_MENU, self.onChooseActive, id=4910)        
#         self.Bind(wx.EVT_MENU, self.onChooseActive, id=4911)        
#         self.Bind(wx.EVT_MENU, self.onChooseActive, id=4912)
#         
#         omenu.AppendSeparator()
#         omenu.Append(4913, "Manage Affiliations",
#                      "Change and Add Affliations",  wx.ITEM_NORMAL)
#         self.Bind(wx.EVT_MENU, self.onAffiliation, id=4913)        
        
        # and put the menu on the menubar
        menuBar.Append(fmenu, "&File")
        # menuBar.Append(tmenu, "&Tables")
        menuBar.Append(omenu, "&Options")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar(2, wx.CAPTION|wx.THICK_FRAME)
        
        # Now create the Panel to put the other controls on.
        splitter  = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(165)

        self.itemlist  = wx.ListBox(splitter) 
        self.itemlist.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.itemlist.Bind(wx.EVT_LISTBOX, self.ShowPerson)
        
        self.rightpanel = wx.Panel(splitter)

        # self.set_person_list()
        # self.build_mainpage()
        splitter.SplitVertically(self.itemlist, self.rightpanel, 1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 5)
        pack(self, sizer)
        
    def build_mainpage(self):
        "build right hand panel"
        panel = self.rightpanel
        sizer =  wx.GridBagSizer(5, 5)
        self.toplabel    = wx.StaticText(panel, label='')

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
    app = wx.PySimpleApp()        
    MainFrame("XAS Data Library").Show()
    app.MainLoop()
