
from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash, Response)

from werkzeug import secure_filename

import sys
import os
import time
import json
import base64
import io

import numpy as np

from xasdb import XASDataLibrary, fmttime
import larch
from utils import (get_session_key, random_string,
                   session_init, parse_spectrum,
                   spectrum_ratings)
from plot import make_xafs_plot

# configuration
UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'xdi'])

NAME = 'XASDB'
DATABASE = 'example.db'
PORT     = 7112
DEBUG    = True
SECRET_KEY = get_session_key()

t0 = time.time()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

print 'Flask App created ', time.time()-t0
db = XASDataLibrary(DATABASE, server='sqlite')

print 'XASDB connected ', time.time()-t0

_larch = larch.Interpreter()
print 'Larch initialized ', time.time()-t0

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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
        person = db.get_person(email)
        session['person_id'] = "-1"
        if person is None:
            error = 'Invalid username'
        else:
            if not db.test_person_password(email, password):
                error = 'Invalid password'
            else:
                session['person_id'] = "%i" % person.id
                session['username'] = request.form['username']
                session['logged_in'] = True
                return redirect(url_for('search'))

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session_init(session, db)
    session.pop('username', None)
    session['person_id'] = None
    flash('You have been logged out')
    return redirect(url_for('search'))

@app.route('/user/')
def user():
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

    spectra = []
    for s in dbspectra:
        edge     = session['edges']['%i' % s.edge_id]
        elem_sym = session['elements']['%i' % s.element_z][0]
        person   = session['people']['%i' % s.person_id]

        spectra.append({'id': s.id,
                    'name': s.name,
                    'element': elem,
                    'edge': edge,
                    'person_email': person[0],
                    'person_name': person[1],
                    'elem_sym': elem_sym})

    return render_template('ptable.html', nspectra=len(dbspectra),
                           elem=elem, spectra=spectra)

@app.route('/spectrum/<int:sid>')
def spectrum(sid=None):
    session_init(session, db)
    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)
    opts['spectrum_owner'] = (session['person_id'] == "%i" % s.person_id)

    ratings = spectrum_ratings(db, sid)
    opts['rating'] = 'No ratings'

    if len(ratings) > 0:
        sum = 0.0
        for rate in ratings: sum = sum + rate[0]
        rating = sum*1.0/len(ratings)
        opts['rating'] = 'Average rating %.1f (%i ratings)' % (rating, len(ratings))

    if True: # try:
        energy = np.array(json.loads(s.energy))
        i0     = np.array(json.loads(s.i0))
        itrans = np.array(json.loads(s.itrans))
        mutrans = -np.log(itrans/i0)
    else: # except:
        error = 'Could not extract data from spectrum'
        return render_template('spectrum.html', **opts)

    opts['fullfig'] = make_xafs_plot(energy, mutrans, s.name, ylabel='Raw XAFS')

    eunits = opts['energy_units']
    if eunits.startswith('keV'):
        energy = energy /1000.0
    elif eunits.startswith('deg'):
        print 'Need to convert angle to energy'

    group = larch.Group(energy=energy, mu=mutrans)
    gname = 'data_%s' % random_string(6)

    _larch.symtable.set_symbol(gname, group)
    _larch.run('pre_edge(%s)' % gname)

    opts['e0'] = e0 = group.e0

    try:
        cmd = "tmp_e0 = xray_edge(%i, '%s')[0]" % (s.element_z, str(opts['edge']))
        _larch.run(cmd)
        e0 = _larch.symtable.tmp_e0
    except:
        pass

    i1 = max(np.where(group.energy<=e0 - 30)[0])
    i2 = max(np.where(group.energy<=e0 + 70)[0]) + 1
    xanes_en = group.energy[i1:i2] - e0
    xanes_mu = group.norm[i1:i2]
    opts['e0'] = '%f' % e0
    opts['xanesfig'] = make_xafs_plot(xanes_en, xanes_mu, s.name,
                                      xlabel='Energy-%.1f (eV)' % e0,
                                      ylabel='Normalized XANES', x0=e0)
    return render_template('spectrum.html', **opts)

