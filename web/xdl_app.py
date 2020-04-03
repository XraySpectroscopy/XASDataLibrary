#!/usr/bin/env python

import sys
import os
import time

t0 = time.time()

import smtplib

import json
import base64
import numpy as np

from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash, Response,
                   send_from_directory)

try:
    from werkzeug.utils import secure_filename
except ImportError:
    from werkzeug import secure_filename


from xasdb import (connect_xasdb, fmttime, valid_score, unique_name)
from xafs_preedge import (preedge, edge_energies)

from utils import (random_string, multiline_text, session_init,
                   session_clear, parse_spectrum,
                   spectrum_ratings, suite_ratings,
                   spectra_for_suite, beamline_for_spectrum,
                   spectra_for_beamline, get_element_list,
                   get_energy_units_list, get_edge_list,
                   get_beamline_list, get_sample_list, get_rating)


# sys.path.insert(0, '/home/newville/XASDB_Secrets')

from xasdb_secrets import (SECRET_KEY, DBNAME, DBCONN, PORT, DEBUG,
                           UPLOAD_FOLDER, LOCAL_ONLY, ADMIN_EMAIL)

from plot import make_xafs_plot

from sqlalchemy import text

ALLOWED_EXTENSIONS = set(['XDI', 'xdi'])

NAME = 'XASDB'

app = Flask(__name__, static_folder='static')
app.config.from_object(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024


db = connect_xasdb(DBNAME, **DBCONN)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

BASE_URL = 'http://cars.uchicago.edu/ptest' # xaslib'

def send_confirm_email(person, hash, style='new'):
    """send email with account confirmation/reset link"""

    subject = "XAS Library Account Password Reset"
    message = """
        Someone (hopefully you) asked to reset your account for the XAS Spectra Library.

        To change your passowrd, please follow this link:
               %s/newpassword/%i/%s

        Thank you.

""" % (BASE_URL, person.id, hash)

    if style == 'new':
        subject = "XAS Library Account Confirmation"
        message = """
        An account at the XAS Spectra Library has been created for %s, but not yet confirmed.

        To confirm this account, please follow this link:
           %s/confirmaccount/%i/%s

        Thank you.

""" % (person.name, BASE_URL, person.id, hash)

    fullmsg   = "From: %s\r\nTo: %s\r\nSubject: %s\r\n%s\n" % (ADMIN_EMAIL, person.email,
                                                               subject, message)
    s  = smtplib.SMTP('localhost')
    s.sendmail(ADMIN_EMAIL, (person.email, ), fullmsg)
    s.quit()

def notify_account_creation(person):
    """send email to administrator about account creation"""

    subject = "XAS Library Account created"
    message = """
        An account on the XAS Spectra Library was created for user:
          email= %s
          name = %s
""" % (person.email, person.name)

    fullmsg   = "From: %s\r\nTo: %s\r\nSubject: %s\r\n%s\n" % (ADMIN_EMAIL,
                                                               ADMIN_EMAIL,
                                                               subject,
                                                               message)
    s  = smtplib.SMTP('localhost')
    s.sendmail(ADMIN_EMAIL, (person.email, ), fullmsg)
    s.quit()



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'ixas_logo.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html')


@app.route('/clear')
def clear():
    session_init(session, db)
    session_clear(session)
    return redirect(url_for('search'))

@app.route('/')
def index():
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
            if len(name) < 4:
                error = 'Must give a valid name (at least 4 characters)'
            elif '@' not in email or '.' not in email or len(email) < 10:
                error = 'Must give a valid email address'
            elif len(password) < 7:
                error = 'password must be at least 7 characters long'
            elif password != password2:
                error = 'passwords must match.'
            else:
                db.add_person(name, email,
                              password=password,
                              affiliation=affiliation)
                hash = db.person_unconfirm(email)
                if LOCAL_ONLY:
                    db.person_confirm(email, hash)
                else:
                    ## send email here!!
                    person = db.get_person(email)
                    send_confirm_email(person, hash, style='new')
                    return render_template('confirmation_email_sent.html',
                                       email=email, error=error)

    return render_template('create_account.html', error=error)



