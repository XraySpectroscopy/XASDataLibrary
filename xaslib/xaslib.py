#!/usr/bin/env python
"""
Principle Python interface to XAS Data Library
requires SQLAlchemy 0.6 or higher

Main Class:  XASDataLibrary

"""

import os
import sys
import time
import random
import json
import logging
import numpy as np
from datetime import datetime

from base64 import b64encode
from hashlib import pbkdf2_hmac

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

from larch.io import XDIFile, read_ascii
from larch.utils import debugtime

from . import initialdata

PW_ALGOR = 'sha512'
PW_NITER = 200000

def isXASDataLibrary(dbname):
    """test if a file is a valid XAS Data Library file:
       must be a sqlite db file, with tables named
          'info', 'spectra', 'element' and 'energy_units'
       the 'element' table must have more than 90 rows and the
       'info' table must have an entries named 'version' and 'create_date'
    """

    try:
        engine  = create_engine('sqlite:///%s' % dbname)
        metadata =  MetaData(engine)
        metadata.reflect()
    except:
        return False

    if ('info' in metadata.tables and
        'spectra' in metadata.tables and
        'element' in metadata.tables and
        'energy_units' in metadata.tables):

        elements = metadata.tables['element'].select().execute().fetchall()
        if len(elements) > 90:
            info = metadata.tables['info'].select().execute().fetchall()
            keys = [row.key for row in info]
            return ('version' in keys and 'create_date' in keys)
    return False

def json_encode(val):
    "simple wrapper around json.dumps"
    if val is None or isinstance(val, str):
        return val
    if isinstance(val, np.ndarray):
        val = val.flatten().tolist()
    return  json.dumps(val)

def valid_score(score, smin=0, smax=5):
    """ensure that the input score is an integr
    in the range [smin, smax]  (inclusive)"""
    return max(smin, min(smax, int(score)))

def unique_name(name, namelist, maxcount=100, msg='spectrum'):
    """
    find a name that is not in namelist by making
       name (1),  name (2), etc
    up to maxcount, at which point an exception is raised.
    """
    basename, count = name, 0
    while name in namelist:
        count += 1
        if count > maxcount:
            msg = "a %s named '%s' already exists"  % (msg, name)
            raise XASLibException(msg)
        name = "%s (%d)" % (basename, count)
    return name

def isotime2datetime(isotime):
    sdate, stime = isotime.replace('T', ' ').split(' ')
    syear, smon, sday = [int(x) for x in sdate.split('-')]
    sfrac = '0'
    if '.' in stime:
        stime, sfrac = stime.split('.')
    shour, smin, ssec  = [int(x) for x in stime.split(':')]
    susec = int(1e6*float('.%s' % sfrac))

    return datetime(syear, smon, sday, shour, smin, ssec, susec)

def guess_datetime(tstring):
    if 'T' in tstring and 'OCT' not in tstring:
        tstring = tstring.replace('T', ' ')

    for dfmt in ("%Y-%m-%d", "%Y-%b-%d", "%Y/%m/%d", "%Y/%b/%d",
                 "%b %d, %Y", "%m/%d/%Y", "%d/%m/%Y"):
        for tfmt in ("%H:%M:%S", "%H:%M"):
            dtfmt = "%s %s" % (dfmt, tfmt)
            try:
                out = datetime.strptime(tstring, dtfmt)
            except ValueError:
                out = None
            if out is not None:
                return out
            

def fmttime(dtime=None):
    if dtime is None:
        dtime = datetime.now()
    return dtime.strftime('%Y-%m-%d %H:%M:%S')


def None_or_one(val, msg='Expected 1 or None result'):
    """expect result (as from query.all() to return
    either None or exactly one result"""
    if len(val) == 1:
        return val[0]
    elif len(val) == 0:
        return None
    else:
        raise XASLibException(msg)

def apply_orderby(q, tab, orderby=None):
    """apply an order_by to a query to sort results"""
    if orderby is not None:
        key = getattr(tab.c, orderby, None)
        if key is None:
            key = getattr(tab.c, "%s_id" % orderby, None)
        if key is not None:
            q = q.order_by(key)
    return q

