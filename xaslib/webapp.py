#!/usr/bin/env python

import os
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

from .xaslib import (connect_xaslib, isotime2datetime, isotime, valid_score,
                     unique_name)
from .initialdata import edge_energies, elem_syms
from larch.io import read_ascii
from larch.xafs.pre_edge import preedge
from larch.utils.jsonutils import encode4js, decode4js
from larch.math import index_of
# from .xafs_preedge import preedge

from .webutils import (row2dict, multiline_text, parse_spectrum,
                       spectrum_ratings, spectra_for_suite,
                       get_person_suites, add_spectra_to_suite,
                       spectra_for_citation, save_zipfile,
                       spectra_for_beamline, get_rating,
                       get_fullpath, guess_metadata, pathjoin,
                       secure_filename, mono_deg2ev, upload2xdi)

from .webplot import make_xafs_plot, xafs_plotly, plot_multiple_spectra

db = None
app = Flask('xaslib', static_folder='static')
app.config.from_object(__name__)

ANY_EDGES = ANY_MODES = SAMPLES_OR_NEW = None
INCLUDED_ELEMS = SPECTRA_COUNT = None
ALL_ELEMS = EN_UNITS = None
BEAMLINE_DATA = ANY_BEAMLINES = None
REFERENC_MODES = SAMPLES_DATA = None

EMAIL_MSG = "From: {mailfrom:s}\r\nTo: {mailto:s}\r\nSubject: {subject:s}\r\n{message:s}\n"

GEN_MONOS = {"None":"-1",
             "generic Si(111)":"3.1355893",
             "generic Si(220)":"1.9201484",
             "generic Si(311)":"1.6375081"}

def make_permalink(selected, func='plots'):
    base_url = app.config['BASE_URL']
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    sel = '/'.join(['%d' % i for i in selected])
    return "%s/%s/%s" % (base_url, func, sel)

def session_init(session, force_refresh=False):
    global db, app, ANY_EDGES, ANY_MODES,  SAMPLES_OR_NEW
    global ANY_BEAMLINES, BEAMLINE_DATA, SAMPLES_DATA, REFERENCE_MODES
    global INCLUDED_ELEMS, SPECTRA_COUNT, ALL_ELEMS, EN_UNITS
    if 'username' not in session:
        session['username'] = None
    if 'person_id' not in session:
        session['person_id'] = "-1"
    if db is None and 'DBNAME' in app.config:
        conn = app.config.get('DBCONN', {})
        db = connect_xaslib(app.config['DBNAME'], **conn)
        force_refresh = True

    if force_refresh:
        ANY_EDGES  = ['Any'] + [e.name for e in db.get_edges()]
        ANY_MODES  = ['Any'] + [e.name for e in db.get_modes()]
        SAMPLES_OR_NEW  = [(0, '<Create New Sample>')]
        SAMPLES_OR_NEW.extend( [(s.id, s.name) for s in db.lookup('sample')])

        INCLUDED_ELEMS = db.included_elements()
        SPECTRA_COUNT = len(db.get_spectra())
        ALL_ELEMS  = db.lookup('element')
        EN_UNITS = [e.units for e in db.lookup('energy_units')]
        REFERENCE_MODES = [r.notes for r in db.lookup('reference_mode')]

        bl_data = db.get_beamlines(order_by='name')
        ANY_BEAMLINES = ['<Select Beamline>', 'Any']
        ANY_BEAMLINES.extend([b.name for b in bl_data])

        BEAMLINE_DATA = []
        for bldat in bl_data:
            blid = bldat.id
            fac = db.lookup('facility', id=bldat.facility_id)
            if bldat.facility_id is not None and len(fac) > 0:
                fac = fac[0]
                loc = fac.country
                if fac.city is not None and len(fac.city) > 0:
                    loc = "%s, %s" % (fac.city, fac.country)

                spectra = spectra_for_beamline(db, blid)
                BEAMLINE_DATA.append({'id': blid, 'name': bldat.name,
                                      'nickname': bldat.nickname,
                                      'facility': fac.name,
                                      'facility_id': fac.id,
                                      'location': loc,
                                      'nspectra': len(spectra),
                                      'spectra': spectra})

        SAMPLES_DATA = []
        for sdat in db.lookup('sample', order_by='name'):
            sid = sdat.id
            nspectra = len(db.lookup('spectrum', sample_id=sid))
            formula = sdat.formula
            if formula in (None, 'None'):
                formula = 'unknown'
            SAMPLES_DATA.append({'id': sid, 'name': sdat.name,
                                'formula': formula,
                                'nspectra': nspectra})


def send_confirm_email(person, hashkey, style='new'):
    """send email with account confirmation/reset link"""
    subject = "XAS Data Library Account Password Reset"
    base_url = app.config['BASE_URL']
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    admin_email = app.config['ADMIN_EMAIL']
    message = """
        Someone (hopefully you) asked to reset your account for the XAS Data Library.

        To enter a new password, please follow this link:
               {base_url:s}/newpassword/{person_id:d}/{hashkey:s}

        Thank you.

""".format(base_url=base_url, person_id=person.id, hashkey=hashkey)

    if style == 'new':
        subject = "XAS Data Library Account Confirmation"
        message = """
        An account at the XAS Data Library has been created for {name:s}, but not yet confirmed.

        To use this account, you will have to confirm it by following this link:
               {base_url:s}/confirmaccount/{person_id:d}/{hashkey:s}

        Thank you.
""".format(base_url=base_url, person_id=person.id, hashkey=hashkey, name=person.name)

    fullmsg = EMAIL_MSG.format(mailfrom=admin_email, mailto=person.email,
                               subject=subject, message=message)

    s = smtplib.SMTP('localhost')
    s.sendmail(admin_email, (person.email, ), fullmsg)
    s.quit()

def notify_account_creation(person):
    """send email to administrator about account creation"""

    subject = "XAS Data Library Account created"
    message = """
        An account on the XAS Data Library was created for user:
          email= {email:s}
          name = {mame:s}
""".format(email=person.email, name=person.name)

    fullmsg = EMAIL_MSG.format(mailfrom=admin_email, mailto=admin_email,
                               subject=subject, message=message)
    s = smtplib.SMTP('localhost')
    s.sendmail(admin_email, (person.email, ), fullmsg)
    s.quit()

def sendback(backto='show_error', error=None, **kws):
    """handles common redirects with error message"""
    return redirect(url_for(backto, error=error, **kws))

