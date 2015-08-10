
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

import xasdb
import larch
from utils import get_session_key, random_string, session_init, dict_repr
from plot import make_xafs_plot

# configuration
DATABASE = 'example.db'
PORT     = 7112
DEBUG    = True
SECRET_KEY = get_session_key()

app = Flask(__name__)
app.config.from_object(__name__)

db = xasdb.connect_xasdb(DATABASE)
_larch = larch.Interpreter()


@app.route('/')
def index():
    session_init(session, db)
    return redirect(url_for('search'))

@app.route('/login/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init(session, db)
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
    session_init(session, db)
    session.pop('username', None)
    flash('You have been logged out')
    return redirect(url_for('search'))

@app.route('/user/')
def user_profile():
    # show the user profile for that user
    session_init(session, db)
    if 'username' not in session:
        return 'Not logged in'

    return 'User %s' % session['username']

@app.route('/search/')
@app.route('/search/<elem>')
def search(elem=None):
    session_init(session, db)
    dbspectra = []
    if elem is not None:
        try:
            dbspectra = db.get_spectra(element=elem)
        except:
            pass

    out = []
    for s in dbspectra:
        edge     = session['edges']['%i' % s.edge_id]
        elem_sym = session['elements']['%i' % s.element_z][0]
        person   = session['people']['%i' % s.person_id]

        out.append({'id': s.id,
                    'name': s.name,
                    'element': elem,
                    'edge': edge,
                    'person_email': person[0],
                    'person_name': person[1],
                    'elem_sym': elem_sym})

    return render_template('ptable.html', nspectra=len(dbspectra),
                           elem=elem, spectra=out)

@app.route('/spectrum/<int:sid>')
def spectrum(sid=None):
    session_init(session, db)
    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)

    edge = session['edges']['%i' % s.edge_id]
    elem = session['elements']['%i' % s.element_z]
    person = session['people']['%i' % s.person_id]

    eunits = session['energy_units']['%i'% s.energy_units_id]
    dspace = '%f'% s.d_spacing
    
    notes =  json.loads(s.notes)

    try:
        beamline = session['beamlines']['%i'% s.beamline_id]
    except:
        beamline = 'unknown -- check notes'
        if 'beamline' in notes:
            beamline = notes['beamline']
            if 'name' in beamline:
                beamline = beamline['name']
            
    try:
        sample = session['sample']['%i'% s.sample_id]
        sample_name = sample[0]
        sample_formula = sample[1]
    except:
        sample_name = 'unknown'
        sample_formula = 'unknown'
        if 'sample' in notes:
            sample_name = notes['sample']
            if isinstance(sample_name, dict):
                sample_name = dict_repr(sample_name)

    mononame = 'unknown'
    if 'mono' in notes:
        if 'name' in notes['mono']:
            mononame = notes['mono']['name']

    notes.pop('column')
    notes.pop('scan')
    notes.pop('element')

    misc = []
    for key, val in notes.items():
        if isinstance(val, dict):
            val = dict_repr(val)
        misc.append({'key': "# %s" % key.title(), 'val': val})
   

    opts = {'spectrum_id': s.id,
            'spectrum_name': s.name,
            'elem_sym': elem[0],
            'elem_name': elem[1],
            'edge': edge,
            'energy_units': eunits,
            'beamline': beamline,
            'mononame': mononame, 
            'dspace': dspace,
            'misc': misc,
            'sample_name':  sample_name,
            'sample_formula':  sample_formula,
            'person_email': person[0],
            'person_name': person[1],
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


    if eunits.startswith('keV'):
        energy = energy /1000.0
    elif eunits.startswith('deg'):
        print 'Need to convert angle to energy'
        
    group = larch.Group(energy=energy, mu=mutrans)
    gname = 'data_%s' % random_string(6)

    _larch.symtable.set_symbol(gname, group)
    _larch.run('pre_edge(%s)' % gname)

    try:
        cmd = "ne0 = xray_edge(%i, '%s')[0]" % (s.element_z, str(edge))
        _larch.run(cmd)
        e0 = _larch.symtable.ne0
    except:
        e0 = group.e0

    opts['e0'] = group.e0

    i1 = max(np.where(group.energy<=e0 - 30)[0])
    i2 = max(np.where(group.energy<=e0 + 70)[0]) + 1
    xanes_en = group.energy[i1:i2] - e0
    xanes_mu = group.norm[i1:i2]
    opts['e0'] = '%f' % e0
    opts['xanesfig'] = make_xafs_plot(xanes_en, xanes_mu, s.name,
                                      xlabel='Energy-%.1f (eV)' % e0,
                                      ylabel='Normalized XANES', x0=e0)

    return render_template('spectrum.html', **opts)

@app.route('/rawfile/<int:sid>/<fname>')
def rawfile(sid, fname):
    session_init(session, db)
    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)
    return Response(s.filetext, mimetype='text/plain')

@app.route('/about')
@app.route('/about/')
def about():
    session_init(session, db)
    return render_template('about.html')

if __name__ == "__main__":
    app.jinja_env.cache = {}
    print 'Ready ', app, time.ctime()
    app.run(port=7112)
