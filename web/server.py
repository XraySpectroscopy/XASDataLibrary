
from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash, Response)
import sys
import os
import time
import json
import base64
import io
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

from random import randrange
from string import printable

import xasdb
import larch
from utils import get_session_key

# configuration
DATABASE = 'example.db'
PORT     = 7112
DEBUG    = True
SECRET_KEY = get_session_key()

mpl_lfont = FontProperties()
mpl_lfont.set_size(9)
mpl_sfont = FontProperties()
mpl_sfont.set_size(7)
rcParams['xtick.labelsize'] =  rcParams['ytick.labelsize'] = 7

app = Flask(__name__)
app.config.from_object(__name__)

db = xasdb.connect_xasdb(DATABASE)
_larch = larch.Interpreter()

def random_string(n):
    """  random_string(n)
    generates a random string of length n, that will match
       [a-z](n)
    """
    return ''.join([printable[randrange(10,36)] for i in range(n)])

def make_xafs_plot(x, y, title, xlabel='Energy (eV)', ylabel='mu', x0=None):
    fig  = plt.figure(figsize=(4.0, 2.5), dpi=100)
    axes = fig.add_axes([0.16, 0.16, 0.75, 0.75], axisbg='#FEFEFE')

    axes.set_xlabel(xlabel, fontproperties=mpl_lfont)
    axes.set_ylabel(ylabel, fontproperties=mpl_lfont)
    axes.set_title(title, fontproperties=mpl_lfont)
    axes.plot(x, y, linewidth=2)
    if x0 is not None:
        axes.axvline(0, ymin=min(y), ymax=max(y),
                     linewidth=1, color='#CCBBDD', zorder=-20)
        # ymax = (0.7*max(y) + 0.3 * min(y))
        # axes.text(-25.0, ymax, "%.1f eV" % x0, fontproperties=mpl_lfont)

    axes.set_xlim((min(x), max(x)), emit=True)

    figdata = io.BytesIO()
    plt.savefig(figdata, format='png', facecolor='#F9F9F9')
    figdata.seek(0)
    return base64.b64encode(figdata.getvalue())

def session_init():
    if 'username' not in session:
        session['username'] = None
    if 'logged_in' not in session:
        session['logged_in'] = False
    if 'elements' not in session:
        elems = {}
        for e in db.get_elements():
            elems["%i" % e.z]  = (e.symbol, e.name)
        session['elements'] = elems
    if 'edges' not in session:
        edges = {}
        for e in db.get_edges():
            edges["%i"% e.id]  = e.name
        session['edges'] = edges
    if 'spectra' not in session:
        session['spectra'] = []
    if 'spectrum' not in session:
        session['spectrum'] = None

def get_persons():
    persons = {}
    for p in db.get_persons():
        persons[p.id]  = (p.email, p.name)
    return persons


@app.route('/')
def index():
    session_init()
    return redirect(url_for('search'))

@app.route('/login/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init()
    error = None
    if session['username'] is not None:
        return redirect(url_for('search'))
    elif request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        if db.get_person(email) is None:
            error = 'Invalid username'
        else:
            if not db.test_person_password(email, password):
                error = 'Invalid password'
            else:
                session['username'] = request.form['username']
                session['logged_in'] = True
                return redirect(url_for('search'))

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session_init()
    session.pop('username', None)
    flash('You have been logged out')
    return redirect(url_for('search'))

@app.route('/user/')
def user_profile():
    # show the user profile for that user
    session_init()
    if 'username' not in session:
        return 'Not logged in'

    return 'User %s' % session['username']

@app.route('/search/')
@app.route('/search/<elem>')
def search(elem=None):
    session_init()
    dbspectra = []
    if elem is not None:
        try:
            dbspectra = db.get_spectra(element=elem)
        except:
            pass

    persons = get_persons()
    out = []
    for s in dbspectra:
        edge = session['edges']["%i" % s.edge_id]
        elem_sym, elem_name = session['elements']["%i" % s.element_z]
        person_email, person_name = persons[s.person_id]

        out.append({'id': s.id,
                    'name': s.name,
                    'element': elem,
                    'edge': edge,
                    'person_email': person_email,
                    'person_name': person_name,
                    'elem_sym': elem_sym})

    return render_template('ptable.html', nspectra=len(dbspectra),
                           elem=elem, spectra=out)

@app.route('/spectrum/<int:sid>')
def spectrum(sid=None):
    session_init()

    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)

    edge = session['edges']["%i" % s.edge_id]
    elem_sym, elem_name = session['elements']["%i" % s.element_z]

    persons = get_persons()
    person_email, person_name = persons[s.person_id]


    opts = {'spectrum_id': s.id,
            'spectrum_name': s.name,
            'element': elem_name,
            'edge': edge,
            'person_email': person_email,
            'person_name': person_name,
            'elem_sym': elem_sym,
            'upload_date': s.submission_date.strftime('%Y-%m-%d %H:%M:%S'),
            'collection_date': s.collection_date.strftime('%Y-%m-%d %H:%M:%S'),
            'fullfig': None, 'xanesfig': None,
            }

    try:
        energy = np.array(json.loads(s.energy))
        i0     = np.array(json.loads(s.i0))
        itrans = np.array(json.loads(s.itrans))
        mutrans = -np.log(itrans/i0)
    except:
        error = 'Could not extract data from spectrum'
        return render_template('spectrum.html', **opts)

    opts['fullfig'] = make_xafs_plot(energy, mutrans, s.name, ylabel='Raw XAFS')

    cmd = "ne0 = xray_edge(%i, '%s')[0]" % (s.element_z, str(edge))
    _larch.run(cmd)
    e0 = _larch.symtable.ne0

    group = larch.Group(energy=energy, mu=mutrans)
    gname = 'data_%s' % random_string(6)
    _larch.symtable.set_symbol(gname, group)
    _larch.run("pre_edge(%s)" % gname)

    i1 = max(np.where(group.energy<=e0 - 30)[0])
    i2 = max(np.where(group.energy<=e0 + 70)[0]) + 1
    xanes_en = group.energy[i1:i2] - e0
    xanes_mu = group.norm[i1:i2]
    opts['e0'] = "%f" % e0
    opts['xanesfig'] = make_xafs_plot(xanes_en, xanes_mu, s.name,
                                      xlabel='Energy-%.1f (eV)' % e0,
                                      ylabel='Normalized XANES', x0=e0)

    return render_template('spectrum.html', **opts)

@app.route('/rawfile/<int:sid>/<fname>')
def rawfile(sid, fname):
    session_init()
    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)
    return Response(s.filetext, mimetype='text/plain')

@app.route('/about')
@app.route('/about/')
def about():
    session_init()
    return render_template('about.html')

if __name__ == "__main__":
    app.jinja_env.cache = {}
    print 'Ready ', app
    app.run(port=7112)