def needslogin(backto='show_error', error='', **kws):
    """handles common 'must be logged in XXXX' redirect"""
    if error is None:
        error = ''
    error = 'must be logged in %s' % error
    return sendback(backto=backto, error=error, **kws)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'ixas_logo.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(error):
    session_init(session)
    return render_template('notfound.html')

@app.route('/clear')
def clear():
    session_init(session)
    return sendback()


@app.route('/create_account/')
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    session_init(session)
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
                hashkey = db.person_unconfirm(email)
                if app.config.get('LOCAL_USE_ONLY', False):
                    db.person_confirm(email, hashkey)
                else:
                    ## send email here!!
                    person = db.get_person(email)
                    send_confirm_email(person, hashkey, style='new')
                    return render_template('confirmation_email_sent.html',
                                       email=email)

    return render_template('create_account.html', error=error)



@app.route('/password_reset_request/')
@app.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    session_init(session)
    error = None
    if request.method == 'POST':
        email = request.form['email']
        person = db.get_person(email)
        # log in existing
        if person is None:
            error = "No account with email '%s' exists" % email
        else:
            hashkey = db.person_unconfirm(email)
            send_confirm_email(person, hashkey, style='reset')
            return render_template('password_reset_response.html',
                                   email=email, error=error)
    return render_template('password_reset_request.html', error=error)


@app.route('/newpassword/<int:pid>/<hashkey>')
def newpassword(pid=-1, hashkey=''):
    session_init(session)
    pid = int(pid)
    if pid > 0 and len(hashkey) > 8:
        person = db.get_person(pid)
        email = person.email
        return render_template('newpassword_form.html',
                               hashkey=hashkey, email=email)
    return render_template('password_reset_request.html')

@app.route('/setnewpassword/', methods=['GET', 'POST'])
def setnewpassword():
    session_init(session)
    if request.method == 'POST':
        password  = request.form['password']
        password2 = request.form['password2']
        hashkey   = request.form['hashkey']
        email     = request.form['email']

        if len(password) < 7:
            error = 'password must be at least 7 characters long'
        elif password != password2:
            error = 'passwords must match.'
        elif not db.person_test_confirmhash(email, hashkey):
            error = 'password reset was not requested correctly.'
        else:
            db.set_person_password(email, password)
            hashkey = db.person_unconfirm(email)
            db.person_confirm(email, hashkey)
            flash("Your password has been reset.")
            error = None
            return render_template('login.html', error=error)

        return render_template('newpassword_form.html', hashkey=hashkey,
                               email=email, error=error)

    return render_template('password_reset_request.html')

@app.route('/confirmaccount/<int:pid>/<hashkey>')
def confirmaccount(pid=-1, hashkey=''):
    session_init(session)
    error = 'Could not confirm an account with that information'
    pid = int(pid)
    if pid > 0 and len(hashkey) > 8:
        person = db.get_person(pid)
        if person is None:
            error = 'Could not locate account'
        elif person.confirmed == 'true':
            error = 'The account for %s is already confirmed' % person.email
        else:
            confirmed = db.person_confirm(person.email, hashkey)
            if not confirmed:
                error = 'Confirmation key incorrect for %s' % person.email
            else:
                flash('''Congratulations, %s, your account is confirmed.
                You can now log in!''' % person.name)
                # notify
                # notify_account_creation(person)
                return render_template('login.html')
    return render_template('confirmation_email_sent.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init(session)
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
            session['person_id'] = "%d" % person.id
            session['username'] = request.form['email']
    if session['username'] is not None:
        return sendback('elem')
    else:
        return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session_init(session)
    session['username'] = None
    session['person_id'] = '-1'
    flash('You have been logged out')
    return sendback()

@app.route('/user')
@app.route('/user', methods=['GET', 'POST'])
def user():
    # show the user profile for that user
    session_init(session)
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

@app.route('/show_error',         methods=['GET', 'POST'])
@app.route('/show_error/',        methods=['GET', 'POST'])
@app.route('/show_error/<error>', methods=['GET', 'POST'])
def show_error(error=''):
    session_init(session)
    return render_template('layout.html', error=error)


@app.route('/elem/', methods=['GET', 'POST'])
@app.route('/elem/<elem>',  methods=['GET', 'POST'])
@app.route('/elem/<elem>/', methods=['GET', 'POST'])
@app.route('/elem/<elem>/<order_by>',  methods=['GET', 'POST'])
@app.route('/elem/<elem>/<order_by>/<reverse>', methods=['GET', 'POST'])
def elem(elem=None, order_by='element_z', reverse=0):
    session_init(session)
    dbspectra = []
    person_id = int(session['person_id'])
    button = request.form.get('submit', 'no button').lower()
    if elem == 'filter' or 'all spectra' in button:
        elem = 'all'
    elif elem is None:
        elem = request.form.get('elem')
    if elem is not None:
        kws = {'order_by': order_by}
        if elem.lower() != 'all':
            kws['element'] = elem

        dbspectra = db.get_spectra(**kws)


    selected = []
    for key, val in request.form.items():
        if key.startswith('sel_'):
            selected.append(int(key[4:]))

    if button.startswith('plot') and len(selected) > 0:
        return render_template('show_plot.html', nspectra=len(selected),
                               permalink=make_permalink(selected),
                               plotdata=plot_multiple_spectra(db, selected))

    elif button.startswith('save') and len(selected) > 0:
        fname = save_zipfile(db, selected, folder=app.config['DOWNLOAD_FOLDER'])
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], fname,
                                   mimetype='application/zip',
                                   as_attachment=True,
                                   download_name='xaslib.zip')

    elif button.startswith('add') and len(selected) > 0:
        target_suite = request.form.get('target_suite', None)
        msg = add_spectra_to_suite(db, selected,
                                   suite_id=int(target_suite),
                                   person_id = person_id)
        flash(msg)

    edge_filter = request.form.get('edge_filter', ANY_EDGES[0])
    mode_filter = request.form.get('mode_filter', ANY_MODES[0])
    beamline_id = request.form.get('beamline', '0')
    searchword  = request.form.get('searchphrase', '')
    rating_min  = request.form.get('rating', '0')

    spectra = []
    for s in dbspectra:
        edge     = db.get_edge(s.edge_id).name
        elem_sym = db.get_element(s.element_z).symbol
        person   = db.get_person(s.person_id)
        mode     = ANY_MODES[s.mode_id]
        rating   = get_rating(s, short=True)
        bl_id, bl_desc = db.get_spectrum_beamline(s.id)

        # filter edge, beamline, and modes:
        if ((edge_filter not in (edge, ANY_EDGES[0])) or
            (beamline_id != '0' and int(bl_id) != int(beamline_id)) or
            (mode_filter not in (mode, ANY_MODES[0]))):
            continue

        # filter rating
        if rating_min != '0':
            try:
                rval = float(rating)
            except:
                rval = 6.0
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

    reverse = int(reverse)
    if reverse:
        spectra.reverse()
        reverse = 0
    else:
        reverse = 1

    return render_template('browse_elements.html',
                           ntotal=len(dbspectra),
                           nspectra=len(spectra),
                           reverse=reverse,
                           elem=elem, spectra=spectra,
                           edge_filter=edge_filter, edges=ANY_EDGES,
                           mode_filter=mode_filter, modes=ANY_MODES,
                           beamlines=db.get_beamline_list(with_any=True),
                           beamline_id=beamline_id,
                           searchword=searchword,
                           rating_min=rating_min,
                           selected_spectra=[],
                           owned_suites=get_person_suites(db, person_id),
                           spectra_count=SPECTRA_COUNT,
                           included_elems=INCLUDED_ELEMS)


