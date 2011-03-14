#!/usr/bin/env python
"""Simple dump of data from example database
"""
import os
import xasdb
xaslib =  xasdb.XASDataLibrary()
xaslib.connect(os.path.join('..', 'data', 'example.xdl'))

print 'Infor:'
for f in xaslib.query(xasdb.Info):
    print ' -- ', f

print 'Edges:' 
for f in xaslib.query(xasdb.Edge):
    print ' -- ', f, f.level

print 'EnergyUnits:'
for f in xaslib.query(xasdb.EnergyUnits):
    print ' -- ', f, f.notes

print 'Facilities:'
for f in xaslib.query(xasdb.Facility):
    print  ' -- ', f, f.notes, f.beamlines

print 'Beamlines:'
for f in xaslib.query(xasdb.Beamline):
    print ' -- ', f,  f.notes, f.facility

print 'People:'
for f in xaslib.query(xasdb.Person):
    print ' -- ', f
