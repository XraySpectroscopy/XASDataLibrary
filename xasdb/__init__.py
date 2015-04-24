"""
   x-ray absorption spectra database
   Matthew Newville <newville@cars.uchicago.edu>
   CARS, University of Chicago

   last update:  2015-April-24
      
== License:
   To the extent possible, the authors have waived all rights
   granted by copyright law and related laws for the code and
   documentation that make up the XAS Data Library.  While
   information about Authorship may be retained in some files
   for historical reasons, this work is hereby placed in the
   Public Domain.  This work is published from: United States.
   
== Overview:
   The xasdb module provides a python interface to the XAFS Database,
   an SQLite tool for organizing XAS spectra.

"""

__version__ = '0.1.1'

import time
import sys
from .xasdb import isXASDataLibrary, XASDataLibrary
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
