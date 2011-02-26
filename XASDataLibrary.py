#!/usr/bin/env python
"""
Principle Python interface to XAS Data Library
requires SQLAlchemy 0.6 or higher

Main Class:  XASDataLibrary

"""
import os
import sys
import json

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker,  mapper, relationship, backref
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import  NoResultFound

class _BaseTable(object):
    "generic class to encapsulate SQLAlchemy table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'UNNAMED')]
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
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'units', '')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Edge(_BaseTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'X')]
        # '%s' % getattr(self, 'level', '')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Element(_BaseTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'symbol', 'NU'),
                  'Z=%i' % getattr(self, 'z', 0),
                  '%s' % getattr(self, 'name', 'UNNAMED'),
                  ]
        return "<%s(%s)>" % (name, ', '.join(fields))


class Ligand(_BaseTable):
    pass

class CrystalStructure(_BaseTable):
    pass

class Citation(_BaseTable):
    pass

class Monchomator(_BaseTable):
    pass

class Format(_BaseTable):
    pass

class Person(_BaseTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s %s' % (getattr(self, 'firstname', ''),
                             getattr(self, 'lastname', '')),
                  '%s' % getattr(self, 'email', 'NO EMAIL')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Spectra_Rating(_BaseTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'spectra', None) is not None:
            fields.append('Spectra %i' % getattr(self, 'spectra', 0))
            
        return "<%s(%s)>" % (name, ', '.join(fields))

class Suite_Rating(_BaseTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'suite', None) is not None:
            fields.append('Suite %i' % getattr(self, 'suite', 0))
            
        return "<%s(%s)>" % (name, ', '.join(fields))

class Suite(_BaseTable):
    pass

class Sample(_BaseTable):
    pass

class Spectra(_BaseTable):
    pass


class XASDataLibrary(object):
    def __init__(self, dbname='xasdat.sqlite'):

        if not os.path.exists(dbname):
            raise IOError("Database '%s' not found!" % dbname)
        
        self.dbname = dbname
        self.engine  = create_engine('sqlite:///%s' % self.dbname)
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

        mapper(Spectra_Rating,   tables['spectra_rating'])

        mapper(Suite_Rating,   tables['suite_rating'])

        mapper(Suite,   tables['suite'],
               properties={'spectra':
                           relationship(Spectra, backref='suite',
                                        secondary=tables['spectra_suite'])})

        mapper(Sample,  tables['sample'])

        mapper(Spectra, tables['spectra'])        

        
    def commit(self):
        "commit session state"
        return self.session.commit()
        
    def query(self, *args, **kws):
        "generic query"
        return self.session.query(*args, **kws)

    def __addRow(self, table, argnames, argvals, **kws):
        """add generic row"""
        me = table() #
        arg0 = argnames[0]
        val0 = argvals[0]
        for name, val in zip(argnames, argvals):
            setattr(me, name, val)
        for key, val in kws.items():
            if key == 'attributes':
                if not isinstance(val, (str, unicode)):
                    val = json.dumps(val)
            setattr(me, key, val)
        try:
            self.session.add(me)
            self.session.commit()
        except IntegrityError, msg:
            self.session.rollback()
            print msg
            raise Warning('Could not add data to table %s' % table)

        return self.query(table).filter(getattr(table, arg0)==val0).one()

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

        fac_id  = self._get_foreign_keyid(Facility, facility)
        mono_id = self._get_foreign_keyid(Monochromator, monochromator)

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['xray_source'] = xray_source
        kw['facility_id'] = fac_id
        kw['monochromator_id'] = mono_id

        return self.__addRow(Beamline, ('name',), (name,), **kws)

    def add_person(self, firstname, lastname, email,
                   affiliation='', attributes='', **kws):
        """add person: arguments are
        firstname, lastname, email  with
        affiliation and attributes optional
        returns Person instance"""
        kws['affiliation'] = affiliation
        kws['attributes'] = attributes
        return self.__addRow(Person, ('email','firstname','lastname'),
                             (email, firstname, lastname), **kws)

    def add_ligand(self, name, notes='', attributes='', **kws):
        """add ligand: name required
        notes and attributes optional
        returns Ligand instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(Ligand, ('name',), (name,), **kws)        

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

    def add_energy_units(self, units, notes=None, attributes=None, **kws):
        """add Energy Units: units required
        notes and attributes optional
        returns EnergyUnits instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(EnergyUnits, ('units',), (units,), **kws)        


    def _get_foreign_keyid(self, table, value, name='name',
                           keyid='id', default=0):
        """generalized lookup for foreign key
        can provide one of:
            table instance
            'name' attribute (or set which attribute with 'name' arg)
            a valid id
            """
        if isinstance(value, table):
            return getattr(table, keyid)
        else:
            if isinstance(value, (str, unicode)):
                filter = getattr(table, name)
            elif isinstance(value, int):
                filter = getattr(table, keyid)
            else:
                return default
            try:
                query = self.query(table).filter(
                    filter==value)
                return getattr(query.one(), keyid)
            except (IntegrityError, NoResultFound):
                return default

        return default
    
    def add_monochromator(self, name, notes='', attributes='',
                          steps_per_degree=None, energy_units=None,
                          lattice_constant=None, **kws):
        """add monochromator: name required
        notes and attributes optional
        returns Monochromator instance"""
        energy_units = self._get_foreign_keyid(EnergyUnits, energy_units,
                                               name='units')
        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['energy_units_id'] = energy_units
        kws['lattice_constant'] = lattice_constant
        kws['steps_per_degreee'] = steps_per_degree

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


if __name__ == '__main__':    
    xaslib =  XASDataLibrary('xasdat.sqlite')

    print xaslib.tables.keys()
    print 'Edges:'
    for f in xaslib.query(Edge):
        print ' -- ', f, f.level
    
    print 'Facilities:'
    for f in xaslib.query(Facility):
        print  ' -- ', f, f.notes, f.beamlines

    print 'Beamlines:'
    for f in xaslib.query(Beamline):
        print ' -- ', f,  f.notes, f.facility
    print 'EnergyUnits:'
    for f in xaslib.query(EnergyUnits):
        print ' -- ', f, f.notes
