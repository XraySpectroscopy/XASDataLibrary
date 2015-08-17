# def add_spectrum(self, name, notes='', attributes='', d_spacing=-1,
#                      notes_i0='', notes_itrans='', notes_ifluor='',
#                      notes_irefer='', submission_date=None,
#                      collection_date=None, temperature='', energy=None,
#                      i0=None, itrans=None, ifluor=None, irefer=None,
#                      energy_stderr=None, i0_stderr=None,
#                      itrans_stderr=None, ifluor_stderr=None,
#                      irefer_stderr=None, energy_units=None, person=None,
#                      edge=None, element=None, sample=None, beamline=None,
#                      data_format=None, citation=None, reference_used=False,
#                      reference_mode=None, reference_sample=None, **kws):

import os

import glob
import xasdb

dbname = 'example.db'
if os.path.exists(dbname):
    os.unlink(dbname)

xasdb.create_xasdb(dbname)
print 'Created'
db = xasdb.connect_xasdb(dbname)
print 'Connected'
db.add_person('Matt Newville',
              'newville@cars.uchicago.edu',
              affiliation='CARS, UChicago')
db.add_person('Bruce Ravel',
              'bravel@bnl.gov',
              affiliation='NIST')

me = db.set_person_password('newville@cars.uchicago.edu', 'xafsdb')
me = db.get_person('newville@cars.uchicago.edu')

datadir = 'data'
n = 0
files = glob.glob("%s/*.xdi"  % datadir)
files.sort()
for f in files:
    if 'nonxafs' in f or 'upload' in f:
        continue
    print 'Addfile ', f, me.email
    n = n + 1
    db.add_xdifile(f, person=me.email)
    if n > 12:
        break