@app.route('/on_selected_spectra', methods=['GET', 'POST'])
def on_selected_spectra():
    session_init(session)
    dbspectra = []
    return redirect(url_for('elem'))


@app.route('/all')
@app.route('/all/')
@app.route('/All')
@app.route('/All/')
def all():
    return redirect(url_for('elem', elem='All'))

@app.route('/')
def index():
    return redirect(url_for('elem'))

@app.route('/spectrum/')
@app.route('/spectrum/<int:spid>')
@app.route('/spectrum/<int:spid>/')
@app.route('/spectrum/<int:spid>/<plotstyle>')
def spectrum(spid=None, plotstyle='xanes'):
    session_init(session)
    s  = db.get_spectrum(spid)
    if s is None:
        return sendback(error='no spectrum #%d found' % spid)

    opts = parse_spectrum(s, db)
    opts['spectrum_owner'] = (session['person_id'] == "%d" % s.person_id)
    opts['person_id'] = s.person_id
    opts['rating'] = get_rating(s)

    eunits = opts['energy_units']
    if eunits.startswith('keV'):
        energy = energy /1000.0
    elif eunits.startswith('deg'):
        print('Need to convert angle to energy')

    try:
        e0 = edge_energies[int(s.element_z)][str(opts['edge'])]
        opts['e0'] = '%f' % e0
    except:
        pass

    plot_mode = mode = db.get_spectrum_mode(spid)

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
        return render_template('spectrum.html', **opts)

    dgroup = preedge(energy, mudata)
    # get reference if possible
    try:
        irefer = np.array(json.loads(s.irefer))
        refmode = opts.get('refmode', 'none')
        if refmode.startswith('none'):
            murefer = None
        elif refmode.startswith('mu'):
            murefer = irefer
        elif refmode.startswith('trans'):
            murefer = -np.log(irefer/itrans)
        elif refmode.startswith('fluor') and 'itrans' in rmode:
            murefer = irefer/itrans
        else:
            murefer = irefer/i0
    except:
        murefer = None

    if plotstyle.lower() == 'rawxafs':
        opts['xasplot'] =  xafs_plotly(energy, mudata, s.name, ylabel='Raw XAFS')
        opts['plotstyle'] = 'xanes'
        opts['plotstyle_label'] = 'normalized XANES'
        if murefer is not None:
            opts['plotstyle_label'] = 'normalized XANES, with reference spectra'
    else:
        opts['plotstyle'] = 'rawxafs'
        opts['plotstyle_label'] = 'Raw XAFS'

        emin = max(e0-50, min(energy))
        emax = min(e0+175, max(energy))

        ie1 = index_of(energy, emin)
        ie2 = index_of(energy, emax)
        ymax = max(dgroup['norm'][ie1:ie2])
        ymin = min(dgroup['norm'][ie1:ie2])
        ymax += (ymax-ymin)*0.05
        ymin -= (ymax-ymin)*0.05

        ref_mu = None
        if murefer is not None:
            rgroup = preedge(energy, murefer)
            ref_mu = rgroup['norm']
        opts['xasplot'] = xafs_plotly(energy, dgroup['norm'], s.name,
                                      ylabel='Normalized XANES',
                                      refer=ref_mu, x_range=[emin, emax],
                                      y_range=[ymin, ymax])

    suites = []
    for r in db.lookup('spectrum_suite', spectrum_id=s.id):
        st = db.lookup('suite', id=r.suite_id)[0]
        suites.append({'id': r.suite_id, 'name': st.name})
    opts['nsuites'] = len(suites)
    opts['suites'] = suites
    opts['owned_suites'] = get_person_suites(db, session['person_id'])
    return render_template('spectrum.html', **opts)

@app.route('/showspectrum_rating/<int:spid>')
def showspectrum_rating(spid=None):
    session_init(session)
    s  = db.get_spectrum(spid)
    if s is None:
        return sendback('spectrum', error='Could not find Spectrum #%d' % spid)

    opts = parse_spectrum(s, db)
    ratings = []
    for row in db.get_spectrum_ratings(spid):
        person = db.get_person(row.person_id)
        ratings.append({'score': row.score,
                        'review': multiline_text(row.comments),
                        'date': isotime(row.datetime),
                        'person_email': person.email,
                        'person_name': person.name,
                        'person_affil': person.affiliation})

    return render_template('show_spectrum_ratings.html',
                           ratings=ratings,
                           spectrum_name=opts['spectrum_name'])


@app.route('/submit_spectrum_edits', methods=['GET', 'POST'])
def submit_spectrum_edits():
    session_init(session)
    error=None
    if session['username'] is None:
        needslogin(error='to edit spectrum')

    spid = 0
    if request.method == 'POST':
        spid  = int(request.form['spectrum'])
        edge_id = ANY_EDGES.index(request.form['edge'])
        mode_id = ANY_MODES.index(request.form['mode'])
        try:
            collection_date = isotime2datetime(request.form['collection_date'])
        except:
            collection_date = None

        db.update('spectrum', int(spid),
                  name=request.form['name'],
                  description=request.form['description'],
                  comments=request.form['comments'],
                  d_spacing=float(request.form['d_spacing']),
                  energy_resolution=request.form['e_resolution'],
                  edge_id=edge_id, mode_id=mode_id,
                  beamline_id= int(request.form['beamline']),
                  sample_id= int(request.form['sample']),
                  collection_date=collection_date,
                  reference_sampled=request.form['reference_sample'],
                  energy_units_id=int(request.form['energy_units']))

        time.sleep(0.25)
    return redirect(url_for('spectrum', spid=spid, error=error))

