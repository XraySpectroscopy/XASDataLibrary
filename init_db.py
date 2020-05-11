#!/usr/bin/env python
# initialize an XAS Spectral Library DB
# with a small amount of data, suitable for testing

import sys
import os
import glob
import xaslib
import sqlalchemy

dbname = sys.argv[1] if len(sys.argv) > 1 else 'xaslib.db'

if os.path.exists(dbname):
    os.unlink(dbname)

xaslib.create_xaslib(dbname)
print( 'Created database %s' % dbname)

db = xaslib.connect_xaslib(dbname)
print( 'Verified that database %s can be accessed.' % dbname)

db.add_person('xaslib admin', 'xaslib@xrayabsorption.org', affiliation='IXAS')
person = db.set_person_password('xaslib@xrayabsorption.org',
                                'b@d_p@ssw0rd!',
                                auto_confirm=True)
email  = db.get_person('xaslib@xrayabsorption.org').email

datadir = 'data'
subdirs = sorted(os.listdir(datadir))
# subdirs = ('Pb', 'Sr')

n = 0
for sdir in subdirs:
    sdirname = os.path.join(datadir, sdir)
    for f in sorted(glob.glob("%s/*.xdi"  % sdirname)):
        if 'nonxafs' in f or 'upload' in f:
            continue
        db.add_xdifile(f, person=email, verbose=True)
        n += 1
print("'%s' has %d spectra" % (dbname, n))
