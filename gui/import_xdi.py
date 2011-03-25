import time
import xdi

import lib as xasdb

xdi_fname = 'data/cu_metal_rt.xdi'

xas_dbname = 'work.xdl'

db = xasdb.XASDataLibrary(xas_dbname)

xdifile = xdi.XDIFile(xdi_fname)

print 'DB: info'
for f in db.query(xasdb.Info):
    print f
print 'EnergyUnits:'
for f in db.query(xasdb.EnergyUnits):
    print ' -- ', f, f.notes

print dir(xdifile)
print xdifile.columns.keys()
#print xdifile.column_data['i0']

db.add_spectra(name=xdi_fname.replace('/', '_'),
                  notes='import from %s' % xdi_fname, 
                  data_energy=xdifile.column_data['energy'],
                  data_i0=xdifile.column_data['i0'],
                  data_itrans=xdifile.column_data['itrans'],
                  data_iemit=xdifile.column_data['ifluor'],
                  data_irefer=xdifile.column_data['irefer'])
# need to be datetimes...
# submission_date=time.ctime(),
# collection_date=xdifile.start_time)

#energy_units=None, monochromator=None, person=None,
#edge=None, element=None, sample=None, beamline=None,
#data_format=None, citation=None, reference=None, **kws):

                  
