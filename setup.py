#!/usr/bin/env python
from distutils.core import setup
import sys
import lib

#
no_sqlalchemy="""
*******************************************************
*** WARNING - WARNING - WARNING - WARNING - WARNING ***

       Install or Upgrade SQLAlchemy!

Version 0.6.5 or higher is needed for the xafs database

try:
      easy_install -U sqlalchemy

*******************************************************
"""

try:
    import sqlalchemy
    major, minor, release = [int(i) for i in  sqlalchemy.__version__.split('.')]
    assert major == 0
    assert minor >= 6
    if minor == 6:
        assert release >= 5
    
except:
    print no_sqlalchemy
    sys.exit()
    
setup(name = 'xasdb',
      version = lib.__version__,
      author = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      url         = 'http://xas.org/XasDataLibrary',
      license = 'Public Domain',
      description = 'x-ray absorption spectra library',
      package_dir = {'xasdb': 'lib'},
      packages = ['xasdb','xasdb.wx'])


