#!/usr/bin/env python
"""GUI App for CARS Phonebook
"""
import time
import copy
import base64
import cStringIO
import warnings
warnings.simplefilter('ignore')

from xasdb import 

from zipfile import ZipFile
import wx

from ordereddict import OrderedDict
 
class AffilFrame(wx.Frame):
    """ GUI Configure Frame"""
    def __init__(self, parent, pos=(-1, -1), dbcursor=None):
        
        self.parent = parent
        self.cursor  = dbcursor
        self.parent.affiliations_changed = False

        style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL 
        wx.Frame.__init__(self, None, -1,  'Change Affiliations',
                          size=(425,350),  pos=pos)
        self.rowdata = []
        self.panel = None
        self.drawFrame()

    def query (self, query, *args):
        "wrapper for mysql query + fetchall"
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def onSave(self, evt=None):
        "save affiliations"
        self.parent.affiliations_changed = True
        update = "update affiliation set name='%s' where id=%i"
        insert = "insert into affiliation(name) values ('%s')"
        for index, ctrl in self.rowdata:
            value = ctrl.GetValue().strip()
            if index >= 0:
                self.cursor.execute(update % (value, index))
            elif len(value) > 0:
                self.cursor.execute(insert% value)
        self.redrawFrame()

    def onDelete(self, evt=None, idx=-1):
        "delete affiliation"
        if idx <  0:
            return
        self.query("delete from affiliation where id='%i'" % idx)
        for rowid, ctrl in self.rowdata:
            if id == rowid:
                ctrl.SetValue("")
        self.redrawFrame()
        
    def redrawFrame(self):
        self.parent.refresh_affiliations()
        pos = self.GetPosition()
        self.Destroy()
        affil_frame = AffilFrame(self.parent, pos=pos,
                                 dbcursor=self.parent.cursor)

    def onDone(self, evt=None):
        "finished changing affiliations"
        self.Destroy()
        
    def drawFrame(self):
        qcount = "select count(*) from person where affiliation='%i'"
        panel = wx.Panel(self)
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.rowdata = []
        index = 0
        for row in self.query("select * from affiliation"):
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            index = index + 1

            label = 'Affiliation %3i: ' % (index)
            sizer.Add(wx.StaticText(panel, label=label, size=(-1,-1)), 
                      0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 1)
            textctrl = wx.TextCtrl(panel, value=row['name'],
                                   size=(225, -1))
            sizer.Add(textctrl, 0, wx.ALIGN_LEFT|wx.ALL, 1)
            try:
                count = self.query(qcount % row['id'])[0]['count(*)']
            except:
                count = 0
            if count  > 0:
                label = ' %i people ' % count
                if count == 1:
                    label = ' 1 person '
                sizer.Add(wx.StaticText(panel, label=label),
                          0, wx.ALIGN_LEFT|wx.ALL, 1)
            else:
                del_btn = add_btn(panel, "delete",
                                  action=Closure(self.onDelete,
                                                 idx =row['id']))
                sizer.Add(del_btn, 0, wx.ALIGN_LEFT|wx.ALL, 1)
                
            self.rowdata.append((row['id'], textctrl))
            mainsizer.Add(sizer, 0, wx.ALIGN_LEFT|wx.ALL, 6)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = 'Affiliation %3i: ' % (index+1)
        sizer.Add(wx.StaticText(panel, label=label, size=(-1,-1)), 
                  0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 1)
        textctrl = wx.TextCtrl(panel, value='',
                               size=(225, -1))
        sizer.Add(textctrl, 0, wx.ALIGN_LEFT|wx.ALL, 1)
        self.rowdata.append((-1, textctrl))
        mainsizer.Add(sizer, 0, wx.ALIGN_LEFT|wx.ALL, 6)

        brow = wx.BoxSizer(wx.HORIZONTAL)

        btn_save = add_btn(panel, "Save Changes",  action=self.onSave)
        btn_done = add_btn(panel, "Done",  action=self.onDone)
        
        brow.Add(btn_save,   0, wx.ALIGN_LEFT|wx.ALL, 5)
        brow.Add(btn_done,   0, wx.ALIGN_LEFT|wx.ALL, 5)
        mainsizer.Add(brow,  0, wx.ALIGN_LEFT|wx.ALL, 5)

        pack(panel, mainsizer)        
        self.Show()
        self.Raise()

