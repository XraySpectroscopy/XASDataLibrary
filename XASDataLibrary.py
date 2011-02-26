import os
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker,  mapper, relationship, backref
  
class SimpleTable(object):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'UNNAMED')]
        if getattr(self, 'id', None) is not None:
            fields.append('id=%i' % getattr(self, 'id'))

        return "<%s(%s)>" % (name, ', '.join(fields))

class Mode(SimpleTable):
    pass

class Facility(SimpleTable):
    pass


class Beamline(SimpleTable):
    pass


class Monochromator(SimpleTable):
    pass

class Edge(SimpleTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'X'),
                  '%s' % getattr(self, 'level', '')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Element(SimpleTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'symbol', 'NU'),
                  'Z=%i' % getattr(self, 'z', 0),
                  '%s' % getattr(self, 'name', 'UNNAMED'),
                  ]
        return "<%s(%s)>" % (name, ', '.join(fields))


class Ligand(SimpleTable):
    pass

class CrystalStructure(SimpleTable):
    pass

class Citation(SimpleTable):
    pass

class Monchomator(SimpleTable):
    pass

class Format(SimpleTable):
    pass

class Person(SimpleTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s %s' % (getattr(self, 'firstname', ''),
                             getattr(self, 'lastname', '')),
                  '%s' % getattr(self, 'email', 'NO EMAIL')]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Spectra_Rating(SimpleTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'spectra', None) is not None:
            fields.append('Spectra %i' % getattr(self, 'spectra', 0))
            
        return "<%s(%s)>" % (name, ', '.join(fields))

class Suite_Rating(SimpleTable):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%i' % (int(getattr(self, 'score', 0)))]
        if getattr(self, 'suite', None) is not None:
            fields.append('Suite %i' % getattr(self, 'suite', 0))
            
        return "<%s(%s)>" % (name, ', '.join(fields))

class Suite(SimpleTable):
    pass

class Sample(SimpleTable):
    pass

class Spectra(SimpleTable):
    pass


class XASDataLibrary(object):
    def __init__(self, dbname='xaslib.sqlite'):

        if not os.path.exists(dbname):
            raise IOError("Database '%s' not found!" % dbname)
        
        
        self.dbname = dbname
        self.engine  = create_engine('sqlite:///%s' % self.dbname)
        self.metadata =  MetaData(self.engine)
        
        self.metadata.reflect()
        class Empty:
            pass
        self.tables = Empty()
        for tablename in self.metadata.tables:
            setattr(self.tables, tablename, self.metadata.tables[tablename])
            
        self.session = sessionmaker(bind=self.engine)()

        mapper(Mode,     self.tables.mode, 
               properties={'spectra': relationship(Spectra, backref='mode',
                                                   secondary=self.tables.spectra_mode)}
        )

        mapper(Edge,     self.tables.edge,
               properties={'spectra': relationship(Spectra, backref='edge')}
               )
                
        mapper(Element,  self.tables.element,
               properties={'spectra': relationship(Spectra, backref='element')}
               )
               
        mapper(Format,   self.tables.format,
               properties={'spectra': relationship(Spectra, backref='format')}
               )

        mapper(Beamline, self.tables.beamline,
               properties={'spectra': relationship(Spectra, backref='beamline')}
               )               

        mapper(Citation, self.tables.citation,
               properties={'spectra': relationship(Spectra, backref='citation')}
               )
               
        mapper(Ligand,   self.tables.ligand,
               properties={'spectra': relationship(Spectra, backref='ligand',
                                                   secondary=self.tables.spectra_ligand)}
               )               

        mapper(CrystalStructure,   self.tables.crystal_structure,
               properties={'samples': relationship(Sample, backref='structure'),
                           }
               )

        mapper(Monochromator,   self.tables.monochromator,
               properties={'beamlines':
                           relationship(Beamline, backref='monochromator'),
                           'spectra': relationship(Spectra, backref='monochromator')
                           }
               )

        mapper(Facility, self.tables.facility,
               properties={'beamlines':
                           relationship(Beamline, backref='facility')})
               

        mapper(Person,   self.tables.person,
               properties={'suites': relationship(Suite, backref='person'),
                           'samples': relationship(Sample, backref='person'),
                           'spectra': relationship(Spectra, backref='person')})
               

        mapper(Spectra_Rating,   self.tables.spectra_rating)

        mapper(Suite_Rating,   self.tables.suite_rating)


        mapper(Suite,   self.tables.suite,
               properties={'spectra': relationship(Spectra, backref='suite',
                                                   secondary=self.tables.spectra_suite)}
               )
        
        mapper(Sample,  self.tables.sample)

        mapper(Spectra, self.tables.spectra)        

        
    def commit(self):
        return self.session.commit()
        
    def query(self, *args, **kws):
        return self.session.query(*args, **kws)

    def add_facility(self, name, notes=None, attributes=None, **kws):
        """add facilty by name, return Facility instance"""
        fac = Facility() #
        fac.name = name
        if notes is not None:
            fac.notes = notes
        if attributes is not None:
            fac.attributes = attributes
        self.session.add(fac)
        self.session.commit()
        return self.query(Facility).filter(Facility.name==name).one()

    def add_beamline(self, name, facility=None, notes=None,
                     xray_source=None, monochromator=None,
                     attributes=None, **kws):
        """add beamline by name, with facility:
               facility= Facility instance or id
               monochromator= Monochromator or id
               returns Beamline instance"""
        bl = Beamline() #
        bl.name = name
        if isinstance(facility, Facility):
            facility = facility.id
        if facility is not None:
            bl.facility_id = facility

        if isinstance(monochromator, Monochromator):
            monochromator = monochromator.id
        if monochromator is not None:
            bl.monochromator_id = monochromator

        bl.notes = notes
        bl.xray_source = xray_source
        bl.attributes = attributes
        
        self.session.add(bl)
        self.session.commit()
        return self.query(Beamline).filter(Beamline.name==name).one()

       

def add_beamline(name, notes, facility_id):
    print 'add beamline! ', name, notes, facility_id

def add_person(firstname, lastname, email):
    print 'add person! ', name, notes

if __name__ == '__main__':    
    xaslib =  XASDataLibrary('xasdat.sqlite')

    print dir(xaslib.tables)
    for f in xaslib.query(Edge):
        print f
    
    print 'Facilities:'
    for f in xaslib.query(Facility):
        print  ' -- ', f, f.notes, f.beamlines

    print 'Beamlines:'
    for f in xaslib.query(Beamline):
        print ' -- ', f,  f.notes, f.facility
# 
#     print '---'
#     x13id = Beamline() #
#     print dir(x13id)
#     
#     x13id.name = '13IDC' # , 
#     x13id.notes = 'GSECARS ID-C'
#     x13id.xray_source = 'APS UA'
#     x13id.facility = 1
#  
#     xaslib.session.add(x13id)
#  
#     xaslib.session.commit()
#     for f in xaslib.session.query(Beamline):
#         print f.name, f.notes, f.facility_ref
# 
#     for f in xaslib.session.query(Facility):
#         print f, f.beamlines
# 
