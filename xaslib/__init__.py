"""
   xaslin: X-ray Absorption Spectra Library


== License:
   To the extent possible, the authors have waived all rights
   granted by copyright law and related laws for the code and
   documentation that make up the XAS Data Library.  While
   information about Authorship may be retained in some files
   for historical reasons, this work is hereby placed in the
   Public Domain.  This work is published from: United States.

== Authors:
   Though copyright is waived, the primary authors of this code are:
   Matthew Newville <newville@cars.uchicago.edu>, University of Chicago
   Bruce Ravel <bruce.ravel@nist.gov>, NIST

== Overview:
   The xaslib module provides data and a python interface to a
   relational database (using either SQLite or Postgresql)
   of experimental X-ray Absorption Spectra

"""
from ._version import __version__

from .xaslib import isXASDataLibrary, XASDataLibrary, connect_xaslib
from .creator import create_xaslib
from .webapp import app


# Info, Mode, Facility, Beamline, EnergyUnits, Edge,
# Element, Ligand, Citation, Person, Spectrum_Rating,
# Suite_Rating, Suite, Sample, Spectrum, fmttime,
# valid_score, unique_name, None_or_one)
