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
      easy_install sqlalchemy

*******************************************************
"""

try:
    import sqlalchemy
    vers_info = sqlalchemy.__version__.split('.')
    assert int(vers_info[1]) >= 6
    if int(vers_info[1]) == 6:
        assert int(vers_info[2]) >= 5
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