@app.route('/edit_spectrum/<int:spid>')
def edit_spectrum(spid=None):
    session_init(session)
    error=None
    if session['username'] is None:
        needslogin(error='to edit spectrum')

    s  = db.get_spectrum(spid)
    if s is None:
        return redirect(url_for('/', error='Could not find Spectrum #%d' % spid))

    opts = parse_spectrum(s, db)
    return render_template('edit_spectrum.html',
                           error=error,
                           elems=db.lookup('element'),
                           eunits=db.lookup('energy_units'),
                           edges=ANY_EDGES[1:],
                           beamlines=db.get_beamline_list(),
                           samples=SAMPLES_OR_NEW,
                           modes=ANY_MODES[1:], **opts)


@app.route('/delete_spectrum/<int:spid>')
@app.route('/delete_spectrum/<int:spid>/ask=<int:ask>')
def delete_spectrum(spid, ask=1):
    session_init(session)
    error=None
    if session['username'] is None:
        return needslogin(error='to delete a spectrum')

    spect_name = db.lookup('spectrum', id=spid)[0].name
    if ask != 0:
        return render_template('confirm_delete_spectrum.html',
                               spectrum_id=spid,
                               spectrum_name=spect_name)

    else:
        db.del_spectrum(spid)
        time.sleep(1)
        flash('Deleted spectrum %s' % spect_name)
    return sendback(error=error)


@app.route('/submit_spectrum_rating', methods=['GET', 'POST'])
def submit_spectrum_rating(spid=None):
    session_init(session)
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
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to rate spectrum'
        return redirect(url_for('spectrum', spid=spid, error=error))

    pid = int(session['person_id'])
    s  = db.get_spectrum(spid)
    if s is None:
        return sendback(error='Could not find Spectrum #%d' % spid)

    opts = parse_spectrum(s, db)
    score = 3
    review = ''
    for _s, _r, _d, _p in spectrum_ratings(db, spid):
        if int(_p) == pid:
            score = _s
            review =  _r
    spid = s.id
    spname = s.name
    if isinstance(score, (int, float)):
        score= '%d' % score
    return render_template('rate_spectrum.html', error=error,
                           spectrum_id=spid, spectrum_name=spname,
                           person_id=pid, score=score, review=review)


@app.route('/submit_suite_rating', methods=['GET', 'POST'])
def submit_suite_rating(spid=None):
    session_init(session)
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
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to rate suite'
        return redirect(url_for('suites', stid=stid, error=error))

    st = db.lookup('suite', id=stid, none_if_empty=True)
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
    session_init(session)

    st = db.lookup('suite', none_if_empty=True)
    if st is None:
        error = 'Could not find Suite #%d' % stid
        return redirect(url_for('suites', error=error))

    ratings = []
    for row in db.get_suite_ratings(stid):
        person = db.get_person(row.person_id)
        ratings.append({'score': row.score,
                        'review': multiline_text(row.comments),
                        'date': isotime(row.datetime),
                        'person_email': person.email,
                        'person_name': person.name,
                        'person_affil': person.affiliation})

    return render_template('show_suite_ratings.html',
                           ratings=ratings, suite_notes=st.notes,
                           suite_name=st.name)

@app.route('/add_spectrum_to_suite',  methods=['GET', 'POST'])
def add_spectrum_to_suite():
    session_init(session)
    error = None
    spid = int(request.form.get('spectrum', -1))
    if session['username'] is None:
        error='must be logged in to add spectrum to suite'
        return redirect(url_for('spectrum', spid=spid, error=error))

    person_id = int(request.form.get('person', -1))
    if person_id < 1 and ('person_id' in request.form):
        person_id = request.form.get('person', -1)
    if person_id < 1:
        session_init(session)
        person_id = getattr(session, 'person_id', -1)
    if person_id > 0:
        suite_id = int(request.form.get('target_suite', -1))
        flash(add_spectra_to_suite(db, [spid], suite_id=suite_id,
                                   person_id=person_id))
    return redirect(url_for('spectrum', spid=spid, error=error))


@app.route('/submit_spectrum_to_suite', methods=['GET', 'POST'])
def submit_spectrum_to_suite():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to add spectrum to a suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        spid  = int(request.form['spectrum_id'])
        stid  = int(request.form['suite_id'])
        pid   = request.form['person']

        found = False
        for r in db.lookup('spectrum_suite', suite_id=stid):
            found = found or (r.spectrum_id == spid)
        if not found:
            db.addrow('spectrum_suite', suite_id=stid, spectrum_id=spid)
            time.sleep(0.1)
        else:
            stname = db.lookup('suite', id=stid)[0].name
            spname = db.get_spectrum(spid).name
            error = "Spectrum '%s' is already in Suite '%s'" % (spname, stname)

    return redirect(url_for('suites', error=error))


@app.route('/rawfile/<int:spid>/<fname>')
def rawfile(spid, fname):
    session_init(session)
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

@app.route('/show_person')
@app.route('/show_person/')
@app.route('/show_person/<int:pid>')
def show_person(pid=-1):
    session_init(session)
    person = db.get_person(pid)
    suites = db.lookup('suite', person_id=pid)
    spectra = db.lookup('spectrum', person_id=pid)
    # print(len(suites), len(spectra), pid)
    return render_template('person.html', person=person, suites=suites,
                           spectra=spectra)



@app.route('/suites')
@app.route('/suites/')
@app.route('/suites/<int:stid>')
def suites(stid=None):
    session_init(session)
    suites = []
    person = db.get_person(1)
    if stid is None:
        for st in db.lookup('suite'):
            person = db.get_person(st.person_id)
            spectra = spectra_for_suite(db, st.id)
            is_owner = (int(session['person_id']) == int(st.person_id))
            suites.append({'id': st.id, 'name': st.name, 'notes': st.notes,
                           'rating': get_rating(st),
                           'suite_owner': is_owner,
                           'nspectra': len(spectra), 'spectra': spectra})

    else:
        st = db.lookup('suite', id=stid)[0]
        person = db.get_person(st.person_id)
        spectra = spectra_for_suite(db, stid)
        is_owner = (int(session['person_id']) == int(st.person_id))

        suites.append({'id': stid, 'name': st.name, 'notes': st.notes,
                       'rating': get_rating(st),
                       'suite_owner': is_owner,
                       'nspectra': len(spectra), 'spectra': spectra})
        # print('spectra for suite ', stid, spectra)

    return render_template('suites.html', nsuites=len(suites), suites=suites,
                           person=person)



