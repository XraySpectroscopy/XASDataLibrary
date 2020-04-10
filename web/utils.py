from os import urandom, path

import json
import time
from base64 import b64encode
from collections import namedtuple
from datetime import datetime
from random import randrange
from string import printable
from sqlalchemy import text

try:
    from werkzeug.utils import secure_filename
except ImportError:
    from werkzeug import secure_filename

from xasdb import fmttime

def pathjoin(*args):
    return path.join(*args)

def get_fullpath(fileobj, upload_folder):
    fname = secure_filename(fileobj.filename)
    return path.abspath(pathjoin(upload_folder, fname))

def allowed_filename(filename):
    return ('.' in filename and
            len(filename) > 4 and
            filename.rsplit('.', 1)[1].lower() == 'xdi')

def make_secret_key():
    "make a secret key for web app"
    f = open('secret.py', 'w')
    f.write("session_key = '%s'\n" % b64encode(os.urandom(24)).decode('utf-8'))
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
    return ''.join([printable[randrange(10, 36)] for i in range(n)])

def multiline_text(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    if '\n' in s:
        return text('%s' % (s.replace('\n', '<br>')))

def session_clear(session):
    pass

def session_init(session, db):
    if 'username' not in session:
        session['username'] = None
    if 'person_id' not in session:
        session['person_id'] = "-1"

def get_rating(item):
    rating = getattr(item, 'rating_summary', None)
    if rating is None or len(rating) < 1:
        rating = 'No ratings'
    return rating

def get_element_list(db, with_any=True):
    l = []
    if with_any:
        l.append({'z':'0', 'symbol': 'Any', 'name': 'Any'})
    for r in db.get_elements():
        l.append({'z': '%d' % r.z, 'symbol': r.symbol, 'name': r.name})
    return l

def get_mode_list(db, with_any=True):
    l = []
    if with_any:
        l.append({'id':'0', 'name': 'Any', 'notes': 'Any'})
    for r in db.get_modes():
        l.append({'id': '%d' % r.id, 'name': r.name, 'notes': r.notes})
    return l

def get_energy_units_list(db):
    l = []
    for r in db.filtered_query('energy_units'):
        l.append({'id': '%d' % r.id, 'units': r.units})
    return l

def get_edge_list(db, with_any=False):
    l = []
    if with_any:
        l.append({'id': '0', 'name': 'Any'})
    for r in db.get_edges():
        l.append({'id': '%d' % r.id, 'name': r.name})
    return l

def get_beamline_list(db, orderby='id', with_any=False):
    l = []
    if with_any:
        l.append({'id': '0', 'name': 'Any', 'notes': '',
                  'xray_source':'', 'fac_name': '', 'fac_loc': ''})

    for r in db.get_beamlines(orderby=orderby):
        fac  = db.filtered_query('facility', id=r.facility_id)[0]
        loc = fac.country
        if fac.city is not None and len(fac.city) > 0:
            loc = "%s, %s" % (fac.city, fac.country)
        l.append({'id': '%d' % r.id,
                  'name': r.name,
                  'notes': r.notes,
                  'xray_source': r.xray_source,
                  'fac_name': fac.name,
                  'fac_loc': loc})
    return l

def get_sample_list(db):
    l = []
    for r in db.filtered_query('sample'):
        l.append({'id': '%d' % r.id, 'name': r.name,
                  'formula': r.formula, 'notes': r.notes,
                  'preparation': r.preparation,
                  'person_id': r.person_id,
                  'material_source': r.material_source})
    return l

def spectrum_ratings(db, sid):
    """list of score, comments, time, person) for spectrum ratings"""
    d = []
    for r in db.filtered_query('spectrum_rating', spectrum_id=sid):
        d.append((r.score, r.comments, r.datetime, r.person_id))
    return d

def spectrum_ratings_summary(db, sid):
    """summary of spectrum ratings"""
    sum, n, rating = 0.0, 0, 'No ratings'
    for r in db.filtered_query('spectrum_rating', spectrum_id=sid):
        sum += 1.0*r.score
        n  += 1
    if n > 0:
        rating = ' %.1f (%d ratings)' % (sum/n, n)
    return rating

def suite_ratings(db, sid):
    """list of score, comments, time, person) for suite ratings"""
    d = []
    for r in db.filtered_query('suite_rating', suite_id=sid):
        d.append((r.score, r.comments, r.datetime, r.person_id))
    return d

def suite_ratings_summary(db, sid):
    """summary of suite ratings"""
    sum, n, rating = 0.0, 0, 'No ratings'
    for r in db.filtered_query('suite_rating', suite_id=sid):
        sum += 1.0*r.score
        n  += 1
    if n > 0:
        rating = ' %.1f (%d ratings)' % (sum/n, n)
    return rating

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

def beamline_for_spectrum(db, s, notes=None):
    "return id, desc for beamline of a spectrum"
    blid  = -1
    desc = 'unknown'
    if s.beamline_id is not None:
        blid = s.beamline_id
        bl   = db.filtered_query('beamline', id=blid)[0]
        fac  = db.filtered_query('facility', id=bl.facility_id)[0]
        desc = '%s @ %s ' % (bl.name, fac.name)
    if (blid is None or blid < 0) and (notes is not None):
        blid = -1
        tname = notes.get('beamline', {}).get('name', None)
        if tname is not None:
            desc = "%s -- may be '%s'" % (desc, tname)
    return '%d' % blid, desc

def citation_for_spectrum(db, s, notes=None):
    "return id, desc for citation of a spectrum"
    cid  = -1
    desc = 'unknown'
    if s.citation_id is not None:
        cid  = s.citation_id
        cit  = db.filtered_query('citation', id=cid)[0]
        desc = cit.name
    if (cid is None or cid < 0) and (notes is not None):
        cid = -1
        desc = notes.get('citation', {}).get('name', 'unknown')
    return '%d' % cid, desc


def spectra_for_beamline(db, blid):
    spectra = []
    for r in db.get_spectra():
        if r.beamline_id !=int(blid):
            continue
        elem = db.get_element(r.element_z)
        edge = db.get_edge(r.edge_id)
        spectra.append({'spectrum_id': r.id, 'name':    r.name,
                        'elem_sym': elem.symbol, 'edge': edge.name})
    return spectra


def spectra_for_citation(db, cid):
    spectra = []
    for r in db.get_spectra():
        if r.citation_id !=int(cid):
            continue
        elem = db.get_element(r.element_z)
        edge = db.get_edge(r.edge_id)
        spectra.append({'spectrum_id': r.id, 'name':    r.name,
                        'elem_sym': elem.symbol, 'edge': edge.name})
    return spectra


def spectra_for_suite(db, stid):
    spectra = []
    if stid is not None:
        for r in db.filtered_query('spectrum_suite', suite_id=int(stid)):
            spec = db.get_spectrum(r.spectrum_id)
            elem = db.get_element(spec.element_z)
            edge = db.get_edge(spec.edge_id)
            spectra.append({'spectrum_id': r.spectrum_id, 'name': spec.name,
                            'elem_sym': elem.symbol, 'edge': edge.name})
    return spectra


def parse_spectrum(s, db):
    edge   = db.get_edge(s.edge_id)
    elem   = db.get_element(s.element_z)
    person = db.get_person(s.person_id)
    eunits = db.filtered_query('energy_units', id=s.energy_units_id)[0].units
    d_spacing = '%f'% s.d_spacing
    notes =  json.loads(s.notes)

    beamline_id, beamline_desc = beamline_for_spectrum(db, s, notes)
    citation_id, citation_name = citation_for_spectrum(db, s, notes)

    try:
        sample = db.filtered_query('sample', id=s.sample_id)[0]
        sample_id = '%d'% s.sample_id
        sample_name = sample.name
        sample_form = sample.formula
        sample_prep = sample.preparation
    except:
        sample_id  = '-1'
        sample_name = 'unknown'
        sample_form = 'unknown'
        sample_prep = 'unknown'
        if 'sample' in notes:
            sample_name = notes['sample']
            if isinstance(sample_name, dict):
                sample_name = dict_repr(sample_name)

    # reference sample
    refer_id = '-1'
    refer_name = ''
    if s.reference_id is not None:
        rsample = db.filtered_query('sample', id=s.reference_id)[0]
        refer_id = s.reference_id
        refer_name = rsample.name

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

    if s.comments is None:
        s.comments = ''

    return {'spectrum_id': s.id,
            'spectrum_name': s.name,
            'elem_sym': elem.symbol,
            'elem_name': elem.name,
            'edge': edge.name,
            'energy_units': eunits,
            'raw_comments': s.comments,
            'comments': multiline_text(s.comments),
            'beamline_id': beamline_id,
            'beamline_desc': beamline_desc,
            'citation_id': citation_id,
            'citation_name': citation_name,
            'mononame': mononame,
            'd_spacing': d_spacing,
            'misc': misc,
            'sample_id':   sample_id,
            'sample_name':  sample_name,
            'sample_form':  sample_form,
            'sample_prep':  sample_prep,
            'refer_id': "%d" % int(refer_id),
            'refer_name': refer_name,
            'person_email': person.email,
            'person_name': person.name,
            'upload_date': fmttime(s.submission_date),
            'collection_date': fmttime(s.collection_date),
            'xdi_filename': "%s.xdi" % (s.name.strip()),
            'fullfig': None,
            'xanesfig': None}
