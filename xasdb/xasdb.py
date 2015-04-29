#!/usr/bin/env python
"""
Principle Python interface to XAS Data Library
requires SQLAlchemy 0.6 or higher

Main Class:  XASDataLibrary

"""

import os
import sys
import json
import logging
import numpy as np
from datetime import datetime

from .creator import make_newdb, backup_versions


from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker,  mapper, relationship, backref
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import  NoResultFound

def isXASDataLibrary(dbname):
    """test if a file is a valid XAS Data Library file:
       must be a sqlite db file, with tables named
          'info', 'spectra', 'sample', 'element' and 'energy_units'
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
        'sample' in metadata.tables and
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
    if val is None or isinstance(val, (str, unicode)):
        return val
    if isinstance(val, np.ndarray):
        val = val.flatten().tolist()
    return  json.dumps(val)

def valid_score(score, smin=0, smax=10):
    """ensure that the input score is an integr
    in the range [smin, smax]  (inclusive)"""
    return max(smin, min(smax, int(score)))


def isotime2datetime(isotime):
    sdate, stime = isotime.replace('T', ' ').split(' ')
    syear, smon, sday = [int(x) for x in sdate.split('-')]
    sfrac = '0'
    if '.' in stime:
        stime, sfrac = stime.split('.')
    shour, smin, ssec  = [int(x) for x in stime.split(':')]
    susec = int(1e6*float('.%s' % sfrac))

    return datetime(syear, smon, sday, shour, smin, ssec, susec)

class XASDBException(Exception):
    """XAS DB Access Exception: General Errors"""
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
                  'Z=%i' % getattr(self, 'z', 0),
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
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'spectra', None) is not None:
            fields.append('Spectrum %i' % getattr(self, 'spectra', 0))

        return "<%s(%s)>" % (name, ', '.join(fields))


class Suite_Rating(_BaseTable):
    "suite rating table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'suite', None) is not None:
            fields.append('Suite %i' % getattr(self, 'suite', 0))

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
    """"full interface to XAS Spectral Library"""
    def __init__(self, dbname=None, server= 'sqlite', user='',
                 password='',  host='', port=5432, logfile=None):
        self.engine = None
        self.session = None
        self.metadata = None
        self.logfile = logfile
        if dbname is not None:
            self.connect(dbname, server=server, user=user,
                         password=password, port=port, host=host)
            
    def create_newdb(self, dbname,  server='sqlite', user='',
                     password='', port=5432, host='', connect=True):
        "create a new, empty database"
        if server.startswith('sqlit') and os.path.exists(dbname):
            backup_versions(dbname)
        make_newdb(dbname, server=server, user=user,
                   password=password, port=port, host=host)
        if connect:
            self.connect(dbname, server=server, user=user,
                   password=password, port=port, host=host)

    def connect(self, dbname, server='sqlite', user='',
                password='', port=5432, host=''):
        "connect to an existing database"

        self.dbname = dbname
        if server.startswith('sqlit'):
            self.engine = create_engine('sqlite:///%s' % self.dbname)
        else:
            conn_str= 'postgresql://%s:%s@%s:%i/%s'
            engine = create_engine(conn_str % (user, password, host,
                                               port, dbname))
            
        self.metadata =  MetaData(self.engine)

        self.metadata.reflect()
        tables = self.tables = self.metadata.tables

        self.session = sessionmaker(bind=self.engine)()

        mapper(Mode, tables['mode'],
               properties={'spectrum':
                           relationship(Spectrum, backref='mode',
                                        secondary=tables['spectrum_mode'])})

        mapper(Edge, tables['edge'],
               properties={'spectrum':
                           relationship(Spectrum, backref='edge')})

        mapper(Element, tables['element'],
               properties={'spectrum':
                           relationship(Spectrum, backref='element')})

        mapper(Beamline, tables['beamline'],
               properties={'spectrum':
                           relationship(Spectrum, backref='beamline')})

        mapper(Citation, tables['citation'],
               properties={'spectrum':
                           relationship(Spectrum, backref='citation')})

        mapper(Ligand,   tables['ligand'],
               properties={'spectrum':
                           relationship(Spectrum, backref='ligand',
                                        secondary=tables['spectrum_ligand'])})

        mapper(Crystal_Structure,   tables['crystal_structure'],
               properties={'samples':
                           relationship(Sample, backref='structure')})

        mapper(Facility, tables['facility'],
               properties={'beamlines':
                           relationship(Beamline, backref='facility')})

        mapper(Person,   tables['person'],
               properties={'suites':
                           relationship(Suite, backref='person'),
                           'samples':
                           relationship(Sample, backref='person'),
                           'spectrum':
                           relationship(Spectrum, backref='person')})

        mapper(EnergyUnits,   tables['energy_units'])

        mapper(Suite,   tables['suite'],
               properties={'spectrum':
                           relationship(Spectrum, backref='suite',
                                        secondary=tables['spectrum_suite'])})

        mapper(Sample,  tables['sample'])
        mapper(Spectrum, tables['spectrum'])
        mapper(Spectrum_Rating,   tables['spectrum_rating'])
        # mapper(Spectrum_Ligand,   tables['spectrum_ligand'])
        mapper(Suite_Rating,   tables['suite_rating'])
        mapper(Info,     tables['info'])

        self.update_mod_time =  None

        if self.logfile is None:
            self.logfile = self.dbname
            if self.logfile.endswith('.xdl'):
                self.logfile = self.logfile[:-4]
        logfile = "%s.log" % self.logfile

        logging.basicConfig()
        logger = logging.getLogger('sqlalchemy.engine')
        logger.addHandler(logging.FileHandler(logfile))

    def commit(self):
        "commit session state"
        return self.session.commit()

    def close(self):
        "close session"
        self.session.commit()
        self.session.flush()
        self.session.close()

    def query(self, *args, **kws):
        "generic query"
        return self.session.query(*args, **kws)

    def set_info(self, key, value):
        """set key / value in the info table"""
        table = self.tables['info']
        vals  = self.query(table).filter(Info.key==key).all()
        if len(vals) < 1:
            # none found -- insert
            table.insert().execute(key=key, value=value)
        else:
            table.update(whereclause="key='%s'" % key).execute(value=value)

    def set_mod_time(self):
        """set modify_date in info table"""
        if self.update_mod_time is None:
            self.update_mod_time = self.tables['info'].update(
                whereclause="key='modify_date'")
        self.update_mod_time.execute(value=datetime.isoformat(datetime.now()))

    def addrow(self, table, argnames, argvals, **kws):
        """add generic row"""
        me = table() #
        arg0 = argnames[0]
        val0 = argvals[0]
        for name, val in zip(argnames, argvals):
            setattr(me, name, val)
        for key, val in kws.items():
            if key == 'attributes':
                val = json_encode(val)
            setattr(me, key, val)
        try:
            self.session.add(me)
            self.set_mod_time()
            self.session.commit()
        except IntegrityError, msg:
            self.session.rollback()
            print msg
            raise Warning('Could not add data to table %s' % table)

        return self.query(table).filter(getattr(table, arg0)==val0).one()


    def foreign_keyid(self, table, value, name='name',
                      keyid='id', default=None):
        """generalized lookup for foreign key
        Parameters
        ----------
         table : a valid table class, as mapped by mapper.
         value : value in row of foreign table 
         name  : column name to use for looking up value.  The default 
                 is 'name', meaning that the value passed in should be 
                 the row name 
         keyid : name of column to use for returned id (default is 'id')

        Returns
        -------
          id of matching row, or None if no match is found
        """
        if isinstance(value, table):
            return getattr(table, keyid)
        else:
            if isinstance(value, basestring):
                xfilter = getattr(table, name)
            elif isinstance(value, int):
                xfilter = getattr(table, keyid)
            else:
                return default
            try:
                query = self.query(table).filter(
                    xfilter==value)
                return getattr(query.one(), keyid)
            except (IntegrityError, NoResultFound):
                return default

        return default

    def get_elements(self, show_all=True):
        """return list of elements,
        Arguments
        ---------
        show_all : bool
            show all elements (default) or only those with data in the database
        """
        if show_all:
            out = []
            for f in self.query(Element):
                out.append((f.name, f.symbol, f.z))
            return out
        else:
            return [(f.name, f.symbol, f.z) for f in self.query(Element)]

    def get_edges(self, show_all=True):
        """return list of edges,
        Arguments
        ---------
        show_all : bool
             show all edges (default) or only those with data in the database
        """
        if show_all:
            return [f.name for f in self.query(Edge)]
        else:
            print 'limit!'
            return [f.name for f in self.query(Edge)]


    def add_energy_units(self, units, notes=None, attributes=None, **kws):
        """add Energy Units: units required
        notes and attributes optional
        returns EnergyUnits instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.addrow(EnergyUnits, ('units',), (units,), **kws)

    def add_mode(self, name, notes='', attributes='', **kws):
        """add collection mode: name required
        notes and attributes optional
        returns Mode instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.addrow(Mode, ('name',), (name,), **kws)

    def add_crystal_structure(self, name, notes='',
                              attributes='', format=None,
                              data=None, **kws):
        """add data format: name required
        notes and attributes optional
        returns Format instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['format'] = format
        kws['data'] = data

        return self.addrow(Crystal_Structure, ('name',), (name,), **kws)

    def add_edge(self, name, level):
        """add edge: name and level required
        returns Edge instance"""
        return self.addrow(Edge, ('name', 'level'), (name, level))

    def add_facility(self, name, notes='', attributes='', **kws):
        """add facilty by name, return Facility instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        return self.addrow(Facility, ('name',), (name,), **kws)

    def add_beamline(self, name, facility=None,
                     xray_source=None,  notes='',
                     attributes='', **kws):
        """add beamline by name, with facility:
               facility= Facility instance or id
               returns Beamline instance"""

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['xray_source'] = xray_source
        kws['facility_id'] = self.foreign_keyid(Facility, facility)

        return self.addrow(Beamline, ('name',), (name,), **kws)

    def add_citation(self, name, notes='', attributes='',
                     journal='',  authors='',  title='',
                     volume='', pages='',  year='',
                     doi='',  **kws):
        """add literature citation: name required
        notes and attributes optional
        returns Citation instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['journal'] = journal
        kws['authors'] = authors
        kws['title'] = title
        kws['volume'] = volume
        kws['pages'] = pages
        kws['year'] = year
        kws['doi'] = doi
        return self.addrow(Citation, ('name',), (name,), **kws)

    def add_info(self, key, value):
        """add Info key value pair -- returns Info instance"""
        return self.addrow(Info, ('key', 'value'), (key, value))

    def add_ligand(self, name, notes='', attributes='', **kws):
        """add ligand: name required
        notes and attributes optional
        returns Ligand instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.addrow(Ligand, ('name',), (name,), **kws)

    def add_person(self, name, email,
                   affiliation='', attributes='', **kws):
        """add person: arguments are
        name, email  with
        affiliation and attributes optional
        returns Person instance"""
        kws['affiliation'] = affiliation
        kws['attributes'] = attributes
        return self.addrow(Person, ('email', 'name'),
                             (email, name), **kws)

    def add_sample(self, name, notes='', attributes='',
                   formula=None, material_source=None,
                   person=None, crystal_structure=None, **kws):
        """add sample: name required
        returns Sample instance"""

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['formula'] = formula
        kws['material_source'] = material_source
        kws['person_id'] = self.foreign_keyid(Person, person)
        kws['crystal_structure_id'] = self.foreign_keyid(Crystal_Structure,
                                                         crystal_structure)
        return self.addrow(Sample, ('name',), (name,), **kws)


    def add_suite(self, name, notes='', attributes='',
                  person=None, **kws):
        """add suite: name required
        returns Suite instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['person_id'] = self.foreign_keyid(Person, person,
                                                   name='email')

        return self.addrow(Suite, ('name',), (name,), **kws)

    def add_suite_rating(self, person, suite, score, comments=None):
        """add a score to a suite:  The following are required:
   person: instance of Person table, a valid email, or Person id
   suite:  instance of Suite table, a valid suite name, or Suite id
   score:  an integer value 0 to 10.
        Optional:
   comments text of comments"""

        kws['person_id'] = self.foreign_keyid(Person, person,
                                                   name='email')
        kws['suite_id'] = self.foreign_keyid(Suite, suite)
        kws['datetime'] = datetime.now()
        if comments is not None:
            kws['comments'] = comments
        score = valid_score(score)
        self.addrow(Suite_Rating, ('score',), (score,), **kws)

    def add_spectrum_rating(self, person, spectrum, score, comments=None):
        """add a score to a suite:  The following are required:
   person: instance of Person table, a valid email, or Person id
   spectrum: instance of Spectrum table, a valid spectrum name, or spectrum id
   score:  an integer value 0 to 5.
