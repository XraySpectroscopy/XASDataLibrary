# specialized classes derived from choice for xasdb controls
import wx
import wx.lib.masked as masked

import xasdb
# import table_managers

class _dbChoice(wx.Choice):
    "basic xasdb-derived choice"
    def __init__(self, parent, choices=None, db=None, size=(125,-1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        self.db  = db
        if choices is None and db is not None and hasattr(self, 'table'):
            choices = [row.name for row in db.query(self.table)]
        if choices is None:
            choices = []
        self.choices = choices
        self.Clear()
        self.SetItems(choices)
        if len(self.choices)  > 0:
            self.SetSelection(0)

    def SetChoices(self, choices, choice=None):
        self.Clear()
        self.SetItems(choices)
        self.choices = choices
        if choice is not None: self.Select(choice)

    def Select(self, choice):
        if isinstance(choice, int):
            choice = '%i' % choice
        if choice in self.choices:
            self.SetSelection(self.choices.index(choice))

class HyperText(wx.StaticText):
    def  __init__(self, parent, label, action=None, colour=(50, 50, 180)):
        self.action = action
        wx.StaticText.__init__(self, parent, -1, label=label)
        font  = self.GetFont()
        font.SetUnderlined(True)
        self.SetFont(font)
        self.SetForegroundColour(colour)
        self.Bind(wx.EVT_LEFT_UP, self.onSelect)

    def onSelect(self, evt=None):
        if self.action is not None:
            self.action(evt=evt, label=self.GetLabel())
        evt.Skip()

class HyperChoice(object):
    """combined HyperText label and Choice, connected """
    def __init__(self, parent, choiceclass, label=None, db=None,
                 manager=None, **kws):
        self.label  = label
        self.db     = db
        self.link   = HyperText(parent, label, action=self.onClick)
        self.choice = choiceclass(parent, db=db)
        self.manager = manager
        self.editor = None

    def SetChoices(self, choices):
        choice = self.choice.GetStringSelection()
        self.choice.SetChoices(choices, choice=choice)

    def onClick(self, evt=None, label=None):
        if label is None:
            label = self.label
        table = self.label.replace(':', '')
        # manager = getattr(table_managers, table, None)
        if self.manager is not None:
            try:
                self.editor.Raise()
            except:
                self.editor = self.manager(parent=None, db=self.db,
                                           rowupdate_cb=self.SetChoices)
                self.editor.show_selection(self.choice.GetStringSelection())

class ColumnChoice(_dbChoice):
    def __init__(self, parent, columns=None, size=(75,-1)):
        if columns is None:
            columns = ['1', '2', '3']
        _dbChoice.__init__(self, parent, choices=columns, size=size)

class TypeChoice(_dbChoice):
    def __init__(self, parent, choices=None, size=(150,-1)):
        _dbChoice.__init__(self, parent, choices=choices, size=size)

class PersonChoice(_dbChoice):
    table = xasdb.Person
    def __init__(self, parent, db=None, size=(190,-1)):
        _dbChoice.__init__(self, parent, db=db, size=size)

class SampleChoice(_dbChoice):
    table = xasdb.Sample
    def __init__(self, parent, db=None, size=(190,-1)):
        _dbChoice.__init__(self, parent, db=db,size=size)

class CitationChoice(_dbChoice):
    table = xasdb.Citation
    def __init__(self, parent, db=None, size=(190,-1)):
        _dbChoice.__init__(self, parent, db=db, size=size)

class FacilityChoice(_dbChoice):
    table = xasdb.Facility
    def __init__(self, parent, db=None, size=(190,-1)):
        _dbChoice.__init__(self, parent, db=db, size=size)

class BeamlineChoice(_dbChoice):
    def __init__(self, parent, db=None, size=(190,-1)):
        choices = []
        if db is not None:
            choices = ["%s" % row.name for \
                       row in db.query(xasdb.Beamline)]
            choices.sort()
        _dbChoice.__init__(self, parent, choices=choices,
                           db=db, size=size)

    def Select(self, choice):
        if choice is None:
            return
        if choice in self.choices:
            self.SetSelection(self.choices.index(choice))
        elif isinstance(choice, int) and choice>=0 and \
             choice<len(self.choices):
            self.SetSelection(choice)
        elif self.db is not None: # look for matches
            choice = choice.lower()
            fnames, bnames = [], []
            for row in self.db.query(xasdb.Beamline):
                fnames.append(row.facility.name)
                bnames.append(row.name)

            _fac, _bl = None, None
            for name in fnames:
                if name.lower() in choice:
                    _fac = name
                    break
            for name in bnames:
                if name.lower() in choice:
                    _bl = name
                    break
            newchoice = "%s: %s" % (_fac, _bl)
            if newchoice in self.choices:
                self.SetSelection(self.choices.index(newchoice))

class MonochromatorChoice(_dbChoice):
    table = xasdb.Monochromator
    def __init__(self, parent, db=None, size=(150,-1)):
        choices = ['Si(111), water-cooled']
        if db is not None:
            choices = ["%s" % (row.name) for row in db.query(xasdb.Monochromator)]
            choices.sort()
        _dbChoice.__init__(self, parent, choices=choices, size=size)

    def Select(self, choice):
        if choice is None:
            return
        if choice in self.choices:
            self.SetSelection(self.choices.index(choice))
            return choice
        elif isinstance(choice, int) and choice>=0 and choice<len(self.choices):
            self.SetSelection(choice)
            return self.choices[choice]
        else:  # look for matches
            choice = choice.lower()
            for delim in '()[]{}<> ':
                choice = choice.replace(delim, '')
            choice = choice.replace('-', ',').split(',')[0]
            for index, name in enumerate(self.choices):
                nam = name.lower()
                for delim in '()[]{}<> ':
                    nam = nam.replace(delim, '')
                nam = nam.replace('-', ',').split(',')[0]
                if choice == nam:
                    self.SetSelection(index)
                    return name
        return None

class ElementChoice(_dbChoice):
    def __init__(self, parent, db=None, size=(150,-1)):
        choices, self.names, self.symbols, self.atnums = ['Cu', 'Fe'], [], [], []
        if db is not None:
            elements = db.get_elements()
            choices = ["%s: %s" % (elem[1], elem[0]) for elem in elements]
            self.names   = [elem[0].lower() for elem in elements]
            self.names   = [elem[0].lower() for elem in elements]
            self.symbols = [elem[1].lower() for elem in elements]
            self.atnums  = [elem[2] for elem in elements]
        _dbChoice.__init__(self, parent, choices=choices, size=size)

    def Select(self, choice):
        if choice is None:
            return
        if isinstance(choice, int):
            choice = '%i' % choice
        choice = choice.lower()
        if choice in self.names:
            self.SetSelection(self.names.index(choice))
        elif choice in self.symbols:
            self.SetSelection(self.symbols.index(choice))
        elif choice in self.atnums:
            self.SetSelection(self.atnums.index(choice))

class EdgeChoice(_dbChoice):
    def __init__(self, parent, db=None, size=(75,-1)):
        choices = ['K', 'L3', 'L2', 'L1', 'M45']
        if db is not None:
            choices = db.get_edges()
        _dbChoice.__init__(self, parent, choices=choices, size=size)

def DateTimeCtrl(parent, name='datetimectrl', use_now=False):
    panel = wx.Panel(parent)
    bgcol = wx.Colour(250,250,250)

    datestyle = wx.DP_DROPDOWN|wx.DP_SHOWCENTURY|wx.DP_ALLOWNONE

    datectrl = wx.DatePickerCtrl(panel, size=(120,-1), style=datestyle)
    timectrl = masked.TimeCtrl(panel, -1, name=name, limited=False,
                               fmt24hr=True, oob_color=bgcol)
    h = timectrl.GetSize().height
    spinner = wx.SpinButton(panel, -1, wx.DefaultPosition,
                            (-1, h), wx.SP_VERTICAL )
    timectrl.BindSpinButton(spinner)
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(datectrl, 0, wx.ALIGN_CENTER)
    sizer.Add(timectrl, 0, wx.ALIGN_CENTER)
    sizer.Add(spinner, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
    panel.SetSizer(sizer)
    sizer.Fit(panel)
    if use_now:
        timectrl.SetValue(wx.DateTime_Now())
    return panel, datectrl, timectrl

def DateCtrl(parent, use_now=False):
    style = wx.DP_DROPDOWN|wx.DP_SHOWCENTURY|wx.DP_ALLOWNONE
    datectrl = wx.DatePickerCtrl(parent, size=(120,-1), style=style)
    # datectrl.Bind(wx.EVT_DATE_CHANGED, onDateChange)
    return datectrl



