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
import numpy
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
    return  json.dumps(val)

def valid_score(score, smin=0, smax=5):
    """ensure that the input score is an integr
    in the range [smin, smax]  (inclusive)"""
    return max(smin, min(smax, int(score)))
    
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

class Monochromator(_BaseTable):
    "monochromator table"
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

class CrystalStructure(_BaseTable):
    "crystal structure table"
    pass

class Citation(_BaseTable):
    "literature citation table"
    pass


class Format(_BaseTable):
    "data format table"
    pass

class Person(_BaseTable):
    "person table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s %s' % (getattr(self, 'firstname', ''),
                             getattr(self, 'lastname', '')),
                  '%s' % getattr(self, 'email', 'NO EMAIL')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Spectra_Rating(_BaseTable):
    "spectra rating"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'spectra', None) is not None:
            fields.append('Spectra %i' % getattr(self, 'spectra', 0))
            
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

class Spectra(_BaseTable):
    "spectra table"
    pass


class XASDataLibrary(object):
    "full interface to XAS Spectral Library"
    def __init__(self, dbname=None, logfile=None):
        self.engine = None
        self.session = None
        self.metadata = None
        self.logfile = logfile
        if dbname is not None:
            self.connect(dbname)
            
    def create_newdb(self, dbname, connect=False):
        "create a new, empty database"
        if os.path.exists(dbname):
            backup_versions(dbname)
        make_newdb(dbname)
        if connect:
            self.connect(dbname)

    def connect(self, dbname):
        "connect to an existing database"
        if not os.path.exists(dbname):
            raise IOError("Database '%s' not found!" % dbname)

        if not isXASDataLibrary(dbname):
            raise ValueError("'%s' is not an XAS Data Library file!" % dbname)

        self.dbname = dbname
        self.engine = create_engine('sqlite:///%s' % self.dbname)
        self.logfile = self.dbname
        if self.logfile.endswith('.xdl'):
            self.logfile = self.logfile[:-4]
        self.logfile = "%s.log" % self.logfile
        
        self.metadata =  MetaData(self.engine)
        
        self.metadata.reflect()
        tables = self.tables = self.metadata.tables

        self.session = sessionmaker(bind=self.engine)()

        mapper(Mode,     tables['mode'], 
               properties={'spectra':
                           relationship(Spectra, backref='mode',
                                        secondary=tables['spectra_mode'])})

        mapper(Edge, tables['edge'],
               properties={'spectra':
                           relationship(Spectra, backref='edge')})
                
        mapper(Element, tables['element'],
               properties={'spectra':
                           relationship(Spectra, backref='element')})
               
        mapper(Format, tables['format'],
               properties={'spectra':
                           relationship(Spectra, backref='format')})

        mapper(Beamline, tables['beamline'],
               properties={'spectra':
                           relationship(Spectra, backref='beamline')})

        mapper(Citation, tables['citation'],
               properties={'spectra':
                           relationship(Spectra, backref='citation')})
               
        mapper(Ligand,   tables['ligand'],
               properties={'spectra':
                           relationship(Spectra, backref='ligand',
                                        secondary=tables['spectra_ligand'])})

        mapper(CrystalStructure,   tables['crystal_structure'],
               properties={'samples':
                           relationship(Sample, backref='structure')})

        mapper(Monochromator,   tables['monochromator'],
               properties={'beamlines':
                           relationship(Beamline, backref='monochromator'),
                           'spectra':
                           relationship(Spectra, backref='monochromator')})

        mapper(Facility, tables['facility'],
               properties={'beamlines':
                           relationship(Beamline, backref='facility')})

        mapper(Person,   tables['person'],
               properties={'suites':
                           relationship(Suite, backref='person'),
                           'samples':
                           relationship(Sample, backref='person'),
                           'spectra':
                           relationship(Spectra, backref='person')})

        mapper(EnergyUnits,   tables['energy_units'],
               properties={'monochromator':
                           relationship(Monochromator, backref='energy_units'),
                           'spectra':
                           relationship(Spectra, backref='energy_units')})

        mapper(Suite,   tables['suite'],
               properties={'spectra':
                           relationship(Spectra, backref='suite',
                                        secondary=tables['spectra_suite'])})

        mapper(Sample,  tables['sample'])
        mapper(Spectra, tables['spectra'])        
        mapper(Spectra_Rating,   tables['spectra_rating'])
        mapper(Suite_Rating,   tables['suite_rating'])
        mapper(Info,     tables['info'])
        
        self.update_mod_time =  None

        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine'
                          ).addHandler(logging.FileHandler(self.logfile))
        
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

    def __addRow(self, table, argnames, argvals, **kws):
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


    def _get_foreign_keyid(self, table, value, name='name',
                           keyid='id', default=None):
        """generalized lookup for foreign key
arguments
    table: a valid table class, as mapped by mapper.
    value: can be one of the following
         table instance:  keyid is returned
         string:          'name' attribute (or set which attribute with 'name' arg)
            a valid id
            """
        if isinstance(value, table):
            return getattr(table, keyid)
        else:
            if isinstance(value, (str, unicode)):
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
    
    def add_energy_units(self, units, notes=None, attributes=None, **kws):
        """add Energy Units: units required
        notes and attributes optional
        returns EnergyUnits instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(EnergyUnits, ('units',), (units,), **kws)        

    def add_mode(self, name, notes='', attributes='', **kws):
        """add collection mode: name required
        notes and attributes optional
        returns Mode instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(Mode, ('name',), (name,), **kws)        

    def add_format(self, name, notes='', attributes='', **kws):
        """add data format: name required
        notes and attributes optional
        returns Format instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(Format, ('name',), (name,), **kws)        

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

        return self.__addRow(CrystalStructure, ('name',), (name,), **kws)

    def add_edge(self, name, level):
        """add edge: name and level required
        returns Edge instance"""
        return self.__addRow(Edge, ('name', 'level'), (name, level))


    def add_facility(self, name, notes='', attributes='', **kws):
        """add facilty by name, return Facility instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        return self.__addRow(Facility, ('name',), (name,), **kws)

    def add_beamline(self, name, facility=None,
                     monochromator=None,
                     xray_source=None,  notes='',                     
                     attributes='', **kws):
        """add beamline by name, with facility:
               facility= Facility instance or id
               monochromator= Monochromator or id
               returns Beamline instance"""

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['xray_source'] = xray_source
        kws['facility_id'] = self._get_foreign_keyid(Facility, facility)
        kws['monochromator_id'] = self._get_foreign_keyid(Monochromator,
                                                         monochromator)

        return self.__addRow(Beamline, ('name',), (name,), **kws)

    def add_monochromator(self, name, notes='', attributes='',
                          steps_per_degree=None, energy_units=None,
                          dspacing=None, pixel_to_energy=None, **kws):
        """add monochromator: name required
        notes and attributes optional
        returns Monochromator instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['dspacing'] = dspacing
        kws['steps_per_degreee'] = steps_per_degree
        kws['energy_units_id'] =  self._get_foreign_keyid(EnergyUnits,
                                                          energy_units,
                                                          name='units')

        return self.__addRow(Monochromator, ('name',), (name,), **kws)        

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
        return self.__addRow(Citation, ('name',), (name,), **kws)        

    def add_info(self, key, value):
        """add Info key value pair -- returns Info instance"""
        return self.__addRow(Info, ('key', 'value'), (key, value))

    def add_ligand(self, name, notes='', attributes='', **kws):
        """add ligand: name required
        notes and attributes optional
        returns Ligand instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(Ligand, ('name',), (name,), **kws)        

    def add_person(self, firstname, lastname, email,
                   affiliation='', attributes='', **kws):
        """add person: arguments are
        firstname, lastname, email  with
        affiliation and attributes optional
        returns Person instance"""
        kws['affiliation'] = affiliation
        kws['attributes'] = attributes
        return self.__addRow(Person, ('email', 'firstname', 'lastname'),
                             (email, firstname, lastname), **kws)

    def add_sample(self, name, notes='', attributes='',
                   formula=None, material_source=None,
                   person=None, crystal_structure=None, **kws):
        """add sample: name required
        returns Sample instance"""

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['formula'] = formula
        kws['material_source'] = material_source
        kws['person_id'] = self._get_foreign_keyid(Person, person)
        kws['crystal_structure_id'] = self._get_foreign_keyid(CrystalStructure,
                                                              crystal_structure)
        return self.__addRow(Sample, ('name',), (name,), **kws)        


    def add_suite(self, name, notes='', attributes='',
                  person=None, **kws):
        """add suite: name required
        returns Suite instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['person_id'] = self._get_foreign_keyid(Person, person,
                                                   name='email')

        return self.__addRow(Suite, ('name',), (name,), **kws)        

    def add_suite_rating(self, person, suite, score, comments=None):
        """add a score to a suite:  The following are required:
   person: instance of Person table, a valid email, or Person id
   suite:  instance of Suite table, a valid suite name, or Suite id
   score:  an integer value 0 to 5.
