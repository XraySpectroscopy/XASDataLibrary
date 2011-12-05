import wx
import string
import fpformat

class Closure:
    """A simple Closure class for extended callbacks
    This class holds a user-defined function to be executed when the
    class is invoked as a function.  This is useful in many situations,
    especially for 'callbacks' where lambda's are quite enough.
    Many Tkinter 'actions' can use such callbacks.

    >>>def my_action(x=None):
    ...        print 'my action: x = ', x
    >>>c = Closure(my_action,x=1)
    ..... sometime later ...
    >>>c()
     my action: x = 1
    >>>c(x=2)
     my action: x = 2

    based on Command class from J. Grayson's Tkinter book.
    """
    def __init__(self, func=None, *args, **kwds):
        self.func = func
        self.kwds = kwds
        self.args = args
    def __call__(self,  *args, **kwds):
        self.kwds.update(kwds)
        if hasattr(self.func, '__call__'):
            self.args = args
            return self.func(*self.args, **self.kwds)


def fix_filename(s):
    """fix string to be a 'good' filename. This may be a more
    restrictive than the OS, but avoids nasty cases."""
    bchars = '<>:"\'\\\t\r\n/|?* !%$'
    t = s.translate(string.maketrans(bchars, '_'*len(bchars)))
    if t[0] in '-,;[]{}()~`@#':
        t = '_%s' % t
    return t

def pack(window, sizer):
    "simple wxPython Pack"
    window.SetSizer(sizer)
    sizer.Fit(window)

def get(wid):
    "get widget string value"
    return wid.GetValue().strip()

def put(wid, val):
    "set widget string value"
    if val is None:
        val = ''
    val = val.strip()
    if val in ('None', '--', '- -'):
        val = ''
    return wid.SetValue(val)

def add_btn(panel, label, action=None):
    "add simple button with bound action"
    thisb = wx.Button(panel, label=label)
    if hasattr(action, '__call__'):
        panel.Bind(wx.EVT_BUTTON, action, thisb)
    return thisb

def popup(parent, message, title, style=None):
    "generic popup message dialog"
    if style is None:
        style = wx.OK | wx.ICON_INFORMATION
    dlg = wx.MessageDialog(parent, message, title, style)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret

def add_menu(parent, menu, label, help, action=None):
    "add a menu item with action"
    id = wx.NewId()
    menu.Append(id, label, help)
    if action is not None:
        parent.Bind(wx.EVT_MENU, action, id=id)


