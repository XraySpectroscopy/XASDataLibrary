import os

from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String

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
if __name__ == '__main__':
    xaslib =  XASDataLibrary('xasdat.sqlite')



    print xaslib.edge.select().execute().fetchall()
    
    
