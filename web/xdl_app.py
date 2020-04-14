#!/usr/bin/env python

import sys
import time

t0 = time.time()

import smtplib
import json
import base64
import numpy as np
from sqlalchemy import text

from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash, Response,
                   send_from_directory)

from xasdb import (connect_xasdb, fmttime, valid_score, unique_name, None_or_one)
from xafs_preedge import (preedge, edge_energies)

from utils import (row2dict, random_string, multiline_text, session_init,
                   parse_spectrum, spectrum_ratings, spectra_for_suite,
                   beamline_for_spectrum, spectra_for_beamline,
                   get_beamline_list, get_rating, allowed_filename,
                   get_fullpath, pathjoin)


# sys.path.insert(0, '/home/newville/XASDB_Secrets')

from xasdb_config import (SECRET_KEY, DBNAME, DBCONN, PORT, DEBUG,
                          UPLOAD_FOLDER, LOCAL_ONLY, ADMIN_EMAIL, BASE_URL)

from plot import make_xafs_plot

app = Flask('xaslib', static_folder='static')
app.config.from_object(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = connect_xasdb(DBNAME, **DBCONN)

ANY_EDGES  = ['Any'] + [e.name for e in db.get_edges()]
ANY_MODES  = ['Any'] + [e.name for e in db.get_modes()]

def send_confirm_email(person, hash, style='new'):
    """send email with account confirmation/reset link"""

    subject = "XAS Library Account Password Reset"
    message = """
        Someone (hopefully you) asked to reset your account for the XAS Spectra Library.

        To change your passowrd, please follow this link:
               %s/newpassword/%d/%s

        Thank you.

""" % (BASE_URL, person.id, hash)

    if style == 'new':
        subject = "XAS Library Account Confirmation"
        message = """
        An account at the XAS Spectra Library has been created for %s, but not yet confirmed.

        To confirm this account, please follow this link:
           %s/confirmaccount/%d/%s

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
    return send_from_directory(pathjoin(app.root_path, 'static'),
                               'ixas_logo.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html')

@app.route('/clear')
def clear():
    session_init(session, db)
    return redirect(url_for('elem'))

@app.route('/')
def index():
    return redirect(url_for('elem'))

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

        print("Login ", email, password, type(email), type(password))
        person = db.get_person(email)
        session['person_id'] = "-1"
        if person is None:
            error = 'Invalid email'
        elif not db.test_person_confirmed(email):
            error = 'Account not confirmed'
        elif not db.test_person_password(email, password):
            error = 'Invalid password'
        else:
            session['person_id'] = "%d" % person.id
            session['username'] = request.form['email']
    if session['username'] is not None:
        return redirect(url_for('elem'))
    else:
        return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session_init(session, db)
    session['username'] = None
    session['person_id'] = '-1'
    flash('You have been logged out')
    return redirect(url_for('elem'))

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

@app.route('/elem', methods=['GET', 'POST'])
@app.route('/elem/', methods=['GET', 'POST'])
@app.route('/elem/<elem>', methods=['GET', 'POST'])
@app.route('/elem/<elem>/<orderby>',  methods=['GET', 'POST'])
@app.route('/elem/<elem>/<orderby>/<reverse>', methods=['GET', 'POST'])
def elem(elem=None, orderby=None, reverse=0):
    session_init(session, db)
    dbspectra = []
    sql_orderby = orderby
    if orderby is None:
        sql_orderby = 'element_z'

    if elem in ('action', 'filter'):
        elem = request.form.get('elem')

    if elem is not None:
        if elem.lower() == 'all':
            try:
                dbspectra = db.get_spectra(orderby='element_z')
            except:
                pass
        else:
            try:
                dbspectra = db.get_spectra(element=elem, orderby=sql_orderby)
            except:
                pass

    edge_filter = request.form.get('edge_filter', ANY_EDGES[0])
    mode_filter = request.form.get('mode_filter', ANY_MODES[0])
    beamline_id = request.form.get('beamline', '0')
    searchword  = request.form.get('searchphrase', '')
    rating_min  = request.form.get('rating', '0')

    reverse = int(reverse)
    if reverse:
        dbspectra.reverse()
        reverse = 0
    else:
        reverse = 1

    spectra = []
    for s in dbspectra:
        edge     = db.get_edge(s.edge_id).name
        elem_sym = db.get_element(s.element_z).symbol
        person   = db.get_person(s.person_id)
        mode     = db.get_mode(s.mode_id)

        rating   = get_rating(s)
        bl_id, bl_desc = beamline_for_spectrum(db, s)

        # filter edge, beamline, and modes:
        if ((edge_filter not in (edge, ANY_EDGES[0])) or
            (beamline_id != '0' and int(bl_id) != int(beamline_id)) or
            (mode_filter not in (mode, ANY_MODES[0]))):
            continue

        # filter rating
        if rating_min != '0':
            try:
                rval = float(rating.split()[0])
            except:
                rval = 100.0
            if (rval-0.01) < int(rating_min):
                continue

        # filter word
        if searchword != '':
            fulldat =  parse_spectrum(s, db)
            misc = fulldat.get('misc', {})
            misc = '\n'.join(['%s:%s' % (m['key'], m['val']) for m in misc])
            if not any((searchword in fulldat.get('spectrum_name', ''),
                        searchword in fulldat.get('xdi_filename',''),
                        searchword in fulldat.get('description', ''),
                        searchword in fulldat.get('sample_name',''),
                        searchword in fulldat.get('raw_comments', ''),
                        searchword in fulldat.get('beamline_desc',''),
                        searchword in fulldat.get('person_name', ''),
                        searchword in fulldat.get('person_email',''),
                        searchword in misc)):
                continue
        spectra.append({'id': s.id,
                        'name': s.name,
                        'description': s.description,
                        'element': elem,
                        'edge': edge,
                        'person_email': person.email,
                        'person_name': person.name,
                        'elem_sym': elem_sym,
                        'rating': rating,
                        'beamline_desc': bl_desc,
                        'beamline_id': bl_id })

    return render_template('ptable.html',
                           ntotal=len(dbspectra),
                           nspectra=len(spectra),
                           elem=elem, spectra=spectra,
                           reverse=reverse,
                           edge_filter=edge_filter, edges=ANY_EDGES,
                           mode_filter=mode_filter, modes=ANY_MODES,
                           beamlines=get_beamline_list(db, with_any=True, orderby='name'),
                           beamline_id=beamline_id,
                           searchword=searchword,
                           rating_min=rating_min)


@app.route('/all')
@app.route('/all/')
def all():
    return redirect(url_for('elem/All', error=error))


@app.route('/spectrum/')
@app.route('/spectrum/<int:spid>')
def spectrum(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%d' % spid
        return redirect(url_for('elem', error=error))

    opts = parse_spectrum(s, db)
    opts['spectrum_owner'] = (session['person_id'] == "%d" % s.person_id)
    opts['rating'] = get_rating(s)

    eunits = opts['energy_units']
    if eunits.startswith('keV'):
        energy = energy /1000.0
    elif eunits.startswith('deg'):
        print('Need to convert angle to energy')

    try:
        e0 = edge_energies[int(s.element_z)][str(opts['edge'])]
    except:
        pass

    plot_mode = mode = db.get_mode(spid)

    # now get real data for plotting
    energy, mudata, murefer = None, None, None
    try:
        if plot_mode.startswith('trans'):
            energy = np.array(json.loads(s.energy))
            i0     = np.array(json.loads(s.i0))
            itrans = np.array(json.loads(s.itrans))
            mudata = -np.log(itrans/i0)
        else:
            energy = np.array(json.loads(s.energy))
            i0     = np.array(json.loads(s.i0))
            ifluor = np.array(json.loads(s.ifluor))
            mudata = ifluor/i0
    except:
        error = 'Could not extract fluorescence data from spectrum'
        return render_template('spectrum.html', **opts)


    dgroup = preedge(energy, mudata)

    # get reference if possible
    try:
        irefer = np.array(json.loads(s.irefer))
        refmode = s.reference_mode_id
        refmode = 1 if refmode is None else refmode
        if refmode == 1:
            murefer = -np.log(irefer/itrans)
        else:
            murefer = irefer/i0
    except:
        pass

    try:
        e1 = max(np.where(energy<=e0 - 25)[0])
    except:
        e1 = 0
    e2 = max(np.where(energy<=e0 + 75)[0]) + 1
    xanes_en = energy[e1:e2] - e0

    xanes_mu = dgroup['norm'][e1:e2]
    xanes_ref = None
    if murefer is not None:
        rgroup = preedge(energy, murefer)
        xanes_ref = rgroup['norm'][e1:e2]

    opts['e0'] = '%f' % e0
    opts['fullfig'] =  make_xafs_plot(energy, mudata, s.name,
                                      ylabel='Raw XAFS').decode('UTF-8')

    opts['xanesfig'] = make_xafs_plot(xanes_en, xanes_mu, s.name,
                                      xlabel='Energy-%.1f (eV)' % e0,
                                      ylabel='Normalized XANES',
                                      x0=e0, ref_mu=xanes_ref,
                                      ref_name='with reference').decode('UTF-8')

    suites = []
    for r in db.fquery('spectrum_suite', spectrum_id=s.id):
        st = db.fquery('suite', id=r.suite_id)[0]
        suites.append({'id': r.suite_id, 'name': st.name})
    opts['nsuites'] = len(suites)
    opts['suites'] = suites

    return render_template('spectrum.html', **opts)

@app.route('/showspectrum_rating/<int:spid>')
def showspectrum_rating(spid=None):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        return redirect(url_for('elem',
                                error='Could not find Spectrum #%d' % spid))

    opts = parse_spectrum(s, db)
    ratings = []
    for row in db.get_spectrum_ratings(spid):
        person = db.get_person(row.person_id)
        ratings.append({'score': row.score,
                        'review': multiline_text(row.comments),
                        'date': fmttime(row.datetime),
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
        return redirect(url_for('elem',
                                error='must be logged in to edit spectrum'))
    spid = 0
    if request.method == 'POST':
        spid  = int(request.form['spectrum'])
        edge_id = ANY_EDGES.index(request.form['edge'])
        mode_id = ANY_MODES.index(request.form['mode'])

        db.update('spectrum', int(spid),
                  name=request.form['name'],
                  description=request.form['description'],
                  comments=request.form['comments'],
                  d_spacing=float(request.form['d_spacing']),
                  energy_resolution=request.form['e_resolution'],
                  edge_id=edge_id, mode_id=mode_id,
                  beamline_id= int(request.form['beamline']),
                  sample_id= int(request.form['sample']),
                  reference_sampled=request.form['reference_sample'],

                  energy_units_id=int(request.form['energy_units']))

        time.sleep(0.25)
    return redirect(url_for('spectrum', spid=spid, error=error))

@app.route('/edit_spectrum/<int:spid>')
def edit_spectrum(spid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        return redirect(url_for('elem',
                                error='must be logged in to edit spectrum'))
    s  = db.get_spectrum(spid)
    if s is None:
        return redirect(url_for('elem',
                                error = 'Could not find Spectrum #%d' % spid))

    opts = parse_spectrum(s, db)
    beamlines = get_beamline_list(db, with_any=False, orderby='name')
    return render_template('edit_spectrum.html', error=error,
                           elems=db.fquery('element'),
                           eunits=db.fquery('energy_units'),
                           edges=ANY_EDGES[1:],
                           beamlines=beamlines,
                           samples=db.fquery('sample'),
                           modes=ANY_MODES[1:], **opts)


@app.route('/delete_spectrum/<int:spid>')
@app.route('/delete_spectrum/<int:spid>/ask=<int:ask>')
def delete_spectrum(spid, ask=1):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to delete a spectrum'
        return redirect(url_for('elem', error=error))

    spect_name = db.fquery('spectrum', id=spid)[0].name
    if ask != 0:
        return render_template('confirm_delete_spectrum.html',
                               spectrum_id=spid,
                               spectrum_name=spect_name)

    else:
        db.del_spectrum(spid)
        time.sleep(1)
        flash('Deleted spectrum %s' % spect_name)
    return redirect(url_for('elem', error=error))


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
            return render_template('rate_spectrum.html', error=error,
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

    pid = int(session['person_id'])
    s  = db.get_spectrum(spid)
    if s is None:

        return redirect(url_for('elem',
                                error='Could not find Spectrum #%d' % spid))

    opts = parse_spectrum(s, db)
    score = 3
    review = ''
    for _s, _r, _d, _p in spectrum_ratings(db, spid):
        if int(_p) == pid:
            score = _s
            review =  _r
    spid = s.id
    spname = s.name

    return render_template('rate_spectrum.html', error=error,
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
            return render_template('rate_suite.html', error=error,
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

    st = None_or_one(db.fquery('suite', id=stid))
    if st is None:
        return redirect(url_for('suites', stid=stid, error='suite not found?'))

    pid = int(session['person_id'])
    score = '3'
    review = ''
    for row in db.get_suite_ratings(stid):
        if int(row.person_id) == pid:
            score = '%d' % row.score
            review =  multiline_text(row.comments)

    return render_template('rate_suite.html', error=error,
                           suite_id=stid, suite_name=st.name,
                           person_id=pid, score=score, review=review)


@app.route('/showsuite_rating/<int:stid>')
def showsuite_rating(stid=None):
    session_init(session, db)

    st = None_or_onw(db.fquery('suite'))
    if st is None:
        error = 'Could not find Suite #%d' % stid
        return redirect(url_for('suites', error=error))

    ratings = []
    for row in db.get_suite_ratings(stid):
        person = db.get_person(row.person_id)
        ratings.append({'score': row.score,
                        'review': multiline_text(row.comments),
                        'date': fmttime(row.datetime),
                        'person_email': person.email,
                        'person_name': person.name,
                        'person_affil': person.affiliation})

    return render_template('show_suite_ratings.html',
                           ratings=ratings, suite_notes=st.notes,
                           suite_name=st.name)

@app.route('/add_spectrum_to_suite/<int:spid>')
def add_spectrum_to_suite(spid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add spectrum to suite'
        return redirect(url_for('spectrum', spid=spid, error=error))

    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%d' % spid
        return redirect(url_for('elem', error=error))

    suites = []
    for st in db.fquery('suite'):
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
        for r in db.fquery('spectrum_suite', suite_id=stid):
            found = found or (r.spectrum_id == spid)
        if not found:
            db.addrow('spectrum_suite', suite_id=stid, spectrum_id=spid)
            time.sleep(0.25)
        else:
            stname = db.fquery('suite', id=stid)[0].name
            spname = db.get_spectrum(spid).name
            error = "Spectrum '%s' is already in Suite '%s'" % (spname, stname)

    return redirect(url_for('suites', error=error))


@app.route('/rawfile/<int:spid>/<fname>')
def rawfile(spid, fname):
    session_init(session, db)
    s  = db.get_spectrum(spid)
    if s is None:
        error = 'Could not find Spectrum #%d' % spid
        return redirect(url_for('spectrum', spid=spid, error=error))

    return Response(s.filetext, mimetype='text/plain')


@app.route('/about')
@app.route('/about/')
def about():
    return render_template('doc/about.html')

@app.route('/doc')
@app.route('/doc/')
@app.route('/doc/<page>')
def doc(page='index.html'):
    return render_template('doc/%s' % page)

@app.route('/suites')
@app.route('/suites/')
@app.route('/suites/<int:stid>')
def suites(stid=None):
    session_init(session, db)
    suites = []
    if stid is None:
        for st in db.fquery('suite'):
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
        st = db.fquery('suite', id=stid)[0]
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
        _sname = [s.name for s in db.fquery('suite')]
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

    suite_name = db.fquery('suite', id=stid)[0].name
    if ask != 0:
        return render_template('confirm_delete_suite.html', stid=stid,
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
        return redirect(url_for('suites', error=error))

    st = db.fquery('suite', id=stid)[0]
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
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        stid  = int(request.form['suite'])
        db.update('suite', stid,
                  name=request.form['name'],
                  notes=request.form['comments'])

        for spec in spectra_for_suite(db, stid):
            spid = int(spec['spectrum_id'])
            key = 'spec_%d' % spid
            if key not in request.form:
                db.remove_spectrum_from_suite(stid, spid)
        time.sleep(0.25)

    return redirect(url_for('suites', stid=stid, error=error))


@app.route('/sample/<int:sid>')
def sample(sid=None):
    session_init(session, db)
    samples = []
    opts = {}
    sdat = None_or_one(db.fquery('sample', id=sid))
    if sdat is not None:
        opts = row2dict(sdat)
    return render_template('sample.html', sid=sid, **opts)

@app.route('/edit_sample/<int:sid>')
def edit_sample(sid=None):
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return redirect(url_for('elem', error=error))

    opts = {}
    for sdat in get_sample_list(db):
        if int(sid) == int(sdat['id']):
            opts = sdat
    return render_template('edit_sample.html', sid=sid, **opts)

@app.route('/submit_sample_edits', methods=['GET', 'POST'])
def submit_sample_edits():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return render_template('elem', error=error)

    sid = 0
    if request.method == 'POST':
        sid  = request.form['sample_id']
        pid  = request.form['person_id']
        name = request.form['name']
        notes = request.form['notes']
        prep = request.form['preparation']
        formula = request.form['formula']
        source = request.form['material_source']

        db.update('sample', int(sid), person=pid, name=name, notes=notes,
                  formula=formula, material_source=source,
                  preparation=prep)
        time.sleep(0.25)
    return redirect(url_for('sample', sid=sid, error=error))

@app.route('/beamlines')
@app.route('/beamlines/<orderby>')
@app.route('/beamlines/<orderby>/<reverse>')
def beamlines(blid=None, orderby='name', reverse=0):
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
    for _bldat in get_beamline_list(db, orderby='name'):
        if _bldat['id'] == "%d" % blid:
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

        _blnames = [s.name for s in db.fquery('beamline')]
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
        return render_template('add_beamline.html', error=error,
                               facilities=db.get_facilities(orderby='country'))


@app.route('/add_facility')
@app.route('/add_facility', methods=['GET', 'POST'])
def add_facility():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to add a facility'
        return redirect(url_for('facilities', error=error))

    if request.method == 'POST':
        fac_name = request.form['facility_name']
        _facnames = [s.name for s in db.fquery('facility')]
        try:
            fac_name = unique_name(fac_name, _facnames,  msg='facility', maxcount=5)
        except:
            error = 'a facility named %s exists'
        db.add_beamline(fac_name)
        time.sleep(1)
        return redirect(url_for('facilities', error=error))
    else:
        return render_template('add_facility.html', error=error,
                               facilities=db.get_facilities(orderby='country'))

@app.route('/facilities')
@app.route('/facilities/')
def facilities():
    session_init(session, db)
    return render_template('facilities.html', error=None,
                           facilities=db.get_facilities(orderby='country'))

@app.route('/edit_facility/<int:fid>')
def edit_facility(fid=None):
    session_init(session, db)
    return render_template('edit_facility.html', error=None,
                           fac = db.get_facility(id=int(fid)),
                           person_id=session['person_id'])


@app.route('/submit_facility_edits', methods=['GET', 'POST'])
def submit_facility_edits():
    session_init(session, db)
    error=None
    if session['username'] is None:
        return redirect(url_for('elem',
                                error='must be logged in to edit facility'))

    fid = 0
    # print("Facility edits ", request.form)
    fid  = int(request.form.get('facility_id', -1))
    if fid < 0:
        return redirect(url_for('elem',
                                error='could not edit facility'))

    if request.method == 'POST':
        print(' -> update', fid, request.form['city'])
        o = db.update('facility', fid,
                      name=request.form['name'],
                      fullname=request.form['fullname'],
                      laboratory=request.form['laboratory'],
                      city=request.form['city'],
                      country=request.form['country'])
        print("Done ", o)
        time.sleep(0.25)

    return redirect(url_for('facilities', error=error))


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
        return redirect(url_for('citation',  error=error))

    return render_template('add_citation.html', spid=spid)


@app.route('/upload')
@app.route('/upload/')
def upload():
    session_init(session, db)
    if session['username'] is None:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('elem', error=error))
    return render_template('upload.html',
                           person_id=session['person_id'])

@app.route('/submit_upload', methods=['GET', 'POST'])
def submit_upload():
    session_init(session, db)
    error=None
    if session['username'] is None:
        error='must be logged in to submit a spectrum'
        return redirect(url_for('elem', error=error))

    if request.method == 'POST':
        pid    = request.form['person']
        pemail = db.get_person(int(pid)).email
        file = request.files['file']
        fname = request.form['spectrum_name']
        spectrum = None
        file_ok = False
        if file and allowed_filename(file.filename):
            fullpath = get_fullpath(file, UPLOAD_FOLDER)
            try:
                file.save(fullpath)
                file_ok = True
            except IOError:
                pass

            if file_ok:
                time.sleep(0.50)
                sid = db.add_xdifile(fullpath, person=pemail, create_sample=True)
                time.sleep(0.50)
                db.session.commit()

            spectrum  = db.get_spectrum(sid)
            if spectrum is None:
                error = 'Could not find uploaded Spectrum #%d (%s)' % (sid, fullpath)
                return render_template('upload.html', error=error)

        if spectrum is None:
            error = "File '%s' not found or not suppported type" %  (file.filename)
            return render_template('upload.html', error=error)


        # try:
        opts = parse_spectrum(spectrum, db)
        print("UPLOAD: parsed to ", spectrum.id, opts)

        # except:
        #    error = "Could not read spectrum from '%s'" % (file.filename)
        #    return render_template('upload.html', error=error)
        return redirect(url_for('spectrum', spid=spectrum.id, error=error))
    return render_template('upload.html', error='upload error')

## <input type="checkbox" name="check1" value="c1">Value 1<br>

if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(port=PORT)