@app.route('/suite_action', methods=['GET', 'POST'])
def suite_action():
    session_init(session)
    error=None
    person_id = int(session['person_id'])
    button = request.form.get('submit', 'no button').lower()
    stid = int(request.form.get('suite'))
    suite = db.lookup('suite', id=stid)[0]

    selected = []
    for key, val in request.form.items():
        if key.startswith('sel_'):
            selected.append(int(key[4:]))

    if button.startswith('plot') and len(selected) > 0:
        pdata = plot_multiple_spectra(db, selected,
                                      title="Spectra from '%s'" % suite.name)
        return render_template('show_plot.html', nspectra=len(selected),
                               permalink=make_permalink(selected), plotdata=pdata)


    elif button.startswith('save') and len(selected) > 0:
        fname = save_zipfile(db, selected, folder=app.config['DOWNLOAD_FOLDER'])
        aname = secure_filename("%s.zip" % suite.name)
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], fname,
                                   mimetype='application/zip',
                                   as_attachment=True,
                                   download_name=aname)

    return reidrect(url_for('suites', stid=stid))


@app.route('/plots/<int:s1>')
@app.route('/plots/<int:s1>/<int:s2>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>/<int:s16>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>/<int:s16>/<int:s17>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>/<int:s16>/<int:s17>/<int:s18>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>/<int:s16>/<int:s17>/<int:s18>/<int:s19>')
@app.route('/plots/<int:s1>/<int:s2>/<int:s3>/<int:s4>/<int:s5>/<int:s6>/<int:s7>/<int:s8>/<int:s9>/<int:s10>/<int:s11>/<int:s12>/<int:s13>/<int:s14>/<int:s15>/<int:s16>/<int:s17>/<int:s18>/<int:s19>/<int:s20>')
def plots(s1=0, s2=0, s3=0, s4=0, s5=0, s6=0, s7=0, s8=0, s9=0, s10=0, s11=0,
          s12=0, s13=0, s14=0, s15=0, s16=0, s17=0, s18=0, s19=0, s20=0):
    session_init(session)
    selected = []
    for s in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14,
              s15, s16, s17, s18, s19, s20):
        if s == 0:
            break
        selected.append(s)
    if len(selected) > 0:
        return render_template('show_plot.html', nspectra=len(selected),
                               permalink=make_permalink(selected),
                               plotdata=plot_multiple_spectra(db, selected))


@app.route('/add_suite')
@app.route('/add_suite', methods=['GET', 'POST'])
def add_suite():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to add a suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        suite_name = request.form['suite_name']
        person_id = request.form['person']
        notes = request.form['notes']
        _sname = [s.name for s in db.lookup('suite')]
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
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to delete a suite'
        return redirect(url_for('suites', error=error))

    suite_name = db.lookup('suite', id=stid)[0].name
    if ask != 0:
        return render_template('confirm_delete_suite.html', stid=stid,
                               suite_name=suite_name)

    else:
        db.del_suite(stid)
        time.sleep(1)
        flash('Deleted suite %s' % suite_name)
    return redirect(url_for('suites', error=error))

@app.route('/edit_suite/<int:stid>')
def edit_suite(stid=None):
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to edit suite'
        return redirect(url_for('suites', error=error))

    st = db.lookup('suite', id=stid)[0]
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
    session_init(session)
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
            if ('remove_%d' % spid) in request.form:
                db.remove_spectrum_from_suite(stid, spid)
        time.sleep(0.1)

    return redirect(url_for('suites', stid=stid, error=error))


@app.route('/sample/<int:sid>')
def sample(sid=None):
    session_init(session)
    sdat = db.lookup('sample', id=sid, none_if_empty=True)
    if sdat is None:
        return sendback(error='no sample #%d found' % sid)

    opts = row2dict(sdat)
    has_image = opts.get('image_data', None) is not None
    opts['spectra'] = db.lookup('spectrum', sample_id=sid)
    return render_template('sample.html', sid=sid, has_image=has_image, **opts)


@app.route('/samples')
@app.route('/samples/')
@app.route('/samples/<int:sid>')
@app.route('/samples/<order_by>')
@app.route('/samples/<order_by>/<reverse>')
def samples(blid=None, order_by='name', reverse=0):
    session_init(session, force_refresh=(SAMPLES_DATA is None))

    if order_by not in ('name', 'formula', 'nspectra'):
        order_by = 'name'
    samples = [s for s in SAMPLES_DATA]
    samples = sorted(samples, key=lambda k: k[order_by])

    reverse = int(reverse)
    if reverse != 0:
        samples.reverse()
    return render_template('samples.html', samples=samples,
                           reverse=(0 if reverse else 1))


@app.route('/new_sample')
@app.route('/new_sample/')
@app.route('/new_sample/<int:spid>')
def new_sample(spid=None):
    session_init(session)
    error = None
    if session['username'] is None:
        error='must be logged in to create a sample'
        return redirect(url_for('spectrum', spid=spid, error=error))

    sid = db.add_sample('New Sample', session['person_id'])
    if spid is not None:
        db.update('spectrum', spid, use_id=True, sample_id=sid)
    session_init(session, force_refresh=True)
    return redirect(url_for('edit_sample', sid=sid,  error=error))


@app.route('/select_spectrum_sample/<int:spid>/<int:sid>')
def select_spectrum_sample(spid=None, sid=None):
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return redirect(url_for('spectrum', spid=spid, error=error))

    opts = {'spectra': db.lookup('spectrum', sample_id=sid)}
    sdat = db.lookup('sample', id=sid, none_if_empty=True)
    if sdat is not None:
        opts = row2dict(sdat)
    opts['has_image'] = opts.get('image_data', None) is not None

    return render_template('edit_sample.html', sid=sid, spid=spid, **opts)

@app.route('/edit_sample/<int:sid>')
def edit_sample(sid=None):
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return redirect(url_for('/', error=error))

    sdat = db.lookup('sample', id=sid, none_if_empty=True)
    if sdat is None:
        error='Cannot find sample to edit'
        return redirect(url_for('/', error=error))

    opts = row2dict(sdat)
    opts['has_image'] = opts.get('image_data', None) is not None

    opts['spectra'] = db.lookup('spectrum', sample_id=sid)
    return render_template('edit_sample.html', sid=sid, **opts)

