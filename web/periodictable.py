CSSData ="""<style type='text/css'>pre {text-indent: 20px}
h5 {font:bold 14px verdana,arial,sans-serif;color:#042264;}
h4 {font:bold 18px verdana,arial,sans-serif;color:#042264;}
h3 {font:bold 18px verdana,arial,sans-serif;color:#A42424;font-weight:bold;font-style:italic;}
h2 {font:bold 22px verdana,arial,sans-serif;color:#044484;font-weight:bold;}
.h5font {font:bold 14px verdana,arial,sans-serif;color:#042264;}
.h4font {font:bold 18px verdana,arial,sans-serif;color:#042264;}
.h3font {font:bold 18px verdana,arial,sans-serif;color:#A42424;font-weight:bold;font-style:italic;}

#ptable {background:#FCFCFC;}
#pelem {font-family: monospace,sans-serif; font-size: 16pt; font-weight:bold;background:#F8F8D8;}
#pelem a, a.active {color: #4444AA; solid #880000; text-decoration: none; }
#pelem a:hover {color: #CC0000;}
#grayentry {color:#B0B0B0;}

.xx {font-size: 3pt;}
body {margin:10px; padding:0px;background:#FCFCFC; font:bold 14px verdana, arial, sans-serif;}
#content {text-align:justify;  background:#FCFCFC; padding: 0px;border:4px solid #88000;
          border-top: none;  z-index: 2; }
#tabmenu {font: bold 11px verdana, arial, sans-serif;
          border-bottom: 2px solid #880000; margin: 1px; padding: 0px 0px 4px 0px; padding-left: 20px;}
#tabmenu li {display: inline;overflow: hidden;margin: 1px;list-style-type: none; }
#tabmenu a, a.active {color: #4444AA;background: #EEDD88;border: 2px solid #880000;
             padding: 3px 3px 4px 3px;margin: 0px ;text-decoration: none; }
#tabmenu a.active {color: #CC0000;background: #FCFCEA;border-bottom: 2px solid #FCFCEA;}
#tabmenu a:hover {color: #CC0000; background: #F9F9E0;}
#time {font: bold 12px verdana, arial, sans-serif; border: 2px; color: #4444AA; margin: 1px;}
</style>
"""

PTable = """<form action='%s'  method="post">
<table  cellpadding=0><tr>
<tr><th colspan=6><input type="submit" name="submit" value= "Absorption Lengths of Compounds"></th>
    <th colspan=6><input type="submit" name="submit" value= "Edge and Emission Energies"></th>
    <th colspan=6><input type="submit" name="submit" value= "Ion Chamber Attenuation"></th>
    </tr>
<th><input id="ptable" type="submit" name="elem" value= "H "><br>
<th colspan=16>
<th><input id="ptable" type="submit" name="elem" value= "He"><br>
</tr><tr>
<th><input id="ptable" type="submit" name="elem" value= "Li"><br>
<th><input id="ptable" type="submit" name="elem" value= "Be"><br>
<th colspan=10>
<th><input id="ptable" type="submit" name="elem" value= "B "><br>
<input type=hidden name='form_elem'    value='%%s'>
</table></form>
"""

def make_ptable(mainlink='.', form_action='action', linkargs='', **kws):
    "code to generate Periodic Table Form"
    out = []
    add = out.append
    def show_elem(sym):
        ssym = ("%s " % sym.title())[:2]
        add('<th id="elem" width=35><a href="%s/%s">%s</a></th>' % (mainlink, ssym, ssym))
    def colspan(n):
        add("<th colspan=%i></th>" % n)
    def nextrow():
        add("</tr><tr>")

    add('<form action="%s"  method="post">' % form_action)
    add('<table id="ptable" cellpadding=0 cellspacing=0 border=0><tr>')
    show_elem('H')
    colspan(16)
    show_elem('He')
    nextrow()
    for s in ('Li','Be'):
        show_elem(s)
    colspan(10)
    for s in ('B','C','N','O','F','Ne'):
        show_elem(s)
    nextrow()
    for s in ('Na','Mg'):
        show_elem(s)
    colspan(10)
    for s in ('Al','Si','P','S','Cl','Ar'):
        show_elem(s)
    nextrow()
    rows = ((0,('K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni',
                'Cu','Zn','Ga','Ge','As','Se','Br','Kr')),
            (0,('Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd',
                'Ag','Cd','In','Sn','Sb','Te','I','Xe')),
            (0,('Cs','Ba','La','Hf','Ta','W','Re','Os','Ir',
                'Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn')),
            (0,('Fr','Ra','Ac')),
            (3,('Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy',
                'Ho','Er','Tm','Yb','Lu')),
            (3,('Th','Pa','U' ,'Np','Pu','Am','Cm','Bk','Cf',
                    'Es','Fm','Md','No','Lr')))

    for indent,elist in rows:
        if indent > 0: colspan(indent)
        for s in elist: show_elem(s)
        nextrow()

    add("</table>")
    return '\n'.join(out)
