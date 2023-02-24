from os import urandom, path

import json
import time
from zipfile import ZipFile
from base64 import b64encode
from collections import namedtuple
from datetime import datetime
from random import randrange
from string import printable
from sqlalchemy import text

import numpy as np
import scipy.constants as consts

try:
    from werkzeug.utils import secure_filename
except ImportError:
    from werkzeug import secure_filename

from xraydb import guess_edge

from lmfit.printfuncs import gformat

from .xaslib import fmttime, isotime2datetime, guess_datetime

PLANCK_HC = 1.e10 * consts.Planck * consts.c / consts.e
def mono_deg2ev(angle, d_spacing):
    return PLANCK_HC / (2*d_spacing*np.sin(angle*np.pi/180))

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

def row2dict(row):
    """convert an sqlalchemy result/row to a dict"""
    return {key: getattr(row, key) for key in row.keys()}


def random_string(n):
    """  random_string(n)
    generates a random string of length n, that will match
       [a-z](n)
    """
    return ''.join([printable[randrange(10, 36)] for i in range(n)])


def get_randomfile(extension='zip'):
    fmt = 'xas%4.4d%2.2d%2.2d_%s.%s'

    now = time.localtime()
    return fmt % (now.tm_year, now.tm_mon, now.tm_mday,
                  random_string(6), extension)

def save_zipfile(db, slist, folder='.'):
    fname = get_randomfile(extension='zip')
    tfile = path.abspath(path.join(folder, fname))
    zfile = ZipFile(tfile, mode='w')
    for spid in slist:
        spect =  db.fquery('spectrum', id=spid)[0]
        zfile.writestr("%s.xdi" % spect.name, spect.filetext)
    zfile.close()
    return fname