Optional:
   comments text of comments"""

        kws['person_id'] = self._get_foreign_keyid(Person, person,
                                                   name='email')
        kws['suite_id'] = self._get_foreign_keyid(Suite, suite)
        if comments is not None:
            kws['comments'] = comments
        score = valid_score(score)
        self.__addRow(Suite_Rating, ('score',), (score,), **kws)

    def add_spectra_rating(self, person, spectra, score, comments=None):
        """add a score to a suite:  The following are required:
   person: instance of Person table, a valid email, or Person id
   spectra: instance of Spectra table, a valid spectra name, or spectra id
   score:  an integer value 0 to 5.
Optional:
   comments text of comments"""

        kws['person_id'] = self._get_foreign_keyid(Person, person,
                                                   name='email')
        kws['spectra_id'] = self._get_foreign_keyid(Spectra, specctra)
        if comments is not None:
            kws['comments'] = comments
        score = valid_score(score)
        self.__addRow(Spectra_Rating, ('score',), (score,), **kws)

    def import_XDIspectra(self, fname):
        """import a spectra from XDI ASCII Format"""
        print 'Hello!'
        
    def add_spectra(self, name, notes='', attributes='', file_link='',
                    data_energy='', data_i0='', data_itrans='',
                    data_iemit='', data_irefer='', data_dtime_corr='',
                    calc_mu_trans='', calc_mu_emit='', calc_mu_refer='',
                    notes_i0='', notes_itrans='', notes_iemit='',
                    notes_irefer='', temperature='', submission_date='',
                    collection_date='', reference_used='',
                    energy_units=None, monochromator=None, person=None,
                    edge=None, element=None, sample=None, beamline=None,
                    data_format=None, citation=None, reference=None, **kws):

        """add spectra: name required
        returns Spectra instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        kws['file_link'] = file_link

        for attr, val in (('data_energy', data_energy),
                          ('data_i0', data_i0),
                          ('data_itrans', data_itrans),
                          ('data_iemit', data_iemit),
                          ('data_irefer', data_irefer),
                          ('data_dtime_corr', data_dtime_corr)):
            if isinstance(val, numpy.ndarray):
                val = list(val.flatten())
            kws[attr] = json_encode(val)

        kws['calc_mu_trans'] = calc_mu_trans
        kws['calc_mu_emit'] = calc_mu_emit
        kws['calc_mu_refer'] = calc_mu_refer
        kws['notes_i0'] = notes_i0
        kws['notes_itrans'] = notes_itrans
        kws['notes_iemit'] = notes_iemit
        kws['notes_irefer'] = notes_irefer
        kws['temperature'] = temperature
        kws['submission_date'] = submission_date
        kws['collection_date'] = collection_date
        kws['reference_used'] = reference_used
        kws['beamline_id'] = self._get_foreign_keyid(Beamline, beamline)
        kws['monochromator_id'] = self._get_foreign_keyid(Monochromator,
                                                         monochromator)
        kws['person_id'] = self._get_foreign_keyid(Person, person,
                                                   name='email')
        kws['edge_id'] = self._get_foreign_keyid(Edge, edge)
        kws['element_z'] = self._get_foreign_keyid(Element, element,
                                                   keyid='z', name='symbol')
        kws['sample_id'] = self._get_foreign_keyid(Sample, sample)
        kws['format_id'] = self._get_foreign_keyid(Format, data_format)
        kws['citation_id'] = self._get_foreign_keyid(Citation, citation)
        kws['reference_id'] = self._get_foreign_keyid(Sample, reference)
        kws['energy_units_id'] = self._get_foreign_keyid(EnergyUnits,
                                                         energy_units,
                                                         name='units')

        return self.__addRow(Spectra, ('name',), (name,), **kws)        