@app.route('/submit_sample_edits', methods=['GET', 'POST'])
def submit_sample_edits():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to edit sample'
        return render_template('/', error=error)

    sid = 0
    if request.method == 'POST':
        sid  = request.form['sample_id']
        pid  = request.form['person_id']
        name = request.form['name']
        notes = request.form['notes']
        prep = request.form['preparation']
        formula = request.form['formula']
        cas_number = request.form['cas_number']
        image_data = None
        ###
        img_file = request.files['image_filename']
        if img_file:
            fullpath = get_fullpath(img_file, app.config['UPLOAD_FOLDER'])
            mimetype = img_file.mimetype
            try:
                img_file.save(fullpath)
            except IOError:
                return render_template('sample.html',
                                       person_id=session['person_id'],
                                       error='Could not save image file')

            time.sleep(0.250)

            try:
                dat = open(fullpath, 'rb').read()
            except:
                return render_template('sample.html',
                                       person_id=session['person_id'],
                                       error='Could not read uploaded file')

            image_data = "data:%s;base64,%s" % (mimetype,
                                                base64.b64encode(dat).decode('utf-8'))
        ###
        db.update('sample', int(sid), person=pid, name=name, notes=notes,
                  formula=formula,  preparation=prep, cas_number=cas_number,
                  image_data=image_data)
        time.sleep(0.1)
    session_init(session, force_refresh=True)
    return redirect(url_for('sample', sid=sid, error=error))

@app.route('/beamlines')
@app.route('/beamlines/')
@app.route('/beamlines/<int:blid>')
@app.route('/beamlines/<order_by>')
@app.route('/beamlines/<order_by>/<reverse>')
def beamlines(blid=None, order_by='name', reverse=0):
    session_init(session, force_refresh=(BEAMLINE_DATA is None))

    if order_by not in ('name', 'nickname', 'nspectra', 'facility'):
        order_by = 'name'

    beamlines = [b for b in BEAMLINE_DATA]
    try:
        beamlines = sorted(BEAMLINE_DATA, key=lambda k: k[order_by])
    except:
        pass
    reverse = int(reverse)
    if reverse != 0:
        beamlines.reverse()
    return render_template('beamlines.html',
                           nbeamlines=len(beamlines),
                           beamlines=db.get_beamline_list(),
                           reverse=(0 if reverse else 1))

@app.route('/beamline/')
@app.route('/beamline/<int:blid>')
def beamline(blid=None):
    session_init(session)
    if blid is None:
        return sendback('beamlines')
    bldat = db.lookup('beamline', id=blid, none_if_empty=True)
    if bldat is None:
        return sendback('beamlines', error='Beamline #%d not found' % blid)

    fac = db.lookup('facility', id=bldat.facility_id)[0]
    loc = fac.country
    if fac.city is not None and len(fac.city) > 0:
        loc = "%s, %s" % (fac.city, fac.country)

    spectra = spectra_for_beamline(db, blid)
    beamlines = [{'id': blid,
                  'name': bldat.name,
                  'nickname': bldat.nickname,
                  'facility': fac.name,
                  'facility_id': fac.id,
                  'location': loc,
                  'nspectra': len(spectra),
                  'spectra': spectra}]

    return render_template('beamlines.html', nbeamlines=1,
                           beamlines=beamlines, reverse=0)


@app.route('/add_beamline')
@app.route('/add_beamline', methods=['GET', 'POST'])
def add_beamline():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to add a beamline'
        return redirect(url_for('beamline', error=error))

    if request.method == 'POST':
        bl_name = request.form['beamline_name']
        notes = request.form['notes']
        fac_id = int(request.form['fac_id'])
        source = request.form['xray_source']

        _blnames = [s.name for s in db.lookup('beamline')]
        try:
            bl_name = unique_name(bl_name, _blnames,
                                  msg='beamline', maxcount=5)
        except:
            error = 'a beamline named %s exists'

        bl = db.add_beamline(bl_name, notes=notes, xray_source=source,
                             facility_id=fac_id)
        time.sleep(0.25)
        session_init(session, force_refresh=True)
        return redirect(url_for('beamline', blid=bl.id, error=error))
    else:
        return render_template('add_beamline.html', error=error,
                               facilities=db.get_facilities(order_by='country'))


@app.route('/add_facility')
@app.route('/add_facility', methods=['GET', 'POST'])
def add_facility():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to add a facility'
        return redirect(url_for('facilities', error=error))

    if request.method == 'POST':
        fac_name = request.form['facility_name']
        _facnames = [s.name for s in db.lookup('facility')]
        try:
            fac_name = unique_name(fac_name, _facnames,  msg='facility', maxcount=5)
        except:
            error = 'a facility named %s exists'
        db.add_beamline(fac_name)
        time.sleep(0.25)
        session_init(session, force_refresh=True)
        return redirect(url_for('facilities', error=error))
    else:
        return render_template('add_facility.html', error=error,
                               facilities=db.get_facilities(order_by='country'))

@app.route('/facilities')
@app.route('/facilities/')
def facilities():
    session_init(session)
    return render_template('facilities.html', error=None,
                           facilities=db.get_facilities(order_by='country'))

@app.route('/edit_facility/<int:fid>')
def edit_facility(fid=None):
    session_init(session)
    return render_template('edit_facility.html', error=None,
                           fac = db.get_facility(id=int(fid)),
                           person_id=session['person_id'])


@app.route('/submit_facility_edits', methods=['GET', 'POST'])
def submit_facility_edits():
    session_init(session)
    error=None
    if session['username'] is None:
        return redirect(url_for('/',
                                error='must be logged in to edit facility'))

    fid = 0
    fid  = int(request.form.get('facility_id', -1))
    if fid < 0:
        return redirect(url_for('/',
                                error='could not edit facility'))

    if request.method == 'POST':
        o = db.update('facility', fid,
                      name=request.form['name'],
                      fullname=request.form['fullname'],
                      laboratory=request.form['laboratory'],
                      city=request.form['city'],
                      country=request.form['country'])
        time.sleep(0.25)

    return redirect(url_for('facilities', error=error))


@app.route('/citation')
@app.route('/citation/')
@app.route('/citation/<int:cid>')
def citation(cid=None):
    session_init(session)
    kws = {}
    if cid is not None:
        kws['id'] = cid

    citations = []
    for cit in db.lookup('citation', **kws):
        person_id = cit.person_id
        person_email = db.get_person(person_id).email
        spectra = spectra_for_citation(db, cid)
        is_owner = (int(session['person_id']) == int(person_id))
        citations.append({'id': cid, 'person_email': person_email,
                          'person_id':person_id, 'citation': cit,
                          'is_owner': is_owner, 'nspectra': len(spectra),
                          'spectra':spectra})

    return render_template('citations.html', citation_id=cid,
                           ncitations=len(citations), citations=citations)



