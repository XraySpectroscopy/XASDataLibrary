import os
import json
import time
import base64
from collections import namedtuple
from random import randrange
from string import printable


def make_secret_key():
    "make a secret key for web app"
    f = open('secret.py', 'w')
    f.write("session_key = '%s'\n" % base64.b64encode(os.urandom(36)))
    f.close()


def get_session_key_DISK():
    try:
        from secret import session_key
    except ImportError:
        make_secret_key()
        time.sleep(0.5)
        from secret import session_key
    return session_key

def get_session_key():
    return base64.b64encode(os.urandom(36))


def dict_repr(d):
    return ', '.join(["%s: %s" % (u) for u in d.items()])

def random_string(n):
    """  random_string(n)
    generates a random string of length n, that will match
       [a-z](n)
    """
    return ''.join([printable[randrange(10,36)] for i in range(n)])


def session_init(session, db):
    if 'username' not in session:
        session['username'] = None

    if 'logged_in' not in session:
        session['logged_in'] = False

    if 'elements' not in session:
        session['elements'] = d = {}
        for r in db.get_elements():
            d['%i'%r.z]  = (r.symbol, r.name)

    if 'edges' not in session:
        session['edges'] = d = {}
        for r in db.get_edges():
            d['%i'%r.id]  = r.name

    if 'energy_units' not in session:
        session['energy_units'] = d = {}
        for r in db.filtered_query('energy_units'):
            d['%i'%r.id] = r.units

    if 'facilities' not in session:
        session['facilities'] = d = {}
        for r in db.get_facility():
            d['%i'%r.id] = (r.name, r.fullname, r.country)

    if 'beamlines' not in session:
        session['beamlines'] = d = {}
        for r in db.get_beamlines():
            facid = '%i' % r.facility_id
            d['%i'%r.id] = (r.name, r.notes, r.xray_source, facid)


    if 'samples' not in session:
        session['samples'] = d = {}
        for r in db.filtered_query('sample'):
            d['%i'%r.id] = (r.name, r.formula, r.preparation,
                            r.material_source, r.notes, '%i'%r.person_id)

    if 'people' not in session:
        session['people'] = d = {}
        for r in db.get_persons():
            d['%i'%r.id] = (r.email, r.name, r.affiliation)

def parse_spectrum(s, session):
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
        sample = session['samples']['%i'% s.sample_id]
        sample_name = sample[0]
        sample_form = sample[1]
        sample_prep = sample[2]
    except:
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
            'beamline': beamline,
            'mononame': mononame,
            'dspace': dspace,
            'misc': misc,
            'sample_name':  sample_name,
            'sample_form':  sample_form,
            'sample_prep':  sample_prep,
            'person_email': person[0],
            'person_name': person[1],
            'upload_date': s.submission_date.strftime('%Y-%m-%d %H:%M:%S'),
            'collection_date': s.collection_date.strftime('%Y-%m-%d %H:%M:%S'),
            'fullfig': None,
            'xanesfig': None}
