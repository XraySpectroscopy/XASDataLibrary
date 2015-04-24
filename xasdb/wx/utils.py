import wx
import string

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


def FileSave(parent, message, wildcard=None):
    "File Save dialog"
    out = None
    dlg = wx.FileDialog(parent, message=message,
                        wildcard=wildcard,
                        style=wx.SAVE|wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        out = dlg.GetPath()
    dlg.Destroy()
    return out

                       
