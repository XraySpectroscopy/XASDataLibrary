#!/usr/bin/env python
# creates an empty, ready-to-be-used XAS Spectral Library DB
#

from __future__ import print_function
import sys
import os
import glob
import xasdb

dbname = 'example.db'

if len(sys.argv) > 1:
    dbname = sys.argv[1]

if os.path.exists(dbname):
    os.unlink(dbname)
    # print("Error:  file '%s' exists" % dbname)
    # print("Usage:  create_empty_db.py  filename")

xasdb.create_xasdb(dbname)
print( 'Created database %s' % dbname)

db = xasdb.connect_xasdb(dbname)
print( 'Verified that database %s can be accessed.' % dbname)
