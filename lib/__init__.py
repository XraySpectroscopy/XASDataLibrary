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
from . import xdiformat

XDIFile = xdiformat.XDIFile

isXASDataLibrary = xasdb.isXASDataLibrary
isotime2datetime = xasdb.isotime2datetime

Info = xasdb.Info
Mode = xasdb.Mode
Facility = xasdb.Facility
Beamline = xasdb.Beamline
Monochromator = xasdb.Monochromator
EnergyUnits = xasdb.EnergyUnits
Edge = xasdb.Edge
Element = xasdb.Element
Ligand = xasdb.Ligand
CrystalStructure = xasdb.CrystalStructure
Citation = xasdb.Citation
Format = xasdb.Format
Person = xasdb.Person
Spectra_Rating = xasdb.Spectra_Rating
Suite_Rating = xasdb.Suite_Rating
Suite = xasdb.Suite
Sample = xasdb.Sample
Spectra = xasdb.Spectra
XASDataLibrary = xasdb.XASDataLibrary
