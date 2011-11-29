# specialized classes derived from choice for xasdb controls
import wx
import wx.lib.masked as masked

import xasdb
import table_managers

class _dbChoice(wx.Choice):
    "basic xasdb-derived choice"
    def __init__(self, parent, choices=None, db=None, size=(125,-1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        if choices is None:
            choices = []
        self.choices = choices
        self.db  = db
        self.Clear()
        self.SetItems(choices)
        if len(self.choices)  > 0:
            self.SetSelection(0)

    def SetChoices(self, choices):
        self.Clear()
        self.SetItems(choices)
        self.choices = choices

    def Select(self, choice):
        if isinstance(choice, int):
            choice = '%i' % choice
        if choice in self.choices:
            self.SetSelection(self.choices.index(choice))

class HyperText(wx.StaticText):
    def  __init__(self, parent, label, action=None, colour=(50, 50, 180)):
        self.action = action
        wx.StaticText.__init__(self, parent, -1, label=label)
        font  = self.GetFont() # .Bold()
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
                 show_all=True):
        self.label  = label
        self.link   = HyperText(parent, label, action=self.onClick)
        self.choice = choiceclass(parent, db=db, show_all=show_all)

    def onClick(self, evt=None, label=None):
        if label is None:
            label = self.label
        table = self.label.replace(':', '')
        print 'onClick for table= ', table, hasattr(table_managers, table)
        print self.choice

class ColumnChoice(_dbChoice):
    def __init__(self, parent, columns=None, size=(75,-1)):
        if columns is None:
            columns = ['1', '2', '3']
        _dbChoice.__init__(self, parent, choices=columns, size=size)

class TypeChoice(_dbChoice):
    def __init__(self, parent, choices=None, size=(150,-1)):
        _dbChoice.__init__(self, parent, choices=choices, size=size)

class PersonChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        choices = []
        if db is not None:
            choices = [row.name for row in db.query(xasdb.Person)]
        _dbChoice.__init__(self, parent, choices=choices,
                           db=db, size=size)

class SampleChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        choices = []
        if db is not None:
            choices = [row.name for row in db.query(xasdb.Sample)]
        _dbChoice.__init__(self, parent, choices=choices,
                           db=db, size=size)

class CitationChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        choices = []
        if db is not None:
            choices = [row.name for row in db.query(xasdb.Citation)]
        _dbChoice.__init__(self, parent, choices=choices,
                           db=db, size=size)

class BeamlineChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        choices = []
        if db is not None:
            choices = ["%s: %s" % (row.facility.name, row.name) for \
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
    def __init__(self, parent, db=None, show_all=True,  size=(150,-1)):
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
    def __init__(self, parent, db=None, show_all=True,  size=(150,-1)):
        choices, self.names, self.symbols, self.atnums = ['Cu', 'Fe'], [], [], []
        if db is not None:
            elements = db.get_elements(show_all=show_all)
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
    def __init__(self, parent, db=None, show_all=True,  size=(75,-1)):
        choices = ['K', 'L3', 'L2', 'L1', 'M45']
        if db is not None:
            choices = db.get_edges(show_all=show_all)
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



