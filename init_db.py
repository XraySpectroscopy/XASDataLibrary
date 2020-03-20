#!/usr/bin/env python
# initialize an XAS Spectral Library DB
# with a small amount of data, suitable for testing
#


from __future__ import print_function
import sys
import os
import glob
import xasdb

dbname = 'example.db'

if len(sys.argv) > 1:
    dbname = sys.argv[1]

if not os.path.exists(dbname):
    print("Error:  database file '%s' does not exist" % dbname)
    print("Use create_empty_db.py to create database")
    sys.exit()


db = xasdb.connect_xasdb(dbname)
print('Connected!')

import sqlalchemy
try:
    db.add_person('Matt Newville',
                  'newville@cars.uchicago.edu',
                  affiliation='CARS, UChicago')
except sqlalchemy.exc.IntegrityError as e:
    pass
person = db.set_person_password('newville@cars.uchicago.edu', str.encode('xafsdb'))
email  = db.get_person('newville@cars.uchicago.edu').email

datadir = 'data'
n = 0
files = glob.glob("%s/*.xdi"  % datadir)
files.sort()
for f in files:
    if 'nonxafs' in f or 'upload' in f:
        continue
    n = n + 1
    db.add_xdifile(f, person=email)
    if n > 12:
        break
