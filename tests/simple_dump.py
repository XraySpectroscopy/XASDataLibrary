#!/usr/bin/env python
"""Simple dump of data from example database.
"""
import os
import xaslib
xdb = xaslib.XASDataLibrary()
xdb.connect(os.path.join('..', 'xaslib.db'))

for table in ('info', 'edge', 'energy_units', 'facility', 'beamline', 'person'):
    print(f"## {table}")
    for row in xdb.get_rows(table):
        print( ' -> ', row)