@app.route('/add_citation')
@app.route('/add_citation', methods=['GET', 'POST'])
def add_citation(spid=None):
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to add citation for spectrum'
        return redirect(url_for('citation',  error=error))

    pid = int(session['person_id'])
    return render_template('add_citation.html', person_id=pid, spectrum_id=spid,
                           authors='')

@app.route('/submit_citation_edits', methods=['GET', 'POST'])
def submit_citation_edits():
    session_init(session)
    error=None
    if session['username'] is None:
        error='must be logged in to edit suite'
        return redirect(url_for('suites', error=error))

    if request.method == 'POST':
        form = {k: v for k, v in request.form.items()}
        person_id   = form.pop('person_id')
        citation_id = form.pop('citation_id')
        spectrum_id = form.pop('spectrum_id')
        name = form.pop('name')
        try:
            cid  = int(citation_id)
        except:
            cid = None

        if cid is None: # new citation
            cid = db.add_citation(name=name, **form)
        else:
            db.update('citation', cid, use_id=True, name=name, **form)

        time.sleep(0.25)
        return redirect(url_for('citation', cid=cid, error=error))
    return redirect(url_for('citation', error=error))



@app.route('/upload')
@app.route('/upload/')
def upload():
    session_init(session)
    return render_template('upload.html',
                           person_id=session['person_id'])

def parse_datagroup(dgroup, fname, fullpath, pid, form=None):
    person = db.get_person(int(pid))
    filename = dgroup.filename
    narrays, npts = dgroup.data.shape

    array_labels = ['None'] + dgroup.array_labels
    if npts > 16384:
        npts = 16384
        dgroup.data = dgroup.data[:, :npts]
    if narrays > 17:
        narrays = 17
        array_labels = array_labels[:narrays]
        dgroup.data = dgroup.data[:narrays, :]

    if len(array_labels) < 3:
        array_labels.extend(['None', 'None'])

    labels = {'en':array_labels[1], 'i0':array_labels[2],
              'i1':array_labels[3], 'if':'None', 'ir':'None'}

    desc = '{} uploaded  {}'.format(fname, isotime())

    opts = dict(elems=ALL_ELEMS,
                eunits=EN_UNITS,
                edges=ANY_EDGES[1:],
                beamlines=BEAMLINES,
                samples=SAMPLES_OR_NEW,
                modes=ANY_MODES[1:],
                gen_monos=GEN_MONOS,
                ref_modes=REFERENCE_MODES,
                ref_mode=REFERENCE_MODES[0])

    opts.update(dict(person_id=pid,
                     filename=fname,
                     fullpath=fullpath,
                     error=None,
                     description=desc,
                     mode='transmission',
                     e_resolution='nominal',
                     beamline=BEAMLINES[0],
                     reference_sample='',
                     person_email=person.email,
                     person_name=person.name,
                     upload_date=isotime(),
                     collection_date=isotime(),
                     en_arrayname=array_labels[1],
                     i0_arrayname=array_labels[2],
                     it_arrayname=array_labels[3],
                     if_arrayname='None',
                     ir_arrayname='None',
                     elem_sym='Cu',
                     edge='K',
                     energy_units='eV',
                     d_spacing='-1',
                     mono_name='',
                     sample=0,
                     array_labels=array_labels,
                     narrays=narrays,
                     npts=npts,
                     header=dgroup.header))

    opts.update(**guess_metadata(dgroup))
    if opts['has_reference']:
        opts['ref_choice'] = REFERENCE_MODES[1]
    return opts


@app.route('/edit_upload', methods=['GET', 'POST'])
def edit_upload():
    session_init(session)
    error =     None
    if session['username'] is None:
        return needslogin(error='to submit a spectrum')
    if request.method == 'POST':
        pid    = request.form['person_id']
        person = db.get_person(int(pid))
        file = request.files['filename']
        fname =  secure_filename(file.filename)
        if file:
            fullpath = get_fullpath(file, app.config['UPLOAD_FOLDER'])
            try:
                file.save(fullpath)
            except IOError:
                print("edit_upload failed ", session, fname, file.filename,
                      app.config['UPLOAD_FOLDER'])
                return render_template('upload.html',
                                       person_id=session['person_id'],
                                       error='Could not save uploaded file (%s)' % (file.filename))

            time.sleep(0.50)
            try:
                dgroup = read_ascii(fullpath)
            except:
                return render_template('upload.html', person_id=pid,
                                       error='Could not read uploaded file (%s)' % (fname))

            opts = parse_datagroup(dgroup, fname, fullpath, pid)
            return render_template('edit_uploadspectrum.html', **opts)

    return render_template('upload.html',
                           person_id=session['person_id'],
                           error='upload error (method?)')