def multiline_text(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    if '\n' in s:
        return text('%s' % (s.replace('\n', '<br>')))

def session_init(session, db):
    if 'username' not in session:
        session['username'] = None
    if 'person_id' not in session:
        session['person_id'] = "-1"

def get_rating(item, short=False):
    rating = getattr(item, 'rating_summary', None)
    if short and rating is not None:
        rating = rating.split()[0]
    if rating is None or len(rating) < 1:
        rating = 'No ratings'
        if short:
            rating = "unrated"
    return rating

def get_beamline_list(db, orderby='id', with_any=False):
    l = []
    if with_any:
        l.append({'id': '0', 'name': 'Any', 'notes': '',
                  'xray_source':'', 'fac_name': '', 'fac_loc': ''})

    for r in db.get_beamlines(orderby=orderby):
        fac  = db.fquery('facility', id=r.facility_id)[0]
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
    for r in db.fquery('sample'):
        l.append({'id': '%d' % r.id, 'name': r.name,
                  'formula': r.formula, 'notes': r.notes,
                  'preparation': r.preparation,
                  'person_id': r.person_id,
                  'material_source': r.material_source})
    return l

def spectrum_ratings(db, sid):
    """list of score, comments, time, person) for spectrum ratings"""
    d = []
    for r in db.fquery('spectrum_rating', spectrum_id=sid):
        d.append((r.score, r.comments, r.datetime, r.person_id))
    return d

def spectrum_ratings_summary(db, sid):
    """summary of spectrum ratings"""
    sum, n, rating = 0.0, 0, 'No ratings'
    for r in db.fquery('spectrum_rating', spectrum_id=sid):
        sum += 1.0*r.score
        n  += 1
    if n > 0:
        rating = ' %.1f (%d ratings)' % (sum/n, n)
    return rating


def suite_ratings_summary(db, sid):
    """summary of suite ratings"""
    sum, n, rating = 0.0, 0, 'No ratings'
    for r in db.fquery('suite_rating', suite_id=sid):
        sum += 1.0*r.score
        n  += 1
    if n > 0:
        rating = ' %.1f (%d ratings)' % (sum/n, n)
    return rating

def get_person_suites(db, pid):
    """get suites owned by a person, for 'add to suite' lists"""
    out = []
    try:
        for s in db.fquery('suite', person_id=int(pid)):
            out.append((s.id, s.name))
    except:
        pass
    return out

def get_suite_spectra(db, sid):
    'spectra in suite'
    d = []
    for r in db.fquery('spectrum_suite', suite_id=sid):
        d.append(r.spectrum_id)
    return d

def add_spectra_to_suite(db, spectrum_ids, suite_id=-1, person_id=-1):
    print("Add Spectra ", db, spectrum_ids, suite_id, person_id)
    # try:
    suite = db.fquery('suite', id=suite_id)
    print(suite)
    if suite is None:
        return "could not find suite %d" % suite_id
    suite = suite[0]
    if suite.person_id != person_id:
        return "not owner of suite '%s'" % (suite.name)

    current_spectrum_ids = []
    for r in db.fquery('spectrum_suite', suite_id=suite_id):
        current_spectrum_ids.append(r.spectrum_id)
    nadded = 0
    for spid in spectrum_ids:
        if spid not in current_spectrum_ids:
            db.addrow('spectrum_suite', suite_id=suite_id, spectrum_id=spid)
            nadded += 1
    return "added %d spectra to suite '%s'" % (nadded, suite.name)


def get_spectrum_suites(db, sid):
    'suites that a spectrum is in'
    d = []
    for r in db.fquery('spectrum_suite', spectrum_id=sid):
        d.append(r.suite_id)
    return d

def beamline_for_spectrum(db, s, notes=None):
    "return id, desc for beamline of a spectrum"
    blid, desc  = -1, 'unknown'

    if s.beamline_id is not None:
        blid = s.beamline_id
        bl   = db.fquery('beamline', id=blid)[0]
        fac  = db.fquery('facility', id=bl.facility_id)[0]
        desc = bl.name
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
        cit  = db.fquery('citation', id=cid)[0]
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
        for r in db.fquery('spectrum_suite', suite_id=int(stid)):
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
    mode   = db.get_spectrum_mode(s.id)
    try:
        refmode = db.get_spectrum_refmode(s.id)
    except:
        refmode = 'none'
    eunits = db.fquery('energy_units', id=s.energy_units_id)[0].units
    d_spacing = '%f'% s.d_spacing
    notes =  json.loads(s.notes)

    beamline_id, beamline_desc = beamline_for_spectrum(db, s, notes)
    citation_id, citation_name = citation_for_spectrum(db, s, notes)

    try:
        sample = db.fquery('sample', id=s.sample_id)[0]
        sample_id = s.sample_id
        sample_name = sample.name
        sample_formula = sample.formula
        sample_prep = sample.preparation
    except:
        sample_id  = 0
        sample_name = 'unknown'
        sample_formula = 'unknown'
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
    notes.pop('element')
    if 'scan' in notes:
        notes.pop('scan')

    misc = []
    for key, val in notes.items():
        if isinstance(val, dict):
            val = dict_repr(val).strip()
        if len(val) > 1:
            misc.append({'key': "# %s" % key.title(), 'val': val})

    if s.comments is None:
        s.comments = ''

    eresolution = s.energy_resolution
    if eresolution is None:
        eresolution = 'nominal'

    header = []
    for tline in s.filetext.split('\n'):
        if tline.startswith('#'):
            header.append(tline)

    return {'spectrum_id': s.id,
            'spectrum_name': s.name,
            'description': s.description,
            'elem_sym': elem.symbol,
            'elem_name': elem.name,
            'edge': edge.name,
            'energy_units': eunits,
            'energy_resolution': eresolution,
            'mode': mode,
            'refmode': refmode,
            'raw_comments': s.comments,
            'comments': multiline_text(s.comments),
            'header': header,
            'beamline_id': beamline_id,
            'beamline_desc': beamline_desc,
            'citation_id': citation_id,
            'citation_name': citation_name,
            'mononame': mononame,
            'd_spacing': d_spacing,
            'misc': misc,
            'temperature': s.temperature,
            'sample_id':   sample_id,
            'sample_name':  sample_name,
            'sample_formula':  sample_formula,
            'sample_prep':  sample_prep,
            'reference_sample': s.reference_sample,
            'person_email': person.email,
            'person_name': person.name,
            'upload_date': fmttime(s.submission_date),
            'collection_date': fmttime(s.collection_date),
            'xdi_filename': "%s.xdi" % (s.name.strip()),
            'fullfig': None,
            'xanesfig': None}


def guess_metadata(dgroup):
    """guess some metadata from data group headers and array labels"""

    out = {'en_arrayname':'None',
           'i0_arrayname':'None',
           'it_arrayname':'None',
           'if_arrayname':'None',
           'ir_arrayname':'None'}

    alabels = ['None'] + dgroup.array_labels
    alabels.reverse()

    e0 = None
    for lab in alabels:
        llab = lab.lower()
        if  'ener' in llab:
            out['en_arrayname'] = lab
        if 'i0' in llab or 'imon' in llab:
            out['i0_arrayname'] = lab
        if 'it' in llab or 'i1' in llab or 'mut' in llab:
            out['it_arrayname'] = lab
        if 'if' in llab or 'fl' in llab or 'muf' in llab:
            out['if_arrayname'] = lab
        if 'iref' in llab or 'i2' in llab or 'mur' in llab:
            out['ir_arrayname'] = lab

    out['has_reference'] = out['ir_arrayname'] != 'None'

    for line in dgroup.header:
        line  = line.strip()
        if len(line) < 4:
            continue
        if line[0] in '#*%;!':
            line = line[1:].strip()
        line = line.replace('||', ':').replace('=', ':').replace('#', ':')
        words = line.split(':', 1)
        if len(words) > 1:
            key = words[0].strip().lower()
            val = words[1].strip()
            if 'e0' in key:
                e0 = val.split()[0]
            if 'elem' in key:
                if 'sym' in key:
                    out['elem_sym'] = val
                elif 'edge' in key:
                    out['edge'] = val
            if 'mono' in key:
                if 'name' in key:
                    out['mono_name'] = val
                elif 'spac' in key:
                    out['d_spacing'] = val.split()[0]
            if 'sample' in key:
                if 'name' in key:
                    out['sample_name'] = val
                elif 'prep' in key:
                    out['sample_prep'] = val
                elif 'form' in key:
                    out['sample_formula'] = val
                elif 'notes' in key:
                    out['sample_notes'] = val
                elif 'desc' in key:
                    out['sample_notes'] = val
            if 'scan' in key and 'start_time' in key:
                dtime = guess_datetime(val)
                if dtime is not None:
                    out['collection_date'] = fmttime(dtime)

    if e0 is not None and out.get('elem_sym', None) is None:
        try:
            elem, edge = guess_edge(float(e0))
        except:
            elem, edge = None, None
        if elem is not None:
            out['elem_sym'] = elem
            out['edge'] = edge
    return out


def upload2xdi(opts, upload_folder):
    """upload result of upload form to XDI file"""

    fname = opts['filename']
    filename = fname.replace('.', '_')
    filename = secure_filename('%s_%s.xdi' % (random_string(4), filename))
    filename = path.abspath(pathjoin(upload_folder, filename))

    buff = ['#XDI/1.0  XASDataLibrary/1.0']
    arrays = opts['data']

    dcolumns = [('energy', arrays['energy'])]
    if arrays['i0'] is not None:
        dcolumns.append(('i0', arrays['i0']))


    if opts['mode'] == 'transmission':
        if arrays['itrans'] is not None:
            dcolumns.append(('itrans', arrays['itrans']))
        elif arrays['mu'] is not None:
            dcolumns.append(('mutrans', arrays['mu']))
    else:
        if arrays['ifluor'] is not None:
            dcolumns.append(('ifluor', arrays['ifluor']))
        elif arrays['mu'] is not None:
            dcolumns.append(('mufluor', arrays['mu']))
    if opts['has_reference'] and arrays.get('irefer', None) is not None:
        dcolumns.append(('irefer', arrays['irefer']))


    icol = 0
    array_labels = []
    for name, darray in dcolumns:
        array_labels.append((" %s         " %name)[:13])
        if name == 'energy':
            name = 'energy eV'
        icol += 1
        buff.append('# Column.%d: %s' % (icol, name))

    buff.append('# Mono.d_spacing: %.6f' % float(opts['d_spacing']))
    buff.append('# Mono.name: %s' % opts['mono_name'])

    for tag, attr in (('Beamline.name',      'beamline'),
                      ('Element.symbol',     'elem_sym'),
                      ('Element.edge',       'edge'),
                      ('Scan.start_time',    'collection_date'),
                      ('Data.upload_date',   'upload_date'),
                      ('Data.submitted_by',  'person_name'),
                      ('Sample.name',        'sample_name'),
                      ('Sample.formula',     'sample_formula'),
                      ('Sample.preparation', 'sample_prep'),
                      ('Sample.notes',       'sample_notes')):
        attr = opts.get(attr, '')
        if len(attr) > 0:
            buff.append('# %s: %s' % (tag, attr))

    if opts['has_reference'] and len(opts.get('ref_mode', '')) > 0:
        buff.append('# Reference.mode: %s' % opts['ref_mode'])

    buff.append('# ///')
    comments = opts['comments'].split('\n')
    for c in comments:
        buff.append('# %s' % c)
    buff.append('#-----------------------')
    buff.append('#  %s' % ('  '.join(array_labels)))
    for i in range(opts['npts']):
        row = []
        for name, darray in dcolumns:
            row.append(gformat(darray[i], 15))
        buff.append('  '.join(row))
    buff.append('')
    with open(filename, 'w') as fh:
        fh.write('\n'.join(buff))

    return filename
