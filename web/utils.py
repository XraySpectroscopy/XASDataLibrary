import os
import json
import time
import base64
from collections import namedtuple
from datetime import datetime
from random import randrange
from string import printable

from xasdb import fmttime

def make_secret_key():
    "make a secret key for web app"
    f = open('secret.py', 'w')
    f.write("session_key = '%s'\n" % base64.b64encode(os.urandom(36)))
    f.close()

def get_session_key():
    try:
        from secret import session_key
    except ImportError:
        make_secret_key()
        time.sleep(0.5)
        from secret import session_key
    return session_key

# def get_session_key():
#     return base64.b64encode(os.urandom(36))

def dict_repr(d):
    return ', '.join(["%s: %s" % (u) for u in d.items()])

def random_string(n):
    """  random_string(n)
    generates a random string of length n, that will match
       [a-z](n)
    """
    return ''.join([printable[randrange(10,36)] for i in range(n)])

def multiline_text(s):
    if '\n' in s:
        return '%s' % (s.replace('\n', '<br>'))

def session_clear(session):
    for s in ('elements', 'edges', 'energy_units', 'facilities',
              'beamlines', 'spectra', 'samples', 'suites', 'people'):
        if s in session:
            session.pop(s)

def session_init(session, db):
    if 'last_refresh' not in session:
        session['last_refresh'] = 0.0

    if time.time() - session.get('last_refresh', time.time()) > 1800.0:
        session_clear(session)
        session['last_refresh'] = time.time()

    if 'username' not in session:
        session['username'] = None

    if 'person_id' not in session:
        session['person_id'] = "-1"

    if 'logged_in' not in session:
        session['logged_in'] = False

    if 'elements' not in session:
        session['elements'] = d = {}
        session['element_list'] = l = []        
        for r in db.get_elements():
            d['%i'%r.z]  = (r.symbol, r.name)
            l.append({'z': '%i' % r.z, 'symbol': r.symbol,
                      'name': r.name})
            
    if 'edges' not in session:
        session['edges'] = d = {}
        session['edge_list'] = l = []
        for r in db.get_edges():
            d['%i'%r.id]  = r.name
            l.append({'id': '%i' % r.id, 'name': r.name})

    if 'energy_units' not in session:
        session['energy_units'] = d = {}
        session['energy_units_list'] = l = []
        for r in db.filtered_query('energy_units'):
            d['%i'%r.id] = r.units
            l.append({'id': '%i' % r.id, 'units': r.units})
            
    if 'facilities' not in session:
        session['facilities'] = d = {}
        for r in db.get_facility():
            d['%i'%r.id] = (r.name, r.fullname,
                            r.laboratory, r.city,  r.region, r.country)

    if 'beamlines' not in session:
        session['beamlines'] = d = {}
        session['beamline_list'] = l = []
        for r in db.get_beamlines():
            facid = '%i' % r.facility_id
            facdat = session['facilities'][facid]
            d['%i'%r.id] = (r.name, r.notes, r.xray_source, facid, facdat[0])
            l.append({'id': '%i' % r.id,
                      'name': r.name,
                      'notes': r.notes,
                      'xray_source': r.xray_source,
                      'fac_id': facid,
                      'fac_name': facdat[0],
                      'fac_loc': "%s, %s" % (facdat[3], facdat[5])})


    if 'spectra' not in session:
        session['spectra'] = d = {}
        for r in db.get_spectra():
            d['%i'%r.id] = (r.name, r.element_z, r.edge_id, r.person_id)

    if 'samples' not in session:
        session['samples'] = d = {}
        session['sample_list'] = l = []           
        for r in db.filtered_query('sample'):
            d['%i'%r.id] = (r.name, r.formula, r.preparation,
                            r.material_source, r.notes, '%i'%r.person_id)
            l.append({'id': '%i' % r.id, 'name': r.name,
                      'formula': r.formula, 'notes': r.notes,
                      'preparation': r.preparation, 
                      'person_id': r.person_id,
                      'material_source': r.material_source})
            
    if 'suites' not in session:
        session['suites'] = d = {}
        session['suite_list'] = l = []
        for r in db.filtered_query('suite'):
            d['%i'%r.id] = (r.name, r.notes, '%i'%r.person_id)
            l.append({'id': '%i' % r.id, 'name': r.name,
                       'notes': r.notes, 'person_id': r.person_id})
            
    if 'people' not in session:
        session['people'] = d = {}
        session['people_list'] = l = []
        for r in db.get_persons():
            d['%i'%r.id] = (r.email, r.name, r.affiliation)
            l.append({'id': '%i' % r.id, 'email': r.email, 'name': r.name,
                      'affiliation': r.affiliation})

            