def slow_string_compare(a, b):
    """
    does a slow-as-possible compare of 2 strings, a and b
    returns whether the two strings are equal
    this is meant to confuse and slow down attempts to guess / crack
    passwords that time how long a string comparison takes to fail.
    """
    isgood = 0
    if len(a) != len(b):
        isgood = 1
    time.sleep(5.e-5*(len(a)*(1+5*random.random())))
    for x, y in zip(a, b):
        isgood |= ord(x) ^ ord(y)
    return isgood == 0


class XASLibException(Exception):
    """XAS Library Exception: General Errors"""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg


class _BaseTable(object):
    "generic class to encapsulate SQLAlchemy table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'UNNAMED')]
        return "<%s(%s)>" % (name, ', '.join(fields))


class Info(_BaseTable):
    "general information table (versions, etc)"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s=%s' % (getattr(self, 'key', '?'),
                               getattr(self, 'value', '?'))]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Mode(_BaseTable):
    "collection mode table"
    pass

class Facility(_BaseTable):
    "facility table"
    pass

class Beamline(_BaseTable):
    "beamline table"
    pass

class EnergyUnits(_BaseTable):
    "Energy Units table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'units', '')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Edge(_BaseTable):
    "edge table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'X')]
        # '%s' % getattr(self, 'level', '')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Element(_BaseTable):
    "element table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'symbol', 'NU'),
                  'Z=%d' % getattr(self, 'z', 0),
                  '%s' % getattr(self, 'name', 'UNNAMED'),
                  ]
        return "<%s(%s)>" % (name, ', '.join(fields))


class Ligand(_BaseTable):
    "ligand table"
    pass

class Crystal_Structure(_BaseTable):
     "crystal structure table"
     pass

class Citation(_BaseTable):
    "literature citation table"
    pass

class Person(_BaseTable):
    "person table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = [getattr(self, 'name', ''),
                  getattr(self, 'email', 'NO EMAIL')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Spectrum_Ligand(_BaseTable):
    "spectrum ligand"
    ligand, spectrum = None, None

class Spectrum_Rating(_BaseTable):
    "spectra rating"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%.1f' % getattr(self, 'score', 0)]
        if getattr(self, 'spectra', None) is not None:
            fields.append('Spectrum %d' % getattr(self, 'spectra', 0))

        return "<%s(%s)>" % (name, ', '.join(fields))


class Suite_Rating(_BaseTable):
    "suite rating table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%d' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'suite', None) is not None:
            fields.append('Suite %d' % getattr(self, 'suite', 0))

        return "<%s(%s)>" % (name, ', '.join(fields))

class Suite(_BaseTable):
    "suite table"
    pass

class Sample(_BaseTable):
    "sample table"
    pass

class Spectrum(_BaseTable):
    "spectra table"
    pass