Optional:
   comments text of comments"""

        kws['person_id'] = self.foreign_keyid(Person, person,
                                                   name='email')
        kws['spectrum_id'] = self.foreign_keyid(Spectrum, specctra)
        kws['datetime'] = datetime.now()        
        if comments is not None:
            kws['comments'] = comments
        score = valid_score(score)
        self.addrow(Spectrum_Rating, ('score',), (score,), **kws)

    def add_spectrum(self, name, notes='', attributes='', file_link='',
                    energy=None, i0=None, itrans=None,
                    ifluor=None, irefer=None, k=None, chi=None,
                    mutrans=None, mufluor=None, murefer=None,  dspacing=0.0,
                    notes_i0='', notes_itrans='', notes_ifluor='',
                    notes_irefer='', temperature='', submission_date=None,
                    collection_date=None, reference_used='',
                    energy_units=None, person=None,
                    edge=None, element=None, sample=None, beamline=None,
                    data_format=None, citation=None, reference=None, **kws):

        """add spectrum: name required
        returns Spectrum instance"""

        spectrum_names = self.query('name'
                                   ).from_statement('select name from spectrum').all()

        if len(spectrum_names) > 1:
            if any([entry[0] == name for entry in spectrum_names]):
                raise XASDBException("A spectrum named '%s' already exists" % name)

        # eif  name in spectrum_names:
        # return

        kws['notes'] = notes
        kws['attributes'] = attributes

        kws['file_link'] = file_link

        for attr, val in (('energy', energy), ('i0', i0), ('k', k),
                          ('chi',  chi), ('itrans', itrans),
                          ('ifluor', ifluor),  ('irefer', irefer),
                          ('mutrans', mutrans), ('mufluor', mufluor),
                          ('murefer', murefer)):
            kws[attr] = json_encode(val)

        if submission_date is None:
            submission_date = datetime.now()
        for attr, val in (('submission_date', submission_date),
                          ('collection_date', collection_date)):
            if isinstance(val, (str, unicode)):
                try:
                    val = isotime2datetime(val)
                except ValueError:
                    val = None
            if val is None:
                val = datetime(1,1,1)
            kws[attr] = val

        kws['notes_i0'] = notes_i0
        kws['notes_itrans'] = notes_itrans
        kws['notes_ifluor'] = notes_ifluor
        kws['notes_irefer'] = notes_irefer
        kws['temperature'] = temperature
        kws['dspacing'] = dspacing

        kws['reference_used'] = reference_used
        kws['beamline_id'] = self.foreign_keyid(Beamline, beamline)
        kws['person_id'] = self.foreign_keyid(Person, person,
                                              name='email')
        kws['edge_id'] = self.foreign_keyid(Edge, edge)
        kws['element_z'] = self.foreign_keyid(Element, element,
                                              keyid='z', name='symbol')
        kws['sample_id'] = self.foreign_keyid(Sample, sample)
        kws['citation_id'] = self.foreign_keyid(Citation, citation)
        kws['reference_id'] = self.foreign_keyid(Sample, reference)
        kws['energy_units_id'] = self.foreign_keyid(EnergyUnits,
                                                    energy_units,
                                                    name='units')
        try:
            return self.addrow(Spectrum, ('name',), (name,), **kws)
        except:
            return None

    def get_beamline(self, facility=None):
        """get all beamlines for a facility
        Parameters
        ----------
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
        elif isinstance(facility, basestring):
            ftab = self.tables['facility']
            row  = ftab.select(ftab.c.name==facility).execute().fetchone()
            fac_id = row.id

        if fac_id is not None:
            query = tab.select(tab.c.facility_id==fac_id)
        else:
            query = tab.select()
        return query.execute().fetchall()

    
    def get_suite_ratings(self, spectrum):
        "get all ratings for a suite"
        raise NotImplementedError
    
    def get_spectrum_ratings(self, spectrum):
        "get all ratings for a spectrum"
        raise NotImplementedError

    def get_spectra(self, edge=None, element=None, suite=None, beamline=None,
                    facility=None, person=None, mode=None, sample=None,
                    citation=None, ligand=None): 
        """get all spectra matching some set of criteria
        
        Parameters
        ----------
        edge
        element
        suite
        beamline
        facility
        person
        mode
        sample
        citation
        ligand
        """
        q = self.tables['spectrum']
        
        raise NotImplementedError
