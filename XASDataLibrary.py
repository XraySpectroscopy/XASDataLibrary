#!/usr/bin/env python
"""
Principle Python interface to XAS Data Library
requires SQLAlchemy 0.6 or higher

Main Class:  XASDataLibrary

"""
import os
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker,  mapper, relationship, backref
import json

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
    def __init__(self, dbname='xaslib.sqlite'):

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
        self.session.add(me)
        self.session.commit()
        return self.query(table).filter(getattr(table, arg0)==val0).one()

    def add_facility(self, name, notes=None, attributes='', **kws):
        """add facilty by name, return Facility instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes
        return self.__addRow(Facility, ('name',), (name,), **kws)

    def add_beamline(self, name, facility=None, notes=None,
                     xray_source=None, monochromator=None,
                     attributes=None, **kws):
        """add beamline by name, with facility:
               facility= Facility instance or id
               monochromator= Monochromator or id
               returns Beamline instance"""
        if isinstance(facility, Facility):
            facility = facility.id
        if isinstance(monochromator, Monochromator):
            monochromator = monochromator.id

        kws['notes'] = notes
        kws['attributes'] = attributes
        kws['xray_source'] = xray_source
        kw['facility'] = facility            
        kw['monochromator'] = monochromator

        return self.__addRow(Beamline, ('name',), (name,), **kws)

    def add_person(self, firstname, lastname, email,
                   affiliation=None, attributes=None, **kws):
        """add person: arguments are
        firstname, lastname, email  with
        affiliation and attributes optional
        returns Person instance"""
        kws['affiliation'] = affiliation
        kws['attributes'] = attributes
        return self.__addRow(Person, ('email','firstname','lastname'),
                             (email, firstname, lastname), **kws)

    def add_ligand(self, name, notes=None, attributes=None, **kws):
        """add ligand: name required
        notes and attributes optional
        returns Ligand instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(Ligand, ('name',), (name,), **kws)        
         
    def add_energy_units(self, units, notes=None, attributes=None, **kws):
        """add Energy Units: units required
        notes and attributes optional
        returns EnergyUnits instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        return self.__addRow(EnergyUnits, ('units',), (units,), **kws)        

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