class XASDataLibrary(object):
    """full interface to XAS Spectral Library"""
    def __init__(self, dbname=None, server= 'sqlite', user='',
                 password='',  host='', port=5432, logfile=None):
        self.engine = None
        self.session = None
        self.metadata = None
        self.logfile = logfile
        if dbname is not None:
            self.connect(dbname, server=server, user=user,
                         password=password, port=port, host=host)

    def connect(self, dbname, server='sqlite', user='',
                password='', port=5432, host=''):
        "connect to an existing database"

        self.dbname = dbname
        if server.startswith('sqlit'):
            self.engine = create_engine('sqlite:///%s' % self.dbname,
                                        connect_args={'check_same_thread': False})
        else:
            conn_str= 'postgresql://%s:%s@%s:%d/%s'
            self.engine = create_engine(conn_str % (user, password, host,
                                                    port, dbname))

        self.session = sessionmaker(bind=self.engine)()
        self.metadata =  MetaData(self.engine)
        try:
            self.metadata.reflect()
        except:
            raise XASLibException('%s is not a valid database' % dbname)

        tables = self.tables = self.metadata.tables

        self.update_mod_time =  None
        if self.logfile is None and server.startswith('sqlit'):
            lfile = self.dbname
            if lfile.endswith('.xdl'):
                lfile = self.logfile[:-4]
            self.logfile = "%s.log" % lfile
            logging.basicConfig()
            logger = logging.getLogger('sqlalchemy.engine')
            logger.addHandler(logging.FileHandler(self.logfile))



    def close(self):
        "close session"
        self.session.commit()
        self.session.flush()
        self.session.close()

    def set_info(self, key, value):
        """set key / value in the info table"""
        table = self.tables['info']
        vals  = self.fquery('info', key=key)
        if len(vals) < 1:
            # none found -- insert
            table.insert().execute(key=key, value=value)
        else:
            table.update(whereclause=text("key='%s'" % key)).execute(value=value)

    def set_mod_time(self):
        """set modify_date in info table"""
        if self.update_mod_time is None:
            self.update_mod_time = self.tables['info'].update(
                whereclause=text("key='modify_date'"))
        self.update_mod_time.execute(value=fmttime())

    def addrow(self, tablename, commit=True, **kws):
        """add generic row"""
        table = self.tables[tablename]
        out = table.insert().execute(**kws)
        self.set_mod_time()
        if commit:
            self.session.commit()
        if out.lastrowid == 0:
            v = self.fquery(tablename, **kws)
            return v[-1].id
        else:
            return out.lastrowid

    def fquery(self, tablename, **kws):
        """
        return filtered query of table with any equality filter on columns

        examples:

        >>> db.fquery('element', z=30)
        >>> db.fquery('spectrum', person_id=3)

        will return all rows from table

        """
        table = self.tables[tablename]
        query = self.session.query(table)
        for key, val in kws.items():
            if key in table.c and val is not None:
                query = query.filter(getattr(table.c, key)==val)
        return query.all()

    def included_elements(self, retval='symbol'):
        """return a list of elements with one or more spectra"""
        zvals = []
        for s in self.fquery('spectrum'):
            ez = s.element_z
            if ez not in zvals:
                zvals.append(ez)
        out = []
        for z, atsym, name in initialdata.elements:
            if z in  zvals:
                val = z
                if retval == 'symbol':
                    val = atsym
                elif retval ==  'name':
                    val = name
                out.append(val)
        return out


    def get_facility(self,  **kws):
        """return facility or list of facilities"""

        out = self.fquery('facility', **kws)
        if len(out) > 1:
            return out
        return None_or_one(out)

    def get_facilities(self, orderby='id'):
        """return facility or list of facilities"""

        tab = self.tables['facility']
        query = apply_orderby(tab.select(), tab, orderby)
        return query.execute().fetchall()

        out = self.fquery('facility')

        return None_or_one(out)

    def get_element(self, val):
        """return element z, name, symbol from one of z, name, symbol"""
        key = 'symbol'
        if isinstance(val, int):
            key = 'z'
        elif len(val) > 2:
            key = 'name'
        kws = {key: val}
        return None_or_one(self.fquery('element', **kws))

    def get_elements(self):
        """return list of elements z, name, symbol"""
        return self.fquery('element')

    def get_modes(self):
        """return list of measurement modes"""
        return self.fquery('mode')

    def get_edge(self, val, key='name'):
        """return edge by name  or id"""
        if isinstance(val, int):
            key = 'id'
        kws = {key: val}
        return None_or_one(self.fquery('edge', **kws))

    def get_edges(self):
        """return list of edges"""
        return self.fquery('edge')

    def get_beamline(self, val, key='name'):
        """return beamline by name  or id"""
        if isinstance(val, int):
            key = 'id'
        kws = {key: val}
        return None_or_one(self.fquery('beamline', **kws))

    def add_energy_units(self, units, notes=None, **kws):
        """add Energy Units: units required
        notes  optional
        returns EnergyUnits instance"""
        return self.addrow('energy_units', units=units, notes=notes, **kws)

    def get_sample(self, sid):
        """return sample by id"""
        return None_or_one(self.fquery('sample', id=sid))

    def add_mode(self, name, notes='', **kws):
        """add collection mode: name required
        returns Mode instance"""
        return self.addrow('mode', name=name, notes=notes, **kws)

    def add_crystal_structure(self, name, notes='',
                               format=None, data=None, **kws):
         """add data format: name required
         returns Format instance"""
         kws['notes'] = notes
         kws['format'] = format
         kws['data'] = data
         return self.addrow(Crystal_Structure, ('name',), (name,), **kws)

    def add_edge(self, name, level):
        """add edge: name and level required
        returns Edge instance"""
        return self.addrow('edge', name=name, level=level)

    def add_facility(self, name, notes='', **kws):
        """add facilty by name, return Facility instance"""
        return self.addrow('facility', name=name, notes=notes, **kws)

    def add_beamline(self, name, facility_id=None,
                     xray_source=None,  notes='', **kws):
        """add beamline by name, with facility:
               facility= Facility instance or id
               returns Beamline instance"""
        return self.addrow('beamline', name=name, xray_source=xray_source,
                           notes=notes, facility_id=facility_id, **kws)

    def add_citation(self, name, **kws):
        """add literature citation: name required
        returns Citation instance"""
        return self.addrow('citation', name=name, **kws)

    def add_info(self, key, value):
        """add Info key value pair -- returns Info instance"""
        return self.addrow('info', key=key, value=value)

    def add_ligand(self, name, **kws):
        """add ligand: name required
        returns Ligand instance"""
        return self.addrow('ligand', name=name, **kws)

    def add_person(self, name, email,
                   affiliation='', password=None, con='false', **kws):
        """add person: arguments are
        name, email with affiliation and password optional
        returns Person instance"""
        person_id = self.addrow('person', email=email, name=name,
                             affiliation=affiliation,
                             confirmed=con, **kws)

        if password is not None:
            self.set_person_password(email, password)
        return person_id

    def get_person(self, val, key='email'):
        """get person by email"""
        if isinstance(val, int):
            key = 'id'
        kws = {key: val}

        return None_or_one(self.fquery('person', **kws),
                           "expected 1 or None person")

    def get_persons(self, **kws):
        """return list of people"""
        return self.fquery('person')

    def set_person_password(self, email, password, auto_confirm=False):
        """ set secure password for person"""
        salt   = b64encode(os.urandom(24))
        result = b64encode(pbkdf2_hmac(PW_ALGOR, password.encode('utf-8'),
                                       salt, PW_NITER))
        hash = '$'.join((PW_ALGOR, '%8.8d'%PW_NITER, salt.decode('utf-8'),
                         result.decode('utf-8')))
        table = self.tables['person']
        ewhere = text("email='%s'" % email)
        confirmed = 'true' if auto_confirm else 'false'
        table.update(whereclause=ewhere).execute(password=hash,
                                                 confirmed=confirmed)

    def test_person_password(self, email, password):
        """test password for person, returns True if valid"""
        table = self.tables['person']
        row  = table.select(table.c.email==email).execute().fetchone()
        try:
            algor, niter, salt, hash_stored = row.password.split('$')
        except:
            algor, niter, salt, hash_stored = PW_ALGOR, PW_NITER, '_nul_', '%bad%'
        hash_test = b64encode(pbkdf2_hmac(algor, password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          int(niter))).decode('utf-8')
        return slow_string_compare(hash_test, hash_stored)

    def test_person_confirmed(self, email):
        """test if account for a person is confirmed"""

        table = self.tables['person']
        row  = table.select(table.c.email==email).execute().fetchone()
        return row.confirmed.lower() == 'true'

    def person_unconfirm(self, email):
        """ sets a person to 'unconfirmed' status, pending confirmation,
        returns hash, which must be used to confirm person"""
        hash = b64encode(os.urandom(24)).decode('utf-8').replace('/', '_')
        table = self.tables['person']
        table.update(whereclause=text("email='%s'" % email)).execute(confirmed=hash)
        return hash

    def person_test_confirmhash(self, email, hash):
        """test if a person's confirmation hash is correct"""
        tab = self.tables['person']
        row = tab.select(tab.c.email==email).execute().fetchone()
        return slow_string_compare(hash, row.confirmed)

    def person_confirm(self, email, hash):
        """try to confirm a person,
        test the supplied hash for confirmation,
        setting 'confirmed' to 'true' if correct.
        """
        tab = self.tables['person']
        row = tab.select(tab.c.email==email).execute().fetchone()
        is_confirmed = False
        if hash == row.confirmed:
            tab.update(whereclause=text("email='%s'" % email)).execute(confirmed='true')
            is_confirmed = True
        return is_confirmed

    def add_sample(self, name, person_id, **kws):
        "add sample: name required returns sample id"
        return self.addrow('sample', name=name, person_id=person_id, **kws)

    def add_suite(self, name, notes='', person_id=None, **kws):
        """add suite: name required
        returns Suite instance"""
        return self.addrow('suite', name=name, notes=notes,
                            person_id=person_id, **kws)

    def del_suite(self, suite_id):
        table = self.tables['suite']
        table.delete().where(table.c.id==suite_id).execute()
        table = self.tables['spectrum_suite']
        table.delete().where(table.c.suite_id==suite_id).execute()
        table = self.tables['suite_rating']
        table.delete().where(table.c.id==suite_id).execute()
        self.set_mod_time()
        self.session.commit()

    def remove_spectrum_from_suite(self, suite_id, spectrum_id):
        tab = self.tables['spectrum_suite']
        rows = tab.select().where(tab.c.suite_id==suite_id
                                  ).where(tab.c.spectrum_id==spectrum_id
                                          ).execute().fetchall()
        for row in rows:
            tab.delete().where(tab.c.id==row.id).execute()
        self.set_mod_time()
        self.session.commit()

    def del_spectrum(self, sid):
        table = self.tables['spectrum']
        table.delete().where(table.c.id==sid).execute()
        table = self.tables['spectrum_suite']
        table.delete().where(table.c.spectrum_id==sid).execute()
        table = self.tables['spectrum_rating']
        table.delete().where(table.c.id==sid).execute()

        self.set_mod_time()
        self.session.commit()

    def set_suite_rating(self, person_id, suite_id, score, comments=None):
        """add a rating score to a suite:"""
        kws = {'score': valid_score(score),
               'person_id': person_id, 'suite_id': suite_id,
               'datetime': datetime.now(), 'comments': ''}
        if comments is not None:
            kws['comments'] = comments

        tab = self.tables['suite_rating']
        rowid = None
        for row in tab.select(tab.c.suite_id==suite_id).execute().fetchall():
            if row.person_id == person_id:
                rowid = row.id

        if rowid is None:
            tab.insert().execute(**kws)
        else:
            tab.update(whereclause=text("id='%d'" % rowid)).execute(**kws)
        self.session.commit()

        sum = 0
        rows = tab.select(tab.c.suite_id==suite_id).execute().fetchall()
        for row in rows:
            sum += 1.0*row.score

        rating = 'No ratings'
        if len(rows) > 0:
            rating = '%.1f (%d ratings)' % (sum/len(rows), len(rows))

        stab = self.tables['suite']
        stab.update(whereclause=text("id='%d'" % suite_id)).execute(rating_summary=rating)


    def set_spectrum_rating(self, person_id, spectrum_id, score, comments=None):
        """add a score to a spectrum: person_id, spectrum_id, score, comment
        score is an integer value 0 to 5"""
        kws = {'score': valid_score(score),
               'person_id': person_id, 'spectrum_id': spectrum_id,
               'datetime': datetime.now(), 'comments': ''}
        if comments is not None:
            kws['comments'] = comments


        tab = self.tables['spectrum_rating']
        rowid = None
        for row in tab.select(tab.c.spectrum_id==spectrum_id).execute().fetchall():
            if row.person_id == person_id:
                rowid = row.id

        if rowid is None:
            tab.insert().execute(**kws)
        else:
            tab.update(whereclause=text("id='%d'" % rowid)).execute(**kws)

        self.session.commit()

        sum = 0
        rows = tab.select(tab.c.spectrum_id==spectrum_id).execute().fetchall()
        for row in rows:
            sum += 1.0*row.score

        rating = 'No ratings'
        if len(rows) > 0:
            rating = '%.1f (%d ratings)' % (sum/len(rows), len(rows))

        stab = self.tables['spectrum']
        stab.update(whereclause=text("id='%d'" % spectrum_id)).execute(rating_summary=rating)


    def update(self, tablename, where, use_id=True, **kws):
        """update a row (by id) in a table (by name) using keyword args
        db.update('spectrum', 5, **kws)

        """
        table = self.tables[tablename]
        if use_id:
            where = "id='%d'" % where

        table.update(whereclause=text(where)).execute(**kws)
        self.set_mod_time()
        self.session.commit()

    def add_spectrum(self, name, description=None, notes='', d_spacing=-1,
                     energy_units=None, edge='K', element=None,
                     mode='transmission', reference_sample='none',
                     reference_mode='transmission', temperature=None,
                     energy=None, i0=None, itrans=None, ifluor=None,
                     irefer=None, energy_stderr=None, i0_stderr=None,
                     itrans_stderr=None, ifluor_stderr=None,
                     irefer_stderr=None, energy_notes='', i0_notes='',
                     itrans_notes='', ifluor_notes='', irefer_notes='',
                     submission_date=None, collection_date=None, person=None,
                     sample=None, beamline=None, citation=None,
                     commit=True, **kws):

        """add spectrum: name required
        returns Spectrum instance"""
        stab = self.tables['spectrum']
        spectrum_names = [s.name for s in stab.select().execute()]

        if name in spectrum_names:
            raise XASLibException("A spectrum named '%s' already exists" % name)

        if description is None:
            description = name
        dlocal = locals()
        # simple values
        for attr in ('description', 'notes', 'd_spacing', 'reference_sample',
                     'temperature', 'energy_notes', 'i0_notes',
                     'itrans_notes', 'ifluor_notes', 'irefer_notes'):
            kws[attr] = dlocal.get(attr, '')

        # arrays
        for attr in ('energy', 'i0', 'itrans', 'ifluor', 'irefer',
                     'energy_stderr', 'i0_stderr', 'itrans_stderr',
                     'ifluor_stderr', 'irefer_stderr'):
            val = ''
            if dlocal[attr] is not None:
                val = json_encode(dlocal.get(attr, ''))
            kws[attr] = val

        # simple pointers
        for attr in ('person', 'sample', 'citation'):
            kws['%s_id' % attr] = dlocal.get(attr, '')

        # dates
        if submission_date is None:
            submission_date = datetime.now()
        for attr, val in (('submission_date', submission_date),
                          ('collection_date', collection_date)):
            if isinstance(val, str):
                try:
                    val = isotime2datetime(val)
                except ValueError:
                    val = None
            if val is None:
                val = datetime(1, 1, 1)
            kws[attr] = val

        # more complicated foreign keys, pointers to other tables

        bline = self.guess_beamline(beamline)
        if bline is not None:
            kws['beamline_id'] = bline.id

        if bline is None:
            print("Add Spectrum : No beamline found = ",name,  beamline)

        kws['edge_id'] = self.get_edge(edge).id
        kws['mode_id'] = self.fquery('mode', name=mode)[0].id
        if irefer is None:
            reference_mode = 'none'
        kws['reference_mode_id'] = self.fquery('reference_mode', name=reference_mode)[0].id
        kws['element_z'] = self.get_element(element).z
        kws['energy_units_id'] = self.fquery('energy_units', name=energy_units)[0].id
        return self.addrow('spectrum', name=name, commit=commit, **kws)

    def get_beamlines(self, facility=None, orderby='id'):
        """get all beamlines for a facility
        Parameters
        --------
        facility  id, name, or Facility instance for facility

        Returns
        -------
        list of matching beamlines

        """
        tab = self.tables['beamline']
        fac_id = None
        if isinstance(facility, Facility):
            fac_id = facility.id
        elif isinstance(facility, int):
            fac_id = facility
        elif isinstance(facility, str):
            ftab = self.tables['facility']
            row  = ftab.select(ftab.c.name==facility).execute().fetchone()
            fac_id = row.id

        if fac_id is not None:
            query = tab.select(tab.c.facility_id==fac_id)
        else:
            query = tab.select()

        query = apply_orderby(query, tab, orderby)
        return query.execute().fetchall()

    def guess_beamline(self, name, facility=None):
        """return best guess of beamline by name"""
        bline = None_or_one(self.fquery('beamline', name=name))
        if bline is not None:
            return bline
        candidates = self.get_beamlines(facility=facility)
        lname = name.lower()
        for b in candidates:
            if lname in b.name.lower() or lname in b.nickname.lower():
                return b

        if '(' in lname:
            lname = lname.split('(')[0].strip()
        for b in candidates:
            if lname in b.name.lower() or lname in b.nickname.lower():
                return b

        # this is  comment

        lname = lname.lower().replace('-', '').replace('_', '').replace(' ', '').replace('&', '')

        for b in candidates:
            bnx = b.name.lower().replace('-', '').replace('_', '').replace(' ', '')
            bn2 = b.nickname.lower().replace('-', '').replace('_', '').replace(' ', '')
            if lname in b.name.lower() or lname in b.nickname.lower():
                return b

        return None


    def get_suite_ratings(self, suite):
        "get all ratings for a suite"
        if hasattr(suite, 'id') and hasattr(spectrum, 'ratings_summary'):
            sid = suite.id
        else:
            sid = suite
        return self.fquery('suite_rating', suite_id=sid)

    def get_spectrum_ratings(self, spectrum):
        "get all ratings for a spectrum"
        if hasattr(spectrum, 'id') and hasattr(spectrum, 'itrans'):
            sid = spectrum.id
        else:
            sid = spectrum
        return self.fquery('spectrum_rating', spectrum_id=sid)

    def get_spectrum_mode(self, spectrum_id):
        """return name of mode for a spectrum"""
        spect = None_or_one(self.fquery('spectrum', id=spectrum_id))
        mode_id = 1
        if spect is not None:
            mode_id = spect.mode_id
        return self.fquery('mode', id=mode_id)[0].name

    def get_spectrum_refmode(self, spectrum_id):
        """return name of refernce mode for a spectrum"""
        spect = None_or_one(self.fquery('spectrum', id=spectrum_id))
        mode_id = 1
        if spect is not None:
            mode_id = spect.reference_mode_id
        return self.fquery('reference_mode', id=mode_id)[0].name

    def get_spectrum_beamline(self, spectrum_id):
        "return id, desc for beamline for aa spectrum"
        blid, desc  = -1, 'unknown'
        spect = None_or_one(self.fquery('spectrum', id=spectrum_id))
        if spect is not None:
            bl = self.fquery('beamline', id=spect.beamline_id)[0]
            if bl is not None:
                blid = bl.id
                desc = bl.name
        if (blid is None or blid < 0) and (spect.notes is not None):
            tname = spect.notes.get('beamline', {}).get('name', None)
            if tname is not None:
                desc = "may be '%s'" % (desc, tname)
        return '%d' % blid, desc

    def get_spectrum(self, id):
        """ get spectrum by id"""
        tab = self.tables['spectrum']
        return tab.select().where(tab.c.id == id).execute().fetchone()

    def get_spectra(self, edge=None, element=None, beamline=None,
                    person=None, mode=None, sample=None, facility=None,
                    suite=None, citation=None, ligand=None, orderby='id'):
        """get all spectra matching some set of criteria

        Parameters
        ----------
        edge       by Name
        element    by Z, Symbol, or Name
        person     by email
        beamline   by name
        facility
        mode
        sample
        citation
        ligand
        suite
        """
        edge_id, element_z, person_id, beamline_id = None, None, None, None

        tab = self.tables['spectrum']
        query = tab.select()

        # edge
        if isinstance(edge, Edge):
            edge_id = edge.id
        elif edge is not None:
            edge_id = self.get_edge(edge).id
        if edge_id is not None:
            query = query.where(tab.c.edge_id==edge_id)

        # element
        if isinstance(element, Element):
            element_z = element.z
        elif element is not None:
            element_z = self.get_element(element).z
        if element_z is not None:
            query = query.where(tab.c.element_z==element_z)

        # beamline
        if isinstance(beamline, Beamline):
            beamline_id = beamline.id
        elif beamline is not None:
            beamline_id = self.get_beamline(name=beamline).id
        if beamline_id is not None:
            query = query.where(tab.c.beamline_id==beamline_id)

        # person
        if isinstance(person, Person):
            person_id = person.id
        elif person is not None:
            person_id = self.get_person(person).id
        if person_id is not None:
            query = query.where(tab.c.person_id==person_id)

        query = apply_orderby(query, tab, orderby)
        return query.execute().fetchall()

    def add_xdifile(self, fname, spectrum_name=None, description=None,
                    person=None, reuse_sample=True, mode=None, commit=True,
                    verbose=False, **kws):

        try:
            fh  = open(fname, 'r')
            filetext  = fh.read()
        except:
            filetext = ''
        finally:
            fh.close()

        xfile = XDIFile(fname)
        try:
            afile = read_ascii(fname)
        except:
            afile = None

        path, fname = os.path.split(fname)
        now = fmttime()

        if spectrum_name is None:
            spectrum_name = fname
        if spectrum_name.endswith('.xdi'):
            spectrum_name = spectrum_name[:-4]

        if description is None:
            description  = spectrum_name
        stab = self.tables['spectrum']

        _s_names = [s.name for s in stab.select().execute()]
        spectrum_name = unique_name(spectrum_name, _s_names)

        try:
            c_date = xfile.attrs['scan']['start_time']
        except:
            c_date = 'collection date unknown'
        d_spacing = xfile.dspacing
        energy    = xfile.energy
        edge      = xfile.edge.decode('utf-8')
        element   = xfile.element.decode('utf-8')
        comments  = ''
        if hasattr(xfile, 'comments'):
            comments = xfile.comments.decode('utf-8')
        # prefer to get comments from original header, if possible
        header = getattr(afile, 'header', None)
        if header is not None:
            comment_lines = []
            slashes_found = False
            for hline in header:
                hline = hline.strip()
                if slashes_found:
                    if hline.startswith('#'):
                        hline = hline[1:].strip()
                    if len(hline) > 0:
                        comment_lines.append(hline)
                slashes_found = hline.startswith('# //')
                if hline.startswith('#---'):
                    break
            if len(comment_lines) > 0:
                comments = '\n'.join(comment_lines)

        i0  = getattr(xfile, 'i0', getattr(xfile, 'io', np.ones(len(energy))*1.0))

        itrans = getattr(xfile, 'itrans', getattr(xfile, 'i1', None))
        ifluor = getattr(xfile, 'ifluor', getattr(xfile, 'if', None))
        irefer = getattr(xfile, 'irefer', getattr(xfile, 'i2', None))

        if hasattr(xfile, 'mutrans'):
            itrans = i0 * np.exp(-xfile.mutrans)
        if hasattr(xfile, 'mufluor'):
            ifluor = i0 * xfile.mufluor

        if mode is None:
            mode = 'fluorescence'
            if itrans is not None:
                mode = 'transmission'
        if mode == 'transmission' and itrans is None:
            raise ValueError("cannot find transmission data")
        elif mode == 'fluoresence' and ifluor is None:
            raise ValueError("cannot find fluorescence data")

        reference_mode = 'none' if irefer is None else 'transmission'

        en_units = 'eV'
        for index, value in xfile.attrs['column'].items():
            words = value.split()
            if len(words) > 1:
                if (value.lower().startswith('energy') or
                    value.lower().startswith('angle') ):
                    en_units = words[1]

        if isinstance(person, Person):
            person_id = person.id
        else:
            person_id = self.get_person(person).id

        beamline = None
        temperature = None
        reference_sample = None
        sample_id = 0
        if 'sample' in xfile.attrs:
            sample_attrs  = xfile.attrs['sample']
            if 'temperature' in sample_attrs:
                temperature = sample_attrs['temperature']
            if 'name' in sample_attrs:
                sample_name = sample_attrs.pop('name')

            if 'reference' in sample_attrs:
                reference_sample = sample_attrs['reference']

            sample_notes = "sample for '%s', uploaded %s" % (fname, now)
            sample_kws = {}
            for attr in ('preparation', 'formula'):
                shortname = attr[:4]
                if shortname in sample_attrs:
                    sample_kws[attr] = sample_attrs.pop(shortname)
                elif attr in sample_attrs:
                    sample_kws[attr] = sample_attrs.pop(attr)

            if len(sample_attrs) > 0:
                sample_notes = '%s\n%s' % (sample_notes, json_encode(sample_attrs))
            if reuse_sample:
                srow = self.fquery('sample', name=sample_name, person_id=person_id)
                if len(srow) > 0:
                    sample_id = srow[0].id
            if sample_id == 0:
                sample_id = self.add_sample(sample_name, person_id,
                                            notes=sample_notes, **sample_kws)
        self.session.commit()
        time.sleep(0.025)
        if reference_mode is not 'none':
            if reference_sample is None:
                reference_sample = 'unknown'
        else:
            reference_sample = 'none'
        beamline_name  = xfile.attrs['beamline']['name']
        notes = json_encode(xfile.attrs)
        if verbose:
            print("adding %s: %s %s mode='%s', %d points" %(fname, element, edge, mode, len(energy)))

        return self.add_spectrum(spectrum_name, description=description,
                                 d_spacing=d_spacing, collection_date=c_date,
                                 person=person_id, beamline=beamline_name,
                                 edge=edge, element=element, mode=mode,
                                 energy=energy, energy_units=en_units,
                                 i0=i0, itrans=itrans, ifluor=ifluor,
                                 irefer=irefer, sample=sample_id,
                                 comments=comments, notes=notes,
                                 filetext=filetext,
                                 reference_sample=reference_sample,
                                 reference_mode=reference_mode,
                                 temperature=temperature,
                                 commit=commit)



def connect_xaslib(dbname, server='sqlite', user='', password='',
                   port=5432, host=''):
    """connect to a XAS Data Library"""
    return XASDataLibrary(dbname,
                          server=server, user=user,
                          password=password, port=port, host=host)
