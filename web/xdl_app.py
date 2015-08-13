#!/usr/bin/env python

import sys
import os
import time

t0 = time.time()

import json
import base64
import numpy as np

from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash, Response)

from werkzeug import secure_filename

import larch

from xasdb import XASDataLibrary, fmttime, valid_score, unique_name


from utils import (get_session_key, random_string, multiline_text,
                   session_init, session_clear,
                   parse_spectrum, spectrum_ratings, suite_ratings,
                   spectra_for_suite, spectra_for_beamline)

from plot import make_xafs_plot

# configuration
UPLOAD_FOLDER = '/tmp/'
if os.name =='nt':
    UPLOAD_FOLDER = 'C:/tmp/'
ALLOWED_EXTENSIONS = set(['XDI', 'xdi'])

NAME = 'XASDB'
DATABASE = 'example.db'
PORT     = 7112
DEBUG    = True
SECRET_KEY = get_session_key()

print 'Imports done %.1f sec ' % (time.time()-t0)

app = Flask(__name__)
app.config.from_object(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

print 'Flask app created %.1f sec ' % (time.time()-t0)
db = XASDataLibrary(DATABASE, server='sqlite')
print 'XASDB connected %.1f sec ' % (time.time()-t0)

_larch = larch.Interpreter()
print 'Larch Interpreter connected %.1f sec ' % (time.time()-t0)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html')
    
@app.route('/')
def index():
    session_init(session, db)
    return redirect(url_for('search'))

@app.route('/clear')
def clear():
    session_init(session, db)
    session_clear(session)
    return redirect(url_for('search'))

@app.route('/create_account/')
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    session_init(session, db)
    error = None
    if request.method == 'POST':
        email = request.form['email']
        name  = request.form['name']
        affiliation = request.form['affiliation']
        password = request.form['password']
        password2 = request.form['password2']
        person = db.get_person(email)
        # log in existing
        if person is not None:
            error = "Account with email '%s' exists" % email
        else:
            if len(name) < 6:
                error = 'Must give a valid name (at least 5 characters)'
            elif '@' not in email or '.' not in email or len(email) < 10:
                error = 'Must give a valid email address'
            elif len(password)<5:
                error = 'password must be at least 5 characters long'
            elif password != password2:
                error = 'passwords must match.'
            else:    
                db.add_person(name, email, password=password,
                              affiliation=affiliation)
                flash('Account created for %s' % email)                    
                return render_template('login.html', error=error)
            
    return render_template('create_account.html', error=error)

@app.route('/login/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init(session, db)
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        person = db.get_person(email)
        session['person_id'] = "-1"
        if person is None:
            error = 'Invalid email'
        else:
            if not db.test_person_password(email, password):
                error = 'Invalid password'
            else:
                session['person_id'] = "%i" % person.id
                session['username'] = request.form['email']
                session['logged_in'] = True
                session.pop('people')
                return redirect(url_for('search'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session_init(session, db)
    session.pop('username', None)
    session['person_id'] = None
    session['logged_in'] = False
    flash('You have been logged out')
    return redirect(url_for('search'))

@app.route('/user/')
def user():
    # show the user profile for that user
    session_init(session, db)
    error = None
    if 'username' not in session or not session['logged_in']:
        error = 'Not logged in'
        email, name, affiliation = '', '', ''
    else:
        email = session['username']
        person = db.get_person(email)
        name = person.name
        affiliation = person.affiliation
    
    return render_template('userprofile.html', error=error, email=email,
                           name=name, affiliation=affiliation)

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


@app.route('/spectrum/<int:spid>')
def spectrum(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)
    opts['spectrum_owner'] = (session['person_id'] == "%i" % s.person_id)

    ratings = spectrum_ratings(db, spid)
    opts['rating'] = 'No ratings'

    if len(ratings) > 0:
        sum = 0.0
        for rate in ratings: sum = sum + rate[0]
        rating = sum*1.0/len(ratings)
        opts['rating'] = 'Average rating %.1f (%i ratings)' % (rating, len(ratings))

    try:
        energy = np.array(json.loads(s.energy))
        i0     = np.array(json.loads(s.i0))
        itrans = np.array(json.loads(s.itrans))
        mutrans = -np.log(itrans/i0)
    except:
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

    suites = []
    for r in db.filtered_query('spectrum_suite', spectrum_id=s.id):
        suites.append({'id': r.suite_id,
                       'name': session['suites']["%i" % (r.suite_id)][0]})
    opts['nsuites'] = len(suites)
    opts['suites'] = suites
    return render_template('spectrum.html', **opts)

@app.route('/showspectrum_rating/<int:spid>')
def showspectrum_rating(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)
    ratings = []
    for score, review, dtime, pid in spectrum_ratings(db, spid):
        person = session['people'][pid]
        ratings.append({'score': score, 'review': multiline_text(review),
                        'date': fmttime(dtime),
                        'person_email': person[0],
                        'person_name': person[1],
                        'person_affil': person[2]})

    return render_template('show_spectrum_ratings.html',
                           ratings=ratings,
                           spectrum_name=opts['spectrum_name'])


@app.route('/submit_spectrum_edits', methods=['GET', 'POST'])
def submit_spectrum_edits():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to edit spectrum'
        return render_template('search', error=error)
    if request.method == 'POST':
        spid  = int(request.form['spectrum'])
        db.update('spectrum', int(spid),
                  name=request.form['name'],
                  comments=request.form['comments'],
                  d_spacing=float(request.form['d_spacing']),
                  edge_id= int(request.form['edge']),
                  beamline_id= int(request.form['beamline']),
                  sample_id= int(request.form['sample']),
                  energy_units_id=int(request.form['energy_units']))
                  
        time.sleep(0.25)
        
    return redirect(url_for('spectrum', spid=spid, error=error))        

@app.route('/editspectrum/<int:spid>')
def editspectrum(spid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to edit spectrum'
        return render_template('search', error=error)

    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('search', error=error)

    opts = parse_spectrum(s, session)

    for s in session['sample_list']:
        x = '     ' 
        if s['id'] == opts['sample_id']: x = ' Bingo!'
        # print x, s['id'], s['name']
        
    return render_template('editspectrum.html', error=error,
                           elems=session['element_list'],
                           eunits=session['energy_units_list'],
                           edges=session['edge_list'],
                           beamlines=session['beamline_list'],
                           samples=session['sample_list'],
                           **opts)

@app.route('/submit_spectrum_rating', methods=['GET', 'POST'])
def submit_spectrum_rating(spid=None):
    session_init(session, db)
    error=None

    if not session['logged_in']:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', spid=spid, error=error))

    if request.method == 'POST':
        score_is_valid = False
        try:
            score = float(request.form['score'])
            vscore = valid_score(score)
            score_is_valid = ((int(score) == vscore) and
                              (abs(score-int(score)) < 1.e-3))
        except:
            pass

        review = request.form['review']
        sname  = request.form['spectrum_name']
        spid   = int(request.form['spectrum'])
        pid    = int(request.form['person'])

        if score_is_valid:
            db.set_spectrum_rating(pid, spid, vscore, comments=review)
            return redirect(url_for('spectrum', spid=spid))
        else:
            error='score must be an integer:  0, 1, 2, 3, 4, or 5'
            return render_template('ratespectrum.html', error=error,
                                   spectrum_id=spid, spectrum_name=sname,
                                   person_id=pid, score=score,
                                   review=multilne_text(review))

@app.route('/rate_spectrum/')
@app.route('/rate_spectrum/<int:spid>')
def rate_spectrum(spid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', spid=spid, error=error))

    pid = session['person_id']
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable', error=error)

    opts = parse_spectrum(s, session)
    score = 3
    review = '<review>'
    for _s, _r, _d, _p in spectrum_ratings(db, spid):
        if _p == pid:
            score = _s
            review =  _r
    spid = s.id
    spname = s.name

    return render_template('ratespectrum.html', error=error,
                           spectrum_id=spid, spectrum_name=spname,
                           person_id=pid, score=score, review=review)


@app.route('/submit_suite_rating', methods=['GET', 'POST'])
def submit_suite_rating(spid=None):
    session_init(session, db)
    error=None

    if not session['logged_in']:
        error='must be logged in to rate suite'
        return redirect(url_for('suite', spid=spid, error=error))

    if request.method == 'POST':
        score_is_valid = False
        try:
            score = float(request.form['score'])
            vscore = valid_score(score)
            score_is_valid = ((int(score) == vscore) and
                              (abs(score-int(score)) < 1.e-3))
        except:
            pass

        review = request.form['review']
        stname = request.form['suite_name']
        stid   = int(request.form['suite'])
        pid    = int(request.form['person'])

        if score_is_valid:
            db.set_suite_rating(pid, stid, vscore, comments=review)
            return redirect(url_for('suites', spid=spid))
        else:
            error='score must be an integer:  0, 1, 2, 3, 4, or 5'
            return render_template('ratesuite.html', error=error,
                                   suite_id=stid, suite_name=stname,
                                   person_id=pid, score=score,
                                   review=multilne_text(review))

@app.route('/rate_suite/')
@app.route('/rate_suite/<int:stid>')
def rate_suite(stid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to rate suite'
        return redirect(url_for('suites', stid=stid, error=error))

    pid = session['person_id']
    for _id, val in session['suites'].items():
        if _id == "%i" % stid:
            spname, notes, person_id = val

    score = 3
    review = '<review>'
    for _s, _r, _d, _p in suite_ratings(db, stid):
        if _p == pid:
            score = _s
            review =  _r
    
    return render_template('ratesuite.html', error=error,
                           suite_id=stid, suite_name=spname,
                           person_id=pid, score=score, review=review)


@app.route('/showsuite_rating/<int:stid>')
def showsuite_rating(stid=None):
    session_init(session, db)


    for _id, val in session['suites'].items():
        if _id == "%i" % stid:
            stname, notes, _pid = val
    if stname is None:
        error = 'Could not find Suite #%i' % stid
        return render_template('search', error=error)

    ratings = []
    for score, review, dtime, pid in suite_ratings(db, stid):
        person = session['people'][pid]
        ratings.append({'score': score, 'review': multiline_text(review),
                        'date': fmttime(dtime),
                        'person_email': person[0],
                        'person_name': person[1],
                        'person_affil': person[2]})

    return render_template('show_suite_ratings.html',
                           ratings=ratings, suite_notes=notes,
                           suite_name=stname)

@app.route('/add_spectrum_to_suite/<int:spid>')
def add_spectrum_to_suite(spid=None):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to add spectrum to suite'
        return redirect(url_for('spectrum', spid=spid, error=error))

    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable', error=error)

    suites = []
    for key, val in session['suites'].items():
        suites.append({'id': key, 'name': val[0]})

    return render_template('add_spectrum_to_suite.html', error=error,
                           spectrum_id=spid, spectrum_name=s.name,
                           person_id=session['person_id'], suites=suites)

@app.route('/submit_spectrum_to_suite', methods=['GET', 'POST'])
def submit_spectrum_to_suite():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to add spectrum to a suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        spid  = int(request.form['spectrum_id'])
        stid  = int(request.form['suite_id'])
        pid   = request.form['person']

        found = False
        for r in db.filtered_query('spectrum_suite', suite_id=stid):
            found = found or (r.spectrum_id == spid)
        if not found:
            db.addrow('spectrum_suite', suite_id=stid, spectrum_id=spid)
            time.sleep(0.25)
            session.pop('suites')
        else:
            stname = session['suites']['%i' % stid][0]
            spname = session['spectra']['%i' % spid][0]
            error = "Spectrum '%s' is already in Suite '%s'" % (spname, stname)

    return redirect(url_for('suites', error=error))


@app.route('/rawfile/<int:spid>/<fname>')
def rawfile(spid, fname):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('search', error=error)
    return Response(s.filetext, mimetype='text/plain')


@app.route('/about')
@app.route('/about/')
def about():
    session_init(session, db)
    return render_template('about.html')

@app.route('/suites')
@app.route('/suites/<int:stid>')
def suites(stid=None):
    session_init(session, db)
    suites = []
    if stid is None:
        for stid, val in session['suites'].items():
            name, notes, person_id = val
            person_email = session['people'][person_id][0]
            spectra = spectra_for_suite(db, session, stid)

            spectra = spectra_for_suite(db, session ,stid)

            ratings = suite_ratings(db, stid)
            rating  = 'No ratings'

            if len(ratings) > 0:
                sum = 0.0
                for rate in ratings: sum = sum + rate[0]
                rating = sum*1.0/len(ratings)
            rating = 'Average rating %.1f (%i ratings)' % (rating, len(ratings))
            suites.append({'id': stid, 'name': name, 'notes': notes,
                           'person_email': person_email,
                           'rating': rating,
                           'nspectra': len(spectra), 'spectra': spectra})

    else:
        for _id, val in session['suites'].items():
            if _id == "%i" % stid:
                name, notes, person_id = val
        person_email = session['people'][person_id][0]
        spectra = spectra_for_suite(db, session, stid)
        ratings = suite_ratings(db, stid)
        rating  = 'No ratings'
        if len(ratings) > 0:
            sum = 0.0
            for rate in ratings: sum = sum + rate[0]
            rating = sum*1.0/len(ratings)
        rating = 'Average rating %.1f (%i ratings)' % (rating, len(ratings))
            
        suites.append({'id': stid, 'name': name, 'notes': notes,
                       'person_email': person_email, 'rating': rating, 
                       'nspectra': len(spectra), 'spectra': spectra})

    return render_template('suites.html', nsuites=len(suites), suites=suites)

@app.route('/add_suite')
@app.route('/add_suite', methods=['GET', 'POST'])
def add_suite():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to add a suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        suite_name = request.form['suite_name']
        person_id = request.form['person']
        notes = request.form['notes']
        _sname = [s[0] for s in session['suites'].keys()]
        try:
            suite_name = unique_name(suite_name, _sname,  msg='suite')
        except:
            error = 'a suite named %s exists'
        db.add_suite(suite_name, notes=notes, person_id=int(person_id))
        time.sleep(1)
        session.pop('suites')
        return redirect(url_for('suites', error=error))
    else:

        return render_template('add_suite.html', error=error,
                               person_id=session['person_id'])

@app.route('/del_suite/<int:stid>/ask=<int:ask>')
def del_suite(stid, ask=1):
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to delete a suite'
        return redirect(url_for('suites', error=error))

    if ask != 0:
        suite_name = session['suites']['%i' % stid][0]
        return render_template('confirm_del_suite.html', stid=stid,
                               suite_name=suite_name)

    else:
        db.del_suite(stid)
        time.sleep(1)
        session.pop('suites')
    return redirect(url_for('suites', error=error))



@app.route('/beamlines')
@app.route('/beamlines/<int:blid>')
def beamlines(blid=None):
    session_init(session, db)
    beamlines = []
    if blid is None:
        for bldat in session['beamline_list']:
            blid = bldat['id']
            spectra = spectra_for_beamline(db, session, blid)
            opts = {'nspectra': len(spectra), 'spectra': spectra}
            opts.update(bldat)
            beamlines.append(opts)
    else:
        for _bldat in session['beamline_list']:
            if _bldat['id'] == "%i" % blid:
                bldat = _bldat
                break

        spectra = spectra_for_beamline(db, session, blid)
        opts = {'nspectra': len(spectra), 'spectra': spectra}
        opts.update(bldat)
        beamlines.append(opts)

    return render_template('beamlines.html',
                           nbeamlines=len(beamlines), beamlines=beamlines)

@app.route('/add_beamline')
@app.route('/add_beamline', methods=['GET', 'POST'])
def add_beamline():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to add a beamline'
        return redirect(url_for('beamlines', error=error))

    if request.method == 'POST':
        bl_name = request.form['beamline_name']
        _blnames = [s[0] for s in session['beamlines'].keys()]
        try:
            bl_name = unique_name(bl_name, _blnames,  msg='beamline', maxcount=5)
        except:
            error = 'a beamline named %s exists'
        db.add_beamline(bl_name)
        time.sleep(1)
        session.pop('beamines')
        return redirect(url_for('beamlines', error=error))
    else:
        facilities = []
        for key, fac in session['facilities'].items():
            facilities.append({'id': key, 'name': fac[0]})
        return render_template('add_beamline.html', error=error,
                               facilities=facilities)


@app.route('/add_facility')
@app.route('/add_facility', methods=['GET', 'POST'])
def add_facility():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to add a facility'
        return redirect(url_for('beamlines', error=error))

    if request.method == 'POST':
        fac_name = request.form['facility_name']
        _facnames = [s[0] for s in session['facilities'].keys()]
        try:
            fac_name = unique_name(fac_name, _facnames,  msg='facility', maxcoutn=5)
        except:
            error = 'a facility named %s exists'
        db.add_beamline(fac_name)
        time.sleep(1)
        session.pop('facilities')
        return redirect(url_for('facilities', error=error))
    else:
        facilities = []
        for key, fac in session['facilities'].items():
            facilities.append({'id': key, 'name': fac[0]})
        return render_template('add_facility.html', error=error,
                               facilities=facilities)


@app.route('/upload')
@app.route('/upload/')
def upload():
    session_init(session, db)
    if not session['logged_in']:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('search', error=error))
    return render_template('upload.html',
                           person_id=session['person_id'])

@app.route('/submit_upload', methods=['GET', 'POST'])
def submit_upload():
    session_init(session, db)
    error=None
    if not session['logged_in']:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('search', error=error))

    if request.method == 'POST':
        pid    = request.form['person']
        pemail = session['people'][pid][0]
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
                pass

            if file_ok:
                time.sleep(0.5)
                db.add_xdifile(fullpath, person=peemail, create_sample=True)
                time.sleep(0.5)
                session.pop('samples')
                session_init(session, db)

            s  = db.get_spectra()[-1]
            if s is None:
                error = 'Could not find Spectrum #%i' % s.id
                return render_template('search', error=error)

        opts = parse_spectrum(s, session)
        return render_template('editspectrum.html', error=error, **opts)
    return render_template('upload.html', error='upload error')

if __name__ == "__main__":
    # app.jinja_env.cache = {}
    print 'Server Ready %s ' % time.ctime()
    app.run(port=7112)