@app.route('/password_reset_request/')
@app.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    session_init(session, db)
    error = None
    if request.method == 'POST':
        email = request.form['email']
        person = db.get_person(email)
        # log in existing
        if person is None:
            error = "No account with email '%s' exists" % email
        else:
            hash = db.person_unconfirm(email)
            send_confirm_email(person, hash, style='reset')
            return render_template('password_reset_response.html',
                                   email=email, error=error)

    return render_template('password_reset_request.html', error=error)



@app.route('/newpassword/<pid>/<hash>')
def newpassword(pid='-1', hash=''):
    session_init(session, db)
    if pid > 0 and len(hash) > 8:
        pid = int(pid)
        person = db.get_person(pid, key='id')
        email = person.email
        return render_template('newpassword_form.html',
                               hash=hash, email=email)
    return render_template('password_reset_request.html')

@app.route('/setnewpassword/', methods=['GET', 'POST'])
def setnewpassword(pid='-1', hash=''):
    session_init(session, db)

    if request.method == 'POST':

        password = request.form['password']
        password2 = request.form['password2']
        hash      = request.form['hash']
        email     = request.form['email']

        if len(password) < 7:
            error = 'password must be at least 7 characters long'
        elif password != password2:
            error = 'passwords must match.'
        elif not db.person_test_confirmhash(email, hash):
            error = 'password reset was not requested correctly.'
        else:
            db.set_person_password(email, password)
            hash = db.person_unconfirm(email)
            db.person_confirm(email, hash)
            flash("Your password has been reset.")
            error = None
            return render_template('login.html', error=error)

        return render_template('newpassword_form.html', hash=hash,
                               email=email, error=error)

    return render_template('password_reset_request.html')

