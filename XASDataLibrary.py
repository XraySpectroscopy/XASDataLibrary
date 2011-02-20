import os
import sys
import time
import sqlite3

SCHEMA = open('Create_XASDataLib.sql', 'r').read()

TABLES = ('spectra', 'sample', 'crystal', 'person', 'citation', 'rating',
          'suite', 'facility', 'beamline', 'monochomator',
          'collection_mode', 'ligand', 'format', 'element', 'edge',
          'spectra_modes', 'spectra_ligand', 'spectra_suite' )

class BaseTable:
    def __init__(self, table=None, dbcursor=None):
        self.table = table
        self.dbcursor = dbcursor

    def sqlexec(self, query, vals=None):
        if vals is None:
            vals = ()
            self.dbcursor.execute(query, vals)
        return self.cursor.fetchall()

    def select(self, where=None):
        if where is None:
            where = '1=1'
        return self.sqlexec("select from %s where %s" % (self.table, where))
        
def element(BaseTable):
    def __init__(self, dbcursor=None):
        BaseTable.__init__(table='element', dbcursor=dbcursor)

    def get_z(self, symbol=None, name=None):
        # if symbol is None
        query = 'select from '
        
class XASDataLibrary(object):
    def __init__(self,dbname='xaslib.sqlite'):
        self.dbname = dbname
        self.conn   = sqlite3.connect(self.dbname,
                                      isolation_level=None)
        self.cursor = self.conn.cursor()
        self.__sql_statements = []
        if not self.validate_db():
            self._create()

    def _create(self):
        print 'Creating new empty database'
        return self.cursor.executescript(SCHEMA)

    def sql_exec(self, sql, vals=None):
        if vals is None:
            vals = ()
        self.cursor.execute(sql, vals)
        return self.cursor.fetchall()

    def validate_db(self): rows = self.sql_exec("""select tbl_name from
        sqlite_master where type='table' order by tbl_name""") tables =
        [row[0] for row in rows] print 'Validate ',rows, tables for
        req_table in TABLES: if req_table not in tables: return False
        return True

if __name__ == '__main__':
    datlib = XASDataLibrary(dbname='test.sqlite')
    print 'Hello'
    
    
