"""
Windows (wx.Frames) for managing ancillary tables for XAS Database

"""

import wx
import utils
from utils import pack, add_btn, add_menu, popup, FileOpen, FileSave, FloatCtrl

from choices import SampleChoice, PersonChoice, FacilityChoice, \
     BeamlineChoice, MonochromatorChoice, HyperChoice

from ordereddict import OrderedDict
import xasdb

TWID=275

def clean(txt):
    if txt in (None, 'None', '--', '- -'): txt = ''
    if isinstance(txt, (str, unicode)):
        txt = txt.strip()
    return txt

class BaseTableFrame(wx.Frame):
    """ basic table -> frame convertor"""
    def __init__(self, parent, tablename='', db=None,
                 rowupdate_cb=None, pos=(-1, -1), size=(-1, -1)):
        self.db = db
        self.rowupdate_cb = rowupdate_cb
        style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL
        self.tablename = tablename
        title = 'Manage Table: %s' % tablename
        wx.Frame.__init__(self, parent, -1,  title, style=style,
                           size=size, pos=pos)
        self.rows = {}
        self.buildFrame()

    def show_selection(self, name=None):
        row = self.rows.get(name, None)
        if row is not None:
            self.rowlist.SetStringSelection(name)
            self.show_row(row)

    def __event_row(self, evt=None):
        row = None
        if evt is not None:
            sel = str(self.rowlist.GetStringSelection())
            row = self.rows.get(sel, None)
        return row

    def show_row(self, row=None):
        "fill in form for the selected row"
        for attr, dtype, extra in self.attrs:
            widget = getattr(self, attr)
            val = ''
            if row is not None:
                val = getattr(row, attr)
            if dtype == 'float':
                try:
                    val = float(val)
                except ValueError:
                    pass
            if dtype == 'foreign':
                if hasattr(val, 'name'):
                    val = val.name
                widget.SetStringSelection(val)
            else:
                widget.SetValue(clean(val))

    def save_row(self, row=None):   print 'overwrite save_row!'

    def remove_row(self, row=None):
        if row is None:
            return
        msg = "Delete %s '%s'?" % (self.tablename, row.name)
        if wx.ID_YES == popup(self, msg, msg,
                              style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION):
            self.db.session.delete(row)
            self.db.commit()

    def onShow(self, evt=None):
        "show table row"
        self.show_row(self.__event_row(evt))

    def onSave(self, evt=None):
        "save table row"
        self.save_row(self.__event_row(evt))
        self.set_rowlist()

    def onRemove(self, evt=None):
        "remove table row"
        self.remove_row(self.__event_row(evt))
        self.set_rowlist()

    def buildFrame(self):
        # Now create the Panel to put the other controls on.
        splitter  = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)
        self.rowlist  = wx.ListBox(splitter)
        self.rowlist.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.rowlist.Bind(wx.EVT_LISTBOX, self.onShow)
        self.rightpanel = wx.Panel(splitter)

        self.set_rowlist()
        self.rowlist.Select(0)

        rpanel = self.rightpanel
        rsizer =  wx.BoxSizer(wx.VERTICAL)

        self.toplabel = wx.StaticText(rpanel, label='')
        rsizer.Add(self.toplabel, 0, wx.ALIGN_CENTRE|wx.ALL, 2)
        rowpanel = self.build_rowpanel(rpanel)
        rsizer.Add(rowpanel, 1, wx.ALIGN_CENTRE|wx.ALL, 2)

        btn_save   = add_btn(rpanel, "Save Changes",  action=self.onSave)
        btn_remove = add_btn(rpanel, "Remove This %s" % self.tablename,
                             action=self.onRemove)

        brow = wx.BoxSizer(wx.HORIZONTAL)
        brow.Add(btn_save,   0, wx.ALIGN_LEFT|wx.ALL, 10)
        brow.Add(btn_remove, 0, wx.ALIGN_LEFT|wx.ALL, 10)

        rsizer.Add(brow,     0, wx.ALIGN_LEFT|wx.ALL, 4)
        pack(rpanel, rsizer)

        splitter.SplitVertically(self.rowlist, self.rightpanel, 1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 5)
        pack(self, sizer)
        self.show_row()
        self.Show()
        self.Raise()

    def set_rowlist(self):
        "set the list of rows on the left-hand-side row panel"
        names, rowdata = self.get_rows()
        self.rowlist.Clear()
        self.rows = OrderedDict()
        addlabel = "<Add New %s>" % self.tablename
        self.rows[addlabel] = None
        self.rowlist.Append(addlabel)
        for name, row in zip(names, rowdata):
            self.rows[name] = row
            self.rowlist.Append(name)

        # this tweaking of the splitter sash seems to be needed to
        # keep sash and scrollbar visible when the list is repopulated
        sash = max(165, self.rowlist.GetParent().GetSashPosition())
        idx = len(names)
        self.rowlist.GetParent().SetSashPosition(sash + (-1 + 2*(idx%2)))
        if hasattr(self.rowupdate_cb, '__call__'):
            self.rowupdate_cb(names)

    def get_rows(self):
        if self.table is None:
            return [], []
        names = []
        rowdata = [row for row in self.db.query(self.table)]
        self.rowdata = rowdata
        for r in rowdata:
            names.append(r.name)
        return names, rowdata

    def build_rowpanel(self, parent):
        "build right hand panel"
        panel = wx.Panel(parent)
        sizer = wx.GridBagSizer(5, 2)
        row = -1
        for attr, dtype, extra in self.attrs:
            row += 1
            label = None
            if dtype is None:
                wid = wx.TextCtrl(panel, value="", size=(TWID, -1))
            elif dtype == 'float':
                prec, xmin, xmax = extra
                wid = FloatCtrl(panel, value="", precision=prec,
                                minval=xmin, maxval=xmax, size=(TWID, -1))
            elif dtype == 'multi':
                height = extra
                wid = wx.TextCtrl(panel, value="", size=(TWID, height),
                                  style=wx.TE_MULTILINE)
            elif dtype == 'foreign':
                choiceclass, manager, llabel = extra
                _wid = HyperChoice(panel, choiceclass,
                                   label='%s:' % llabel.title(),
                                   manager=manager, db=self.db)
                wid = _wid.choice
                label = _wid.link
            setattr(self, attr, wid)
            if label is None:
                label = wx.StaticText(panel, label="%s:" % attr.title())
            sizer.Add(label, (row, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL, 2)
            sizer.Add(wid,   (row, 1), (1, 1), wx.ALIGN_LEFT|wx.ALL, 2)
        pack(panel, sizer)
        return panel


class PersonManager(BaseTableFrame):
    attrs = (('name', None, None),
             ('email',  None, None),
             ('affiliation', None, None))
    table = xasdb.Person
    def __init__(self, parent=None, rowupdate_cb=None, db=None, **kws):
        BaseTableFrame.__init__(self, parent, tablename='Person',
                                 db=db, rowupdate_cb=rowupdate_cb,
                                 size=(450,350), **kws)
    def save_row(self, row=None):
        "save table entry"
        if row is None:
            name = self.name.GetValue()
            email= self.email.GetValue()
            affiliation= self.affiliation.GetValue()
            self.db.add_person(name, email, affiliation)
        else:
            for attr, dtype, extra in self.attrs:
                val = getattr(self, attr).GetValue()
                setattr(row, attr, val)
        self.db.commit()

class SampleManager(BaseTableFrame):
    attrs = (('name', None, None),
             ('formula', None, None),
             ('material_source', 'multi', 75),
             ('notes', 'multi', 75),
             ('person', 'foreign', (PersonChoice, PersonManager, 'person')))
    table =  xasdb.Sample
    def __init__(self, parent=None, rowupdate_cb=None, db=None, **kws):
        BaseTableFrame.__init__(self, parent, tablename='Sample',
                                 db=db, rowupdate_cb=rowupdate_cb,
                                 size=(450,350), **kws)

    def save_row(self, row=None):
        "save table entry"
        if row is None:
            name = self.name.GetValue()
            formula = self.formula.GetValue()
            notes = self.notes.GetValue()
            msource = self.material_source.GetValue()
            p = self.person.GetSelection()
            self.db.add_sample(name, notes=notes, formula=formula,
                               material_source=msource, person=p)
        else:
            for attr, dtype, extra in self.attrs:
                if dtype == 'foreign':
                    table = xasdb.Person
                    pname = getattr(self, attr).GetStringSelection()
                    val = self.db.session.query(table).filter(
                        table.name == pname).first()
                else:
                    val = getattr(self, attr).GetValue()
                setattr(row, attr, val)
        self.db.commit()


class MonochromatorManager(BaseTableFrame):
    attrs = (('name', None, None),
             ('dspacing', 'float', (7, 0, 1000.0)),
             ('steps_per_degree', 'float', (2, 0, 1e12)),
             ('notes', 'multi', 85))
    table = xasdb.Monochromator
    def __init__(self, parent=None, rowupdate_cb=None, db=None, **kws):
        BaseTableFrame.__init__(self, parent, tablename='Monochromator',
                                 db=db, rowupdate_cb=rowupdate_cb,
                                 size=(450,350), **kws)

    def save_row(self, row=None):
        "save table entry"
        if row is None:
            name = self.name.GetValue()
            notes = self.notes.GetValue()
            dspacing = float(self.dspacing.GetValue())
            steps_pd = float(self.steps_per_degree.GetValue())
            self.db.add_monochromator(name, notes=notes, dspacing=dspacing,
                                      steps_per_degree=steps_pd)
        else:
            for attr, dtype, extra in self.attrs:
                val = getattr(self, attr).GetValue()
                if dtype == 'float':
                    val = float(val)
                setattr(row, attr, val)
        self.db.commit()

class FacilityManager(BaseTableFrame):
    attrs = (('name', None, None),
             ('notes', 'multi', 75))
    table =  xasdb.Facility
    def __init__(self, parent=None, rowupdate_cb=None, db=None, **kws):
        BaseTableFrame.__init__(self, parent, tablename='Facility',
                                 db=db, rowupdate_cb=rowupdate_cb,
                                 size=(450,350), **kws)

    def save_row(self, row=None):
        "save table entry"
        if row is None:
            name = self.name.GetValue()
            notes = self.notes.GetValue()
            self.db.add_facility(name, notes=notes)
        else:
            for attr, dtype, extra in self.attrs:
                val = getattr(self, attr).GetValue()
                setattr(row, attr, val)
        self.db.commit()

class BeamlineManager(BaseTableFrame):
    attrs = (('facility', 'foreign',
                     (FacilityChoice, FacilityManager, 'facility')),
             ('name', None, None),
             ('xray_source', None, None),
             ('notes', 'multi', 75))
    table =  xasdb.Beamline
    def __init__(self, parent=None, rowupdate_cb=None, db=None, **kws):
        BaseTableFrame.__init__(self, parent, tablename='Beamline',
                                 db=db, rowupdate_cb=rowupdate_cb,
                                 size=(450,350), **kws)

    def save_row(self, row=None):
        "save table entry"
        if row is None:
            name = self.name.GetValue()
            notes = self.notes.GetValue()
            source = self.xray_source.GetValue()
            facility = self.facility.GetSelection()
            self.db.add_beamline(name, notes=notes, xray_source=source,
                               facility=facility)
        else:
            for attr, dtype, extra in self.attrs:
                if dtype == 'foreign':
                    table = xasdb.Facility
                    pname = getattr(self, attr).GetStringSelection()
                    val = self.db.session.query(table).filter(
                        table.name == pname).first()
                else:
                    val = getattr(self, attr).GetValue()
                setattr(row, attr, val)
        self.db.commit()