def FileOpen(parent, message, wildcard=None):
    "File Open dialog"
    out = None
    dlg = wx.FileDialog(parent, message=message,
                        wildcard=wildcard,
                        style=wx.OPEN|wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        out = dlg.GetPath()
    dlg.Destroy()
    return out


def FileSave(parent, message, default=None, wildcard=None):
    "File Save dialog"
    out = None
    dlg = wx.FileDialog(parent, message=message,
                        defaultFile=default,
                        wildcard=wildcard,
                        style=wx.SAVE|wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        out = dlg.GetPath()
    dlg.Destroy()
    return out


def set_float(val, default=0):
    """ utility to set a floating value,
    useful for converting from strings """
    if val in (None, ''):
        return default
    try:
        return float(val)
    except ValueError:
        return default

class FloatCtrl(wx.TextCtrl):
    """ Numerical Float Control::
    a wx.TextCtrl that allows only numerical input, can take a precision argument
    and optional upper / lower bounds
    Options:

    """
    def __init__(self, parent, value='', minval=None, maxval=None,
                 precision=3, bell_on_invalid = True,
                 action=None, action_kw=None, **kws):

        self.__digits = '0123456789.-'
        self.__prec   = precision
        if precision is None:
            self.__prec = 0
        self.format   = '%%.%if' % self.__prec
        self.is_valid = True
        self.__val = set_float(value)
        self.__max = set_float(maxval)
        self.__min = set_float(minval)
        self.__bound_val = None
        self.__mark = None
        self.__action = None

        self.fgcol_valid   = "Black"
        self.bgcol_valid   = "White"
        self.fgcol_invalid = "Red"
        self.bgcol_invalid = (254, 254, 80)
        self.bell_on_invalid = bell_on_invalid

        # set up action
        if action_kw is None:
            action_kw = {}
        self.SetAction(action, **action_kw)

        this_sty =  wx.TE_PROCESS_ENTER|wx.TE_RIGHT
        if 'style' in kws:
            this_sty = this_sty | kws['style']
        kws['style'] = this_sty

        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, **kws)

        self.__CheckValid(self.__val)
        self.SetValue(self.__val)

        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_TEXT, self.OnText)

        self.Bind(wx.EVT_SET_FOCUS,  self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.__GetMark()

    def SetAction(self, action, **kws):
        "set callback action"
        if hasattr(action,'__call__'):
            self.__action = Closure(action, **kws)

    def SetPrecision(self, prec=0):
        "set precision"
        self.__prec = prec
        self.format = '%%.%if' % prec

    def __GetMark(self):
        " keep track of cursor position within text"
        try:
            self.__mark = min(wx.TextCtrl.GetSelection(self)[0],
                              len(wx.TextCtrl.GetValue(self).strip()))
        except:
            self.__mark = 0

    def __SetMark(self, mark=None):
        "set mark for later"
        if mark is None:
            mark = self.__mark
        self.SetSelection(mark, mark)

    def SetValue(self, value=None, act=True):
        " main method to set value "
        if value is None:
            value = wx.TextCtrl.GetValue(self).strip()
        self.__CheckValid(value)
        self.__GetMark()
        if value is not None:
            wx.TextCtrl.SetValue(self, self.format % set_float(value))

        if self.is_valid and hasattr(self.__action, '__call__') and act:
            self.__action(value=self.__val)
        elif not self.is_valid and self.bell_on_invalid:
            wx.Bell()

        self.__SetMark()

    def OnKillFocus(self, event):
        "focus lost"
        self.__GetMark()
        event.Skip()

    def OnSetFocus(self, event):
        "focus gained - resume editing from last mark point"
        self.__SetMark()
        event.Skip()

    def OnChar(self, event):
        """ on Character event"""
        key   = event.GetKeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        pos   = wx.TextCtrl.GetSelection(self)
        # really, the order here is important:
        # 1. return sends to ValidateEntry
        if key == wx.WXK_RETURN:
            if not self.is_valid:
                wx.TextCtrl.SetValue(self, self.format % set_float(self.__bound_val))
            else:
                self.SetValue(entry)
            return

        # 2. other non-text characters are passed without change
        if (key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255):
            event.Skip()
            return

        # 3. check for multiple '.' and out of place '-' signs and ignore these
        #    note that chr(key) will now work due to return at #2

        has_minus = '-' in entry
        ckey = chr(key)
        if ((ckey == '.' and (self.__prec == 0 or '.' in entry) ) or
            (ckey == '-' and (has_minus or  pos[0] != 0)) or
            (ckey != '-' and  has_minus and pos[0] == 0)):
            return
        # 4. allow digits, but not other characters
        if chr(key) in self.__digits:
            event.Skip()
            return
        # return without event.Skip() : do not propagate event
        return

    def OnText(self, event=None):
        "text event"
        try:
            if event.GetString() != '':
                self.__CheckValid(event.GetString())
        except:
            pass
        event.Skip()

    def GetValue(self):
        if self.__prec > 0:
            return set_float(fpformat.fix(self.__val, self.__prec))
        else:
            return int(self.__val)

    def GetMin(self):
        "return min value"
        return self.__min

    def GetMax(self):
        "return max value"
        return self.__max

    def SetMin(self, val):
        "set min value"
        self.__min = set_float(val)

    def SetMax(self, val):
        "set max value"
        self.__max = set_float(val)

    def __CheckValid(self, value):
        "check for validity of value"
        val = self.__val
        self.is_valid = True
        try:
            val = set_float(value)
            if self.__min is not None and (val < self.__min):
                self.is_valid = False
                val = self.__min
            if self.__max is not None and (val > self.__max):
                self.is_valid = False
                val = self.__max
        except:
            self.is_valid = False
        self.__bound_val = self.__val = val
        fgcol, bgcol = self.fgcol_valid, self.bgcol_valid
        if not self.is_valid:
            fgcol, bgcol = self.fgcol_invalid, self.bgcol_invalid

        self.SetForegroundColour(fgcol)
        self.SetBackgroundColour(bgcol)
        self.Refresh()
