# specialized classes derived from choice for xasdb controls
import wx
import wx.lib.masked as masked

from xasdb import Person, Beamline, Monochromator, Element, Edge

class _dbChoice(wx.Choice):
    "basic xasdb-derived choice"
    def __init__(self, parent, choices=None, db=None, size=(120,-1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        if choices is None:
            choices = []
        self.choices = choices
        self.db  = db
        self.Clear()
        self.SetItems(choices)

    def SetChoices(self, choices):
        self.Clear()
        self.SetItems(choices)
        self.choices = choices
        
    def Select(self, choice):
        if isinstance(choice, int):
            choice = '%i' % choice
        if choice in self.choices:
            self.SetSelection(self.choices.index(choice))
    
class ColumnChoice(_dbChoice):
    def __init__(self, parent, columns=None, size=(80,-1)):
        if columns is None:
            columns = ['1', '2', '3']
        _dbChoice.__init__(self, parent, choices=columns, size=size)
        
class TypeChoice(_dbChoice):
    def __init__(self, parent, choices=None, size=(130,-1)):
        _dbChoice.__init__(self, parent, choices=choices, size=size)

class PersonChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        self.names = []
        if db is not None:
            self.names = [row.name for row in db.query(Person)]

        _dbChoice.__init__(self, parent, choices=self.names, db=db, size=size)
        if len(self.names)  > 0:
            self.SetSelection(0)
            
    def Select(self, choice):
        if choice in self.names:
            self.SetSelection(self.names.index(choice))

class BeamlineChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        self.names = []
        if db is not None:
            self.names = ["%s: %s" % (row.facility.name, row.name) for \
                          row in db.query(Beamline)]
            self.names.sort()
            
        _dbChoice.__init__(self, parent, choices=self.names, db=db, size=size)
        if len(self.names)  > 0:
            self.SetSelection(0)
            
    def Select(self, choice):
        if choice in self.names:
            self.SetSelection(self.names.index(choice))
        elif isinstance(choice, int) and choice>=0 and choice<len(self.names):
            self.SetSelection(choice)
        elif self.db is not None: # look for matches
            choice = choice.lower()
            fnames, bnames = [], []
            for row in self.db.query(Beamline):
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
            if newchoice in self.names:
                self.SetSelection(self.names.index(newchoice))


class MonochromatorChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(190,-1)):
        self.names = []
        if db is not None:
            self.names = ["%s" % (row.name) for row in db.query(Monochromator)]
            self.names.sort()
            
        _dbChoice.__init__(self, parent, choices=self.names, size=size)
        if len(self.names)  > 0:
            self.SetSelection(0)
            
    def Select(self, choice):
        if choice in self.names:
            self.SetSelection(self.names.index(choice))
            return choice
        elif isinstance(choice, int) and choice>=0 and choice<len(self.names):
            self.SetSelection(choice)
            return self.names[choice]
        else:  # look for matches
            choice = choice.lower()
            for delim in '()[]{}<> ':
                choice = choice.replace(delim, '')
            choice = choice.replace('-', ',').split(',')[0]                
            for index, name in enumerate(self.names):
                nam = name.lower()
                for delim in '()[]{}<> ':
                    nam = nam.replace(delim, '')
                nam = nam.replace('-', ',').split(',')[0]
                if choice == nam:
                    self.SetSelection(index)
                    return name
        return None
class ElementChoice(_dbChoice):
    def __init__(self, parent, db=None, show_all=True,  size=(130,-1)):
        self.choices, self.names, self.symbols, self.atnums = [], [], [], []
        if db is not None:
            elements = db.get_elements(show_all=show_all)
            self.choices = ["%s: %s" % (elem[1], elem[0]) for elem in elements]
            self.names   = [elem[0].lower() for elem in elements]
            self.names   = [elem[0].lower() for elem in elements]
            self.symbols = [elem[1].lower() for elem in elements]
            self.atnums  = [elem[2] for elem in elements]
        _dbChoice.__init__(self, parent, choices=self.choices, size=size)

    def Select(self, choice):
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
    def __init__(self, parent, db=None, show_all=True,  size=(60,-1)):
        choices = []
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


      
