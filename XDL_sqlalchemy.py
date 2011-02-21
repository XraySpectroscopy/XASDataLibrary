import os

from sqlalchemy.orm import sessionmaker, create_session, mapper, relationship, backref

from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String

class SimpleTable(object):
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'UNNAMED')]
        if getattr(self, 'id', None) is not None:
            fields.append('id=%i' % getattr(self, 'id'))

        return "<%s(%s)>" % (name, ', '.join(fields))

class Facility(SimpleTable):
    pass

class Beamline(SimpleTable):
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

class Mode(SimpleTable):
    pass


class XASDataLibrary(object):
    def __init__(self, dbname='xaslib.sqlite'):

        if not os.path.exists(dbname):
            raise IOError("Database '%s' not found!" % dbname)
        
        
        self.dbname = dbname
        self.engine  = create_engine('sqlite:///%s' % self.dbname)
        self.metadata =  MetaData(self.engine)
        
        self.metadata.reflect()
        for tablename in self.metadata.tables:
            setattr(self, tablename, self.metadata.tables[tablename])
            
        self.session = sessionmaker(bind=self.engine)()

    def commit():
        self.session.commit()

    def get_element(self, z=None, symbol=None, name=None):
        "get elements"
        return self.element.select().execute().fetchall()

    def add_element(self, z=None, symbol=None, name=None):
        if name is None or symbol is None or z is None:
            print 'Must provide z, symbol, name'
            return
        return self.element.insert().execute(z=z, symbol=symbol,
                                      name=name)
def test1():
    xaslib =  XASDataLibrary('xasdat.sqlite')
    print xaslib.edge.select().execute().fetchall()

if __name__ == '__main__':
    xaslib =  XASDataLibrary('xasdat.sqlite')

    mapper(Facility, xaslib.facility,
           properties={'beamlines':
                       relationship(Beamline, backref='facility_ref')})

    mapper(Beamline, xaslib.beamline)
    mapper(Edge, xaslib.edge)
    mapper(Element, xaslib.element)
    mapper(Mode, xaslib.mode)

    for f in xaslib.session.query(Edge):
        print f
    
    for f in xaslib.session.query(Facility):
        print f, f.beamlines

#     for f in xaslib.session.query(Beamline):
#         print f
#         print f.name, f.notes, f.facility_ref
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
