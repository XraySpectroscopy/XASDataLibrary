"""
   x-ray absorption spectra database
   Matthew Newville <newville@cars.uchicago.edu>
   CARS, University of Chicago

   last update:  2001-March-06
      
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

__version__ = '0.1.0'

import time
import sys
from . import xasdb