@app.route('/showspectrum_rating/<int:sid>')
def showspectrum_rating(sid=None):
    session_init(session, db)
    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)
    ratings = []
    for score, review, dtime, pid in spectrum_ratings(db, sid):

        person = session['people'][pid]
        ratings.append({'score': score, 'review': review,
                        'date': fmttime(dtime),
                        'person_email': person[0],
                        'person_name': person[1],
                        'person_affil': person[2]})

    return render_template('show_spectrum_ratings.html',
                           ratings=ratings,
                           spectrum_name=opts['spectrum_name'])

@app.route('/editspectrum/<int:sid>')
def editspectrum(sid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to edit spectrum'
        return render_template('search', error=error)

    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)
    return render_template('editspectrum.html', error=error, **opts)

@app.route('/submit_spectrum_rating', methods=['GET', 'POST'])
def submit_spectrum_rating(sid=None):
    session_init(session, db)
    error=None

    if not session['logged_in']:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', sid=sid, error=error))

    if request.method == 'POST':
        score = request.form['score']
        review = request.form['review']
        spectrum_id = request.form['spectrum']
        spectrum_name = request.form['spectrum_name']
        person_id = request.form['person']
        message = 'Review saved!'
        db.set_spectrum_rating(int(person_id),
                               int(spectrum_id),
                               int(score), comments=review)

        return redirect(url_for('spectrum', sid=spectrum_id))

    return render_template('ratespectrum.html', error=error,
                           spectrum_id=spectrum_id,
                           spectrum_name=spectrum_name,
                           person_id=session['person_id'],
                           score=score, review=review)


@app.route('/rate_spectrum/')
@app.route('/rate_spectrum/<int:sid>')
def rate_spectrum(sid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', sid=sid, error=error))

    s  = db.get_spectrum(sid)
    if s is None:
        error = 'Could not find Spectrum #%i' % sid
        return render_template('ptable', error=error)

    opts = parse_spectrum(s, session)
    score = 1
    review = '<review>'
    for _s, _r, _d, _p in spectrum_ratings(db, sid):
        if _p == session['person_id']:
            score = _s
            review =  _r
    spectrum_id = s.id
    spectrum_name = s.name

    return render_template('ratespectrum.html', error=error,
                           spectrum_id=spectrum_id,
                           spectrum_name=spectrum_name,
                           person_id=session['person_id'],
                           score=score, review=review)



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


@app.route('/suites')
@app.route('/suites/<int:sid>')
def suites():
    session_init(session, db)

    return render_template('suites.html')

@app.route('/beamlines')
@app.route('/beamlines/<int:sid>')
def beamlines():
    session_init(session, db)
    return render_template('about.html')

@app.route('/upload')
@app.route('/upload/')
def upload():
    session_init(session, db)
    if not session['logged_in']:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('spectrum', sid=sid, error=error))
    return render_template('upload.html',
                           person_id=session['person_id'])

@app.route('/submit_upload', methods=['GET', 'POST'])
def submit_upload():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('spectrum', sid=sid, error=error))

    if request.method == 'POST':
        person_id = request.form['person']
        person_email = session['people'][person_id][0]
        file = request.files['file']

        file_ok = False

        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            fullpath = os.path.abspath(os.path.join(
                app.config['UPLOAD_FOLDER'], fname))

            try:
                file.save(fullpath)
                file_ok = True
            except IOError:
                print 'Could not save file ', fullpath

            if file_ok:
                time.sleep(0.5)
                db.add_xdifile(fullpath, person=person_email,
                               create_sample=True)
                time.sleep(0.5)

                session.pop('samples')
                session_init(session, db)

            s  = db.get_spectra()[-1]
            sid = s.id
            if s is None:
                error = 'Could not find Spectrum #%i' % sid
                return render_template('search', error=error)

        opts = parse_spectrum(s, session)
        return render_template('editspectrum.html', error=error, **opts)

    return render_template('upload.html', error='upload error')

if __name__ == "__main__":
    # app.jinja_env.cache = {}
    print 'Server Ready ', app, time.ctime()
    app.run(port=7112)