def verify_uploaded_data(form, with_arrays=False):
    pid    = form['person_id']
    person = db.get_person(int(pid))

    fullpath = form.get('fullpath', None)
    if fullpath is None or not os.path.exists(fullpath):
        return {'verify_read': 'nofile', 'pid': pid, 'fname': fullpath}

    dname, fname =  os.path.split(fullpath)
    fname = secure_filename(fname)
    try:
        dgroup = read_ascii(fullpath)
    except:
        return {'verirfy_read': 'noread', 'pid': pid, 'fname': fname}

    opts = parse_datagroup(dgroup, fname, fullpath, pid)
    for key, val in form.items():
        opts[key] = val

    opts['verify_read'] = 'OK'
    opts['verify_ok']   = 1
    opts['verify_messages']   = []
    opts['verify_errors']   = []

    if float(opts['d_spacing']) < 0.0:
        opts['verify_ok']  = 0
        opts['verify_errors'].append('d-spacing for mono cannot be < 0')

    mode = form['mode'].lower()
    energy = getattr(dgroup, form['en_arrayname'])
    if opts['energy_units'].lower().startswith('kev'):
        energy = 1000.0 * energy
    elif opts['energy_units'].lower().startswith('deg') and float(opts['d_spacing']) > 0.0:
        energy = mono_deg2ev(energy, float(opts['d_spacing']))


    i0 = getattr(dgroup, form['i0_arrayname'], None)
    itrans = getattr(dgroup, form['it_arrayname'], None)
    ifluor = irefer = mu = murefer = None

    if mode.startswith('trans'):
        itrans = getattr(dgroup, form['it_arrayname'], None)
        if 'is_mutrans' in form:
            mu = itrans
        elif itrans is not None and i0 is not None:
            mu = -np.log(itrans/i0)
    elif 'if_arrayname' in form:
        ifluor = getattr(dgroup, form['if_arrayname'], None)
        if 'is_mufluor' in form:
            mu = ifluor
        elif ifluor is not None and i0 is not None:
            mu = ifluor/i0
    else:
        print("Could not get mu array")

    ir_arrayname = form.get('ir_arrayname', None)
    refmode = form.get('ref_mode', 'none').lower()
    if ir_arrayname is not None and refmode != 'none':
        irefer = getattr(dgroup, ir_arrayname, None)
        if irefer is None:
            murefer = None
        elif refmode.startswith('mu'):
            murefer = irefer
        elif refmode.startswith('trans'):
            murefer = -np.log(irefer/itrans)
        elif refmode.startswith('fluor') and 'itrans' in refmode:
            murefer = irefer/itrans
        elif refmode.startswith('fluor') and 'i0' in refmode:
            murefer = irefer/i0

    # ensure data is ordered by increasing energy:
    en_order = np.argsort(energy)
    if abs(np.diff(en_order) - 1).sum() > 0: # there is some out-of-order data
        energy = energy[en_order]
        mu = mu[en_order]
        i0 = i0[en_order]
        if itrans is not None:
            itrans = itrans[en_order]
        if ifluor is not None:
            ifluor = ifluor[en_order]
        if irefer is not None:
            irefer = irefer[en_order]
        if murefer is not None:
            murefer = murefer[en_order]

    try:
        opts['muplot'] =  xafs_plotly(energy, mu, fname, ylabel=mode, refer=murefer)
    except:
        opts['muplot'] =  'noplot'
        opts['verify_ok']  = 0
        opts['verify_errors'].append('could not plot data -- arrays must not be correct')


    if opts['beamline'] == ANY_BEAMLINES[0]:
        opts['verify_ok']  = 0
        opts['verify_errors'].append('Must select a valid beamline')

    try:
        pgroup = preedge(energy, mu)
    except:
        pgroup = {'e0': 0, 'edge_step': 0}

    opts['verify_edge_energy'] = "%.2f" % pgroup['e0']
    opts['verify_edge_step']   = "%10.5g" % pgroup['edge_step']
    opts['verify_edge_range']  = "[%10.5g, %10.5g]" % (min(energy), max(energy))

    elem_z = elem_syms.index(opts['elem_sym'])
    nominal_e0 = edge_energies[elem_z][opts['edge']]

    e0msg = "%sEdge energy appears %s for %s %s edge (expected %.2f)"
    if abs(pgroup['e0'] - nominal_e0) > 200:
        opts['verify_ok']  = 0
        opts['verify_errors'].append(e0msg % ('', 'too far off', opts['elem_sym'],
                                                opts['edge'], nominal_e0))

    elif abs(pgroup['e0'] - nominal_e0) > 25:
        opts['verify_messages'].append(e0msg % ('Warning: ',
                                                'a little off', opts['elem_sym'],
                                                opts['edge'], nominal_e0))

    if pgroup['edge_step'] < -1.e-5:
        opts['verify_ok']  = 0
        opts['verify_errors'].append('Edge jump is negative')
    elif pgroup['edge_step'] < 1.e-5:
        opts['verify_messages'].append('Warning: Edge jump looks very small')

    if min(np.diff(energy)) < 0.001:
        opts['verify_messages'].append('Warning: Energy array has some very small steps')

    opts['sample'] = int(opts['sample'])
    if opts['sample'] > 0:
        s = db.lookup('sample', id=opts['sample'], none_if_empty=True)
        if s is not None:
            opts['sample_name'] = s.name
            opts['sample_prep'] = s.preparation
            opts['sample_notes'] = s.notes.replace('\n', ', ')[:128]
            opts['sample_formula'] = s.formula

    if opts['verify_ok']:
        opts['verify_messages'].append('')
        opts['verify_messages'].append('Data looks OK for upload')
        if with_arrays:
            if energy is not None:
                energy = energy.tolist()
            if i0 is not None:
                i0 = i0.tolist()
            if itrans is not None:
                itrans = itrans.tolist()
            if ifluor is not None:
                ifluor = ifluor.tolist()
            if irefer is not None:
                irefer = irefer.tolist()
            if mu is not None:
                mu = mu.tolist()

            opts['data'] = {'energy': energy, 'i0': i0, 'itrans': itrans,
                            'ifluor': ifluor, 'irefer': irefer, 'mu': mu}
    return opts


@app.route('/verify_upload', methods=['GET', 'POST'])
def verify_upload():
    session_init(session)
    error=None
    if session['username'] is None:
        return needslogin(error='to submit a spectrum')

    if request.method != 'POST':
        return sendback('upload', error='upload must use POST')

    opts = verify_uploaded_data(request.form)
    if opts['verify_read'] != 'OK':
        error = 'cannot locate file (%s)' % opts['fname']
        if opts['verify_error'] == 'noread':
            error = 'Could not read uploaded file (%s)' % (opts['fname'])
        return sendback('upload', error=error, person_id=opts['pid'])
    return render_template('verify_uploadspectrum.html', **opts)


@app.route('/submit_upload', methods=['GET', 'POST'])
def submit_upload():
    session_init(session)
    error=None
    if session['username'] is None:
        return needslogin(error='to submit a spectrum')

    if request.method != 'POST':
        return sendback('upload', error='upload must use POST')

    pid    = request.form['person_id']
    pemail = db.get_person(int(pid)).email
    if request.form.get('submit', '').lower().startswith('verify'):
        opts = verify_uploaded_data(request.form)
        if opts['verify_read'] != 'OK':
            error = 'cannot locate file (%s)' % opts['fname']
            if opts['verify_error'] == 'noread':
                error = 'Could not read uploaded file (%s)' % (opts['fname'])
            return sendback('upload', error=error, person_id=opts['pid'])

        return render_template('verify_uploadspectrum.html', **opts)

    else:
        spid = 1
        opts = verify_uploaded_data(request.form, with_arrays=True)
        filename = upload2xdi(opts, app.config['UPLOAD_FOLDER'])
        time.sleep(0.25)
        spid = db.add_xdifile(filename, person=pemail,
                              spectrum_name=opts['filename'],
                              description=opts['description'],
                              create_sample=True)
        time.sleep(0.25)
        session_init(session, force_refresh=True)

        return redirect(url_for('spectrum', spid=spid, error=error))



if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(port=PORT)
