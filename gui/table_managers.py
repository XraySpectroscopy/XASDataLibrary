"""
Windows (wx.Frames) for managing ancillary tables for XAS Database

"""

import wx
import utils
import xasdb

class _BaseTableFrame(wx.Frame):
    """ basic table -> frame convertor"""
    def __init__(self, title='', db=None, choice=None,
                 pos=(-1, -1), size=(-1, -1)):
        self.db = db
        self.choice= choice
        style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL 
        _wx.Frame.__init__(self, None, -1,  title, style=style,
                           size=size, pos=pos)

    def SetChoices(self, choices=None,index=0):
        if self.choice is None or choices is None:
            return
        self.choice.SetItems(choices)
        self.choice.SetSelection(index)
        
class Person(_BaseTableFrame):
    def __init__(self, pos=(-1, -1), db=None, choice=None):
        _BaseTableFrame.__init__(self, -1,  'Manage Person Table',
                                 db=db, choice=choice,
                                 size=(425,350),  pos=pos)
        self.buildFrame()

    def onSave(self, evt=None):
        "save person"
        print 'Save'

    def onDelete(self, evt=None, idx=-1):
        "delete affiliation"
        if idx <  0:
            return
        self.redrawFrame()
        
    def redrawFrame(self):
        print 'Redraw!'
        #pos = self.GetPosition()
        #self.Destroy()
        #affil_frame = AffilFrame(self.parent, pos=pos,
        #                         dbcursor=self.parent.cursor)

    def onDone(self, evt=None):
        "finished changing affiliations"
        self.Destroy()
        
    def drawFrame(self):
        rows = [row for row in db.query(xasdb.Person)]
        print 'Person Frame: rows = ', rows

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        index = 0
        # name, email, attributes, notes, affiliation
        for row in rows:
            print row
#         for row in self.query("select * from affiliation"):
#             sizer = wx.BoxSizer(wx.HORIZONTAL)
#             index = index + 1
# 
#             label = 'Affiliation %3i: ' % (index)
#             sizer.Add(wx.StaticText(panel, label=label, size=(-1,-1)), 
#                       0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 1)
#             textctrl = wx.TextCtrl(panel, value=row['name'],
#                                    size=(225, -1))
#             sizer.Add(textctrl, 0, wx.ALIGN_LEFT|wx.ALL, 1)
#             try:
#                 count = self.query(qcount % row['id'])[0]['count(*)']
#             except:
#                 count = 0
#             if count  > 0:
#                 label = ' %i people ' % count
#                 if count == 1:
#                     label = ' 1 person '
#                 sizer.Add(wx.StaticText(panel, label=label),
#                           0, wx.ALIGN_LEFT|wx.ALL, 1)
#             else:
#                 del_btn = add_btn(panel, "delete",
#                                   action=Closure(self.onDelete,
#                                                  idx =row['id']))
#                 sizer.Add(del_btn, 0, wx.ALIGN_LEFT|wx.ALL, 1)
#                 
#             self.rowdata.append((row['id'], textctrl))
#             mainsizer.Add(sizer, 0, wx.ALIGN_LEFT|wx.ALL, 6)
# 
#         sizer = wx.BoxSizer(wx.HORIZONTAL)
#         label = 'Affiliation %3i: ' % (index+1)
#         sizer.Add(wx.StaticText(panel, label=label, size=(-1,-1)), 
#                   0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 1)
#         textctrl = wx.TextCtrl(panel, value='',
#                                size=(225, -1))
#         sizer.Add(textctrl, 0, wx.ALIGN_LEFT|wx.ALL, 1)
#         self.rowdata.append((-1, textctrl))
#         mainsizer.Add(sizer, 0, wx.ALIGN_LEFT|wx.ALL, 6)
# 
#         brow = wx.BoxSizer(wx.HORIZONTAL)
# 
#         btn_save = add_btn(panel, "Save Changes",  action=self.onSave)
#         btn_done = add_btn(panel, "Done",  action=self.onDone)
#         
#         brow.Add(btn_save,   0, wx.ALIGN_LEFT|wx.ALL, 5)
#         brow.Add(btn_done,   0, wx.ALIGN_LEFT|wx.ALL, 5)
#         mainsizer.Add(brow,  0, wx.ALIGN_LEFT|wx.ALL, 5)
# 
#         pack(panel, mainsizer)        
#         self.Show()
#         self.Raise()