@app.route('/confirmaccount/<pid>/<hash>')
def confirmaccount(pid='-1', hash=''):
    session_init(session, db)
    error = 'Could not confirm an account with that information'
    if pid > 0 and len(hash) > 8:
        pid = int(pid)
        person = db.get_person(pid, key='id')
        if person is None:
            error = 'Could not locate account'
        elif person.confirmed == 'true':
            error = 'The account for %s is already confirmed' % person.email
        else:
            confirmed = db.person_confirm(person.email, hash)
            if not confirmed:
                error = 'Confirmation key incorrect for %s' % person.email
            else:
                flash('''Congratulations, %s, your account is confirmed.
                You can now log in!''' % person.name)
                # notify
                notify_account_creation(person)

                return render_template('login.html')
    return render_template('confirmation_email_sent.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init(session, db)
    error = None
    session['username'] = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        person = db.get_person(email)
        session['person_id'] = "-1"
        if person is None:
            error = 'Invalid email'
        elif not db.test_person_confirmed(email):
            error = 'Account not confirmed'
        elif not db.test_person_password(email, password):
            error = 'Invalid password'
        else:
            session['person_id'] = "%i" % person.id
            session['username'] = request.form['email']
    if session['username'] is not None:
        return redirect(url_for('search'))
    else:
        return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session_init(session, db)
    session['username'] = None
    session['person_id'] = '-1'
    flash('You have been logged out')
    return redirect(url_for('search'))

@app.route('/user')
@app.route('/user', methods=['GET', 'POST'])
def user():
    # show the user profile for that user
    session_init(session, db)
    error = None
    if request.method == 'POST':
        email = request.form['email']
        name  = request.form['name']
        affiliation = request.form['affiliation']
        person = db.get_person(email)

        ptab = db.tables['person']
        kws = {}
        if name != person.name:
            kws['name'] = name
        if affiliation != person.affiliation:
            kws['affiliation'] = affiliation
        if len(kws) > 1:
            ptab.update(whereclause=text("email='%s'" % email)).execute(**kws)

    elif 'username' not in session:
        error = 'Not logged in'
        email, name, affiliation = '', '', ''
    else:
        email = session['username']
        person = db.get_person(email)
        name = person.name
        affiliation = person.affiliation

    return render_template('userprofile.html', error=error, email=email,
                           name=name, affiliation=affiliation)

@app.route('/search')
@app.route('/search/<elem>')
@app.route('/search/<elem>/<orderby>')
@app.route('/search/<elem>/<orderby>/<reverse>')
def search(elem=None, orderby=None, reverse=0):
    session_init(session, db)
    dbspectra = []
    if orderby is None: orderby = 'id'
    if elem is not None:
        try:
            dbspectra = db.get_spectra(element=elem, orderby=orderby)
        except:
            pass

    reverse = int(reverse)
    if reverse:
        dbspectra.reverse()
        reverse = 0
    else:
        reverse = 1

    spectra = []
    for s in dbspectra:
        edge     = db.get_edge(s.edge_id)
        elem_sym = db.get_element(s.element_z).symbol
        person   = db.get_person(s.person_id)
        bl_id, bl_desc = beamline_for_spectrum(db, s)

        spectra.append({'id': s.id,
                        'name': s.name,
                        'element': elem,
                        'edge': edge.name,
                        'person_email': person.email,
                        'person_name': person.name,
                        'elem_sym': elem_sym,
                        'rating': get_rating(s),
                        'beamline_desc': bl_desc,
                        'beamline_id': bl_id,
                        })

    return render_template('ptable.html', nspectra=len(dbspectra),
                           elem=elem, spectra=spectra,
                           reverse=reverse)


@app.route('/all')
@app.route('/all/')
def all():
    session_init(session, db)
    spectra = []
    dbspectra = db.get_spectra()
    for s in dbspectra:
        edge     = db.get_edge(s.edge_id)
        elem_sym = db.get_element(s.element_z).symbol
        elem     = s.element_z
        person   = db.get_person(s.person_id)

        bl_id, bl_desc = beamline_for_spectrum(db, s)

        spectra.append({'id': s.id,
                        'name': s.name,
                        'element': elem,
                        'edge': edge.name,
                        'person_email': person.email,
                        'person_name': person.name,
                        'elem_sym': elem_sym,
                        'rating': get_rating(s),
                        'beamline_desc': bl_desc,
                        'beamline_id': bl_id,
                        })

    return render_template('ptable.html', nspectra=len(dbspectra),
                           elem='All Elements', spectra=spectra)

@app.route('/spectrum/')
@app.route('/spectrum/<int:spid>')
def spectrum(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable.html', error=error)

    opts = parse_spectrum(s, db)
    opts['spectrum_owner'] = (session['person_id'] == "%i" % s.person_id)
    opts['rating'] = get_rating(s)

    modes = db.get_spectrum_mode(spid)
    if modes is None:
        modes = 1
    else:
        modes = modes[0][1]

    if modes == 1:
        try:
            energy = np.array(json.loads(s.energy))
            i0     = np.array(json.loads(s.i0))
            itrans = np.array(json.loads(s.itrans))
            mutrans = -np.log(itrans/i0)
        except:
            error = 'Could not extract data from spectrum'
            return render_template('spectrum.html', **opts)
    else: #get a fluorescence
        try:
            energy = np.array(json.loads(s.energy))
            i0     = np.array(json.loads(s.i0))
            ifluor = np.array(json.loads(s.ifluor))
            mutrans = ifluor/i0
        except:
            error = 'Could not extract data from spectrum'
            return render_template('spectrum.html', **opts)

    murefer = None
    try:
        irefer = np.array(json.loads(s.irefer))
        murefer = -np.log(irefer/itrans)
    except:
        pass


    eunits = opts['energy_units']
    if eunits.startswith('keV'):
        energy = energy /1000.0
    elif eunits.startswith('deg'):
        print('Need to convert angle to energy')


    if modes != 7:
        group = preedge(energy, mutrans)
        e0 = group['e0']
    try:
        e0 = edge_energies[int(s.element_z)][str(opts['edge'])]
    except:
        pass

    try:
        i1 = max(np.where(energy<=e0 - 25)[0])
    except:
        i1 = 0
    i2 = max(np.where(energy<=e0 + 75)[0]) + 1
    xanes_en = energy[i1:i2] - e0

    if modes !=3:
        xanes_mu = group['norm'][i1:i2]
    else:
        xanes_mu = mutrans[i1:i2]

    xanes_ref = None
    if murefer is not None:
        rgroup = preedge(energy, murefer)
        xanes_ref = rgroup['norm'][i1:i2]

    opts['e0'] = '%f' % e0
    opts['fullfig'] =  make_xafs_plot(energy, mutrans, s.name,
                                      ylabel='Raw XAFS').decode('UTF-8')

    opts['xanesfig'] = make_xafs_plot(xanes_en, xanes_mu, s.name,
                                      xlabel='Energy-%.1f (eV)' % e0,
                                      ylabel='Normalized XANES',
                                      x0=e0, ref_mu=xanes_ref,
                                      ref_name='with reference').decode('UTF-8')

    suites = []
    for r in db.filtered_query('spectrum_suite', spectrum_id=s.id):
        st = db.filtered_query('suite', id=r.suite_id)[0]
        suites.append({'id': r.suite_id, 'name': st.name})
    opts['nsuites'] = len(suites)
    opts['suites'] = suites

    return render_template('spectrum.html', **opts)

@app.route('/showspectrum_rating/<int:spid>')
def showspectrum_rating(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable.html', error=error)

    opts = parse_spectrum(s, db)
    ratings = []
    for score, review, dtime, pid in spectrum_ratings(db, spid):
        person = db.get_person(pid)
        ratings.append({'score': score,
                        'review': multiline_text(review),
                        'date': fmttime(dtime),
                        'person_email': person.email,
                        'person_name': person.name,
                        'person_affil': person.affiliation})

    return render_template('show_spectrum_ratings.html',
                           ratings=ratings,
                           spectrum_name=opts['spectrum_name'])


@app.route('/submit_spectrum_edits', methods=['GET', 'POST'])
def submit_spectrum_edits():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit spectrum'
        return render_template('ptable.html', error=error)
    spid = 0
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

@app.route('/edit_spectrum/<int:spid>')
def edit_spectrum(spid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit spectrum'
        return render_template('ptable.html',
                               error=error)

    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable.html', error=error)

    opts = parse_spectrum(s, db)
    return render_template('editspectrum.html', error=error,
                           elems=get_element_list(db),
                           eunits=get_energy_units_list(db),
                           edges=get_edge_list(db),
                           beamlines=get_beamline_list(db),
                           samples=get_sample_list(db),
                           **opts)


@app.route('/delete_spectrum/<int:spid>')
@app.route('/delete_spectrum/<int:spid>/ask=<int:ask>')
def delete_spectrum(spid, ask=1):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to delete a spectrum'
        return redirect(url_for('search', error=error))

    s_name = db.filtered_query('spectrum', id=spid)[0].name
    if ask != 0:
        return render_template('confirm_delete_spectrum.html',
                               spectrum_id=spid,
                               spectrum_name=s_name)

    else:
        db.del_spectrum(spid)
        time.sleep(1)
        flash('Deleted spectrum %s' % s_name)
    return redirect(url_for('search', error=error))


@app.route('/submit_spectrum_rating', methods=['GET', 'POST'])
def submit_spectrum_rating(spid=None):
    session_init(session, db)
    error=None

    if session['username'] is None:
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
    if session['username'] is None:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', spid=spid, error=error))

    pid = session['person_id']
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable', error=error)

    opts = parse_spectrum(s, db)
    score = 3
    review = '<review>'
    for _s, _r, _d, _p in spectrum_ratings(db, spid):
        if int(_p) == int(pid):
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

    if session['username'] is None:
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
    if session['username'] is None:
        error='must be logged in to rate suite'
        return redirect(url_for('suites', stid=stid, error=error))

    for st in db.filtered_query('suite'):
        if st.id == stid:
            stname, notes, person_id = st.name, st.notes, st.person_id

    pid = session['person_id']
    score = 3
    review = '<review>'
    for _s, _r, _d, _p in suite_ratings(db, stid):
        if _p == pid:
            score = _s
            review =  _r

    return render_template('ratesuite.html', error=error,
                           suite_id=stid, suite_name=stname,
                           person_id=pid, score=score, review=review)


@app.route('/showsuite_rating/<int:stid>')
def showsuite_rating(stid=None):
    session_init(session, db)

    for st in db.filtered_query('suite'):
        if st.id == stid:
            stname, notes, _pid = st.name, st.notes, st.person_id
    if stname is None:
        error = 'Could not find Suite #%i' % stid
        return render_template('ptable.html', error=error)

    ratings = []
    for score, review, dtime, pid in suite_ratings(db, stid):
        person = db.get_person(pid)
        ratings.append({'score': score, 'review': multiline_text(review),
                        'date': fmttime(dtime),
                        'person_email': person.email,
                        'person_name': person.name,
                        'person_affil': person.affiliation})

    return render_template('show_suite_ratings.html',
                           ratings=ratings, suite_notes=notes,
                           suite_name=stname)

@app.route('/add_spectrum_to_suite/<int:spid>')
def add_spectrum_to_suite(spid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add spectrum to suite'
        return redirect(url_for('spectrum', spid=spid, error=error))

    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable', error=error)

    suites = []
    for st in db.filtered_query('suite'):
        suites.append({'id': st.id, 'name': st.name})

    return render_template('add_spectrum_to_suite.html', error=error,
                           spectrum_id=spid, spectrum_name=s.name,
                           person_id=session['person_id'], suites=suites)

@app.route('/submit_spectrum_to_suite', methods=['GET', 'POST'])
def submit_spectrum_to_suite():
    session_init(session, db)
    error=None
    if session['username'] is None:
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
        else:
            stname = db.filtered_query('suite', id=stid)[0].name
            spname = db.get_spectrum(spid).name
            error = "Spectrum '%s' is already in Suite '%s'" % (spname, stname)

    return redirect(url_for('suites', error=error))


@app.route('/rawfile/<int:spid>/<fname>')
def rawfile(spid, fname):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%i' % spid
        return render_template('ptable.html', error=error)
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
        for st in db.filtered_query('suite'):
            name, notes, person_id = st.name, st.notes, st.person_id
            person_email = db.get_person(person_id).email
            spectra = spectra_for_suite(db, st.id)

            is_owner = (int(session['person_id']) == int(st.person_id))
            suites.append({'id': st.id, 'name': name, 'notes': notes,
                           'person_email': person_email,
                           'rating': get_rating(st),
                           'suite_owner': is_owner,
                           'nspectra': len(spectra), 'spectra': spectra})

    else:
        st = db.filtered_query('suite', id=stid)[0]
        name, notes, person_id = st.name, st.notes, st.person_id
        person_email = db.get_person(person_id).email
        spectra = spectra_for_suite(db, stid)

        is_owner = (int(session['person_id']) == int(st.person_id))
        suites.append({'id': stid, 'name': name, 'notes': notes,
                       'person_email': person_email,
                       'rating': get_rating(st),
                       'suite_owner': is_owner,
                       'nspectra': len(spectra), 'spectra': spectra})
    return render_template('suites.html', nsuites=len(suites), suites=suites)

@app.route('/add_suite')
@app.route('/add_suite', methods=['GET', 'POST'])
def add_suite():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add a suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        suite_name = request.form['suite_name']
        person_id = request.form['person']
        notes = request.form['notes']
        _sname = [s.name for s in db.filtered_query('suite')]
        try:
            suite_name = unique_name(suite_name, _sname,  msg='suite')
        except:
            error = 'a suite named %s exists'
        db.add_suite(suite_name, notes=notes, person_id=int(person_id))
        time.sleep(0.5)
        return redirect(url_for('suites', error=error))
    else:

        return render_template('add_suite.html', error=error,
                               person_id=session['person_id'])

@app.route('/delete_suite/<int:stid>')
@app.route('/delete_suite/<int:stid>/ask=<int:ask>')
def delete_suite(stid, ask=1):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to delete a suite'
        return redirect(url_for('suites', error=error))

    suite_name = db.filtered_query('suite', id=stid)[0].name
    if ask != 0:
        return render_template('confirm_del_suite.html', stid=stid,
                               suite_name=suite_name)

    else:
        db.del_suite(stid)
        time.sleep(1)
        flash('Deleted suite %s' % s_name)
    return redirect(url_for('suites', error=error))

@app.route('/edit_suite/<int:stid>')
def edit_suite(stid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit suite'
        return render_template('ptable.html', error=error)

    st = db.filtered_query('suite', id=stid)[0]
    name, notes, person_id = st.name, st.notes, st.person_id
    person_email = db.get_person(person_id).email
    spectra = spectra_for_suite(db, stid)

    is_owner = (int(session['person_id']) == int(st.person_id))
    opts = {'id': stid, 'name': name, 'notes': notes,
            'person_email': person_email,
            'rating': get_rating(st),
            'suite_owner': is_owner,
            'nspectra': len(spectra), 'spectra': spectra}
    return render_template('edit_suite.html', **opts)

@app.route('/submit_suite_edits', methods=['GET', 'POST'])
def submit_suite_edits():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit suite'
        return render_template('ptable.html', error=error)
    if request.method == 'POST':
        stid  = int(request.form['suite'])
        db.update('suite', stid,
                  name=request.form['name'],
                  notes=request.form['comments'])

        for spec in spectra_for_suite(db, stid):
            spid = int(spec['spectrum_id'])
            key = 'spec_%i' % spid
            if key not in request.form:
                db.remove_spectrum_from_suite(stid, spid)
        time.sleep(0.25)

    return redirect(url_for('suites', stid=stid, error=error))


@app.route('/sample/<int:sid>')
def sample(sid=None):
    session_init(session, db)
    samples = []
    opts = {}
    for sdat in get_sample_list(db):
        if int(sid) == int(sdat['id']):
            opts = sdat
    return render_template('sample.html', sid=sid, **opts)

@app.route('/edit_sample/<int:sid>')
def edit_sample(sid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return render_template('ptable.html', error=error)

    opts = {}
    for sdat in get_sample_list(db):
        if int(sid) == int(sdat['id']):
            opts = sdat
    return render_template('editsample.html', sid=sid, **opts)

@app.route('/submit_sample_edits', methods=['GET', 'POST'])
def submit_sample_edits():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return render_template('ptable.html', error=error)
    sid = 0
    if request.method == 'POST':
        sid  = request.form['sample_id']
        pid  = request.form['person_id']
        name = request.form['name']
        notes = request.form['notes']
        prep = request.form['preparation']
        formula = request.form['formula']
        source = request.form['material_source']
        # xtal_format = request.form['xtal_format']
        # xtal_data   = request.form['xtal_data']

        db.update('sample', int(sid),
                  person=pid,
                  name=name,
                  notes=notes,
                  formula=formula,
                  material_source=source,
                  preparation=prep)
        time.sleep(0.25)
    return redirect(url_for('sample', sid=sid, error=error))

@app.route('/beamlines')
@app.route('/beamlines/<orderby>')
@app.route('/beamlines/<orderby>/<reverse>')
def beamlines(blid=None, orderby='id', reverse=0):
    session_init(session, db)
    beamlines = []

    for bldat in get_beamline_list(db, orderby=orderby):
        blid = bldat['id']
        spectra = spectra_for_beamline(db, blid)
        opts = {'nspectra': len(spectra), 'spectra': spectra}
        opts.update(bldat)
        beamlines.append(opts)

    reverse = int(reverse)
    if reverse:
        beamlines.reverse()
        reverse = 0
    else:
        reverse = 1

    return render_template('beamlines.html',
                           nbeamlines=len(beamlines),
                           beamlines=beamlines, reverse=reverse)

@app.route('/beamline')
@app.route('/beamline/<int:blid>')
def beamline(blid=None):
    session_init(session, db)
    beamlines = []
    for _bldat in get_beamline_list(db):
        if _bldat['id'] == "%i" % blid:
            bldat = _bldat
            break

    spectra = spectra_for_beamline(db, blid)
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
    if session['username'] is None:
        error='must be logged in to add a beamline'
        return redirect(url_for('beamlines', error=error))

    if request.method == 'POST':
        bl_name = request.form['beamline_name']
        notes = request.form['notes']
        fac_id = int(request.form['fac_id'])
        source = request.form['xray_source']

        _blnames = [s.name for s in db.filtered_query('beamline')]
        try:
            bl_name = unique_name(bl_name, _blnames,
                                  msg='beamline', maxcount=5)
        except:
            error = 'a beamline named %s exists'

        db.add_beamline(bl_name, notes=notes, xray_source=source,
                        facility_id=fac_id)

        time.sleep(1)
        return redirect(url_for('beamlines', error=error))
    else:
        facilities = []
        for r in db.filtered_query('facility'):
            facilities.append({'id': r.id, 'name': r.name})
        return render_template('add_beamline.html', error=error,
                               facilities=facilities)


@app.route('/facility')
def facility():
    session_init(session, db)
    return render_template('beamline.html')


@app.route('/add_facility')
@app.route('/add_facility', methods=['GET', 'POST'])
def add_facility():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add a facility'
        return redirect(url_for('beamlines', error=error))

    if request.method == 'POST':
        fac_name = request.form['facility_name']
        _facnames = [s.name for s in db.filtered_query('facility')]
        try:
            fac_name = unique_name(fac_name, _facnames,  msg='facility', maxcount=5)
        except:
            error = 'a facility named %s exists'
        db.add_beamline(fac_name)
        time.sleep(1)
        return redirect(url_for('list_facilities', error=error))
    else:
        facilities = []
        for r in db.filtered_query('facility'):
            facilities.append({'id': r.id, 'name': r.name})
        return render_template('add_facility.html', error=error,
                               facilities=facilities)


@app.route('/list_facilities')
def list_facilities():
    session_init(session, db)
    error=None
    facilities = db.filtered_query('facility')
    return render_template('facilities_list.html', error=error,
                           facilities=facilities)

@app.route('/citation')
@app.route('/citation/<int:cid>')
def citation(blid=None):
    session_init(session, db)
    spectra = spectra_for_citation(db, cid)
    opts = {'nspectra': len(spectra), 'spectra': spectra}
    return render_template('citations.html', ncitations=1, **opts)


@app.route('/add_citation')
@app.route('/add_citation', methods=['GET', 'POST'])
def add_citation(spid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add citation for spectrum'
        return redirect(url_for('ptable',  error=error))

    return render_template('add_citation.html', spid=spid)


@app.route('/upload')
@app.route('/upload/')
def upload():
    session_init(session, db)
    if session['username'] is None:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('search', error=error))
    return render_template('upload.html',
                           person_id=session['person_id'])

@app.route('/submit_upload', methods=['GET', 'POST'])
def submit_upload():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('search', error=error))

    if request.method == 'POST':
        pid    = request.form['person']
        pemail = db.get_person(int(pid)).email
        file = request.files['file']
        s = None
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
                time.sleep(1.0)
                db.add_xdifile(fullpath, person=pemail, create_sample=True)
                time.sleep(1.0)
                db.session.commit()

            s  = db.get_spectra()[-1]
            if s is None:
                error = 'Could not find Spectrum #%i' % s.id
                return render_template('upload.html', error=error)

        if s is None:
            error = "File '%s' not found or not suppported type" %  (file.filename)
            return render_template('upload.html', error=error)

        try:
            opts = parse_spectrum(s, db)
        except:
            error = "Could not read spectrum from '%s'" % (file.filename)
            return render_template('upload.html', error=error)
        return redirect(url_for('spectrum', spid=s.id, error=error))
    return render_template('upload.html', error='upload error')

if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(port=PORT)
