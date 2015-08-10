import os
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
            d['%i'%r.id] = (r.name, r.formula, r.notes,
                            r.material_source, '%i'%r.person_id)

    if 'people' not in session:
        session['people'] = d = {}
        for r in db.get_persons():
            d['%i'%r.id] = (r.email, r.name, r.affiliation)

