#!/usr/bin/env python
# initialize an XAS Spectral Library DB
# with a small amount of data, suitable for testing

import sys
import os
import glob
import xasdb
import sqlalchemy

dbname = sys.argv[1] if len(sys.argv) > 1 else 'xastest.db'

if os.path.exists(dbname):
    os.unlink(dbname)

xasdb.create_xasdb(dbname)
print( 'Created database %s' % dbname)

db = xasdb.connect_xasdb(dbname)
print( 'Verified that database %s can be accessed.' % dbname)

db.add_person('xaslib admin', 'xaslib@xrayabsorption.org', affiliation='IXAS')
person = db.set_person_password('xaslib@xrayabsorption.org',
                                'Re3{t_Th1s_P@ssw0rd!')
email  = db.get_person('xaslib@xrayabsorption.org').email

datadir = 'data'
n = 0
for f in sorted(glob.glob("%s/*.xdi"  % datadir)):
    if 'nonxafs' in f or 'upload' in f:
        continue
    db.add_xdifile(f, person=email)
    print("added ", f)
    n += 1
print("'%s' has %d spectra" % (dbname, n))