class MainFrame(wx.Frame):
    """This is the main XAS DataBrowser Frame."""
    def __init__(self, title='XAS Data Library', dbfile=None):
        
        wx.Frame.__init__(self, None, -1, title, size=(500, 700))
        
        if dbfile is None:

        username = ''
        while not login_success:
            dlg = LoginDialog(title="CARS Phone Directory", username=username)
            dlg.CenterOnScreen()
            # this does not return until the dialog is closed.
            if dlg.ShowModal() == wx.ID_OK:
                username = dlg.username.GetValue()
                password = dlg.password.GetValue()
                for row in self.query("select * from login"):
                    login_success = (username == row['username'] and
                                     password == row['password'])
                    if login_success:
                        break
            else:
                break
            dlg.Destroy()
        self.affil = None
        if login_success:
            self.initialize_data()
            self.create_frame()
        else:
            self.Destroy()
            
    def query (self, query, *args):
        "wrapper for mysql query + fetchall"
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def get_people(self, active=True, inactive=True):
        "make ordereddict of self.people  name: id "
        self.people = OrderedDict()
        self.people["<Add New Person>"] = None
        for row in self.getall():
            try:
                status = row['status'].strip().lower()
            except:
                status = 'inactive'
            if ((active and status == 'active') or
                (inactive and status == 'inactive')):
                            
                name ="%s, %s" % (row['last_name'].strip(),
                                 row['first_name'].strip())
                if name.strip() != '':
                    self.people[name] = row['id']
                
    def getall(self, active_only=False):
        condition = ''
        if active_only:
            condition = "where status='Active'"
        q = "select * from person %s order by last_name, first_name" % condition
        return self.query(q)
        
    def initialize_data(self):
        "get initial data from database"
        self.display_names = []
        rows = self.getall()
        self.initial_data = copy.deepcopy(rows)
        self.get_people()
        self.status_choices = ['Inactive', 'Active']
        self.sector_choices = []
        for row in self.query("select * from sector"):
            self.sector_choices.append((row['id'], row['name']))
        self.refresh_affiliations()

    def refresh_affiliations(self):
        self.affiliations_changed = False
        self.affil_choices = []
        self.affil_dict    = {}
        for row in self.query("select * from affiliation"):
            self.affil_choices.append(row['name'])
            self.affil_dict[row['id']] = row['name']
        if self.affil is not None:
            this_affil = self.affil.GetSelection()
            self.affil.SetItems(self.affil_choices)
            self.affil.SetSelection(this_affil)        
        
    def create_frame(self):
        "create top level frame"
        # Create the menubar
        menuBar = wx.MenuBar()
        fmenu = wx.Menu()
        omenu = wx.Menu()
        omenu.Append(4910, "Show All", "Show All People", 
                     wx.ITEM_RADIO)
        omenu.Append(4911, "Show Active Only",
                     "Show Active People Only", wx.ITEM_RADIO)
        omenu.Append(4912, "Show Inactive Only",
                     "Show Inactive People Only",  wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onChooseActive, id=4910)        
        self.Bind(wx.EVT_MENU, self.onChooseActive, id=4911)        
        self.Bind(wx.EVT_MENU, self.onChooseActive, id=4912)
        
        omenu.AppendSeparator()
        omenu.Append(4913, "Manage Affiliations",
                     "Change and Add Affliations",  wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onAffiliation, id=4913)        
        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        id_close = wx.NewId()
        id_export_data = wx.NewId()
        id_export_images = wx.NewId()        

        fmenu.Append(id_export_data, "Export All Data",
                     "Export data (except pictures) to spreadsheet")
        self.Bind(wx.EVT_MENU,  self.onExportAll, id=id_export_data)

        fmenu.Append(id_export_data, "Export Active People Data",
                     "Export data (except pictures) to spreadsheet")
        self.Bind(wx.EVT_MENU,  self.onExportActive, id=id_export_data)
        
        fmenu.Append(id_export_images, "Export Pictures",
                     "Export pictures to zip file")
        self.Bind(wx.EVT_MENU,  self.onExportImages, id=id_export_images)
        
        fmenu.AppendSeparator()
        fmenu.Append(id_close, "E&xit\tAlt-X", "Exit this Program")
        self.Bind(wx.EVT_MENU,  self.onClose, id=id_close)

        
        # and put the menu on the menubar
        menuBar.Append(fmenu, "&File")
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

        self.set_person_list()
        self.build_mainpage()
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
        if row['picture'] not in (None, 'None', ''):
            self.raw_image = base64.b64decode(row['picture'])
        self.display_image()
        
    def display_image(self):
        "display raw jpeg image as wx bitmap"
        self.img.SetBitmap(
            wx.BitmapFromImage(wx.ImageFromStream(
            cStringIO.StringIO(self.raw_image)).Rescale(144, 164)))        

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
        ret = popup(self, "Really Quit?", "Exit Phonebook?",
                    style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        if ret == wx.ID_YES:
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
            
    def onAffiliation(self, evt=None):
        "show 'Change Affiliations' page"
        try:
            self.affil_frame.Raise()
        except:
            self.affiliations_changed = False
            self.affil_frame = AffilFrame(self, dbcursor=self.cursor)

    def onChooseActive(self, evt=None):
        "respond to menu choice of All/Active only/Inactive only"
        try:
            idx = evt.GetId()
        except:
            return
        active, inactive = True, True
        if idx == 4911:
            inactive = False
        elif idx == 4912:
            active = False
        self.set_person_list(make_list=True, active=active, inactive=inactive)
                
    def onExportAll(self, evt=None):
        "exports data to CSV file"
        dlg = wx.FileDialog(self, message="Export data to file",
                            defaultFile='Phonebook.csv',
                            style=wx.SAVE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText('exporting data to %s' % dlg.GetPath())
            self.export_data(dlg.GetPath())
        dlg.Destroy()
        self.SetStatusText('exported data to %s' % dlg.GetPath())

    def onExportActive(self, evt=None):
        "exports data to CSV file"
        dlg = wx.FileDialog(self, message="Export data to file",
                            defaultFile='Phonebook_Active.csv',
                            style=wx.SAVE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText('exporting data to %s' % dlg.GetPath())
            self.export_data(dlg.GetPath(), active_only=True)
        dlg.Destroy()
        self.SetStatusText('exported data to %s' % dlg.GetPath())


    def onExportImages(self, evt=None):
        "exports images to a zip file"
        dlg = wx.FileDialog(self, message="Export Pictures to zip file",
                            defaultFile='PhonebookImages.zip',
                            style=wx.SAVE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText('exporting images to %s' % dlg.GetPath())
            fout = ZipFile(dlg.GetPath(), 'w')
            for row in self.getall():
                fname = fix_filename("%s_%s.jpg" % (row['first_name'],
                                                    row['last_name']))
                fout.writestr(fname, base64.b64decode(row['picture']))
            fout.close()
        dlg.Destroy()
        self.SetStatusText('exported images to %s' % dlg.GetPath())

    def export_data(self, fname='Phonebook.csv', active_only=False):
        "save data to csv file"
        fout = open(fname, 'w')
        s_names = []
        s_ids   = []
        affiliations = {}
        for row in self.query('select * from affiliation'):
            affiliations[row['id']] =  row['name']

        for row in self.query("select * from sector order by id"):
            s_ids.append(row['id'])
            s_names.append(row['name'])
        # titles
        txt = []
        for attr in (self.simple_attr + self.multiline_attr +
                     ('status' , 'affiliation')):
            txt.append(attr.title().replace('_', ' '))
        txt.extend(s_names)
        fout.write("%s\n" % ('\t'.join(txt)))

        q_sect = 'select * from person_sector where user_id=%i'
        for row in self.getall(active_only=active_only):
            txt = []
            for attr in (self.simple_attr + self.multiline_attr):
                val = row[attr]
                if val is None:   val = ' '
                val = val.replace('\n',' ').replace('\t',' ').strip()
                txt.append(val)
            affil_name = affiliations[row['affiliation']]
            txt.extend([row['status'], affil_name])

            row_sectors = ['No'] * len(s_ids)
            for sect in self.query(q_sect % row['id']):
                row_sectors[s_ids.index(sect['sector_id'])] = 'Yes'
            txt.extend(row_sectors)
            fout.write("%s\n" % ('\t'.join(txt)))
        fout.close()
       
    def onDelPicture(self, evt=None):
        "replace picture with default image"
        self.raw_image = DEFAULT_IMAGE
        self.display_image()

    def onPicture(self, evt=None):
        "prompt for and save picture"
        wildcard = "Images (*.jpg,*jpeg)|*.jpg|All files (*.*)|*.*"
        dlg = wx.FileDialog(self, message="Choose a Picture",
                            wildcard=wildcard,
                            style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.raw_image = open(dlg.GetPath(), "rb").read()
            self.img_size = len(self.raw_image)
            self.display_image()
        dlg.Destroy()
        self.SetStatusText('updated Picture')

    def onRemove(self, evt=None):
        "prompt for and remover current person from phonebook"
        if self.current_id is None or len(self.current_name.strip()) < 1:
            return
        msg = """Really Delete Person?
      %s
This will permanently remove them from the CARS Phonebook
and cannot be undone!""" % self.current_name
        dlg = wx.MessageDialog(self, msg, 'Delete %s?' % self.current_name,
                               wx.NO_DEFAULT|wx.YES_NO|wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_YES:
            if self.current_id is not None:
                self.query("delete from person where id='%i'" %
                           self.current_id)
                self.query("delete from person_sector where user_id='%i'" %
                           self.current_id)
                time.sleep(0.25)
                self.SetStatusText("Removed %s" % self.current_name)
                self.set_person_list(make_list=True)
                self.ShowPerson()
        dlg.Destroy()
    
class ConnectDialog(wx.Dialog):
    "simple login popup window"
    def __init__(self, parent=None,
                 title='CARS Phonebook Admin Log in', username=''):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=title)
        self.username = wx.TextCtrl(self, value=username, size=(120, -1))
        self.password = wx.TextCtrl(self, value="",       size=(120, -1),
                                    style=wx.TE_PASSWORD)
        
        grid  = wx.GridBagSizer(2, 5)
        title = "Please Log in to\nCARS Phone Book Administration"
        grid.Add(wx.StaticText(self, label=title),
                 (0, 0), (1, 2), wx.ALIGN_CENTER|wx.ALL, 2)
        grid.Add(wx.StaticText(self, label="Name:"),
                 (1, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL,  5)
        grid.Add(self.username,
                 (1, 1), (1, 1), wx.ALIGN_RIGHT|wx.ALL, 5)
        grid.Add(wx.StaticText(self, label="Password:"),
                 (2, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL,  5)
        grid.Add(self.password,
                 (2, 1), (1, 1), wx.ALIGN_RIGHT|wx.ALL, 5)
        
        grid.Add(wx.StaticLine(self, size=(200, -1), style=wx.LI_HORIZONTAL),
                 (3, 0), (1, 2), wx.ALIGN_CENTER|wx.ALL, 2)
        grid.Add(self.CreateButtonSizer(wx.OK| wx.CANCEL),
                 (4, 0),(1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        pack(self, grid)
        
if __name__ == '__main__':
    app = wx.PySimpleApp()        
    MainFrame("XAS Data Library").Show()
    app.MainLoop()