def spectrum_ratings(db, sid):
    """list of score, comments, time, person) for spectrum ratings"""
    d = []
    for r in db.filtered_query('spectrum_rating', spectrum_id=sid):
        d.append((r.score, r.comments, r.datetime, "%i" % r.person_id))
    return d

def suite_ratings(db, sid):
    """list of score, comments, time, person) for suite ratings"""
    d = []
    for r in db.filtered_query('suite_rating', suite_id=sid):
        d.append((r.score, r.comments, r.datetime, "%i" % r.person_id))
    return d

def get_suite_spectra(db, sid):
    'spectra in suite'
    d = []
    for r in db.filtered_query('spectrum_suite', suite_id=sid):
        d.append(r.spectrum_id)
    return d

def get_spectrum_suites(db, sid):
    'suites that a spectrum is in'
    d = []
    for r in db.filtered_query('spectrum_suite', spectrum_id=sid):
        d.append(r.suite_id)
    return d

def spectra_for_beamline(db, session, blid):
    spectra = []
    for r in db.get_spectra():
        if r.beamline_id is None or int(r.beamline_id) !=int(blid):
            continue
        _nam, _z, _edge, _pid = session['spectra']["%i" % (r.id)]
        elem_sym, elem_name = session['elements']["%i" % _z]
        edge =  session['edges']["%i" % _edge]
        spectra.append({'spectrum_id': r.id,
                        'name':    r.name,
                        'elem_sym': elem_sym, 'edge': edge})
    return spectra

def spectra_for_suite(db, session, stid):
    spectra = []
    for r in db.filtered_query('spectrum_suite', suite_id=int(stid)):
        _nam, _z, _edge, _pid = session['spectra']["%i" % (r.spectrum_id)]
        elem_sym, elem_name = session['elements']["%i" % _z]
        edge =  session['edges']["%i" % _edge]
        spectra.append({'spectrum_id': r.spectrum_id,
                        'name': _nam, 'elem_sym': elem_sym, 'edge': edge})
    return spectra


def parse_spectrum(s, session):
    edge = session['edges']['%i' % s.edge_id]
    elem = session['elements']['%i' % s.element_z]
    person = session['people']['%i' % s.person_id]

    eunits = session['energy_units']['%i'% s.energy_units_id]
    d_spacing = '%f'% s.d_spacing

    notes =  json.loads(s.notes)

    try:
        beamline_id  = '%i'% s.beamline_id
        beamline     = session['beamlines'][beamline_id]
        beamline_desc = '%s @ %s ' % (beamline[0], beamline[4])
    except:
        beamline_desc = 'unknown '
        beamline = None
        beamline_id  = '-1'
        tname = notes.get('beamline', {}).get('name', None)
        if tname is not None:
            beamline_desc = "%s -- may be '%s'" % (beamline_desc, tname)

    try:
        sample = session['samples']['%i'% s.sample_id]
        sample_id = '%i'% s.sample_id
        sample_name = sample[0]
        sample_form = sample[1]
        sample_prep = sample[2]
    except:
        sample_id  = '-1'        
        sample_name = 'unknown'
        sample_form = 'unknown'
        sample_prep = 'unknown'
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
            val = dict_repr(val).strip()
        if len(val) > 1:
            misc.append({'key': "# %s" % key.title(), 'val': val})

    return {'spectrum_id': s.id,
            'spectrum_name': s.name,
            'elem_sym': elem[0],
            'elem_name': elem[1],
            'edge': edge,
            'energy_units': eunits,
            'raw_comments': s.comments,
            'comments': multiline_text(s.comments),
            'beamline_id': beamline_id,
            'beamline_desc': beamline_desc,
            'beamline': beamline,
            'mononame': mononame,
            'd_spacing': d_spacing,
            'misc': misc,
            'sample_id':   sample_id,
            'sample_name':  sample_name,
            'sample_form':  sample_form,
            'sample_prep':  sample_prep,
            'person_email': person[0],
            'person_name': person[1],
            'upload_date': fmttime(s.submission_date),
            'collection_date': fmttime(s.collection_date),
            'fullfig': None,
            'xanesfig': None}
