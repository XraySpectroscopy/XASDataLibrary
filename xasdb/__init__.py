"""
   x-ray absorption spectra database


== License:
   To the extent possible, the authors have waived all rights
   granted by copyright law and related laws for the code and
   documentation that make up the XAS Data Library.  While
   information about Authorship may be retained in some files
   for historical reasons, this work is hereby placed in the
   Public Domain.  This work is published from: United States.

== Authors:
   Though copyright is waived, the authors of this code are:
      Matthew Newville <newville@cars.uchicago.edu>
           CARS, University of Chicago

== Overview:
   The xasdb module provides a python interface to the XAFS Database,
   an SQLite tool for organizing XAS spectra.

"""
from ._version import __version__

from .xasdb import (isXASDataLibrary, XASDataLibrary, XASDBException, Info,
                    Mode, Facility, Beamline, EnergyUnits, Edge, Element,
                    Ligand, Citation, Person, Spectrum_Rating,
                    Suite_Rating, Suite, Sample, Spectrum, fmttime,
                    valid_score, unique_name, None_or_one)


from .creator import make_newdb

def create_xasdb(dbname, server='sqlite', user='',
              password='', port=5432, host=''):
    """create a new XAS Data Library"""
    return make_newdb(dbname,
                      server=server, user=user,
                      password=password, port=port, host=host)

def connect_xasdb(dbname, server='sqlite', user='',
            password='', port=5432, host=''):
    """connect to a XAS Data Library"""
    return XASDataLibrary(dbname,
                          server=server, user=user,
                          password=password, port=port, host=host)
